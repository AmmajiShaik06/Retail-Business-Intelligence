"""
Store Performance Segmentation

Segments stores using:
1. Sales revenue
2. Purchase spending

Baseline:
- Median sales revenue
- Median purchase spending

Segments:
- High Sales / High Purchase
- High Sales / Lower Purchase
- Lower Sales / High Purchase
- Lower Sales / Lower Purchase

This analysis is descriptive.
It does not rank stores as good or bad.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1


# ============================================================
# 1. LOAD STORE SALES DATA
# ============================================================

def load_store_sales():

    print("\nLoading store sales data...")

    query = """
        SELECT
            store_number,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = %s
    """

    chunks = []

    for chunk in pd.read_sql(
        query,
        con=engine,
        params=(BUSINESS_ID,),
        chunksize=100_000
    ):

        grouped = (
            chunk
            .groupby("store_number", as_index=False)
            .agg(
                sales_quantity=("sales_quantity", "sum"),
                sales_revenue=("sales_dollars", "sum")
            )
        )

        chunks.append(grouped)

    store_sales = pd.concat(
        chunks,
        ignore_index=True
    )

    store_sales = (
        store_sales
        .groupby("store_number", as_index=False)
        .agg(
            sales_quantity=("sales_quantity", "sum"),
            sales_revenue=("sales_revenue", "sum")
        )
    )

    print(
        f"Stores with sales data: "
        f"{len(store_sales):,}"
    )

    return store_sales


# ============================================================
# 2. LOAD STORE PURCHASE DATA
# ============================================================

def load_store_purchases():

    print("\nLoading store purchase data...")

    query = """
        SELECT
            store_number,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = %s
    """

    chunks = []

    for chunk in pd.read_sql(
        query,
        con=engine,
        params=(BUSINESS_ID,),
        chunksize=100_000
    ):

        grouped = (
            chunk
            .groupby("store_number", as_index=False)
            .agg(
                purchase_quantity=("quantity", "sum"),
                purchase_spending=("dollars", "sum")
            )
        )

        chunks.append(grouped)

    store_purchases = pd.concat(
        chunks,
        ignore_index=True
    )

    store_purchases = (
        store_purchases
        .groupby("store_number", as_index=False)
        .agg(
            purchase_quantity=("purchase_quantity", "sum"),
            purchase_spending=("purchase_spending", "sum")
        )
    )

    print(
        f"Stores with purchase data: "
        f"{len(store_purchases):,}"
    )

    return store_purchases


# ============================================================
# 3. COMBINE SALES AND PURCHASES
# ============================================================

def combine_store_data(
    store_sales,
    store_purchases
):

    print("\nCombining store sales and purchase data...")

    store_data = pd.merge(
        store_sales,
        store_purchases,
        on="store_number",
        how="outer"
    )

    numeric_columns = [
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending"
    ]

    for column in numeric_columns:

        store_data[column] = (
            store_data[column]
            .fillna(0)
        )

    # --------------------------------------------------------
    # Quantity difference
    # --------------------------------------------------------

    store_data["quantity_difference"] = (
        store_data["sales_quantity"]
        - store_data["purchase_quantity"]
    )

    # --------------------------------------------------------
    # Sales contribution
    # --------------------------------------------------------

    total_sales = store_data["sales_revenue"].sum()

    store_data["sales_contribution_pct"] = (
        store_data["sales_revenue"]
        / total_sales
        * 100
    )

    # --------------------------------------------------------
    # Purchase contribution
    # --------------------------------------------------------

    total_purchase = store_data["purchase_spending"].sum()

    store_data["purchase_contribution_pct"] = (
        store_data["purchase_spending"]
        / total_purchase
        * 100
    )

    return store_data


# ============================================================
# 4. CREATE STORE SEGMENTS
# ============================================================

def create_segments(store_data):

    print("\nCreating store performance segments...")

    sales_median = store_data[
        "sales_revenue"
    ].median()

    purchase_median = store_data[
        "purchase_spending"
    ].median()

    print(
        f"\nSales revenue median: "
        f"${sales_median:,.2f}"
    )

    print(
        f"Purchase spending median: "
        f"${purchase_median:,.2f}"
    )

    # --------------------------------------------------------
    # Segment function
    # --------------------------------------------------------

    def assign_segment(row):

        high_sales = (
            row["sales_revenue"]
            >= sales_median
        )

        high_purchase = (
            row["purchase_spending"]
            >= purchase_median
        )

        if high_sales and high_purchase:

            return "High Sales / High Purchase"

        elif high_sales and not high_purchase:

            return "High Sales / Lower Purchase"

        elif not high_sales and high_purchase:

            return "Lower Sales / High Purchase"

        else:

            return "Lower Sales / Lower Purchase"

    store_data["segment"] = store_data.apply(
        assign_segment,
        axis=1
    )

    return store_data


# ============================================================
# 5. DISPLAY SEGMENT SUMMARY
# ============================================================

def display_segment_summary(
    store_data
):

    print("\n" + "=" * 70)
    print("STORE PERFORMANCE SEGMENTATION")
    print("=" * 70)

    summary = (
        store_data
        .groupby("segment")
        .agg(
            store_count=("store_number", "count"),
            sales_revenue=("sales_revenue", "sum"),
            purchase_spending=("purchase_spending", "sum"),
            sales_quantity=("sales_quantity", "sum"),
            purchase_quantity=("purchase_quantity", "sum")
        )
        .reset_index()
    )

    total_sales = store_data[
        "sales_revenue"
    ].sum()

    total_purchase = store_data[
        "purchase_spending"
    ].sum()

    summary["sales_contribution_pct"] = (
        summary["sales_revenue"]
        / total_sales
        * 100
    )

    summary["purchase_contribution_pct"] = (
        summary["purchase_spending"]
        / total_purchase
        * 100
    )

    print("\nSegment Summary:\n")

    print(
        summary.to_string(
            index=False,
            formatters={
                "sales_revenue":
                    lambda x: f"${x:,.2f}",

                "purchase_spending":
                    lambda x: f"${x:,.2f}",

                "sales_contribution_pct":
                    lambda x: f"{x:.2f}%",

                "purchase_contribution_pct":
                    lambda x: f"{x:.2f}%"
            }
        )
    )

    # --------------------------------------------------------
    # Store count verification
    # --------------------------------------------------------

    print(
        f"\nTotal stores: "
        f"{len(store_data):,}"
    )

    print(
        f"Stores assigned to segments: "
        f"{store_data['segment'].notna().sum():,}"
    )

    # --------------------------------------------------------
    # Top stores in each segment
    # --------------------------------------------------------

    segments = [
        "High Sales / High Purchase",
        "High Sales / Lower Purchase",
        "Lower Sales / High Purchase",
        "Lower Sales / Lower Purchase"
    ]

    for segment in segments:

        segment_data = (
            store_data[
                store_data["segment"] == segment
            ]
            .sort_values(
                "sales_revenue",
                ascending=False
            )
            .head(5)
        )

        print(
            f"\n{segment} — Top Stores:"
        )

        if len(segment_data) == 0:

            print("No stores in this segment.")

            continue

        print(
            segment_data[
                [
                    "store_number",
                    "sales_revenue",
                    "purchase_spending",
                    "quantity_difference"
                ]
            ].to_string(
                index=False,
                formatters={
                    "sales_revenue":
                        lambda x: f"${x:,.2f}",

                    "purchase_spending":
                        lambda x: f"${x:,.2f}"
                }
            )
        )

    return summary


# ============================================================
# 6. VERIFY RESULTS
# ============================================================

def verify_results(
    store_data
):

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Store count
    # --------------------------------------------------------

    assert len(store_data) == 80

    print(
        "✓ Store count verified: 80"
    )

    # --------------------------------------------------------
    # Sales revenue
    # --------------------------------------------------------

    sales_total = store_data[
        "sales_revenue"
    ].sum()

    expected_sales = 452_062_952.02

    assert abs(
        sales_total - expected_sales
    ) < 0.01

    print(
        "✓ Sales revenue verified: "
        f"${sales_total:,.2f}"
    )

    # --------------------------------------------------------
    # Purchase spending
    # --------------------------------------------------------

    purchase_total = store_data[
        "purchase_spending"
    ].sum()

    expected_purchase = 321_900_765.53

    assert abs(
        purchase_total - expected_purchase
    ) < 0.01

    print(
        "✓ Purchase spending verified: "
        f"${purchase_total:,.2f}"
    )

    # --------------------------------------------------------
    # Sales quantity
    # --------------------------------------------------------

    sales_quantity = store_data[
        "sales_quantity"
    ].sum()

    expected_sales_quantity = 32_917_876

    assert sales_quantity == expected_sales_quantity

    print(
        "✓ Sales quantity verified: "
        f"{sales_quantity:,}"
    )

    # --------------------------------------------------------
    # Purchase quantity
    # --------------------------------------------------------

    purchase_quantity = store_data[
        "purchase_quantity"
    ].sum()

    expected_purchase_quantity = 33_584_377

    assert purchase_quantity == expected_purchase_quantity

    print(
        "✓ Purchase quantity verified: "
        f"{purchase_quantity:,}"
    )

    # --------------------------------------------------------
    # Segment assignment
    # --------------------------------------------------------

    assert (
        store_data["segment"].notna().all()
    )

    print(
        "✓ Every store assigned to a segment"
    )

    # --------------------------------------------------------
    # Segment count
    # --------------------------------------------------------

    segment_count = (
        store_data["segment"]
        .nunique()
    )

    assert segment_count <= 4

    print(
        f"✓ Number of segments: "
        f"{segment_count}"
    )

    print(
        "\n✓ ALL STORE SEGMENTATION "
        "CHECKS PASSED"
    )


# ============================================================
# 7. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("STORE PERFORMANCE SEGMENTATION")
    print("=" * 70)

    # Load existing fact data
    store_sales = load_store_sales()

    store_purchases = load_store_purchases()

    # Combine
    store_data = combine_store_data(
        store_sales,
        store_purchases
    )

    # Create segments
    store_data = create_segments(
        store_data
    )

    # Display results
    display_segment_summary(
        store_data
    )

    # Verify
    verify_results(
        store_data
    )

    print("\n" + "=" * 70)
    print("STORE PERFORMANCE SEGMENTATION COMPLETED")
    print("=" * 70)