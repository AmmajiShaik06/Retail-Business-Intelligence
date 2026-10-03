"""
Classification Sales Performance Analysis

Analyzes sales performance by product classification.

This script:
1. Reads sales data from MySQL in chunks.
2. Aggregates sales quantity and revenue by classification.
3. Calculates average selling price.
4. Calculates revenue contribution.
5. Shows top classifications.
6. Verifies totals against the sales table.

Memory-safe:
Sales data is processed in chunks instead of loading
all 12.8M rows into memory at once.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 250_000


# ============================================================
# 1. LOAD SALES DATA IN CHUNKS
# ============================================================

def load_sales_by_classification():

    print("\n" + "=" * 70)
    print("CLASSIFICATION SALES PERFORMANCE")
    print("=" * 70)

    print("\nProcessing sales data in chunks...")

    query = """
        SELECT
            classification,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = 1
    """

    classification_results = []

    total_rows = 0

    for chunk_number, chunk in enumerate(
        pd.read_sql(
            query,
            con=engine,
            chunksize=CHUNK_SIZE
        ),
        start=1
    ):

        total_rows += len(chunk)

        print(
            f"Processing chunk {chunk_number}: "
            f"{len(chunk):,} rows"
        )

        # ----------------------------------------------------
        # Clean classification
        # ----------------------------------------------------

        chunk["classification"] = (
            chunk["classification"]
            .astype("string")
            .str.strip()
        )

        # ----------------------------------------------------
        # Remove rows where classification is missing
        # ----------------------------------------------------

        chunk = chunk.dropna(
            subset=["classification"]
        )

        # ----------------------------------------------------
        # Aggregate by classification
        # ----------------------------------------------------

        grouped = (
            chunk
            .groupby("classification", dropna=False)
            .agg(
                sales_quantity=("sales_quantity", "sum"),
                sales_revenue=("sales_dollars", "sum")
            )
            .reset_index()
        )

        classification_results.append(
            grouped
        )

    print(
        f"\nTotal sales rows processed: "
        f"{total_rows:,}"
    )

    return classification_results


# ============================================================
# 2. COMBINE CHUNK RESULTS
# ============================================================

def combine_results(classification_results):

    print("\nCombining classification results...")

    combined = pd.concat(
        classification_results,
        ignore_index=True
    )

    final = (
        combined
        .groupby("classification", as_index=False)
        .agg(
            sales_quantity=("sales_quantity", "sum"),
            sales_revenue=("sales_revenue", "sum")
        )
    )

    # --------------------------------------------------------
    # Calculate average selling price
    # --------------------------------------------------------

    final["average_selling_price"] = (
        final["sales_revenue"]
        / final["sales_quantity"]
    )

    # --------------------------------------------------------
    # Calculate revenue contribution
    # --------------------------------------------------------

    total_revenue = final["sales_revenue"].sum()

    final["revenue_contribution_pct"] = (
        final["sales_revenue"]
        / total_revenue
        * 100
    )

    # --------------------------------------------------------
    # Sort by revenue
    # --------------------------------------------------------

    final = final.sort_values(
        "sales_revenue",
        ascending=False
    ).reset_index(drop=True)

    return final


# ============================================================
# 3. DISPLAY RESULTS
# ============================================================

def display_results(final):

    print("\n" + "=" * 70)
    print("CLASSIFICATION SALES SUMMARY")
    print("=" * 70)

    print(
        f"\nNumber of classifications: "
        f"{len(final):,}"
    )

    print(
        f"Total sales quantity: "
        f"{final['sales_quantity'].sum():,}"
    )

    print(
        f"Total sales revenue: "
        f"${final['sales_revenue'].sum():,.2f}"
    )

    # --------------------------------------------------------
    # Top classifications by revenue
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("TOP 10 CLASSIFICATIONS BY SALES REVENUE")
    print("-" * 70)

    top_revenue = final.head(10)

    for index, row in top_revenue.iterrows():

        print(
            f"{index + 1}. "
            f"{row['classification']} | "
            f"Qty: {row['sales_quantity']:,.0f} | "
            f"Revenue: ${row['sales_revenue']:,.2f} | "
            f"ASP: ${row['average_selling_price']:.2f} | "
            f"Contribution: "
            f"{row['revenue_contribution_pct']:.2f}%"
        )

    # --------------------------------------------------------
    # Top classifications by quantity
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("TOP 10 CLASSIFICATIONS BY SALES QUANTITY")
    print("-" * 70)

    top_quantity = (
        final
        .sort_values(
            "sales_quantity",
            ascending=False
        )
        .head(10)
    )

    for index, row in top_quantity.iterrows():

        print(
            f"{index + 1}. "
            f"{row['classification']} | "
            f"Qty: {row['sales_quantity']:,.0f} | "
            f"Revenue: ${row['sales_revenue']:,.2f} | "
            f"ASP: ${row['average_selling_price']:.2f}"
        )

    # --------------------------------------------------------
    # Highest average selling price
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("TOP 10 CLASSIFICATIONS BY AVERAGE SELLING PRICE")
    print("-" * 70)

    top_asp = (
        final
        .sort_values(
            "average_selling_price",
            ascending=False
        )
        .head(10)
    )

    for index, row in top_asp.iterrows():

        print(
            f"{index + 1}. "
            f"{row['classification']} | "
            f"ASP: ${row['average_selling_price']:.2f} | "
            f"Qty: {row['sales_quantity']:,.0f} | "
            f"Revenue: ${row['sales_revenue']:,.2f}"
        )


# ============================================================
# 4. CONCENTRATION ANALYSIS
# ============================================================

def concentration_analysis(final):

    print("\n" + "=" * 70)
    print("CLASSIFICATION REVENUE CONCENTRATION")
    print("=" * 70)

    total_revenue = final["sales_revenue"].sum()

    for n in [3, 5, 10]:

        contribution = (
            final
            .head(n)["sales_revenue"]
            .sum()
            / total_revenue
            * 100
        )

        print(
            f"Top {n} classifications: "
            f"{contribution:.2f}% of total sales revenue"
        )


# ============================================================
# 5. VERIFICATION
# ============================================================

def verify_results(final):

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Expected totals from database
    # --------------------------------------------------------

    verification_query = """
        SELECT
            COUNT(*) AS total_rows,
            SUM(sales_quantity) AS total_quantity,
            SUM(sales_dollars) AS total_revenue
        FROM sales
        WHERE business_id = 1
    """

    with engine.connect() as connection:

        result = connection.exec_driver_sql(
            verification_query
        ).fetchone()

    expected_rows = result[0]
    expected_quantity = result[1]
    expected_revenue = float(result[2])

    # --------------------------------------------------------
    # Classification totals
    # --------------------------------------------------------

    actual_quantity = final["sales_quantity"].sum()
    actual_revenue = final["sales_revenue"].sum()

    # --------------------------------------------------------
    # Verify quantity
    # --------------------------------------------------------

    quantity_passed = (
        actual_quantity == expected_quantity
    )

    print(
        "Sales quantity verification: "
        f"{'PASSED' if quantity_passed else 'FAILED'}"
    )

    print(
        f"Expected quantity: {expected_quantity:,}"
    )

    print(
        f"Classification quantity: {actual_quantity:,}"
    )

    # --------------------------------------------------------
    # Verify revenue
    # --------------------------------------------------------

    revenue_passed = (
        abs(actual_revenue - expected_revenue)
        < 0.01
    )

    print(
        "Sales revenue verification: "
        f"{'PASSED' if revenue_passed else 'FAILED'}"
    )

    print(
        f"Expected revenue: ${expected_revenue:,.2f}"
    )

    print(
        f"Classification revenue: "
        f"${actual_revenue:,.2f}"
    )

    # --------------------------------------------------------
    # Verify classification count
    # --------------------------------------------------------

    classification_count = len(final)

    print(
        f"\nClassifications identified: "
        f"{classification_count:,}"
    )

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    if (
        quantity_passed
        and revenue_passed
        and classification_count > 0
    ):

        print(
            "\n✓ ALL CLASSIFICATION SALES "
            "VERIFICATION CHECKS PASSED"
        )

    else:

        raise ValueError(
            "\n✗ CLASSIFICATION SALES "
            "VERIFICATION FAILED"
        )


# ============================================================
# 6. MAIN
# ============================================================

if __name__ == "__main__":

    classification_results = (
        load_sales_by_classification()
    )

    final = combine_results(
        classification_results
    )

    display_results(
        final
    )

    concentration_analysis(
        final
    )

    verify_results(
        final
    )

    print("\n" + "=" * 70)
    print(
        "CLASSIFICATION SALES PERFORMANCE "
        "ANALYSIS COMPLETED"
    )
    print("=" * 70)