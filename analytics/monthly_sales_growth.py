import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_monthly_sales_growth():

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

    print("Starting Monthly Sales Growth Analysis...")
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

            chunk["month"] = (
                chunk["sales_date"]
                .dt.to_period("M")
                .astype(str)
            )

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

    # Combine chunk results
    monthly_sales = pd.concat(
        monthly_data,
        ignore_index=True
    )

    # Final monthly aggregation
    monthly_sales = (
        monthly_sales
        .groupby("month")
        .agg(
            units_sold=("units_sold", "sum"),
            sales_amount=("sales_amount", "sum")
        )
        .reset_index()
        .sort_values("month")
        .reset_index(drop=True)
    )

    # Previous month sales
    monthly_sales["previous_month_sales"] = (
        monthly_sales["sales_amount"].shift(1)
    )

    # Month-over-month dollar change
    monthly_sales["mom_change"] = (
        monthly_sales["sales_amount"]
        - monthly_sales["previous_month_sales"]
    )

    # Month-over-month percentage growth
    monthly_sales["mom_growth_percent"] = (
        monthly_sales["mom_change"]
        / monthly_sales["previous_month_sales"]
        * 100
    )

    print("\n" + "=" * 80)
    print("MONTHLY SALES GROWTH ANALYSIS")
    print("=" * 80)

    print(
        monthly_sales.to_string(index=False)
    )

    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    print(
        f"Number of Months : "
        f"{len(monthly_sales):,}"
    )

    print(
        f"Total Units Sold : "
        f"{monthly_sales['units_sold'].sum():,.0f}"
    )

    print(
        f"Total Sales $    : "
        f"{monthly_sales['sales_amount'].sum():,.2f}"
    )

    # First month has no previous month
    first_month_previous = monthly_sales.iloc[0]["previous_month_sales"]

    print(
        f"First Month Previous Sales : "
        f"{first_month_previous}"
    )

    print("\nHighest Positive MoM Growth:")

    print(
        monthly_sales
        .dropna(subset=["mom_growth_percent"])
        .sort_values(
            "mom_growth_percent",
            ascending=False
        )
        .head(5)
        .to_string(index=False)
    )

    print("\nLargest Negative MoM Growth:")

    print(
        monthly_sales
        .dropna(subset=["mom_growth_percent"])
        .sort_values(
            "mom_growth_percent",
            ascending=True
        )
        .head(5)
        .to_string(index=False)
    )

    print("=" * 80)


if __name__ == "__main__":
    calculate_monthly_sales_growth()