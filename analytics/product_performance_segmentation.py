import pandas as pd
from sqlalchemy import text

from database.connection import engine


BUSINESS_ID = 1

PURCHASE_CHUNK_SIZE = 50_000
SALES_RANGE_SIZE = 250_000


# ============================================================
# PURCHASE SUMMARY BY PRODUCT
# ============================================================

def load_purchase_summary():

    print("\n" + "=" * 70)
    print("ANALYZING PURCHASES BY PRODUCT")
    print("=" * 70)

    query = """
        SELECT
            brand,
            description,
            size,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = :business_id
    """

    results = []
    total_rows = 0

    with engine.connect() as connection:

        for chunk in pd.read_sql(
            text(query),
            connection,
            params={"business_id": BUSINESS_ID},
            chunksize=PURCHASE_CHUNK_SIZE
        ):

            chunk["quantity"] = pd.to_numeric(
                chunk["quantity"],
                errors="coerce"
            )

            chunk["dollars"] = pd.to_numeric(
                chunk["dollars"],
                errors="coerce"
            )

            grouped = (
                chunk
                .groupby(
                    [
                        "brand",
                        "description",
                        "size"
                    ],
                    dropna=False
                )
                .agg(
                    purchase_quantity=(
                        "quantity",
                        "sum"
                    ),
                    purchase_amount=(
                        "dollars",
                        "sum"
                    )
                )
                .reset_index()
            )

            results.append(grouped)

            total_rows += len(chunk)

            print(
                f"Purchase rows processed: "
                f"{total_rows:,}"
            )

    summary = (
        pd.concat(
            results,
            ignore_index=True
        )
        .groupby(
            [
                "brand",
                "description",
                "size"
            ],
            dropna=False
        )
        .agg(
            purchase_quantity=(
                "purchase_quantity",
                "sum"
            ),
            purchase_amount=(
                "purchase_amount",
                "sum"
            )
        )
        .reset_index()
    )

    return summary, total_rows


# ============================================================
# SALES SUMMARY BY PRODUCT
# ============================================================

def load_sales_summary():

    print("\n" + "=" * 70)
    print("ANALYZING SALES BY PRODUCT")
    print("=" * 70)

    range_query = """
        SELECT
            MIN(sales_id) AS min_id,
            MAX(sales_id) AS max_id,
            COUNT(*) AS total_rows
        FROM sales
        WHERE business_id = :business_id
    """

    with engine.connect() as connection:

        result = connection.execute(
            text(range_query),
            {
                "business_id": BUSINESS_ID
            }
        ).fetchone()

    min_id = int(result.min_id)
    max_id = int(result.max_id)
    expected_rows = int(result.total_rows)

    print(
        f"Sales ID range: "
        f"{min_id:,} to {max_id:,}"
    )

    print(
        f"Expected sales rows: "
        f"{expected_rows:,}"
    )

    results = []
    total_rows = 0
    current_id = min_id

    while current_id <= max_id:

        end_id = min(
            current_id + SALES_RANGE_SIZE - 1,
            max_id
        )

        query = """
            SELECT
                brand,
                description,
                size,
                sales_quantity,
                sales_dollars
            FROM sales
            WHERE business_id = :business_id
              AND sales_id BETWEEN :start_id AND :end_id
        """

        with engine.connect() as connection:

            chunk = pd.read_sql(
                text(query),
                connection,
                params={
                    "business_id": BUSINESS_ID,
                    "start_id": current_id,
                    "end_id": end_id
                }
            )

        if not chunk.empty:

            chunk["sales_quantity"] = pd.to_numeric(
                chunk["sales_quantity"],
                errors="coerce"
            )

            chunk["sales_dollars"] = pd.to_numeric(
                chunk["sales_dollars"],
                errors="coerce"
            )

            grouped = (
                chunk
                .groupby(
                    [
                        "brand",
                        "description",
                        "size"
                    ],
                    dropna=False
                )
                .agg(
                    sales_quantity=(
                        "sales_quantity",
                        "sum"
                    ),
                    sales_amount=(
                        "sales_dollars",
                        "sum"
                    )
                )
                .reset_index()
            )

            results.append(grouped)

            total_rows += len(chunk)

        print(
            f"Sales rows processed: "
            f"{total_rows:,} "
            f"(through sales_id {end_id:,})"
        )

        current_id = end_id + 1

    summary = (
        pd.concat(
            results,
            ignore_index=True
        )
        .groupby(
            [
                "brand",
                "description",
                "size"
            ],
            dropna=False
        )
        .agg(
            sales_quantity=(
                "sales_quantity",
                "sum"
            ),
            sales_amount=(
                "sales_amount",
                "sum"
            )
        )
        .reset_index()
    )

    return summary, total_rows


