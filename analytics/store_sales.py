import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_store_sales():
    query = """
        SELECT
            store_number,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = :business_id
    """

    store_data = []
    total_rows = 0

    print("Starting Store Sales Analysis...")
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

            chunk["sales_quantity"] = pd.to_numeric(
                chunk["sales_quantity"],
                errors="coerce"
            )

            chunk["sales_dollars"] = pd.to_numeric(
                chunk["sales_dollars"],
                errors="coerce"
            )

            grouped = (
                chunk.groupby("store_number")
                .agg(
                    units_sold=("sales_quantity", "sum"),
                    sales_amount=("sales_dollars", "sum")
                )
                .reset_index()
            )

            store_data.append(grouped)

            total_rows += len(chunk)

            print(
                f"Chunk {chunk_number}: "
                f"{len(chunk):,} rows processed | "
                f"Total rows: {total_rows:,}"
            )

    store_sales = pd.concat(store_data, ignore_index=True)

    store_sales = (
        store_sales
        .groupby("store_number")
        .agg(
            units_sold=("units_sold", "sum"),
            sales_amount=("sales_amount", "sum")
        )
        .reset_index()
        .sort_values("sales_amount", ascending=False)
    )

    print("\n" + "=" * 70)
    print("STORE SALES ANALYSIS")
    print("=" * 70)

    print(store_sales.to_string(index=False))

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    print(f"Number of Stores in Sales Data : {len(store_sales)}")
    print(f"Total Units Sold               : {store_sales['units_sold'].sum():,.0f}")
    print(f"Total Sales $                  : {store_sales['sales_amount'].sum():,.2f}")

    print("\nTop 5 Stores by Sales:")
    print(
        store_sales.head(5).to_string(index=False)
    )

    print("\nBottom 5 Stores by Sales:")
    print(
        store_sales.tail(5).sort_values("sales_amount").to_string(index=False)
    )

    print("=" * 70)


if __name__ == "__main__":
    calculate_store_sales()