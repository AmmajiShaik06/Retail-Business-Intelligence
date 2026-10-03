import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_monthly_sales():
    query = """
        SELECT
            sales_date,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = :business_id
    """

    monthly_data = []

    total_rows = 0

    print("Starting Monthly Sales Analysis...")
    print(f"Chunk size: {CHUNK_SIZE:,}")

    with engine.connect() as connection:

        for chunk_number, chunk in enumerate(
            pd.read_sql(
                text(query),
                connection,
                params={"business_id": BUSINESS_ID},
                chunksize=CHUNK_SIZE
            ),
            start=1
        ):

            chunk["sales_date"] = pd.to_datetime(
                chunk["sales_date"],
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

            chunk["month"] = chunk["sales_date"].dt.to_period("M")

            grouped = (
                chunk.groupby("month")
                .agg(
                    units_sold=("sales_quantity", "sum"),
                    sales_amount=("sales_dollars", "sum")
                )
                .reset_index()
            )

            monthly_data.append(grouped)

            total_rows += len(chunk)

            print(
                f"Chunk {chunk_number}: "
                f"{len(chunk):,} rows processed | "
                f"Total rows: {total_rows:,}"
            )

    monthly_sales = pd.concat(monthly_data, ignore_index=True)

    monthly_sales = (
        monthly_sales
        .groupby("month")
        .agg(
            units_sold=("units_sold", "sum"),
            sales_amount=("sales_amount", "sum")
        )
        .reset_index()
        .sort_values("month")
    )

    monthly_sales["month"] = monthly_sales["month"].astype(str)

    print("\n" + "=" * 70)
    print("MONTHLY SALES ANALYSIS")
    print("=" * 70)

    print(monthly_sales.to_string(index=False))

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    print(f"Total Units Sold : {monthly_sales['units_sold'].sum():,.0f}")
    print(f"Total Sales $    : {monthly_sales['sales_amount'].sum():,.2f}")
    print(f"Number of Months : {len(monthly_sales)}")

    print("=" * 70)


if __name__ == "__main__":
    calculate_monthly_sales()