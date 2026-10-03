import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
RANGE_SIZE = 250_000


def analyze_product_sales_contribution():

    min_max_query = """
        SELECT
            MIN(sales_id) AS min_id,
            MAX(sales_id) AS max_id,
            COUNT(*) AS total_rows
        FROM sales
        WHERE business_id = :business_id
    """

    sales_query = """
        SELECT
            sales_id,
            brand,
            description,
            size,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = :business_id
          AND sales_id BETWEEN :start_id AND :end_id
    """

    print("Starting Product Sales Contribution Analysis...")
    print(f"ID range size: {RANGE_SIZE:,}")

    # ---------------------------------------------------------
    # GET SALES ID RANGE
    # ---------------------------------------------------------

    with engine.connect() as connection:

        result = connection.execute(
            text(min_max_query),
            {"business_id": BUSINESS_ID}
        ).fetchone()

    min_id = int(result.min_id)
    max_id = int(result.max_id)
    expected_rows = int(result.total_rows)

    print("\nSales table information")
    print("-" * 90)
    print(f"Minimum Sales ID : {min_id:,}")
    print(f"Maximum Sales ID : {max_id:,}")
    print(f"Expected Rows    : {expected_rows:,}")

    # ---------------------------------------------------------
    # STORAGE
    # ---------------------------------------------------------

    product_results = []

    total_rows_processed = 0

    current_start = min_id

    # ---------------------------------------------------------
    # PROCESS SALES IN ID RANGES
    # ---------------------------------------------------------

    while current_start <= max_id:

        current_end = min(
            current_start + RANGE_SIZE - 1,
            max_id
        )

        with engine.connect() as connection:

            chunk = pd.read_sql(
                text(sales_query),
                connection,
                params={
                    "business_id": BUSINESS_ID,
                    "start_id": current_start,
                    "end_id": current_end
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
                    units_sold=("sales_quantity", "sum"),
                    sales_amount=("sales_dollars", "sum"),
                    sales_transactions=("sales_id", "count")
                )
                .reset_index()
            )

            product_results.append(grouped)

            total_rows_processed += len(chunk)

        print(
            f"Processed Sales ID "
            f"{current_start:,} - {current_end:,} | "
            f"Rows processed: {total_rows_processed:,}"
        )

        current_start = current_end + 1

    # ---------------------------------------------------------
    # COMBINE PRODUCT RESULTS
    # ---------------------------------------------------------

    product_sales = pd.concat(
        product_results,
        ignore_index=True
    )

    product_sales = (
        product_sales
        .groupby(
            [
                "brand",
                "description",
                "size"
            ],
            dropna=False
        )
        .agg(
            units_sold=("units_sold", "sum"),
            sales_amount=("sales_amount", "sum"),
            sales_transactions=("sales_transactions", "sum")
        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # CALCULATE CONTRIBUTION
    # ---------------------------------------------------------

    total_sales = product_sales["sales_amount"].sum()
    total_units = product_sales["units_sold"].sum()

    product_sales["sales_contribution_percent"] = (
        product_sales["sales_amount"]
        / total_sales
        * 100
    )

    product_sales["unit_contribution_percent"] = (
        product_sales["units_sold"]
        / total_units
        * 100
    )

    product_sales["sales_rank"] = (
        product_sales["sales_amount"]
        .rank(
            method="dense",
            ascending=False
        )
        .astype(int)
    )

    product_sales = product_sales.sort_values(
        "sales_amount",
        ascending=False
    )

    # ---------------------------------------------------------
    # TOP 10 PRODUCTS
    # ---------------------------------------------------------

    print("\n" + "=" * 110)
    print("TOP 10 PRODUCTS BY SALES CONTRIBUTION")
    print("=" * 110)

    print(
        product_sales[
            [
                "sales_rank",
                "brand",
                "description",
                "size",
                "units_sold",
                "sales_amount",
                "sales_contribution_percent",
                "unit_contribution_percent",
                "sales_transactions"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # BOTTOM 10 PRODUCTS
    # ---------------------------------------------------------

    print("\n" + "=" * 110)
    print("BOTTOM 10 PRODUCTS BY SALES")
    print("=" * 110)

    print(
        product_sales[
            [
                "sales_rank",
                "brand",
                "description",
                "size",
                "units_sold",
                "sales_amount",
                "sales_contribution_percent",
                "unit_contribution_percent",
                "sales_transactions"
            ]
        ]
        .tail(10)
        .sort_values("sales_amount")
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # SALES CONCENTRATION
    # ---------------------------------------------------------

    top_5_sales = (
        product_sales
        .head(5)["sales_amount"]
        .sum()
    )

    top_10_sales = (
        product_sales
        .head(10)["sales_amount"]
        .sum()
    )

    top_20_sales = (
        product_sales
        .head(20)["sales_amount"]
        .sum()
    )

    top_5_contribution = (
        top_5_sales / total_sales * 100
    )

    top_10_contribution = (
        top_10_sales / total_sales * 100
    )

    top_20_contribution = (
        top_20_sales / total_sales * 100
    )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print("\n" + "=" * 110)
    print("PRODUCT SALES CONCENTRATION")
    print("=" * 110)

    print(
        f"Total Products in Sales Data : "
        f"{len(product_sales):,}"
    )

    print(
        f"Total Sales                  : "
        f"${total_sales:,.2f}"
    )

    print(
        f"Top 5 Products Sales         : "
        f"${top_5_sales:,.2f}"
    )

    print(
        f"Top 5 Contribution           : "
        f"{top_5_contribution:.2f}%"
    )

    print(
        f"Top 10 Products Sales        : "
        f"${top_10_sales:,.2f}"
    )

    print(
        f"Top 10 Contribution          : "
        f"{top_10_contribution:.2f}%"
    )

    print(
        f"Top 20 Products Sales        : "
        f"${top_20_sales:,.2f}"
    )

    print(
        f"Top 20 Contribution          : "
        f"{top_20_contribution:.2f}%"
    )

    # ---------------------------------------------------------
    # VERIFICATION
    # ---------------------------------------------------------

    print("\n" + "=" * 110)
    print("VERIFICATION")
    print("=" * 110)

    print(
        f"Expected Sales Rows : "
        f"{expected_rows:,}"
    )

    print(
        f"Processed Sales Rows: "
        f"{total_rows_processed:,}"
    )

    if total_rows_processed == expected_rows:
        print("Row count verification: PASSED")
    else:
        print("Row count verification: FAILED")

    print(
        f"\nNumber of Products: "
        f"{len(product_sales):,}"
    )

    print(
        f"Total Units Sold: "
        f"{total_units:,.0f}"
    )

    print(
        f"Total Sales: "
        f"${total_sales:,.2f}"
    )

    print("\n" + "=" * 110)
    print("PRODUCT SALES CONTRIBUTION ANALYSIS COMPLETE")
    print("=" * 110)


if __name__ == "__main__":
    analyze_product_sales_contribution()