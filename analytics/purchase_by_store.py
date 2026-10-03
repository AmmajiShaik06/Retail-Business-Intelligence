import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def analyze_purchase_by_store():

    query = """
        SELECT
            store_number,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = :business_id
    """

    print("Starting Purchase by Store Analysis...")
    print(f"Chunk size: {CHUNK_SIZE:,}")

    store_results = []
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

            chunk["quantity"] = pd.to_numeric(
                chunk["quantity"],
                errors="coerce"
            )

            chunk["dollars"] = pd.to_numeric(
                chunk["dollars"],
                errors="coerce"
            )

            grouped = (
                chunk
                .groupby(
                    "store_number",
                    dropna=False
                )
                .agg(
                    purchase_quantity=("quantity", "sum"),
                    purchase_amount=("dollars", "sum"),
                    purchase_transactions=("dollars", "count")
                )
                .reset_index()
            )

            store_results.append(grouped)

            total_rows_processed += len(chunk)

            print(
                f"Processed rows: "
                f"{total_rows_processed:,}"
            )

    # ---------------------------------------------------------
    # COMBINE CHUNK RESULTS
    # ---------------------------------------------------------

    store_purchase = (
        pd.concat(
            store_results,
            ignore_index=True
        )
        .groupby(
            "store_number",
            dropna=False
        )
        .agg(
            purchase_quantity=("purchase_quantity", "sum"),
            purchase_amount=("purchase_amount", "sum"),
            purchase_transactions=("purchase_transactions", "sum")
        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # CALCULATE TOTALS
    # ---------------------------------------------------------

    total_quantity = store_purchase[
        "purchase_quantity"
    ].sum()

    total_amount = store_purchase[
        "purchase_amount"
    ].sum()

    # ---------------------------------------------------------
    # CONTRIBUTION PERCENTAGES
    # ---------------------------------------------------------

    store_purchase[
        "purchase_contribution_percent"
    ] = (
        store_purchase["purchase_amount"]
        / total_amount
        * 100
    )

    store_purchase[
        "quantity_contribution_percent"
    ] = (
        store_purchase["purchase_quantity"]
        / total_quantity
        * 100
    )

    # ---------------------------------------------------------
    # RANK STORES
    # ---------------------------------------------------------

    store_purchase["purchase_rank"] = (
        store_purchase["purchase_amount"]
        .rank(
            method="dense",
            ascending=False
        )
        .astype(int)
    )

    store_purchase = store_purchase.sort_values(
        "purchase_amount",
        ascending=False
    )

    # ---------------------------------------------------------
    # TOP 10 STORES
    # ---------------------------------------------------------

    print("\n" + "=" * 110)
    print("TOP 10 STORES BY PURCHASE AMOUNT")
    print("=" * 110)

    print(
        store_purchase[
            [
                "purchase_rank",
                "store_number",
                "purchase_quantity",
                "purchase_amount",
                "purchase_contribution_percent",
                "quantity_contribution_percent",
                "purchase_transactions"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # BOTTOM 10 STORES
    # ---------------------------------------------------------

    print("\n" + "=" * 110)
    print("BOTTOM 10 STORES BY PURCHASE AMOUNT")
    print("=" * 110)

    print(
        store_purchase[
            [
                "purchase_rank",
                "store_number",
                "purchase_quantity",
                "purchase_amount",
                "purchase_contribution_percent",
                "quantity_contribution_percent",
                "purchase_transactions"
            ]
        ]
        .tail(10)
        .sort_values("purchase_amount")
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # PURCHASE CONCENTRATION
    # ---------------------------------------------------------

    top_5_amount = (
        store_purchase
        .head(5)["purchase_amount"]
        .sum()
    )

    top_10_amount = (
        store_purchase
        .head(10)["purchase_amount"]
        .sum()
    )

    top_5_percent = (
        top_5_amount
        / total_amount
        * 100
    )

    top_10_percent = (
        top_10_amount
        / total_amount
        * 100
    )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print("\n" + "=" * 110)
    print("STORE PURCHASE CONCENTRATION")
    print("=" * 110)

    print(
        f"Number of Stores: "
        f"{len(store_purchase):,}"
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
        f"Top 5 Stores Purchase Amount: "
        f"${top_5_amount:,.2f}"
    )

    print(
        f"Top 5 Contribution: "
        f"{top_5_percent:.2f}%"
    )

    print(
        f"Top 10 Stores Purchase Amount: "
        f"${top_10_amount:,.2f}"
    )

    print(
        f"Top 10 Contribution: "
        f"{top_10_percent:.2f}%"
    )

    # ---------------------------------------------------------
    # VERIFICATION
    # ---------------------------------------------------------

    print("\n" + "=" * 110)
    print("VERIFICATION")
    print("=" * 110)

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

    print("\n" + "=" * 110)
    print("PURCHASE BY STORE ANALYSIS COMPLETE")
    print("=" * 110)


if __name__ == "__main__":
    analyze_purchase_by_store()