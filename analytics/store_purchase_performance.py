"""
Store Purchase Performance Analysis

Phase 9.6.2

Purpose:
Analyze purchase performance for each store.

Metrics:
1. Purchase quantity
2. Purchase spending
3. Average purchase price
4. Spending contribution percentage
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

def analyze_store_purchases():

    print("\n" + "=" * 70)
    print("STORE PURCHASE PERFORMANCE ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # SQL query
    # --------------------------------------------------------

    query = """
        SELECT
            store_number,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = 1
    """

    # --------------------------------------------------------
    # Read purchases in chunks
    #
    # IMPORTANT:
    # purchases contains 2.37M rows.
    # We process it in chunks to control memory usage.
    # --------------------------------------------------------

    print("\nProcessing purchase data in chunks...")

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
        # Group purchases by store
        # ----------------------------------------------------

        grouped = (
            chunk
            .groupby("store_number")
            .agg(
                purchase_quantity=("quantity", "sum"),
                purchase_spending=("dollars", "sum")
            )
        )

        # ----------------------------------------------------
        # Add chunk results to store summary
        # ----------------------------------------------------

        for store_number, row in grouped.iterrows():

            if store_number not in store_summary:

                store_summary[store_number] = {
                    "purchase_quantity": 0,
                    "purchase_spending": 0.0
                }

            store_summary[store_number][
                "purchase_quantity"
            ] += row["purchase_quantity"]

            store_summary[store_number][
                "purchase_spending"
            ] += row["purchase_spending"]

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
    # Calculate average purchase price
    #
    # Spending / Quantity
    # --------------------------------------------------------

    result["average_purchase_price"] = (
        result["purchase_spending"]
        / result["purchase_quantity"]
    )

    # --------------------------------------------------------
    # Calculate spending contribution
    # --------------------------------------------------------

    total_spending = result[
        "purchase_spending"
    ].sum()

    result["spending_contribution_pct"] = (
        result["purchase_spending"]
        / total_spending
        * 100
    )

    # --------------------------------------------------------
    # Rank stores by purchase spending
    # --------------------------------------------------------

    result["spending_rank"] = (
        result["purchase_spending"]
        .rank(
            method="dense",
            ascending=False
        )
        .astype(int)
    )

    # --------------------------------------------------------
    # Sort by spending
    # --------------------------------------------------------

    result = result.sort_values(
        "purchase_spending",
        ascending=False
    )

    # --------------------------------------------------------
    # Overall verification
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("VERIFICATION")
    print("-" * 70)

    print(
        f"Purchase rows processed: "
        f"{total_rows:,}"
    )

    print(
        f"Stores represented: "
        f"{len(result):,}"
    )

    print(
        f"Total purchase quantity: "
        f"{result['purchase_quantity'].sum():,.0f}"
    )

    print(
        f"Total purchase spending: "
        f"${result['purchase_spending'].sum():,.2f}"
    )

    # --------------------------------------------------------
    # Top 10 stores
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("TOP 10 STORES BY PURCHASE SPENDING")
    print("-" * 70)

    top_10 = result.head(10)

    for _, row in top_10.iterrows():

        print(
            f"Rank {row['spending_rank']:>2} | "
            f"Store {int(row['store_number']):>3} | "
            f"Quantity: {row['purchase_quantity']:>10,.0f} | "
            f"Spending: ${row['purchase_spending']:>15,.2f} | "
            f"APP: ${row['average_purchase_price']:>7.2f} | "
            f"Contribution: "
            f"{row['spending_contribution_pct']:>6.2f}%"
        )

    # --------------------------------------------------------
    # Bottom 10 stores
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("BOTTOM 10 STORES BY PURCHASE SPENDING")
    print("-" * 70)

    bottom_10 = result.tail(10).sort_values(
        "purchase_spending"
    )

    for _, row in bottom_10.iterrows():

        print(
            f"Store {int(row['store_number']):>3} | "
            f"Quantity: {row['purchase_quantity']:>10,.0f} | "
            f"Spending: ${row['purchase_spending']:>15,.2f} | "
            f"APP: ${row['average_purchase_price']:>7.2f} | "
            f"Contribution: "
            f"{row['spending_contribution_pct']:>6.2f}%"
        )

    # --------------------------------------------------------
    # Purchase spending concentration
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("STORE PURCHASE SPENDING CONCENTRATION")
    print("-" * 70)

    for n in [5, 10, 20]:

        top_n_spending = result.head(n)[
            "purchase_spending"
        ].sum()

        contribution = (
            top_n_spending
            / total_spending
            * 100
        )

        print(
            f"Top {n} stores: "
            f"${top_n_spending:,.2f} "
            f"({contribution:.2f}%)"
        )

    # --------------------------------------------------------
    # Average purchase price
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("AVERAGE PURCHASE PRICE")
    print("-" * 70)

    highest_app = result.sort_values(
        "average_purchase_price",
        ascending=False
    ).head(5)

    print("\nHighest average purchase price:")

    for _, row in highest_app.iterrows():

        print(
            f"Store {int(row['store_number'])}: "
            f"${row['average_purchase_price']:.2f}"
        )

    lowest_app = result.sort_values(
        "average_purchase_price"
    ).head(5)

    print("\nLowest average purchase price:")

    for _, row in lowest_app.iterrows():

        print(
            f"Store {int(row['store_number'])}: "
            f"${row['average_purchase_price']:.2f}"
        )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    expected_quantity = 33_584_377
    expected_spending = 321_900_765.53

    actual_quantity = result[
        "purchase_quantity"
    ].sum()

    actual_spending = result[
        "purchase_spending"
    ].sum()

    print("\n" + "-" * 70)
    print("FINAL VALIDATION")
    print("-" * 70)

    if actual_quantity == expected_quantity:

        print(
            "✓ Purchase quantity verification passed."
        )

    else:

        print(
            "✗ Purchase quantity verification failed."
        )

    if abs(
        actual_spending - expected_spending
    ) < 0.01:

        print(
            "✓ Purchase spending verification passed."
        )

    else:

        print(
            "✗ Purchase spending verification failed."
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
    print("STORE PURCHASE PERFORMANCE ANALYSIS COMPLETED")
    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    analyze_store_purchases()