
"""
Phase 10.1 - Vendor Intelligence

Purpose:
Combine verified vendor sales and purchase information
into a vendor-level intelligence dataset.

This script:
1. Reads sales and purchases from MySQL in chunks.
2. Aggregates vendor-level performance.
3. Calculates business intelligence indicators.
4. Assigns descriptive vendor segments.
5. Saves the result for later recommendation work.

Important:
- VendorNumber + VendorName is used as the vendor identity.
- This avoids incorrectly merging conflicting vendor names.
- No database tables are modified.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1

CHUNK_SIZE = 250_000


# ============================================================
# LOAD VENDOR SALES DATA
# ============================================================

def load_vendor_sales():

    print("\n" + "=" * 70)
    print("LOADING VENDOR SALES DATA")
    print("=" * 70)

    query = """
        SELECT
            vendor_number,
            vendor_name,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = %s
    """

    vendor_sales = {}

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
                    [
                        "vendor_number",
                        "vendor_name"
                    ],
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

                key = (
                    row.vendor_number,
                    row.vendor_name
                )

                if key not in vendor_sales:

                    vendor_sales[key] = {
                        "sales_quantity": 0,
                        "sales_revenue": 0
                    }

                vendor_sales[key]["sales_quantity"] += (
                    row.sales_quantity
                )

                vendor_sales[key]["sales_revenue"] += (
                    row.sales_revenue
                )

    print(
        f"Sales rows processed: {total_rows:,}"
    )

    result = []

    for key, values in vendor_sales.items():

        result.append(
            {
                "vendor_number": key[0],
                "vendor_name": key[1],
                "sales_quantity":
                    values["sales_quantity"],
                "sales_revenue":
                    values["sales_revenue"]
            }
        )

    return pd.DataFrame(result)


# ============================================================
# LOAD VENDOR PURCHASE DATA
# ============================================================

def load_vendor_purchases():

    print("\n" + "=" * 70)
    print("LOADING VENDOR PURCHASE DATA")
    print("=" * 70)

    query = """
        SELECT
            vendor_number,
            vendor_name,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = %s
    """

    vendor_purchases = {}

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
                    purchase_spending=(
                        "dollars",
                        "sum"
                    )
                )
                .reset_index()
            )

            for row in grouped.itertuples(index=False):

                key = (
                    row.vendor_number,
                    row.vendor_name
                )

                if key not in vendor_purchases:

                    vendor_purchases[key] = {
                        "purchase_quantity": 0,
                        "purchase_spending": 0
                    }

                vendor_purchases[key]["purchase_quantity"] += (
                    row.purchase_quantity
                )

                vendor_purchases[key]["purchase_spending"] += (
                    row.purchase_spending
                )

    print(
        f"Purchase rows processed: {total_rows:,}"
    )

    result = []

    for key, values in vendor_purchases.items():

        result.append(
            {
                "vendor_number": key[0],
                "vendor_name": key[1],
                "purchase_quantity":
                    values["purchase_quantity"],
                "purchase_spending":
                    values["purchase_spending"]
            }
        )

    return pd.DataFrame(result)


# ============================================================
# BUILD VENDOR INTELLIGENCE
# ============================================================

def build_vendor_intelligence(
    vendor_sales,
    vendor_purchases
):

    print("\n" + "=" * 70)
    print("BUILDING VENDOR INTELLIGENCE")
    print("=" * 70)

    vendors = pd.merge(
        vendor_sales,
        vendor_purchases,
        on=[
            "vendor_number",
            "vendor_name"
        ],
        how="outer"
    )

    numeric_columns = [
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending"
    ]

    for column in numeric_columns:

        vendors[column] = (
            pd.to_numeric(
                vendors[column],
                errors="coerce"
            )
            .fillna(0)
        )

    # --------------------------------------------------------
    # Overall totals
    # --------------------------------------------------------

    total_sales_revenue = (
        vendors["sales_revenue"].sum()
    )

    total_purchase_spending = (
        vendors["purchase_spending"].sum()
    )

    # --------------------------------------------------------
    # Contribution percentages
    # --------------------------------------------------------

    vendors["sales_contribution_percent"] = (
        vendors["sales_revenue"]
        / total_sales_revenue
        * 100
    )

    vendors["purchase_contribution_percent"] = (
        vendors["purchase_spending"]
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

    vendors["quantity_balance"] = (
        vendors["purchase_quantity"]
        - vendors["sales_quantity"]
    )

    # --------------------------------------------------------
    # Value ratio
    #
    # IMPORTANT:
    # This is NOT profit margin.
    # --------------------------------------------------------

    vendors["sales_purchase_value_ratio"] = 0.0

    mask = (
        vendors["purchase_spending"] > 0
    )

    vendors.loc[mask, "sales_purchase_value_ratio"] = (
        vendors.loc[mask, "sales_revenue"]
        / vendors.loc[mask, "purchase_spending"]
    )

    # --------------------------------------------------------
    # Average selling value per unit
    # --------------------------------------------------------

    vendors["average_sales_value"] = 0.0

    sales_mask = (
        vendors["sales_quantity"] > 0
    )

    vendors.loc[
        sales_mask,
        "average_sales_value"
    ] = (
        vendors.loc[
            sales_mask,
            "sales_revenue"
        ]
        / vendors.loc[
            sales_mask,
            "sales_quantity"
        ]
    )

    # --------------------------------------------------------
    # Average purchase cost per unit
    # --------------------------------------------------------

    vendors["average_purchase_cost"] = 0.0

    purchase_mask = (
        vendors["purchase_quantity"] > 0
    )

    vendors.loc[
        purchase_mask,
        "average_purchase_cost"
    ] = (
        vendors.loc[
            purchase_mask,
            "purchase_spending"
        ]
        / vendors.loc[
            purchase_mask,
            "purchase_quantity"
        ]
    )

    # --------------------------------------------------------
    # Percentage quantity balance
    # --------------------------------------------------------

    vendors["quantity_balance_percent"] = 0.0

    vendors.loc[
        purchase_mask,
        "quantity_balance_percent"
    ] = (
        vendors.loc[
            purchase_mask,
            "quantity_balance"
        ]
        / vendors.loc[
            purchase_mask,
            "purchase_quantity"
        ]
        * 100
    )

    # --------------------------------------------------------
    # Vendor segment
    #
    # Uses median sales and purchase values.
    # This is descriptive segmentation, not a ranking.
    # --------------------------------------------------------

    sales_median = (
        vendors["sales_revenue"]
        .median()
    )

    purchase_median = (
        vendors["purchase_spending"]
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

    vendors["vendor_segment"] = (
        vendors.apply(
            assign_segment,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Sort by sales revenue
    # --------------------------------------------------------

    vendors = vendors.sort_values(
        "sales_revenue",
        ascending=False
    )

    vendors = vendors.reset_index(
        drop=True
    )

    return vendors


# ============================================================
# DISPLAY VENDOR INTELLIGENCE
# ============================================================

def display_vendor_intelligence(
    vendors
):

    print("\n" + "=" * 70)
    print("TOP VENDOR INTELLIGENCE")
    print("=" * 70)

    display_columns = [
        "vendor_number",
        "vendor_name",
        "sales_revenue",
        "purchase_spending",
        "sales_contribution_percent",
        "purchase_contribution_percent",
        "quantity_balance",
        "sales_purchase_value_ratio",
        "vendor_segment"
    ]

    print(
        vendors[
            display_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print("\n" + "-" * 70)
    print("VENDOR SEGMENT COUNTS")
    print("-" * 70)

    print(
        vendors[
            "vendor_segment"
        ]
        .value_counts()
        .to_string()
    )

    print("\n" + "-" * 70)
    print("VENDOR QUANTITY BALANCE")
    print("-" * 70)

    sales_less_than_purchase = (
        vendors[
            "quantity_balance"
        ] > 0
    ).sum()

    sales_greater_than_purchase = (
        vendors[
            "quantity_balance"
        ] < 0
    ).sum()

    balanced = (
        vendors[
            "quantity_balance"
        ] == 0
    ).sum()

    print(
        f"Purchase quantity > Sales quantity: "
        f"{sales_less_than_purchase}"
    )

    print(
        f"Sales quantity > Purchase quantity: "
        f"{sales_greater_than_purchase}"
    )

    print(
        f"Sales quantity = Purchase quantity: "
        f"{balanced}"
    )


# ============================================================
# SAVE RESULT
# ============================================================

def save_vendor_intelligence(
    vendors
):

    output_path = (
        "data/processed/vendor_intelligence.csv"
    )

    vendors.to_csv(
        output_path,
        index=False
    )

    print("\n" + "-" * 70)
    print("OUTPUT")
    print("-" * 70)

    print(
        f"Vendor intelligence saved to:"
    )

    print(
        output_path
    )

    print(
        f"Vendor records saved: "
        f"{len(vendors):,}"
    )


# ============================================================
# VERIFY
# ============================================================

def verify_vendor_intelligence(
    vendors
):

    print("\n" + "=" * 70)
    print("VERIFYING VENDOR INTELLIGENCE")
    print("=" * 70)

    # --------------------------------------------------------
    # Vendor count
    # --------------------------------------------------------

    expected_vendor_combinations = 131

    actual_vendor_combinations = len(
        vendors
    )

    if (
        actual_vendor_combinations
        == expected_vendor_combinations
    ):

        print(
            "✓ Vendor combinations: PASSED"
        )

    else:

        print(
            "✗ Vendor combinations: FAILED"
        )

        print(
            f"Expected: "
            f"{expected_vendor_combinations}"
        )

        print(
            f"Actual: "
            f"{actual_vendor_combinations}"
        )

        raise ValueError(
            "Vendor combination count failed."
        )

    # --------------------------------------------------------
    # Sales quantity
    # --------------------------------------------------------

    sales_quantity = (
        vendors["sales_quantity"].sum()
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
        vendors["sales_revenue"].sum()
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
        vendors["purchase_quantity"].sum()
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
        vendors["purchase_spending"].sum()
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
        "vendor_number",
        "vendor_name",
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
        "vendor_segment"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in vendors.columns
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
    # Check for duplicate vendor identities
    # --------------------------------------------------------

    duplicate_count = (
        vendors
        .duplicated(
            subset=[
                "vendor_number",
                "vendor_name"
            ]
        )
        .sum()
    )

    if duplicate_count == 0:

        print(
            "✓ Duplicate vendor identities: PASSED"
        )

    else:

        print(
            "✗ Duplicate vendor identities: FAILED"
        )

        raise ValueError(
            "Duplicate vendor identities found."
        )

    print(
        "\n✓ ALL VENDOR INTELLIGENCE "
        "VERIFICATION CHECKS PASSED"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 10.1 - VENDOR INTELLIGENCE")
    print("=" * 70)

    vendor_sales = load_vendor_sales()

    vendor_purchases = load_vendor_purchases()

    vendors = build_vendor_intelligence(
        vendor_sales,
        vendor_purchases
    )

    display_vendor_intelligence(
        vendors
    )

    save_vendor_intelligence(
        vendors
    )

    verify_vendor_intelligence(
        vendors
    )

    print("\n" + "=" * 70)
    print("PHASE 10.1 COMPLETED SUCCESSFULLY")
    print("=" * 70)
