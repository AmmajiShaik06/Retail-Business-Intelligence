import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def analyze_purchase_price():

    query = """
        SELECT
            vendor_number,
            vendor_name,
            brand,
            description,
            size,
            quantity,
            purchase_price,
            dollars
        FROM purchases
        WHERE business_id = :business_id
    """

    print("Starting Purchase Price Analysis...")
    print(f"Chunk size: {CHUNK_SIZE:,}")

    vendor_results = []
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

            chunk["purchase_price"] = pd.to_numeric(
                chunk["purchase_price"],
                errors="coerce"
            )

            chunk["dollars"] = pd.to_numeric(
                chunk["dollars"],
                errors="coerce"
            )

            # -------------------------------------------------
            # Weighted purchase price
            #
            # purchase_price × quantity
            # -------------------------------------------------

            chunk["price_x_quantity"] = (
                chunk["purchase_price"]
                * chunk["quantity"]
            )

            grouped = (
                chunk
                .groupby(
                    [
                        "vendor_number",
                        "vendor_name"
                    ],
                    dropna=False
                )
                .agg(
                    purchase_quantity=(
                        "quantity",
                        "sum"
                    ),
                    purchase_amount=(
                        "dollars",
                        "sum"
                    ),
                    price_x_quantity=(
                        "price_x_quantity",
                        "sum"
                    ),
                    purchase_transactions=(
                        "dollars",
                        "count"
                    ),
                    unique_products=(
                        "description",
                        "nunique"
                    )
                )
                .reset_index()
            )

            vendor_results.append(grouped)

            total_rows_processed += len(chunk)

            print(
                f"Processed rows: "
                f"{total_rows_processed:,}"
            )

    # ---------------------------------------------------------
    # COMBINE CHUNK RESULTS
    # ---------------------------------------------------------

    vendor_price = (
        pd.concat(
            vendor_results,
            ignore_index=True
        )
        .groupby(
            [
                "vendor_number",
                "vendor_name"
            ],
            dropna=False
        )
        .agg(
            purchase_quantity=(
                "purchase_quantity",
                "sum"
            ),
            purchase_amount=(
                "purchase_amount",
                "sum"
            ),
            price_x_quantity=(
                "price_x_quantity",
                "sum"
            ),
            purchase_transactions=(
                "purchase_transactions",
                "sum"
            ),
            unique_products=(
                "unique_products",
                "sum"
            )
        )
        .reset_index()
    )

    # ---------------------------------------------------------
    # WEIGHTED AVERAGE PURCHASE PRICE
    # ---------------------------------------------------------

    vendor_price["weighted_avg_purchase_price"] = (
        vendor_price["price_x_quantity"]
        / vendor_price["purchase_quantity"]
    )

    # ---------------------------------------------------------
    # PURCHASE CONTRIBUTION
    # ---------------------------------------------------------

    total_purchase_amount = (
        vendor_price["purchase_amount"].sum()
    )

    vendor_price["purchase_contribution_percent"] = (
        vendor_price["purchase_amount"]
        / total_purchase_amount
        * 100
    )

    # ---------------------------------------------------------
    # SORT BY PURCHASE SPENDING
    # ---------------------------------------------------------

    vendor_price = vendor_price.sort_values(
        "purchase_amount",
        ascending=False
    )

    # ---------------------------------------------------------
    # TOP 10 VENDORS BY PURCHASE SPENDING
    # ---------------------------------------------------------

    print("\n" + "=" * 120)
    print("TOP 10 VENDORS BY PURCHASE SPENDING AND PRICE")
    print("=" * 120)

    print(
        vendor_price[
            [
                "vendor_number",
                "vendor_name",
                "purchase_quantity",
                "purchase_amount",
                "weighted_avg_purchase_price",
                "purchase_contribution_percent",
                "unique_products",
                "purchase_transactions"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # HIGHEST WEIGHTED PURCHASE PRICE
    # ---------------------------------------------------------

    print("\n" + "=" * 120)
    print("TOP 10 VENDORS BY WEIGHTED AVERAGE PURCHASE PRICE")
    print("=" * 120)

    highest_price = (
        vendor_price
        .sort_values(
            "weighted_avg_purchase_price",
            ascending=False
        )
        .head(10)
    )

    print(
        highest_price[
            [
                "vendor_number",
                "vendor_name",
                "weighted_avg_purchase_price",
                "purchase_quantity",
                "purchase_amount",
                "unique_products"
            ]
        ]
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # LOWEST WEIGHTED PURCHASE PRICE
    # ---------------------------------------------------------

    print("\n" + "=" * 120)
    print("BOTTOM 10 VENDORS BY WEIGHTED AVERAGE PURCHASE PRICE")
    print("=" * 120)

    lowest_price = (
        vendor_price
        .sort_values(
            "weighted_avg_purchase_price",
            ascending=True
        )
        .head(10)
    )

    print(
        lowest_price[
            [
                "vendor_number",
                "vendor_name",
                "weighted_avg_purchase_price",
                "purchase_quantity",
                "purchase_amount",
                "unique_products"
            ]
        ]
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    total_quantity = (
        vendor_price["purchase_quantity"].sum()
    )

    total_amount = (
        vendor_price["purchase_amount"].sum()
    )

    overall_weighted_price = (
        vendor_price["price_x_quantity"].sum()
        / total_quantity
    )

    print("\n" + "=" * 120)
    print("PURCHASE PRICE SUMMARY")
    print("=" * 120)

    print(
        f"Vendor Number + Name Combinations: "
        f"{len(vendor_price):,}"
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
        f"Overall Weighted Average Purchase Price: "
        f"${overall_weighted_price:.4f}"
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

    expected_quantity = 33_584_377
    expected_amount = 321_900_765.53

    print(
        f"\nTotal Purchase Quantity: "
        f"{total_quantity:,.2f}"
    )

    print(
        f"Total Purchase Amount: "
        f"${total_amount:,.2f}"
    )

    if abs(total_quantity - expected_quantity) < 0.01:
        print("Purchase quantity verification: PASSED")
    else:
        print("Purchase quantity verification: FAILED")

    if abs(total_amount - expected_amount) < 0.01:
        print("Purchase amount verification: PASSED")
    else:
        print("Purchase amount verification: FAILED")

    print("\n" + "=" * 120)
    print("PURCHASE PRICE ANALYSIS COMPLETE")
    print("=" * 120)


if __name__ == "__main__":
    analyze_purchase_price()