import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_sales_by_city():

    print("Starting Sales by City Analysis...")
    print(f"Chunk size: {CHUNK_SIZE:,}")

    # ---------------------------------------------------------
    # STEP 1: Load Store -> City mapping
    # ---------------------------------------------------------

    store_query = """
        SELECT
            store_number,
            city
        FROM stores
        WHERE business_id = :business_id
    """

    with engine.connect() as connection:
        stores = pd.read_sql(
            text(store_query),
            connection,
            params={"business_id": BUSINESS_ID}
        )

    print(f"Stores loaded: {len(stores):,}")

    # Check whether any store has multiple cities
    duplicate_store_city = (
        stores.groupby("store_number")["city"]
        .nunique(dropna=True)
    )

    multiple_city_stores = duplicate_store_city[
        duplicate_store_city > 1
    ]

    print(
        f"Stores mapped to multiple cities: "
        f"{len(multiple_city_stores):,}"
    )

    # ---------------------------------------------------------
    # STEP 2: Read sales in chunks
    # ---------------------------------------------------------

    query = """
        SELECT
            store_number,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = :business_id
    """

    city_data = []
    total_rows = 0

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

            # Convert numeric columns
            chunk["sales_quantity"] = pd.to_numeric(
                chunk["sales_quantity"],
                errors="coerce"
            )

            chunk["sales_dollars"] = pd.to_numeric(
                chunk["sales_dollars"],
                errors="coerce"
            )

            # -------------------------------------------------
            # STEP 3: Add city to sales using store number
            # -------------------------------------------------

            chunk = chunk.merge(
                stores,
                on="store_number",
                how="left"
            )

            # -------------------------------------------------
            # STEP 4: Aggregate current chunk by city
            # -------------------------------------------------

            grouped = (
                chunk.groupby(
                    "city",
                    dropna=False
                )
                .agg(
                    units_sold=("sales_quantity", "sum"),
                    sales_amount=("sales_dollars", "sum"),
                    stores_with_sales=("store_number", "nunique")
                )
                .reset_index()
            )

            city_data.append(grouped)

            total_rows += len(chunk)

            print(
                f"Chunk {chunk_number}: "
                f"{len(chunk):,} rows processed | "
                f"Total rows: {total_rows:,}"
            )

    # ---------------------------------------------------------
    # STEP 5: Combine all chunk results
    # ---------------------------------------------------------

    sales_by_city = pd.concat(
        city_data,
        ignore_index=True
    )

    sales_by_city = (
        sales_by_city
        .groupby(
            "city",
            dropna=False
        )
        .agg(
            units_sold=("units_sold", "sum"),
            sales_amount=("sales_amount", "sum"),
            stores_with_sales=("stores_with_sales", "sum")
        )
        .reset_index()
        .sort_values(
            "sales_amount",
            ascending=False
        )
    )

    # ---------------------------------------------------------
    # STEP 6: Display results
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("SALES BY CITY")
    print("=" * 80)

    print(
        sales_by_city.to_string(index=False)
    )

    # ---------------------------------------------------------
    # STEP 7: Verification
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    print(
        f"Number of Cities in Sales Data : "
        f"{sales_by_city['city'].notna().sum():,}"
    )

    print(
        f"Total Units Sold                : "
        f"{sales_by_city['units_sold'].sum():,.0f}"
    )

    print(
        f"Total Sales $                   : "
        f"{sales_by_city['sales_amount'].sum():,.2f}"
    )

    print(
        f"Rows with Missing City          : "
        f"{sales_by_city.loc[sales_by_city['city'].isna(), 'units_sold'].sum():,.0f} units"
    )

    print("\nTop 10 Cities by Sales:")

    print(
        sales_by_city
        .head(10)
        .to_string(index=False)
    )

    print("\nBottom 10 Cities by Sales:")

    print(
        sales_by_city
        .tail(10)
        .sort_values("sales_amount")
        .to_string(index=False)
    )

    print("=" * 80)


if __name__ == "__main__":
    calculate_sales_by_city()