import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def analyze_monthly_purchase_trend():

    query = """
        SELECT
            po_date,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = :business_id
    """

    print("Starting Monthly Purchase Trend Analysis...")
    print(f"Chunk size: {CHUNK_SIZE:,}")

    monthly_results = []
    total_rows_processed = 0

    # ---------------------------------------------------------
    # READ PURCHASE DATA IN CHUNKS
    # ---------------------------------------------------------

    with engine.connect() as connection:

        for chunk in pd.read_sql(
            text(query),
            connection,
            params={"business_id": BUSINESS_ID},
            chunksize=CHUNK_SIZE
        ):

            chunk["po_date"] = pd.to_datetime(
                chunk["po_date"],
                errors="coerce"
            )

            chunk["quantity"] = pd.to_numeric(
                chunk["quantity"],
                errors="coerce"
            )

            chunk["dollars"] = pd.to_numeric(
                chunk["dollars"],
                errors="coerce"
            )

            # Remove rows where PO date is invalid
            chunk = chunk.dropna(
                subset=["po_date"]
            )

            # Create month
            chunk["month"] = (
                chunk["po_date"]
                .dt.to_period("M")
                .astype(str)
            )

            grouped = (
                chunk
                .groupby("month")
                .agg(
                    purchase_quantity=("quantity", "sum"),
                    purchase_amount=("dollars", "sum"),
                    purchase_transactions=("dollars", "count")
                )
                .reset_index()
            )

            monthly_results.append(grouped)

            total_rows_processed += len(chunk)

            print(
                f"Processed rows: "
                f"{total_rows_processed:,}"
            )

    # ---------------------------------------------------------
    # COMBINE CHUNK RESULTS
    # ---------------------------------------------------------

    monthly_purchase = (
        pd.concat(
            monthly_results,
            ignore_index=True
        )
        .groupby("month")
        .agg(
            purchase_quantity=("purchase_quantity", "sum"),
            purchase_amount=("purchase_amount", "sum"),
            purchase_transactions=("purchase_transactions", "sum")
        )
        .reset_index()
    )

    # Convert month to datetime for correct sorting
    monthly_purchase["month"] = pd.to_datetime(
        monthly_purchase["month"]
    )

    monthly_purchase = monthly_purchase.sort_values(
        "month"
    ).reset_index(drop=True)

    # ---------------------------------------------------------
    # MONTH-OVER-MONTH ANALYSIS
    # ---------------------------------------------------------

    monthly_purchase["previous_month_purchase"] = (
        monthly_purchase["purchase_amount"]
        .shift(1)
    )

    monthly_purchase["mom_change"] = (
        monthly_purchase["purchase_amount"]
        - monthly_purchase["previous_month_purchase"]
    )

    monthly_purchase["mom_growth_percent"] = (
        monthly_purchase["mom_change"]
        / monthly_purchase["previous_month_purchase"]
        * 100
    )

    # ---------------------------------------------------------
    # PRINT MONTHLY RESULTS
    # ---------------------------------------------------------

    print("\n" + "=" * 120)
    print("MONTHLY PURCHASE TREND")
    print("=" * 120)

    display_data = monthly_purchase.copy()

    display_data["month"] = (
        display_data["month"]
        .dt.strftime("%Y-%m")
    )

    print(
        display_data[
            [
                "month",
                "purchase_quantity",
                "purchase_amount",
                "purchase_transactions",
                "previous_month_purchase",
                "mom_change",
                "mom_growth_percent"
            ]
        ]
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # TOTALS
    # ---------------------------------------------------------

    total_quantity = monthly_purchase[
        "purchase_quantity"
    ].sum()

    total_amount = monthly_purchase[
        "purchase_amount"
    ].sum()

    # ---------------------------------------------------------
    # HIGHEST / LOWEST MONTH
    # ---------------------------------------------------------

    highest_month = monthly_purchase.loc[
        monthly_purchase["purchase_amount"].idxmax()
    ]

    lowest_month = monthly_purchase.loc[
        monthly_purchase["purchase_amount"].idxmin()
    ]

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print("\n" + "=" * 120)
    print("PURCHASE TREND SUMMARY")
    print("=" * 120)

    print(
        f"Number of Months: "
        f"{len(monthly_purchase):,}"
    )

    print(
        f"Total Purchase Quantity: "
        f"{total_quantity:,.2f}"
    )

    print(
        f"Total Purchase Amount: "
        f"${total_amount:,.2f}"
    )

    print(
        f"Highest Purchase Month: "
        f"{highest_month['month'].strftime('%Y-%m')}"
    )

    print(
        f"Highest Purchase Amount: "
        f"${highest_month['purchase_amount']:,.2f}"
    )

    print(
        f"Lowest Purchase Month: "
        f"{lowest_month['month'].strftime('%Y-%m')}"
    )

    print(
        f"Lowest Purchase Amount: "
        f"${lowest_month['purchase_amount']:,.2f}"
    )

    # ---------------------------------------------------------
    # VERIFICATION
    # ---------------------------------------------------------

    print("\n" + "=" * 120)
    print("VERIFICATION")
    print("=" * 120)

    print(
        f"Processed Purchase Rows: "
        f"{total_rows_processed:,}"
    )

    print(
        "Expected Purchase Rows: "
        "2,372,474"
    )

    if total_rows_processed == 2_372_474:
        print("Row count verification: PASSED")
    else:
        print("Row count verification: FAILED")

    print(
        f"\nTotal Purchase Quantity: "
        f"{total_quantity:,.2f}"
    )

    print(
        f"Total Purchase Amount: "
        f"${total_amount:,.2f}"
    )

    # Compare with previously verified totals
    expected_quantity = 33_584_377
    expected_amount = 321_900_765.53

    if abs(total_quantity - expected_quantity) < 0.01:
        print("Purchase quantity verification: PASSED")
    else:
        print("Purchase quantity verification: FAILED")

    if abs(total_amount - expected_amount) < 0.01:
        print("Purchase amount verification: PASSED")
    else:
        print("Purchase amount verification: FAILED")

    print("\n" + "=" * 120)
    print("MONTHLY PURCHASE TREND ANALYSIS COMPLETE")
    print("=" * 120)


if __name__ == "__main__":
    analyze_monthly_purchase_trend()