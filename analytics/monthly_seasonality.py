import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_monthly_seasonality():

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

    print("Starting Monthly Seasonality Analysis...")
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

            chunk["month_number"] = (
                chunk["sales_date"].dt.month
            )

            chunk["month_name"] = (
                chunk["sales_date"].dt.month_name()
            )

            grouped = (
                chunk.groupby(
                    ["month_number", "month_name"]
                )
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

    # Combine all chunk results
    monthly_sales = pd.concat(
        monthly_data,
        ignore_index=True
    )

    # Final monthly aggregation
    monthly_sales = (
        monthly_sales
        .groupby(
            ["month_number", "month_name"]
        )
        .agg(
            units_sold=("units_sold", "sum"),
            sales_amount=("sales_amount", "sum")
        )
        .reset_index()
        .sort_values("month_number")
        .reset_index(drop=True)
    )

    # Calculate each month's share of annual sales
    total_sales = monthly_sales["sales_amount"].sum()

    monthly_sales["sales_share_percent"] = (
        monthly_sales["sales_amount"]
        / total_sales
        * 100
    )

    # Calculate each month's share of annual units
    total_units = monthly_sales["units_sold"].sum()

    monthly_sales["units_share_percent"] = (
        monthly_sales["units_sold"]
        / total_units
        * 100
    )

    # Average monthly sales
    average_monthly_sales = (
        monthly_sales["sales_amount"].mean()
    )

    # Compare each month with average monthly sales
    monthly_sales["vs_average_percent"] = (
        (
            monthly_sales["sales_amount"]
            - average_monthly_sales
        )
        / average_monthly_sales
        * 100
    )

    print("\n" + "=" * 90)
    print("MONTHLY SALES SEASONALITY ANALYSIS")
    print("=" * 90)

    print(
        monthly_sales.to_string(index=False)
    )

    print("\n" + "=" * 90)
    print("VERIFICATION")
    print("=" * 90)

    print(
        f"Number of Months       : "
        f"{len(monthly_sales):,}"
    )

    print(
        f"Total Units Sold       : "
        f"{monthly_sales['units_sold'].sum():,.0f}"
    )

    print(
        f"Total Sales $          : "
        f"{monthly_sales['sales_amount'].sum():,.2f}"
    )

    print(
        f"Average Monthly Sales $: "
        f"{average_monthly_sales:,.2f}"
    )

    print("\nHighest Sales Month:")

    print(
        monthly_sales
        .sort_values(
            "sales_amount",
            ascending=False
        )
        .head(3)
        .to_string(index=False)
    )

    print("\nLowest Sales Month:")

    print(
        monthly_sales
        .sort_values(
            "sales_amount",
            ascending=True
        )
        .head(3)
        .to_string(index=False)
    )

    print("\nMonths Above Average:")

    print(
        monthly_sales[
            monthly_sales["sales_amount"]
            > average_monthly_sales
        ][
            [
                "month_number",
                "month_name",
                "sales_amount",
                "vs_average_percent"
            ]
        ].to_string(index=False)
    )

    print("\nMonths Below Average:")

    print(
        monthly_sales[
            monthly_sales["sales_amount"]
            < average_monthly_sales
        ][
            [
                "month_number",
                "month_name",
                "sales_amount",
                "vs_average_percent"
            ]
        ].to_string(index=False)
    )

    print("=" * 90)


if __name__ == "__main__":
    calculate_monthly_seasonality()