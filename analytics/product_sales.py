import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_product_sales():

    query = """
        SELECT
            brand,
            description,
            size,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = :business_id
    """

    product_data = []
    total_rows = 0

    print("Starting Product Sales Analysis...")
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

            # Keep product identity using Brand + Description + Size
            grouped = (
                chunk.groupby(
                    ["brand", "description", "size"],
                    dropna=False
                )
                .agg(
                    units_sold=("sales_quantity", "sum"),
                    sales_amount=("sales_dollars", "sum")
                )
                .reset_index()
            )

            product_data.append(grouped)

            total_rows += len(chunk)

            print(
                f"Chunk {chunk_number}: "
                f"{len(chunk):,} rows processed | "
                f"Total rows: {total_rows:,}"
            )

    # Combine all chunk-level results
    product_sales = pd.concat(
        product_data,
        ignore_index=True
    )

    # Aggregate products again after combining chunks
    product_sales = (
        product_sales
        .groupby(
            ["brand", "description", "size"],
            dropna=False
        )
        .agg(
            units_sold=("units_sold", "sum"),
            sales_amount=("sales_amount", "sum")
        )
        .reset_index()
        .sort_values(
            "sales_amount",
            ascending=False
        )
    )

    print("\n" + "=" * 80)
    print("PRODUCT SALES ANALYSIS")
    print("=" * 80)

    print(
        product_sales.head(20).to_string(index=False)
    )

    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    print(
        f"Unique Products in Sales Data : {len(product_sales):,}"
    )

    print(
        f"Total Units Sold              : "
        f"{product_sales['units_sold'].sum():,.0f}"
    )

    print(
        f"Total Sales $                 : "
        f"{product_sales['sales_amount'].sum():,.2f}"
    )

    print("\nTop 10 Products by Sales:")

    print(
        product_sales
        .head(10)
        .to_string(index=False)
    )

    print("\nBottom 10 Products by Sales:")

    print(
        product_sales
        .tail(10)
        .sort_values("sales_amount")
        .to_string(index=False)
    )

    print("=" * 80)


if __name__ == "__main__":
    calculate_product_sales()