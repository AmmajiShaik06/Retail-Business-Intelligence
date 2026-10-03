
"""
Phase 10.2 - Store Intelligence

Purpose:
Combine verified store sales and purchase information
into a store-level intelligence dataset.

This script:
1. Reads sales and purchases from MySQL in chunks.
2. Aggregates store-level performance.
3. Calculates business intelligence indicators.
4. Assigns descriptive store segments.
5. Saves the result for later recommendation work.

Important:
- Store number is the store identity.
- No database tables are modified.
- Existing verified Phase 9 results are used for validation.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1

CHUNK_SIZE = 250_000


# ============================================================
# LOAD STORE SALES DATA
# ============================================================

def load_store_sales():

    print("\n" + "=" * 70)
    print("LOADING STORE SALES DATA")
    print("=" * 70)

    query = """
        SELECT
            store_number,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = %s
    """

    store_sales = {}

    total_rows = 0

    with engine.connect() as connection:

        for chunk in pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,),
            chunksize=CHUNK_SIZE
        ):

            total_rows += len(chunk)

            chunk["sales_quantity"] = pd.to_numeric(
                chunk["sales_quantity"],
                errors="coerce"
            ).fillna(0)

            chunk["sales_dollars"] = pd.to_numeric(
                chunk["sales_dollars"],
                errors="coerce"
            ).fillna(0)

            grouped = (
                chunk
                .groupby(
                    "store_number",
                    dropna=False
                )
                .agg(
                    sales_quantity=(
                        "sales_quantity",
                        "sum"
                    ),
                    sales_revenue=(
                        "sales_dollars",
                        "sum"
                    )
                )
                .reset_index()
            )

            for row in grouped.itertuples(index=False):

                store_number = row.store_number

                if store_number not in store_sales:

                    store_sales[store_number] = {
                        "sales_quantity": 0,
                        "sales_revenue": 0
                    }

                store_sales[store_number][
                    "sales_quantity"
                ] += row.sales_quantity

                store_sales[store_number][
                    "sales_revenue"
                ] += row.sales_revenue

    print(
        f"Sales rows processed: {total_rows:,}"
    )

    result = []

    for store_number, values in store_sales.items():

        result.append(
            {
                "store_number": store_number,
                "sales_quantity":
                    values["sales_quantity"],
                "sales_revenue":
                    values["sales_revenue"]
            }
        )

    return pd.DataFrame(result)


# ============================================================
# LOAD STORE PURCHASE DATA
# ============================================================

def load_store_purchases():

    print("\n" + "=" * 70)
    print("LOADING STORE PURCHASE DATA")
    print("=" * 70)

    query = """
        SELECT
            store_number,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = %s
    """

    store_purchases = {}

    total_rows = 0

    with engine.connect() as connection:

        for chunk in pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,),
            chunksize=CHUNK_SIZE
        ):

            total_rows += len(chunk)

            chunk["quantity"] = pd.to_numeric(
                chunk["quantity"],
                errors="coerce"
            ).fillna(0)

            chunk["dollars"] = pd.to_numeric(
                chunk["dollars"],
                errors="coerce"
            ).fillna(0)

            grouped = (
                chunk
                .groupby(
                    "store_number",
                    dropna=False
                )
                .agg(
                    purchase_quantity=(
                        "quantity",
                        "sum"
                    ),
                    purchase_spending=(
                        "dollars",
                        "sum"
                    )
                )
                .reset_index()
            )

            for row in grouped.itertuples(index=False):

                store_number = row.store_number

                if store_number not in store_purchases:

                    store_purchases[store_number] = {
                        "purchase_quantity": 0,
                        "purchase_spending": 0
                    }

                store_purchases[store_number][
                    "purchase_quantity"
                ] += row.purchase_quantity

                store_purchases[store_number][
                    "purchase_spending"
                ] += row.purchase_spending

    print(
        f"Purchase rows processed: {total_rows:,}"
    )

    result = []

    for store_number, values in store_purchases.items():

        result.append(
            {
                "store_number": store_number,
                "purchase_quantity":
                    values["purchase_quantity"],
                "purchase_spending":
                    values["purchase_spending"]
            }
        )

    return pd.DataFrame(result)


# ============================================================
# BUILD STORE INTELLIGENCE
# ============================================================

def build_store_intelligence(
    store_sales,
    store_purchases
):

    print("\n" + "=" * 70)
    print("BUILDING STORE INTELLIGENCE")
    print("=" * 70)

    stores = pd.merge(
        store_sales,
        store_purchases,
        on="store_number",
        how="outer"
    )

    numeric_columns = [
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending"
    ]

    for column in numeric_columns:

        stores[column] = (
            pd.to_numeric(
                stores[column],
                errors="coerce"
            )
            .fillna(0)
        )

    # --------------------------------------------------------
    # Overall totals
    # --------------------------------------------------------

    total_sales_revenue = (
        stores["sales_revenue"].sum()
    )

    total_purchase_spending = (
        stores["purchase_spending"].sum()
    )

    # --------------------------------------------------------
    # Contribution percentages
    # --------------------------------------------------------

    stores["sales_contribution_percent"] = (
        stores["sales_revenue"]
        / total_sales_revenue
        * 100
    )

    stores["purchase_contribution_percent"] = (
        stores["purchase_spending"]
        / total_purchase_spending
        * 100
    )

    # --------------------------------------------------------
    # Quantity balance
    #
    # Positive:
    # purchases > sales
    #
    # Negative:
    # sales > purchases
    # --------------------------------------------------------

    stores["quantity_balance"] = (
        stores["purchase_quantity"]
        - stores["sales_quantity"]
    )

    # --------------------------------------------------------
    # Sales-to-purchase value ratio
    #
    # IMPORTANT:
    # This is NOT profit margin.
    # --------------------------------------------------------

    stores["sales_purchase_value_ratio"] = 0.0

    purchase_mask = (
        stores["purchase_spending"] > 0
    )

    stores.loc[
        purchase_mask,
        "sales_purchase_value_ratio"
    ] = (
        stores.loc[
            purchase_mask,
            "sales_revenue"
        ]
        / stores.loc[
            purchase_mask,
            "purchase_spending"
        ]
    )

    # --------------------------------------------------------
    # Average sales value per unit
    # --------------------------------------------------------

    stores["average_sales_value"] = 0.0

    sales_mask = (
        stores["sales_quantity"] > 0
    )

    stores.loc[
        sales_mask,
        "average_sales_value"
    ] = (
        stores.loc[
            sales_mask,
            "sales_revenue"
        ]
        / stores.loc[
            sales_mask,
            "sales_quantity"
        ]
    )

    # --------------------------------------------------------
    # Average purchase cost per unit
    # --------------------------------------------------------

    stores["average_purchase_cost"] = 0.0

    stores.loc[
        purchase_mask,
        "average_purchase_cost"
    ] = (
        stores.loc[
            purchase_mask,
            "purchase_spending"
        ]
        / stores.loc[
            purchase_mask,
            "purchase_quantity"
        ]
    )

    # --------------------------------------------------------
    # Quantity balance percentage
    # --------------------------------------------------------

    stores["quantity_balance_percent"] = 0.0

    stores.loc[
        purchase_mask,
        "quantity_balance_percent"
    ] = (
        stores.loc[
            purchase_mask,
            "quantity_balance"
        ]
        / stores.loc[
            purchase_mask,
            "purchase_quantity"
        ]
        * 100
    )

    # --------------------------------------------------------
    # Store segmentation
    #
    # Uses median sales and purchase values.
    # This is descriptive segmentation, not ranking.
    # --------------------------------------------------------

    sales_median = (
        stores["sales_revenue"]
        .median()
    )

    purchase_median = (
        stores["purchase_spending"]
        .median()
    )

    def assign_segment(row):

        high_sales = (
            row["sales_revenue"]
            >= sales_median
        )

        high_purchase = (
            row["purchase_spending"]
            >= purchase_median
        )

        if high_sales and high_purchase:

            return "High Sales / High Purchase"

        elif high_sales and not high_purchase:

            return "High Sales / Lower Purchase"

        elif not high_sales and high_purchase:

            return "Lower Sales / High Purchase"

        else:

            return "Lower Sales / Lower Purchase"

    stores["store_segment"] = (
        stores.apply(
            assign_segment,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Sort by sales revenue
    # --------------------------------------------------------

    stores = stores.sort_values(
        "sales_revenue",
        ascending=False
    )

    stores = stores.reset_index(
        drop=True
    )

    return stores


# ============================================================
# DISPLAY STORE INTELLIGENCE
# ============================================================

def display_store_intelligence(
    stores
):

    print("\n" + "=" * 70)
    print("TOP STORE INTELLIGENCE")
    print("=" * 70)

    display_columns = [
        "store_number",
        "sales_revenue",
        "purchase_spending",
        "sales_contribution_percent",
        "purchase_contribution_percent",
        "quantity_balance",
        "sales_purchase_value_ratio",
        "store_segment"
    ]

    print(
        stores[
            display_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print("\n" + "-" * 70)
    print("STORE SEGMENT COUNTS")
    print("-" * 70)

    print(
        stores[
            "store_segment"
        ]
        .value_counts()
        .to_string()
    )

    print("\n" + "-" * 70)
    print("STORE QUANTITY BALANCE")
    print("-" * 70)

    purchase_greater = (
        stores[
            "quantity_balance"
        ] > 0
    ).sum()

    sales_greater = (
        stores[
            "quantity_balance"
        ] < 0
    ).sum()

    balanced = (
        stores[
            "quantity_balance"
        ] == 0
    ).sum()

    print(
        f"Purchase quantity > Sales quantity: "
        f"{purchase_greater}"
    )

    print(
        f"Sales quantity > Purchase quantity: "
        f"{sales_greater}"
    )

    print(
        f"Sales quantity = Purchase quantity: "
        f"{balanced}"
    )


# ============================================================
# SAVE RESULT
# ============================================================

def save_store_intelligence(
    stores
):

    output_path = (
        "data/processed/store_intelligence.csv"
    )

    stores.to_csv(
        output_path,
        index=False
    )

    print("\n" + "-" * 70)
    print("OUTPUT")
    print("-" * 70)

    print(
        "Store intelligence saved to:"
    )

    print(
        output_path
    )

    print(
        f"Store records saved: "
        f"{len(stores):,}"
    )


# ============================================================
# VERIFY
# ============================================================

def verify_store_intelligence(
    stores
):

    print("\n" + "=" * 70)
    print("VERIFYING STORE INTELLIGENCE")
    print("=" * 70)

    # --------------------------------------------------------
    # Store count
    # --------------------------------------------------------

    expected_store_count = 80

    if len(stores) == expected_store_count:

        print(
            "✓ Store count: PASSED"
        )

    else:

        print(
            "✗ Store count: FAILED"
        )

        print(
            f"Expected: {expected_store_count}"
        )

        print(
            f"Actual: {len(stores)}"
        )

        raise ValueError(
            "Store count verification failed."
        )

    # --------------------------------------------------------
    # Sales quantity
    # --------------------------------------------------------

    sales_quantity = (
        stores["sales_quantity"].sum()
    )

    if sales_quantity == 32_917_876:

        print(
            "✓ Sales quantity: PASSED"
        )

    else:

        print(
            "✗ Sales quantity: FAILED"
        )

        raise ValueError(
            "Sales quantity verification failed."
        )

    # --------------------------------------------------------
    # Sales revenue
    # --------------------------------------------------------

    sales_revenue = (
        stores["sales_revenue"].sum()
    )

    if abs(
        sales_revenue
        - 452_062_952.02
    ) <= 0.01:

        print(
            "✓ Sales revenue: PASSED"
        )

    else:

        print(
            "✗ Sales revenue: FAILED"
        )

        raise ValueError(
            "Sales revenue verification failed."
        )

    # --------------------------------------------------------
    # Purchase quantity
    # --------------------------------------------------------

    purchase_quantity = (
        stores["purchase_quantity"].sum()
    )

    if purchase_quantity == 33_584_377:

        print(
            "✓ Purchase quantity: PASSED"
        )

    else:

        print(
            "✗ Purchase quantity: FAILED"
        )

        raise ValueError(
            "Purchase quantity verification failed."
        )

    # --------------------------------------------------------
    # Purchase spending
    # --------------------------------------------------------

    purchase_spending = (
        stores["purchase_spending"].sum()
    )

    if abs(
        purchase_spending
        - 321_900_765.53
    ) <= 0.01:

        print(
            "✓ Purchase spending: PASSED"
        )

    else:

        print(
            "✗ Purchase spending: FAILED"
        )

        raise ValueError(
            "Purchase spending verification failed."
        )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "store_number",
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending",
        "sales_contribution_percent",
        "purchase_contribution_percent",
        "quantity_balance",
        "sales_purchase_value_ratio",
        "average_sales_value",
        "average_purchase_cost",
        "quantity_balance_percent",
        "store_segment"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in stores.columns
    ]

    if not missing_columns:

        print(
            "✓ Required intelligence columns: PASSED"
        )

    else:

        print(
            "✗ Required intelligence columns: FAILED"
        )

        print(
            f"Missing: {missing_columns}"
        )

        raise ValueError(
            "Required intelligence columns missing."
        )

    # --------------------------------------------------------
    # Duplicate store identities
    # --------------------------------------------------------

    duplicate_count = (
        stores
        .duplicated(
            subset=["store_number"]
        )
        .sum()
    )

    if duplicate_count == 0:

        print(
            "✓ Duplicate store identities: PASSED"
        )

    else:

        print(
            "✗ Duplicate store identities: FAILED"
        )

        raise ValueError(
            "Duplicate store identities found."
        )

    print(
        "\n✓ ALL STORE INTELLIGENCE "
        "VERIFICATION CHECKS PASSED"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 10.2 - STORE INTELLIGENCE")
    print("=" * 70)

    store_sales = load_store_sales()

    store_purchases = load_store_purchases()

    stores = build_store_intelligence(
        store_sales,
        store_purchases
    )

    display_store_intelligence(
        stores
    )

    save_store_intelligence(
        stores
    )

    verify_store_intelligence(
        stores
    )

    print("\n" + "=" * 70)
    print("PHASE 10.2 COMPLETED SUCCESSFULLY")
    print("=" * 70)
