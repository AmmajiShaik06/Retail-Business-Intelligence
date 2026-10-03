import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_sales_distribution():

    query = """
        SELECT
            sales_quantity,
            sales_dollars,
            sales_price
        FROM sales
        WHERE business_id = :business_id
    """

    total_rows = 0

    quantity_values = []
    sales_amount_values = []
    sales_price_values = []

    print("Starting Sales Distribution Analysis...")
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

            chunk["sales_price"] = pd.to_numeric(
                chunk["sales_price"],
                errors="coerce"
            )

            # Remove invalid values
            quantity = chunk["sales_quantity"].dropna()
            sales_amount = chunk["sales_dollars"].dropna()
            sales_price = chunk["sales_price"].dropna()

            quantity_values.append(quantity)
            sales_amount_values.append(sales_amount)
            sales_price_values.append(sales_price)

            total_rows += len(chunk)

            print(
                f"Chunk {chunk_number}: "
                f"{len(chunk):,} rows processed | "
                f"Total rows: {total_rows:,}"
            )

    # Combine all valid values
    all_quantity = pd.concat(
        quantity_values,
        ignore_index=True
    )

    all_sales_amount = pd.concat(
        sales_amount_values,
        ignore_index=True
    )

    all_sales_price = pd.concat(
        sales_price_values,
        ignore_index=True
    )

    print("\n" + "=" * 90)
    print("SALES DISTRIBUTION ANALYSIS")
    print("=" * 90)

    # ---------------------------------------------------------
    # SALES QUANTITY
    # ---------------------------------------------------------

    print("\nSALES QUANTITY DISTRIBUTION")
    print("-" * 90)

    quantity_summary = all_quantity.describe(
        percentiles=[
            0.25,
            0.50,
            0.75,
            0.90,
            0.95,
            0.99
        ]
    )

    print(quantity_summary)

    # ---------------------------------------------------------
    # SALES AMOUNT
    # ---------------------------------------------------------

    print("\nSALES AMOUNT DISTRIBUTION")
    print("-" * 90)

    sales_amount_summary = all_sales_amount.describe(
        percentiles=[
            0.25,
            0.50,
            0.75,
            0.90,
            0.95,
            0.99
        ]
    )

    print(sales_amount_summary)

    # ---------------------------------------------------------
    # SALES PRICE
    # ---------------------------------------------------------

    print("\nSALES PRICE DISTRIBUTION")
    print("-" * 90)

    sales_price_summary = all_sales_price.describe(
        percentiles=[
            0.25,
            0.50,
            0.75,
            0.90,
            0.95,
            0.99
        ]
    )

    print(sales_price_summary)

    # ---------------------------------------------------------
    # VERIFICATION
    # ---------------------------------------------------------

    print("\n" + "=" * 90)
    print("VERIFICATION")
    print("=" * 90)

    print(
        f"Total Sales Rows Processed : "
        f"{total_rows:,}"
    )

    print(
        f"Valid Quantity Values      : "
        f"{len(all_quantity):,}"
    )

    print(
        f"Valid Sales Amount Values  : "
        f"{len(all_sales_amount):,}"
    )

    print(
        f"Valid Sales Price Values   : "
        f"{len(all_sales_price):,}"
    )

    print(
        f"\nMinimum Quantity           : "
        f"{all_quantity.min():,.2f}"
    )

    print(
        f"Maximum Quantity           : "
        f"{all_quantity.max():,.2f}"
    )

    print(
        f"Average Quantity           : "
        f"{all_quantity.mean():,.2f}"
    )

    print(
        f"\nMinimum Sales Amount       : "
        f"${all_sales_amount.min():,.2f}"
    )

    print(
        f"Maximum Sales Amount       : "
        f"${all_sales_amount.max():,.2f}"
    )

    print(
        f"Average Sales Amount       : "
        f"${all_sales_amount.mean():,.2f}"
    )

    print(
        f"\nMinimum Sales Price        : "
        f"${all_sales_price.min():,.2f}"
    )

    print(
        f"Maximum Sales Price        : "
        f"${all_sales_price.max():,.2f}"
    )

    print(
        f"Average Sales Price        : "
        f"${all_sales_price.mean():,.2f}"
    )

    # ---------------------------------------------------------
    # HIGH-VALUE TRANSACTIONS
    # ---------------------------------------------------------

    print("\n" + "=" * 90)
    print("TOP 10 SALES AMOUNTS")
    print("=" * 90)

    print(
        all_sales_amount
        .sort_values(ascending=False)
        .head(10)
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # HIGH-QUANTITY TRANSACTIONS
    # ---------------------------------------------------------

    print("\n" + "=" * 90)
    print("TOP 10 SALES QUANTITIES")
    print("=" * 90)

    print(
        all_quantity
        .sort_values(ascending=False)
        .head(10)
        .to_string(index=False)
    )

    print("\n" + "=" * 90)
    print("SALES DISTRIBUTION ANALYSIS COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    calculate_sales_distribution()