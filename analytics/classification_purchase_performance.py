"""
Classification Purchase Performance Analysis

Analyzes purchase performance by product classification.

This script:
1. Reads purchases from MySQL in chunks.
2. Aggregates purchase quantity and spending by classification.
3. Calculates average purchase price.
4. Calculates spending contribution.
5. Shows top classifications.
6. Verifies totals against the purchases table.

Memory-safe:
Purchases are processed in chunks instead of loading
all 2.37M rows into memory at once.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 250_000


# ============================================================
# 1. LOAD PURCHASE DATA IN CHUNKS
# ============================================================

def load_purchases_by_classification():

    print("\n" + "=" * 70)
    print("CLASSIFICATION PURCHASE PERFORMANCE")
    print("=" * 70)

    print("\nProcessing purchase data in chunks...")

    query = """
        SELECT
            classification,
            quantity,
            dollars
        FROM purchases
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
                purchase_quantity=("quantity", "sum"),
                purchase_spending=("dollars", "sum")
            )
            .reset_index()
        )

        classification_results.append(
            grouped
        )

    print(
        f"\nTotal purchase rows processed: "
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
            purchase_quantity=("purchase_quantity", "sum"),
            purchase_spending=("purchase_spending", "sum")
        )
    )

    # --------------------------------------------------------
    # Calculate average purchase price
    # --------------------------------------------------------

    final["average_purchase_price"] = (
        final["purchase_spending"]
        / final["purchase_quantity"]
    )

    # --------------------------------------------------------
    # Calculate spending contribution
    # --------------------------------------------------------

    total_spending = final["purchase_spending"].sum()

    final["spending_contribution_pct"] = (
        final["purchase_spending"]
        / total_spending
        * 100
    )

    # --------------------------------------------------------
    # Sort by spending
    # --------------------------------------------------------

    final = final.sort_values(
        "purchase_spending",
        ascending=False
    ).reset_index(drop=True)

    return final


# ============================================================
# 3. DISPLAY RESULTS
# ============================================================

def display_results(final):

    print("\n" + "=" * 70)
    print("CLASSIFICATION PURCHASE SUMMARY")
    print("=" * 70)

    print(
        f"\nNumber of classifications: "
        f"{len(final):,}"
    )

    print(
        f"Total purchase quantity: "
        f"{final['purchase_quantity'].sum():,}"
    )

    print(
        f"Total purchase spending: "
        f"${final['purchase_spending'].sum():,.2f}"
    )

    # --------------------------------------------------------
    # Top classifications by spending
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("TOP 10 CLASSIFICATIONS BY PURCHASE SPENDING")
    print("-" * 70)

    top_spending = final.head(10)

    for index, row in top_spending.iterrows():

        print(
            f"{index + 1}. "
            f"{row['classification']} | "
            f"Qty: {row['purchase_quantity']:,.0f} | "
            f"Spending: ${row['purchase_spending']:,.2f} | "
            f"APP: ${row['average_purchase_price']:.2f} | "
            f"Contribution: "
            f"{row['spending_contribution_pct']:.2f}%"
        )

    # --------------------------------------------------------
    # Top classifications by quantity
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("TOP 10 CLASSIFICATIONS BY PURCHASE QUANTITY")
    print("-" * 70)

    top_quantity = (
        final
        .sort_values(
            "purchase_quantity",
            ascending=False
        )
        .head(10)
    )

    for index, row in top_quantity.iterrows():

        print(
            f"{index + 1}. "
            f"{row['classification']} | "
            f"Qty: {row['purchase_quantity']:,.0f} | "
            f"Spending: ${row['purchase_spending']:,.2f} | "
            f"APP: ${row['average_purchase_price']:.2f}"
        )

    # --------------------------------------------------------
    # Highest average purchase price
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("TOP 10 CLASSIFICATIONS BY AVERAGE PURCHASE PRICE")
    print("-" * 70)

    top_app = (
        final
        .sort_values(
            "average_purchase_price",
            ascending=False
        )
        .head(10)
    )

    for index, row in top_app.iterrows():

        print(
            f"{index + 1}. "
            f"{row['classification']} | "
            f"APP: ${row['average_purchase_price']:.2f} | "
            f"Qty: {row['purchase_quantity']:,.0f} | "
            f"Spending: ${row['purchase_spending']:,.2f}"
        )


# ============================================================
# 4. CONCENTRATION ANALYSIS
# ============================================================

def concentration_analysis(final):

    print("\n" + "=" * 70)
    print("CLASSIFICATION PURCHASE SPENDING CONCENTRATION")
    print("=" * 70)

    total_spending = final["purchase_spending"].sum()

    for n in [3, 5, 10]:

        contribution = (
            final
            .head(n)["purchase_spending"]
            .sum()
            / total_spending
            * 100
        )

        print(
            f"Top {n} classifications: "
            f"{contribution:.2f}% of total purchase spending"
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
            SUM(quantity) AS total_quantity,
            SUM(dollars) AS total_spending
        FROM purchases
        WHERE business_id = 1
    """

    with engine.connect() as connection:

        result = connection.exec_driver_sql(
            verification_query
        ).fetchone()

    expected_rows = result[0]
    expected_quantity = result[1]
    expected_spending = float(result[2])

    # --------------------------------------------------------
    # Classification totals
    # --------------------------------------------------------

    actual_quantity = final["purchase_quantity"].sum()
    actual_spending = final["purchase_spending"].sum()

    # --------------------------------------------------------
    # Verify quantity
    # --------------------------------------------------------

    quantity_passed = (
        actual_quantity == expected_quantity
    )

    print(
        "Purchase quantity verification: "
        f"{'PASSED' if quantity_passed else 'FAILED'}"
    )

    print(
        f"Expected quantity: {expected_quantity:,}"
    )

    print(
        f"Classification quantity: {actual_quantity:,}"
    )

    # --------------------------------------------------------
    # Verify spending
    # --------------------------------------------------------

    spending_passed = (
        abs(actual_spending - expected_spending)
        < 0.01
    )

    print(
        "Purchase spending verification: "
        f"{'PASSED' if spending_passed else 'FAILED'}"
    )

    print(
        f"Expected spending: ${expected_spending:,.2f}"
    )

    print(
        f"Classification spending: "
        f"${actual_spending:,.2f}"
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
        and spending_passed
        and classification_count > 0
    ):

        print(
            "\n✓ ALL CLASSIFICATION PURCHASE "
            "VERIFICATION CHECKS PASSED"
        )

    else:

        raise ValueError(
            "\n✗ CLASSIFICATION PURCHASE "
            "VERIFICATION FAILED"
        )


# ============================================================
# 6. MAIN
# ============================================================

if __name__ == "__main__":

    classification_results = (
        load_purchases_by_classification()
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
        "CLASSIFICATION PURCHASE PERFORMANCE "
        "ANALYSIS COMPLETED"
    )
    print("=" * 70)