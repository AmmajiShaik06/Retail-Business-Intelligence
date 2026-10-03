import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_sales_by_weekday():

    query = """
        SELECT
            sales_date,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = :business_id
    """

    weekday_data = []
    total_rows = 0

    print("Starting Sales by Day of Week Analysis...")
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

            chunk["weekday_number"] = (
                chunk["sales_date"].dt.dayofweek
            )

            chunk["weekday_name"] = (
                chunk["sales_date"].dt.day_name()
            )

            grouped = (
                chunk.groupby(
                    ["weekday_number", "weekday_name"]
                )
                .agg(
                    units_sold=("sales_quantity", "sum"),
                    sales_amount=("sales_dollars", "sum")
                )
                .reset_index()
            )

            weekday_data.append(grouped)

            total_rows += len(chunk)

            print(
                f"Chunk {chunk_number}: "
                f"{len(chunk):,} rows processed | "
                f"Total rows: {total_rows:,}"
            )

    # Combine chunk-level results
    weekday_sales = pd.concat(
        weekday_data,
        ignore_index=True
    )

    # Final weekday aggregation
    weekday_sales = (
        weekday_sales
        .groupby(
            ["weekday_number", "weekday_name"]
        )
        .agg(
            units_sold=("units_sold", "sum"),
            sales_amount=("sales_amount", "sum")
        )
        .reset_index()
        .sort_values("weekday_number")
        .reset_index(drop=True)
    )

    # Calculate ASP
    weekday_sales["average_selling_price"] = (
        weekday_sales["sales_amount"]
        / weekday_sales["units_sold"]
    )

    # Calculate sales share
    total_sales = weekday_sales["sales_amount"].sum()

    weekday_sales["sales_share_percent"] = (
        weekday_sales["sales_amount"]
        / total_sales
        * 100
    )

    # Calculate units share
    total_units = weekday_sales["units_sold"].sum()

    weekday_sales["units_share_percent"] = (
        weekday_sales["units_sold"]
        / total_units
        * 100
    )

    print("\n" + "=" * 90)
    print("SALES BY DAY OF WEEK")
    print("=" * 90)

    print(
        weekday_sales.to_string(index=False)
    )

    print("\n" + "=" * 90)
    print("VERIFICATION")
    print("=" * 90)

    print(
        f"Number of Weekdays : "
        f"{len(weekday_sales):,}"
    )

    print(
        f"Total Units Sold   : "
        f"{weekday_sales['units_sold'].sum():,.0f}"
    )

    print(
        f"Total Sales $      : "
        f"{weekday_sales['sales_amount'].sum():,.2f}"
    )

    print("\nHighest Sales Weekdays:")

    print(
        weekday_sales
        .sort_values(
            "sales_amount",
            ascending=False
        )
        .head(3)
        .to_string(index=False)
    )

    print("\nLowest Sales Weekdays:")

    print(
        weekday_sales
        .sort_values(
            "sales_amount",
            ascending=True
        )
        .head(3)
        .to_string(index=False)
    )

    print("\nHighest ASP Weekdays:")

    print(
        weekday_sales
        .sort_values(
            "average_selling_price",
            ascending=False
        )
        .head(3)
        .to_string(index=False)
    )

    print("\nLowest ASP Weekdays:")

    print(
        weekday_sales
        .sort_values(
            "average_selling_price",
            ascending=True
        )
        .head(3)
        .to_string(index=False)
    )

    print("=" * 90)


if __name__ == "__main__":
    calculate_sales_by_weekday()