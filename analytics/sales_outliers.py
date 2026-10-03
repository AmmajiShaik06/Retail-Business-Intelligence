import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1

RANGE_SIZE = 250_000

QUANTITY_THRESHOLD = 18
SALES_AMOUNT_THRESHOLD = 275.88

TOP_N = 20


def analyze_sales_outliers():

    min_max_query = """
        SELECT
            MIN(sales_id) AS min_id,
            MAX(sales_id) AS max_id,
            COUNT(*) AS total_rows
        FROM sales
        WHERE business_id = :business_id
    """

    print("Starting Sales Outlier Analysis...")
    print(f"ID range size: {RANGE_SIZE:,}")
    print(f"Quantity threshold: > {QUANTITY_THRESHOLD}")
    print(f"Sales amount threshold: > ${SALES_AMOUNT_THRESHOLD:.2f}")

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
    # STORAGE FOR TOP OUTLIERS
    # ---------------------------------------------------------

    top_quantity_records = []
    top_sales_records = []

    quantity_outlier_count = 0
    sales_amount_outlier_count = 0

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

        query = """
            SELECT
                sales_id,
                inventory_id,
                store_number,
                brand,
                description,
                size,
                sales_quantity,
                sales_dollars,
                sales_price,
                sales_date,
                vendor_number,
                vendor_name
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

            chunk["sales_price"] = pd.to_numeric(
                chunk["sales_price"],
                errors="coerce"
            )

            total_rows_processed += len(chunk)

            # -------------------------------------------------
            # QUANTITY OUTLIERS
            # -------------------------------------------------

            high_quantity = chunk[
                chunk["sales_quantity"] > QUANTITY_THRESHOLD
            ].copy()

            quantity_outlier_count += len(high_quantity)

            if not high_quantity.empty:

                top_quantity_records.append(
                    high_quantity.nlargest(
                        TOP_N,
                        "sales_quantity"
                    )
                )

            # -------------------------------------------------
            # SALES AMOUNT OUTLIERS
            # -------------------------------------------------

            high_sales = chunk[
                chunk["sales_dollars"] > SALES_AMOUNT_THRESHOLD
            ].copy()

            sales_amount_outlier_count += len(high_sales)

            if not high_sales.empty:

                top_sales_records.append(
                    high_sales.nlargest(
                        TOP_N,
                        "sales_dollars"
                    )
                )

        print(
            f"Processed Sales ID "
            f"{current_start:,} - {current_end:,} | "
            f"Rows processed: {total_rows_processed:,}"
        )

        current_start = current_end + 1

    # ---------------------------------------------------------
    # COMBINE TOP QUANTITY RECORDS
    # ---------------------------------------------------------

    if top_quantity_records:

        quantity_outliers_df = pd.concat(
            top_quantity_records,
            ignore_index=True
        )

        quantity_outliers_df = (
            quantity_outliers_df
            .sort_values(
                "sales_quantity",
                ascending=False
            )
            .head(TOP_N)
        )

    else:

        quantity_outliers_df = pd.DataFrame()

    # ---------------------------------------------------------
    # COMBINE TOP SALES RECORDS
    # ---------------------------------------------------------

    if top_sales_records:

        sales_outliers_df = pd.concat(
            top_sales_records,
            ignore_index=True
        )

        sales_outliers_df = (
            sales_outliers_df
            .sort_values(
                "sales_dollars",
                ascending=False
            )
            .head(TOP_N)
        )

    else:

        sales_outliers_df = pd.DataFrame()

    # ---------------------------------------------------------
    # DISPLAY HIGH QUANTITY TRANSACTIONS
    # ---------------------------------------------------------

    print("\n" + "=" * 100)
    print("TOP HIGH-QUANTITY TRANSACTIONS")
    print("=" * 100)

    print(
        f"Total quantity outlier candidates: "
        f"{quantity_outlier_count:,}"
    )

    if not quantity_outliers_df.empty:

        print("\nTop 20 transactions by quantity:\n")

        print(
            quantity_outliers_df[
                [
                    "sales_id",
                    "inventory_id",
                    "store_number",
                    "brand",
                    "description",
                    "size",
                    "sales_quantity",
                    "sales_dollars",
                    "sales_price",
                    "sales_date",
                    "vendor_number",
                    "vendor_name"
                ]
            ].to_string(index=False)
        )

    # ---------------------------------------------------------
    # DISPLAY HIGH SALES VALUE TRANSACTIONS
    # ---------------------------------------------------------

    print("\n" + "=" * 100)
    print("TOP HIGH-SALES-VALUE TRANSACTIONS")
    print("=" * 100)

    print(
        f"Total sales amount outlier candidates: "
        f"{sales_amount_outlier_count:,}"
    )

    if not sales_outliers_df.empty:

        print("\nTop 20 transactions by sales amount:\n")

        print(
            sales_outliers_df[
                [
                    "sales_id",
                    "inventory_id",
                    "store_number",
                    "brand",
                    "description",
                    "size",
                    "sales_quantity",
                    "sales_dollars",
                    "sales_price",
                    "sales_date",
                    "vendor_number",
                    "vendor_name"
                ]
            ].to_string(index=False)
        )

    # ---------------------------------------------------------
    # VERIFICATION
    # ---------------------------------------------------------

    print("\n" + "=" * 100)
    print("VERIFICATION")
    print("=" * 100)

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
        f"\nQuantity Outlier Candidates: "
        f"{quantity_outlier_count:,}"
    )

    print(
        f"Sales Amount Outlier Candidates: "
        f"{sales_amount_outlier_count:,}"
    )

    print(
        f"\nQuantity Threshold: "
        f"> {QUANTITY_THRESHOLD}"
    )

    print(
        f"Sales Amount Threshold: "
        f"> ${SALES_AMOUNT_THRESHOLD:.2f}"
    )

    print("\n" + "=" * 100)
    print("SALES OUTLIER ANALYSIS COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    analyze_sales_outliers()