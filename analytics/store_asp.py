import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_store_asp():

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

    print("Starting Store Average Selling Price Analysis...")
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

    # Sort by ASP
    store_sales = store_sales.sort_values(
        "average_selling_price",
        ascending=False
    )

    print("\n" + "=" * 80)
    print("STORE AVERAGE SELLING PRICE ANALYSIS")
    print("=" * 80)

    print(
        store_sales.to_string(index=False)
    )

    # Verification
    total_units = store_sales["units_sold"].sum()
    total_sales = store_sales["sales_amount"].sum()

    overall_asp = total_sales / total_units

    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    print(
        f"Number of Stores : "
        f"{len(store_sales):,}"
    )

    print(
        f"Total Units Sold : "
        f"{total_units:,.0f}"
    )

    print(
        f"Total Sales $    : "
        f"{total_sales:,.2f}"
    )

    print(
        f"Overall ASP      : "
        f"${overall_asp:,.2f}"
    )

    print("\nTop 10 Stores by ASP:")

    print(
        store_sales
        .head(10)
        .to_string(index=False)
    )

    print("\nBottom 10 Stores by ASP:")

    print(
        store_sales
        .tail(10)
        .sort_values("average_selling_price")
        .to_string(index=False)
    )

    print("=" * 80)


if __name__ == "__main__":
    calculate_store_asp()