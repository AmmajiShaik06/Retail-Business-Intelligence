import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_vendor_sales():

    query = """
        SELECT
            vendor_number,
            vendor_name,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = :business_id
    """

    vendor_data = []
    total_rows = 0

    print("Starting Vendor Sales Analysis...")
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

            # Preserve Vendor Number + Vendor Name together.
            # This is important because our data analysis found
            # that some vendor numbers have multiple names.
            grouped = (
                chunk.groupby(
                    ["vendor_number", "vendor_name"],
                    dropna=False
                )
                .agg(
                    units_sold=("sales_quantity", "sum"),
                    sales_amount=("sales_dollars", "sum")
                )
                .reset_index()
            )

            vendor_data.append(grouped)

            total_rows += len(chunk)

            print(
                f"Chunk {chunk_number}: "
                f"{len(chunk):,} rows processed | "
                f"Total rows: {total_rows:,}"
            )

    # Combine chunk-level results
    vendor_sales = pd.concat(
        vendor_data,
        ignore_index=True
    )

    # Aggregate again after combining chunks
    vendor_sales = (
        vendor_sales
        .groupby(
            ["vendor_number", "vendor_name"],
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
    print("VENDOR SALES ANALYSIS")
    print("=" * 80)

    print(
        vendor_sales.head(20).to_string(index=False)
    )

    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    print(
        f"Unique Vendor Number + Name Combinations : "
        f"{len(vendor_sales):,}"
    )

    print(
        f"Total Units Sold                          : "
        f"{vendor_sales['units_sold'].sum():,.0f}"
    )

    print(
        f"Total Sales $                             : "
        f"{vendor_sales['sales_amount'].sum():,.2f}"
    )

    print("\nTop 10 Vendors by Sales:")

    print(
        vendor_sales
        .head(10)
        .to_string(index=False)
    )

    print("\nBottom 10 Vendors by Sales:")

    print(
        vendor_sales
        .tail(10)
        .sort_values("sales_amount")
        .to_string(index=False)
    )

    print("=" * 80)


if __name__ == "__main__":
    calculate_vendor_sales()