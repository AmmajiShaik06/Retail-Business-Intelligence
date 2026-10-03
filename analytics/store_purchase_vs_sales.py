import pandas as pd
from sqlalchemy import text

from database.connection import engine


BUSINESS_ID = 1
PURCHASE_CHUNK_SIZE = 50_000
SALES_RANGE_SIZE = 250_000


# ============================================================
# PURCHASE ANALYSIS BY STORE
# ============================================================

def load_purchase_summary():

    print("\n" + "=" * 70)
    print("ANALYZING PURCHASES BY STORE")
    print("=" * 70)

    query = """
        SELECT
            store_number,
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

            chunk["store_number"] = pd.to_numeric(
                chunk["store_number"],
                errors="coerce"
            )

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
                    "store_number",
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
            "store_number",
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
# SALES ANALYSIS BY STORE
# ============================================================

def load_sales_summary():

    print("\n" + "=" * 70)
    print("ANALYZING SALES BY STORE")
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
                store_number,
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

        if len(chunk) > 0:

            chunk["store_number"] = pd.to_numeric(
                chunk["store_number"],
                errors="coerce"
            )

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
                    "store_number",
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
            "store_number",
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
# STORE PURCHASE VS SALES
# ============================================================

def analyze_store_purchase_vs_sales():

    print("\n" + "=" * 70)
    print("STORE PURCHASE VS SALES ANALYSIS")
    print("=" * 70)

    purchases, purchase_rows = load_purchase_summary()

    sales, sales_rows = load_sales_summary()

    # --------------------------------------------------------
    # OUTER JOIN
    # --------------------------------------------------------

    comparison = purchases.merge(
        sales,
        on="store_number",
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
    # DIFFERENCES
    # --------------------------------------------------------

    comparison["quantity_difference"] = (
        comparison["sales_quantity"]
        - comparison["purchase_quantity"]
    )

    comparison["amount_difference"] = (
        comparison["sales_amount"]
        - comparison["purchase_amount"]
    )

    # --------------------------------------------------------
    # RATIOS
    # --------------------------------------------------------

    comparison["sales_to_purchase_quantity_ratio"] = (
        comparison["sales_quantity"]
        / comparison["purchase_quantity"].replace(
            0,
            pd.NA
        )
    )

    comparison["sales_to_purchase_amount_ratio"] = (
        comparison["sales_amount"]
        / comparison["purchase_amount"].replace(
            0,
            pd.NA
        )
    )

    # --------------------------------------------------------
    # CONTRIBUTION
    # --------------------------------------------------------

    total_purchase_amount = (
        comparison["purchase_amount"].sum()
    )

    total_sales_amount = (
        comparison["sales_amount"].sum()
    )

    comparison["purchase_contribution_percent"] = (
        comparison["purchase_amount"]
        / total_purchase_amount
        * 100
    )

    comparison["sales_contribution_percent"] = (
        comparison["sales_amount"]
        / total_sales_amount
        * 100
    )

    # ========================================================
    # TOP STORES BY SALES
    # ========================================================

    print("\n" + "=" * 120)
    print("TOP 10 STORES BY SALES REVENUE")
    print("=" * 120)

    top_sales = (
        comparison
        .sort_values(
            "sales_amount",
            ascending=False
        )
        .head(10)
    )

    print(
        top_sales[
            [
                "store_number",
                "purchase_quantity",
                "sales_quantity",
                "quantity_difference",
                "purchase_amount",
                "sales_amount",
                "amount_difference",
                "sales_to_purchase_quantity_ratio",
                "sales_to_purchase_amount_ratio"
            ]
        ]
        .to_string(index=False)
    )

    # ========================================================
    # STORES WITH SALES QUANTITY ABOVE PURCHASE QUANTITY
    # ========================================================

    print("\n" + "=" * 120)
    print("TOP 10 STORES WITH SALES QUANTITY ABOVE PURCHASE QUANTITY")
    print("=" * 120)

    positive_difference = (
        comparison
        .sort_values(
            "quantity_difference",
            ascending=False
        )
        .head(10)
    )

    print(
        positive_difference[
            [
                "store_number",
                "purchase_quantity",
                "sales_quantity",
                "quantity_difference",
                "sales_to_purchase_quantity_ratio"
            ]
        ]
        .to_string(index=False)
    )

    # ========================================================
    # STORES WITH PURCHASE QUANTITY ABOVE SALES
    # ========================================================

    print("\n" + "=" * 120)
    print("TOP 10 STORES WITH PURCHASE QUANTITY ABOVE SALES QUANTITY")
    print("=" * 120)

    negative_difference = (
        comparison
        .sort_values(
            "quantity_difference",
            ascending=True
        )
        .head(10)
    )

    print(
        negative_difference[
            [
                "store_number",
                "purchase_quantity",
                "sales_quantity",
                "quantity_difference",
                "sales_to_purchase_quantity_ratio"
            ]
        ]
        .to_string(index=False)
    )

    # ========================================================
    # HIGHEST SALES/PURCHASE AMOUNT RATIOS
    # ========================================================

    print("\n" + "=" * 120)
    print("TOP 10 SALES-TO-PURCHASE AMOUNT RATIOS BY STORE")
    print("=" * 120)

    ratio_analysis = (
        comparison[
            comparison["purchase_amount"] > 0
        ]
        .sort_values(
            "sales_to_purchase_amount_ratio",
            ascending=False
        )
        .head(10)
    )

    print(
        ratio_analysis[
            [
                "store_number",
                "purchase_amount",
                "sales_amount",
                "sales_to_purchase_amount_ratio"
            ]
        ]
        .to_string(index=False)
    )

    # ========================================================
    # OVERALL SUMMARY
    # ========================================================

    total_purchase_quantity = (
        comparison["purchase_quantity"].sum()
    )

    total_sales_quantity = (
        comparison["sales_quantity"].sum()
    )

    total_purchase_amount = (
        comparison["purchase_amount"].sum()
    )

    total_sales_amount = (
        comparison["sales_amount"].sum()
    )

    quantity_ratio = (
        total_sales_quantity
        / total_purchase_quantity
    )

    amount_ratio = (
        total_sales_amount
        / total_purchase_amount
    )

    print("\n" + "=" * 120)
    print("OVERALL STORE PURCHASE VS SALES SUMMARY")
    print("=" * 120)

    print(
        f"Purchase rows processed: "
        f"{purchase_rows:,}"
    )

    print(
        f"Sales rows processed: "
        f"{sales_rows:,}"
    )

    print(
        f"Stores compared: "
        f"{len(comparison):,}"
    )

    print(
        f"Total Purchase Quantity: "
        f"{total_purchase_quantity:,.2f}"
    )

    print(
        f"Total Sales Quantity: "
        f"{total_sales_quantity:,.2f}"
    )

    print(
        f"Quantity Difference: "
        f"{total_sales_quantity - total_purchase_quantity:,.2f}"
    )

    print(
        f"Total Purchase Amount: "
        f"${total_purchase_amount:,.2f}"
    )

    print(
        f"Total Sales Amount: "
        f"${total_sales_amount:,.2f}"
    )

    print(
        f"Sales / Purchase Quantity Ratio: "
        f"{quantity_ratio:.4f}"
    )

    print(
        f"Sales / Purchase Amount Ratio: "
        f"{amount_ratio:.4f}"
    )

    # ========================================================
    # VERIFICATION
    # ========================================================

    print("\n" + "=" * 120)
    print("VERIFICATION")
    print("=" * 120)

    if purchase_rows == 2_372_474:
        print(
            "Purchase row count verification: PASSED"
        )
    else:
        print(
            "Purchase row count verification: FAILED"
        )

    if sales_rows == 12_825_363:
        print(
            "Sales row count verification: PASSED"
        )
    else:
        print(
            "Sales row count verification: FAILED"
        )

    if len(comparison) == 80:
        print(
            "Store count verification: PASSED"
        )
    else:
        print(
            "Store count verification: FAILED"
        )

    if abs(
        total_purchase_quantity - 33_584_377
    ) < 0.01:

        print(
            "Purchase quantity verification: PASSED"
        )

    else:

        print(
            "Purchase quantity verification: FAILED"
        )

    if abs(
        total_purchase_amount - 321_900_765.53
    ) < 0.01:

        print(
            "Purchase amount verification: PASSED"
        )

    else:

        print(
            "Purchase amount verification: FAILED"
        )

    if abs(
        total_sales_quantity - 32_917_876
    ) < 0.01:

        print(
            "Sales quantity verification: PASSED"
        )

    else:

        print(
            "Sales quantity verification: FAILED"
        )

    if abs(
        total_sales_amount - 452_062_952.02
    ) < 0.01:

        print(
            "Sales amount verification: PASSED"
        )

    else:

        print(
            "Sales amount verification: FAILED"
        )

    print("\n" + "=" * 120)
    print("STORE PURCHASE VS SALES ANALYSIS COMPLETE")
    print("=" * 120)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    analyze_store_purchase_vs_sales()