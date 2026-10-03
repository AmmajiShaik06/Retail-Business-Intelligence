import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_quantity_vs_revenue():

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

    print("Starting Store Quantity vs Revenue Analysis...")
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
                chunk.groupby(
                    "store_number",
                    dropna=False
                )
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

    # Combine chunk results
    store_sales = pd.concat(
        store_data,
        ignore_index=True
    )

    # Final aggregation
    store_sales = (
        store_sales
        .groupby(
            "store_number",
            dropna=False
        )
        .agg(
            units_sold=("units_sold", "sum"),
            sales_amount=("sales_amount", "sum")
        )
        .reset_index()
    )

    # Calculate ASP
    store_sales["average_selling_price"] = (
        store_sales["sales_amount"]
        / store_sales["units_sold"]
    )

    # Rank stores separately
    store_sales["quantity_rank"] = (
        store_sales["units_sold"]
        .rank(method="min", ascending=False)
        .astype(int)
    )

    store_sales["revenue_rank"] = (
        store_sales["sales_amount"]
        .rank(method="min", ascending=False)
        .astype(int)
    )

    # Difference between quantity and revenue rank
    store_sales["rank_difference"] = (
        store_sales["quantity_rank"]
        - store_sales["revenue_rank"]
    )

    print("\n" + "=" * 80)
    print("SALES QUANTITY VS SALES REVENUE")
    print("=" * 80)

    print(
        store_sales.sort_values(
            "sales_amount",
            ascending=False
        ).to_string(index=False)
    )

    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    print(
        f"Number of Stores : "
        f"{len(store_sales):,}"
    )

    print(
        f"Total Units Sold : "
        f"{store_sales['units_sold'].sum():,.0f}"
    )

    print(
        f"Total Sales $    : "
        f"{store_sales['sales_amount'].sum():,.2f}"
    )

    print("\nTop 10 Stores by Units Sold:")

    print(
        store_sales
        .sort_values("units_sold", ascending=False)
        .head(10)
        .to_string(index=False)
    )

    print("\nTop 10 Stores by Sales Revenue:")

    print(
        store_sales
        .sort_values("sales_amount", ascending=False)
        .head(10)
        .to_string(index=False)
    )

    print("\nLargest Positive Quantity-vs-Revenue Rank Difference:")

    print(
        store_sales
        .sort_values("rank_difference", ascending=False)
        .head(10)
        .to_string(index=False)
    )

    print("\nLargest Negative Quantity-vs-Revenue Rank Difference:")

    print(
        store_sales
        .sort_values("rank_difference", ascending=True)
        .head(10)
        .to_string(index=False)
    )

    print("=" * 80)


if __name__ == "__main__":
    calculate_quantity_vs_revenue()