# ============================================================
# PRODUCT PERFORMANCE SEGMENTATION
# ============================================================

def analyze_product_performance_segmentation():

    print("\n" + "=" * 80)
    print("PRODUCT PERFORMANCE SEGMENTATION")
    print("=" * 80)

    purchases, purchase_rows = load_purchase_summary()

    sales, sales_rows = load_sales_summary()

    # --------------------------------------------------------
    # OUTER JOIN
    #
    # Keep products appearing in either purchases or sales.
    # --------------------------------------------------------

    comparison = purchases.merge(
        sales,
        on=[
            "brand",
            "description",
            "size"
        ],
        how="outer"
    )

    numeric_columns = [
        "purchase_quantity",
        "purchase_amount",
        "sales_quantity",
        "sales_amount"
    ]

    for column in numeric_columns:

        comparison[column] = (
            comparison[column]
            .fillna(0)
        )

    # --------------------------------------------------------
    # QUANTITY DIFFERENCE
    # --------------------------------------------------------

    comparison["quantity_difference"] = (
        comparison["sales_quantity"]
        - comparison["purchase_quantity"]
    )

    # --------------------------------------------------------
    # CONTRIBUTIONS
    # --------------------------------------------------------

    total_sales_amount = (
        comparison["sales_amount"].sum()
    )

    total_purchase_amount = (
        comparison["purchase_amount"].sum()
    )

    comparison["sales_contribution_percent"] = (
        comparison["sales_amount"]
        / total_sales_amount
        * 100
    )

    comparison["purchase_contribution_percent"] = (
        comparison["purchase_amount"]
        / total_purchase_amount
        * 100
    )

    # --------------------------------------------------------
    # MEDIAN THRESHOLDS
    #
    # Median is used because product sales/purchase
    # distributions are highly skewed.
    # --------------------------------------------------------

    sales_median = (
        comparison["sales_amount"]
        .median()
    )

    purchase_median = (
        comparison["purchase_amount"]
        .median()
    )

    print("\n" + "=" * 80)
    print("SEGMENTATION THRESHOLDS")
    print("=" * 80)

    print(
        f"Sales revenue median   : "
        f"${sales_median:,.2f}"
    )

    print(
        f"Purchase spending median: "
        f"${purchase_median:,.2f}"
    )

    # --------------------------------------------------------
    # ASSIGN SEGMENTS
    # --------------------------------------------------------

    def assign_segment(row):

        high_sales = (
            row["sales_amount"] >= sales_median
        )

        high_purchase = (
            row["purchase_amount"] >= purchase_median
        )

        if high_sales and high_purchase:
            return "High Sales / High Purchase"

        elif high_sales and not high_purchase:
            return "High Sales / Lower Purchase"

        elif not high_sales and high_purchase:
            return "Lower Sales / High Purchase"

        else:
            return "Lower Sales / Lower Purchase"

    comparison["segment"] = (
        comparison.apply(
            assign_segment,
            axis=1
        )
    )

    # --------------------------------------------------------
    # SEGMENT SUMMARY
    # --------------------------------------------------------

    segment_summary = (
        comparison
        .groupby("segment")
        .agg(
            product_count=(
                "brand",
                "count"
            ),
            sales_amount=(
                "sales_amount",
                "sum"
            ),
            purchase_amount=(
                "purchase_amount",
                "sum"
            ),
            sales_quantity=(
                "sales_quantity",
                "sum"
            ),
            purchase_quantity=(
                "purchase_quantity",
                "sum"
            ),
            quantity_difference=(
                "quantity_difference",
                "sum"
            )
        )
        .reset_index()
    )

    segment_summary["sales_contribution_percent"] = (
        segment_summary["sales_amount"]
        / total_sales_amount
        * 100
    )

    segment_summary["purchase_contribution_percent"] = (
        segment_summary["purchase_amount"]
        / total_purchase_amount
        * 100
    )

    segment_order = [
        "High Sales / High Purchase",
        "High Sales / Lower Purchase",
        "Lower Sales / High Purchase",
        "Lower Sales / Lower Purchase"
    ]

    segment_summary["segment"] = pd.Categorical(
        segment_summary["segment"],
        categories=segment_order,
        ordered=True
    )

    segment_summary = (
        segment_summary
        .sort_values("segment")
    )

    # --------------------------------------------------------
    # DISPLAY SEGMENT SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 120)
    print("PRODUCT SEGMENT SUMMARY")
    print("=" * 120)

    print(
        segment_summary[
            [
                "segment",
                "product_count",
                "sales_amount",
                "purchase_amount",
                "sales_quantity",
                "purchase_quantity",
                "quantity_difference",
                "sales_contribution_percent",
                "purchase_contribution_percent"
            ]
        ]
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # TOP PRODUCTS IN EACH SEGMENT
    # --------------------------------------------------------

    print("\n" + "=" * 120)
    print("TOP PRODUCTS WITHIN EACH SEGMENT")
    print("=" * 120)

    for segment_name in segment_order:

        segment_products = (
            comparison[
                comparison["segment"]
                == segment_name
            ]
            .sort_values(
                "sales_amount",
                ascending=False
            )
            .head(5)
        )

        print("\n" + "-" * 100)
        print(segment_name)
        print("-" * 100)

        if segment_products.empty:

            print("No products found.")

            continue

        print(
            segment_products[
                [
                    "brand",
                    "description",
                    "size",
                    "sales_amount",
                    "purchase_amount",
                    "sales_quantity",
                    "purchase_quantity",
                    "quantity_difference"
                ]
            ]
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # OVERALL SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 120)
    print("OVERALL PRODUCT SEGMENTATION SUMMARY")
    print("=" * 120)

    print(
        f"Purchase rows processed : "
        f"{purchase_rows:,}"
    )

    print(
        f"Sales rows processed    : "
        f"{sales_rows:,}"
    )

    print(
        f"Products compared       : "
        f"{len(comparison):,}"
    )

    print(
        f"Total sales amount      : "
        f"${total_sales_amount:,.2f}"
    )

    print(
        f"Total purchase amount   : "
        f"${total_purchase_amount:,.2f}"
    )

    print(
        f"Total sales quantity    : "
        f"{comparison['sales_quantity'].sum():,.0f}"
    )

    print(
        f"Total purchase quantity : "
        f"{comparison['purchase_quantity'].sum():,.0f}"
    )

    # --------------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------------

    print("\n" + "=" * 120)
    print("VERIFICATION")
    print("=" * 120)

    checks_passed = True

    if purchase_rows == 2_372_474:

        print(
            "Purchase row count verification: PASSED"
        )

    else:

        print(
            "Purchase row count verification: FAILED"
        )

        checks_passed = False

    if sales_rows == 12_825_363:

        print(
            "Sales row count verification: PASSED"
        )

    else:

        print(
            "Sales row count verification: FAILED"
        )

        checks_passed = False

    if abs(
        comparison["purchase_quantity"].sum()
        - 33_584_377
    ) < 0.01:

        print(
            "Purchase quantity verification: PASSED"
        )

    else:

        print(
            "Purchase quantity verification: FAILED"
        )

        checks_passed = False

    if abs(
        comparison["purchase_amount"].sum()
        - 321_900_765.53
    ) < 0.01:

        print(
            "Purchase amount verification: PASSED"
        )

    else:

        print(
            "Purchase amount verification: FAILED"
        )

        checks_passed = False

    if abs(
        comparison["sales_quantity"].sum()
        - 32_917_876
    ) < 0.01:

        print(
            "Sales quantity verification: PASSED"
        )

    else:

        print(
            "Sales quantity verification: FAILED"
        )

        checks_passed = False

    if abs(
        comparison["sales_amount"].sum()
        - 452_062_952.02
    ) < 0.01:

        print(
            "Sales amount verification: PASSED"
        )

    else:

        print(
            "Sales amount verification: FAILED"
        )

        checks_passed = False

    if len(segment_summary) == 4:

        print(
            "Segment count verification: PASSED"
        )

    else:

        print(
            "Segment count verification: FAILED"
        )

        checks_passed = False

    if (
        comparison["segment"].notna().all()
    ):

        print(
            "Product segmentation completeness: PASSED"
        )

    else:

        print(
            "Product segmentation completeness: FAILED"
        )

        checks_passed = False

    print("\n" + "=" * 120)

    if checks_passed:

        print(
            "ALL PRODUCT SEGMENTATION CHECKS PASSED"
        )

    else:

        print(
            "SOME PRODUCT SEGMENTATION CHECKS FAILED"
        )

    print("=" * 120)

    print(
        "\nPRODUCT PERFORMANCE SEGMENTATION COMPLETE"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    analyze_product_performance_segmentation()