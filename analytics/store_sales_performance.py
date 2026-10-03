"""
Store Sales Performance Analysis

Phase 9.6.1

Purpose:
Analyze sales performance for each store.

Metrics:
1. Sales quantity
2. Sales revenue
3. Average selling price
4. Revenue contribution percentage
5. Store ranking
"""

import pandas as pd

from database.connection import engine


# ============================================================
# CONFIGURATION
# ============================================================

BUSINESS_ID = 1
CHUNK_SIZE = 100_000


# ============================================================
# MAIN ANALYSIS
# ============================================================

def analyze_store_sales():

    print("\n" + "=" * 70)
    print("STORE SALES PERFORMANCE ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # SQL query
    # --------------------------------------------------------

    query = """
        SELECT
            store_number,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = 1
    """

    # --------------------------------------------------------
    # Read sales in chunks
    #
    # IMPORTANT:
    # sales contains 12.8M rows.
    # We intentionally DO NOT load the entire table
    # into memory.
    # --------------------------------------------------------

    print("\nProcessing sales data in chunks...")

    store_summary = {}

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
        # Group by store
        # ----------------------------------------------------

        grouped = (
            chunk
            .groupby("store_number")
            .agg(
                sales_quantity=("sales_quantity", "sum"),
                sales_revenue=("sales_dollars", "sum")
            )
        )

        # ----------------------------------------------------
        # Add chunk results to store summary
        # ----------------------------------------------------

        for store_number, row in grouped.iterrows():

            if store_number not in store_summary:

                store_summary[store_number] = {
                    "sales_quantity": 0,
                    "sales_revenue": 0.0
                }

            store_summary[store_number][
                "sales_quantity"
            ] += row["sales_quantity"]

            store_summary[store_number][
                "sales_revenue"
            ] += row["sales_revenue"]

    # --------------------------------------------------------
    # Convert dictionary to DataFrame
    # --------------------------------------------------------

    result = pd.DataFrame.from_dict(
        store_summary,
        orient="index"
    )

    result.index.name = "store_number"

    result = result.reset_index()

    # --------------------------------------------------------
    # Calculate average selling price
    #
    # Revenue / Quantity
    # --------------------------------------------------------

    result["average_selling_price"] = (
        result["sales_revenue"]
        / result["sales_quantity"]
    )

    # --------------------------------------------------------
    # Calculate revenue contribution
    # --------------------------------------------------------

    total_revenue = result[
        "sales_revenue"
    ].sum()

    result["revenue_contribution_pct"] = (
        result["sales_revenue"]
        / total_revenue
        * 100
    )

    # --------------------------------------------------------
    # Rank stores by sales revenue
    # --------------------------------------------------------

    result["revenue_rank"] = (
        result["sales_revenue"]
        .rank(
            method="dense",
            ascending=False
        )
        .astype(int)
    )

    # --------------------------------------------------------
    # Sort by revenue
    # --------------------------------------------------------

    result = result.sort_values(
        "sales_revenue",
        ascending=False
    )

    # --------------------------------------------------------
    # Display overall verification
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("VERIFICATION")
    print("-" * 70)

    print(
        f"Sales rows processed: "
        f"{total_rows:,}"
    )

    print(
        f"Stores represented: "
        f"{len(result):,}"
    )

    print(
        f"Total sales quantity: "
        f"{result['sales_quantity'].sum():,.0f}"
    )

    print(
        f"Total sales revenue: "
        f"${result['sales_revenue'].sum():,.2f}"
    )

    # --------------------------------------------------------
    # Display top 10 stores
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("TOP 10 STORES BY SALES REVENUE")
    print("-" * 70)

    top_10 = result.head(10)

    for _, row in top_10.iterrows():

        print(
            f"Rank {row['revenue_rank']:>2} | "
            f"Store {int(row['store_number']):>3} | "
            f"Quantity: {row['sales_quantity']:>10,.0f} | "
            f"Revenue: ${row['sales_revenue']:>15,.2f} | "
            f"ASP: ${row['average_selling_price']:>7.2f} | "
            f"Contribution: "
            f"{row['revenue_contribution_pct']:>6.2f}%"
        )

    # --------------------------------------------------------
    # Display bottom 10 stores
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("BOTTOM 10 STORES BY SALES REVENUE")
    print("-" * 70)

    bottom_10 = result.tail(10).sort_values(
        "sales_revenue"
    )

    for _, row in bottom_10.iterrows():

        print(
            f"Store {int(row['store_number']):>3} | "
            f"Quantity: {row['sales_quantity']:>10,.0f} | "
            f"Revenue: ${row['sales_revenue']:>15,.2f} | "
            f"ASP: ${row['average_selling_price']:>7.2f} | "
            f"Contribution: "
            f"{row['revenue_contribution_pct']:>6.2f}%"
        )

    # --------------------------------------------------------
    # Concentration analysis
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("STORE REVENUE CONCENTRATION")
    print("-" * 70)

    for n in [5, 10, 20]:

        top_n_revenue = result.head(n)[
            "sales_revenue"
        ].sum()

        contribution = (
            top_n_revenue
            / total_revenue
            * 100
        )

        print(
            f"Top {n} stores: "
            f"${top_n_revenue:,.2f} "
            f"({contribution:.2f}%)"
        )

    # --------------------------------------------------------
    # Average selling price
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("AVERAGE SELLING PRICE")
    print("-" * 70)

    highest_asp = result.sort_values(
        "average_selling_price",
        ascending=False
    ).head(5)

    print("\nHighest average selling price:")

    for _, row in highest_asp.iterrows():

        print(
            f"Store {int(row['store_number'])}: "
            f"${row['average_selling_price']:.2f}"
        )

    lowest_asp = result.sort_values(
        "average_selling_price"
    ).head(5)

    print("\nLowest average selling price:")

    for _, row in lowest_asp.iterrows():

        print(
            f"Store {int(row['store_number'])}: "
            f"${row['average_selling_price']:.2f}"
        )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    expected_quantity = 32_917_876
    expected_revenue = 452_062_952.02

    actual_quantity = result[
        "sales_quantity"
    ].sum()

    actual_revenue = result[
        "sales_revenue"
    ].sum()

    print("\n" + "-" * 70)
    print("FINAL VALIDATION")
    print("-" * 70)

    if actual_quantity == expected_quantity:

        print("✓ Sales quantity verification passed.")

    else:

        print(
            "✗ Sales quantity verification failed."
        )

    if abs(
        actual_revenue - expected_revenue
    ) < 0.01:

        print("✓ Sales revenue verification passed.")

    else:

        print(
            "✗ Sales revenue verification failed."
        )

    if len(result) == 80:

        print(
            "✓ Store count verification passed: 80 stores."
        )

    else:

        print(
            f"✗ Store count verification failed: "
            f"{len(result)}"
        )

    print("\n" + "=" * 70)
    print("STORE SALES PERFORMANCE ANALYSIS COMPLETED")
    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    analyze_store_sales()