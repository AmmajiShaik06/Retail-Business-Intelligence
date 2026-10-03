"""
Phase 9.5.3
Vendor Sales vs Purchase Analysis

Purpose:
Compare vendor sales performance with vendor purchase activity.

Important:
Sales revenue / purchase spending is NOT profit.
The ratio is only a sales-value-to-purchase-value comparison.

Vendor identity:
VendorNumber + VendorName

Because the dataset contains vendor-number/name conflicts,
we preserve the combination rather than using VendorNumber alone.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1

CHUNK_SIZE = 50_000

EXPECTED_SALES_QUANTITY = 32_917_876

EXPECTED_SALES_REVENUE = 452_062_952.02

EXPECTED_PURCHASE_QUANTITY = 33_584_377

EXPECTED_PURCHASE_VALUE = 321_900_765.53


# ============================================================
# 1. LOAD SALES BY VENDOR
# ============================================================

def load_vendor_sales():

    print("\n" + "=" * 70)
    print("LOADING SALES DATA BY VENDOR")
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

    vendor_data = {}

    total_rows = 0

    for chunk in pd.read_sql_query(
        query,
        engine,
        params=(BUSINESS_ID,),
        chunksize=CHUNK_SIZE
    ):

        total_rows += len(chunk)

        chunk["vendor_number"] = pd.to_numeric(
            chunk["vendor_number"],
            errors="coerce"
        )

        chunk["sales_quantity"] = pd.to_numeric(
            chunk["sales_quantity"],
            errors="coerce"
        ).fillna(0)

        chunk["sales_dollars"] = pd.to_numeric(
            chunk["sales_dollars"],
            errors="coerce"
        ).fillna(0)

        chunk["vendor_name"] = (
            chunk["vendor_name"]
            .astype("string")
            .str.strip()
            .fillna("UNKNOWN")
        )

        chunk = chunk.dropna(
            subset=["vendor_number"]
        )

        grouped = (
            chunk
            .groupby(
                [
                    "vendor_number",
                    "vendor_name"
                ]
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

        for _, row in grouped.iterrows():

            key = (
                int(row["vendor_number"]),
                row["vendor_name"]
            )

            if key not in vendor_data:

                vendor_data[key] = {
                    "sales_quantity": 0,
                    "sales_revenue": 0
                }

            vendor_data[key]["sales_quantity"] += (
                row["sales_quantity"]
            )

            vendor_data[key]["sales_revenue"] += (
                row["sales_revenue"]
            )

    print(
        f"Sales rows processed: "
        f"{total_rows:,}"
    )

    return vendor_data


# ============================================================
# 2. LOAD PURCHASES BY VENDOR
# ============================================================

def load_vendor_purchases():

    print("\n" + "=" * 70)
    print("LOADING PURCHASE DATA BY VENDOR")
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

    vendor_data = {}

    total_rows = 0

    for chunk in pd.read_sql_query(
        query,
        engine,
        params=(BUSINESS_ID,),
        chunksize=CHUNK_SIZE
    ):

        total_rows += len(chunk)

        chunk["vendor_number"] = pd.to_numeric(
            chunk["vendor_number"],
            errors="coerce"
        )

        chunk["quantity"] = pd.to_numeric(
            chunk["quantity"],
            errors="coerce"
        ).fillna(0)

        chunk["dollars"] = pd.to_numeric(
            chunk["dollars"],
            errors="coerce"
        ).fillna(0)

        chunk["vendor_name"] = (
            chunk["vendor_name"]
            .astype("string")
            .str.strip()
            .fillna("UNKNOWN")
        )

        chunk = chunk.dropna(
            subset=["vendor_number"]
        )

        grouped = (
            chunk
            .groupby(
                [
                    "vendor_number",
                    "vendor_name"
                ]
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

        for _, row in grouped.iterrows():

            key = (
                int(row["vendor_number"]),
                row["vendor_name"]
            )

            if key not in vendor_data:

                vendor_data[key] = {
                    "purchase_quantity": 0,
                    "purchase_spending": 0
                }

            vendor_data[key]["purchase_quantity"] += (
                row["purchase_quantity"]
            )

            vendor_data[key]["purchase_spending"] += (
                row["purchase_spending"]
            )

    print(
        f"Purchase rows processed: "
        f"{total_rows:,}"
    )

    return vendor_data


# ============================================================
# 3. BUILD COMBINED VENDOR DATASET
# ============================================================

def build_vendor_comparison(
    sales_data,
    purchase_data
):

    all_vendors = (
        set(sales_data.keys())
        | set(purchase_data.keys())
    )

    rows = []

    for key in all_vendors:

        vendor_number = key[0]
        vendor_name = key[1]

        sales = sales_data.get(
            key,
            {
                "sales_quantity": 0,
                "sales_revenue": 0
            }
        )

        purchases = purchase_data.get(
            key,
            {
                "purchase_quantity": 0,
                "purchase_spending": 0
            }
        )

        sales_quantity = sales[
            "sales_quantity"
        ]

        sales_revenue = sales[
            "sales_revenue"
        ]

        purchase_quantity = purchases[
            "purchase_quantity"
        ]

        purchase_spending = purchases[
            "purchase_spending"
        ]

        # ----------------------------------------------------
        # Quantity difference
        #
        # Positive = more sold than purchased
        # Negative = more purchased than sold
        # ----------------------------------------------------

        quantity_difference = (
            sales_quantity
            - purchase_quantity
        )

        # ----------------------------------------------------
        # Sales / purchase quantity ratio
        # ----------------------------------------------------

        if purchase_quantity != 0:

            quantity_ratio = (
                sales_quantity
                / purchase_quantity
            )

        else:

            quantity_ratio = None

        # ----------------------------------------------------
        # Sales revenue / purchase spending ratio
        #
        # This is NOT profit.
        # ----------------------------------------------------

        if purchase_spending != 0:

            value_ratio = (
                sales_revenue
                / purchase_spending
            )

        else:

            value_ratio = None

        # ----------------------------------------------------
        # Average selling value
        # ----------------------------------------------------

        if sales_quantity != 0:

            average_sales_value = (
                sales_revenue
                / sales_quantity
            )

        else:

            average_sales_value = None

        # ----------------------------------------------------
        # Average purchase cost
        # ----------------------------------------------------

        if purchase_quantity != 0:

            average_purchase_cost = (
                purchase_spending
                / purchase_quantity
            )

        else:

            average_purchase_cost = None

        rows.append(
            {
                "vendor_number":
                    vendor_number,

                "vendor_name":
                    vendor_name,

                "sales_quantity":
                    sales_quantity,

                "purchase_quantity":
                    purchase_quantity,

                "quantity_difference":
                    quantity_difference,

                "quantity_ratio":
                    quantity_ratio,

                "sales_revenue":
                    sales_revenue,

                "purchase_spending":
                    purchase_spending,

                "value_ratio":
                    value_ratio,

                "average_sales_value":
                    average_sales_value,

                "average_purchase_cost":
                    average_purchase_cost
            }
        )

    result = pd.DataFrame(rows)

    # --------------------------------------------------------
    # Sales contribution
    # --------------------------------------------------------

    total_sales = result[
        "sales_revenue"
    ].sum()

    result["sales_contribution_pct"] = (
        result["sales_revenue"]
        / total_sales
        * 100
    )

    # --------------------------------------------------------
    # Purchase contribution
    # --------------------------------------------------------

    total_purchases = result[
        "purchase_spending"
    ].sum()

    result["purchase_contribution_pct"] = (
        result["purchase_spending"]
        / total_purchases
        * 100
    )

    return result


# ============================================================
# 4. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 9.5.3")
    print("VENDOR SALES VS PURCHASE ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # Load sales
    # --------------------------------------------------------

    sales_data = load_vendor_sales()

    # --------------------------------------------------------
    # Load purchases
    # --------------------------------------------------------

    purchase_data = load_vendor_purchases()

    # --------------------------------------------------------
    # Build comparison
    # --------------------------------------------------------

    result = build_vendor_comparison(
        sales_data,
        purchase_data
    )

    pd.set_option(
        "display.max_columns",
        None
    )

    pd.set_option(
        "display.width",
        260
    )

    # ========================================================
    # OVERALL SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("OVERALL SALES VS PURCHASE SUMMARY")
    print("=" * 70)

    total_sales_quantity = result[
        "sales_quantity"
    ].sum()

    total_purchase_quantity = result[
        "purchase_quantity"
    ].sum()

    total_sales_revenue = result[
        "sales_revenue"
    ].sum()

    total_purchase_spending = result[
        "purchase_spending"
    ].sum()

    total_quantity_difference = (
        result["quantity_difference"].sum()
    )

    print(
        f"Vendor combinations represented: "
        f"{len(result):,}"
    )

    print(
        f"Sales quantity: "
        f"{total_sales_quantity:,.0f}"
    )

    print(
        f"Purchase quantity: "
        f"{total_purchase_quantity:,.0f}"
    )

    print(
        f"Quantity difference: "
        f"{total_quantity_difference:,.0f}"
    )

    print(
        f"Sales revenue: "
        f"${total_sales_revenue:,.2f}"
    )

    print(
        f"Purchase spending: "
        f"${total_purchase_spending:,.2f}"
    )

    # ========================================================
    # TOP VENDORS BY SALES REVENUE
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 VENDORS BY SALES REVENUE")
    print("=" * 70)

    top_sales = (
        result
        .sort_values(
            "sales_revenue",
            ascending=False
        )
        .head(10)
    )

    print(
        top_sales[
            [
                "vendor_number",
                "vendor_name",
                "sales_quantity",
                "purchase_quantity",
                "sales_revenue",
                "purchase_spending",
                "quantity_difference",
                "value_ratio"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "sales_quantity":
                    "{:,.0f}".format,

                "purchase_quantity":
                    "{:,.0f}".format,

                "sales_revenue":
                    "${:,.2f}".format,

                "purchase_spending":
                    "${:,.2f}".format,

                "quantity_difference":
                    "{:,.0f}".format,

                "value_ratio":
                    "{:.4f}".format
            }
        )
    )

    # ========================================================
    # TOP POSITIVE QUANTITY DIFFERENCES
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 POSITIVE QUANTITY DIFFERENCES")
    print("=" * 70)

    positive_difference = (
        result[
            result["quantity_difference"] > 0
        ]
        .sort_values(
            "quantity_difference",
            ascending=False
        )
        .head(10)
    )

    print(
        positive_difference[
            [
                "vendor_number",
                "vendor_name",
                "sales_quantity",
                "purchase_quantity",
                "quantity_difference",
                "quantity_ratio"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "sales_quantity":
                    "{:,.0f}".format,

                "purchase_quantity":
                    "{:,.0f}".format,

                "quantity_difference":
                    "{:,.0f}".format,

                "quantity_ratio":
                    "{:.4f}".format
            }
        )
    )

    # ========================================================
    # TOP NEGATIVE QUANTITY DIFFERENCES
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 NEGATIVE QUANTITY DIFFERENCES")
    print("=" * 70)

    negative_difference = (
        result[
            result["quantity_difference"] < 0
        ]
        .sort_values(
            "quantity_difference",
            ascending=True
        )
        .head(10)
    )

    print(
        negative_difference[
            [
                "vendor_number",
                "vendor_name",
                "sales_quantity",
                "purchase_quantity",
                "quantity_difference",
                "quantity_ratio"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "sales_quantity":
                    "{:,.0f}".format,

                "purchase_quantity":
                    "{:,.0f}".format,

                "quantity_difference":
                    "{:,.0f}".format,

                "quantity_ratio":
                    "{:.4f}".format
            }
        )
    )

    # ========================================================
    # HIGHEST VALUE RATIOS
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 SALES-VALUE / PURCHASE-VALUE RATIOS")
    print("=" * 70)

    high_value_ratio = (
        result[
            result["purchase_spending"] > 0
        ]
        .sort_values(
            "value_ratio",
            ascending=False
        )
        .head(10)
    )

    print(
        high_value_ratio[
            [
                "vendor_number",
                "vendor_name",
                "sales_quantity",
                "purchase_quantity",
                "sales_revenue",
                "purchase_spending",
                "value_ratio"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "sales_quantity":
                    "{:,.0f}".format,

                "purchase_quantity":
                    "{:,.0f}".format,

                "sales_revenue":
                    "${:,.2f}".format,

                "purchase_spending":
                    "${:,.2f}".format,

                "value_ratio":
                    "{:.4f}".format
            }
        )
    )

    # ========================================================
    # LOWEST VALUE RATIOS
    # ========================================================

    print("\n" + "=" * 70)
    print("BOTTOM 10 SALES-VALUE / PURCHASE-VALUE RATIOS")
    print("=" * 70)

    low_value_ratio = (
        result[
            result["purchase_spending"] > 0
        ]
        .sort_values(
            "value_ratio",
            ascending=True
        )
        .head(10)
    )

    print(
        low_value_ratio[
            [
                "vendor_number",
                "vendor_name",
                "sales_quantity",
                "purchase_quantity",
                "sales_revenue",
                "purchase_spending",
                "value_ratio"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "sales_quantity":
                    "{:,.0f}".format,

                "purchase_quantity":
                    "{:,.0f}".format,

                "sales_revenue":
                    "${:,.2f}".format,

                "purchase_spending":
                    "${:,.2f}".format,

                "value_ratio":
                    "{:.4f}".format
            }
        )
    )

    # ========================================================
    # VENDOR CONCENTRATION COMPARISON
    # ========================================================

    print("\n" + "=" * 70)
    print("VENDOR CONCENTRATION COMPARISON")
    print("=" * 70)

    sales_sorted = (
        result
        .sort_values(
            "sales_revenue",
            ascending=False
        )
    )

    purchase_sorted = (
        result
        .sort_values(
            "purchase_spending",
            ascending=False
        )
    )

    top_5_sales = (
        sales_sorted
        .head(5)["sales_revenue"]
        .sum()
    )

    top_10_sales = (
        sales_sorted
        .head(10)["sales_revenue"]
        .sum()
    )

    top_5_purchases = (
        purchase_sorted
        .head(5)["purchase_spending"]
        .sum()
    )

    top_10_purchases = (
        purchase_sorted
        .head(10)["purchase_spending"]
        .sum()
    )

    print(
        f"Top 5 sales concentration: "
        f"{top_5_sales / total_sales_revenue * 100:.2f}%"
    )

    print(
        f"Top 10 sales concentration: "
        f"{top_10_sales / total_sales_revenue * 100:.2f}%"
    )

    print(
        f"Top 5 purchase concentration: "
        f"{top_5_purchases / total_purchase_spending * 100:.2f}%"
    )

    print(
        f"Top 10 purchase concentration: "
        f"{top_10_purchases / total_purchase_spending * 100:.2f}%"
    )

    # ========================================================
    # VERIFICATION
    # ========================================================

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    # Sales quantity

    if abs(
        total_sales_quantity
        - EXPECTED_SALES_QUANTITY
    ) < 0.01:

        print(
            "✓ Sales quantity PASSED."
        )

    else:

        raise ValueError(
            "Sales quantity mismatch."
        )

    # Sales revenue

    if abs(
        total_sales_revenue
        - EXPECTED_SALES_REVENUE
    ) < 0.01:

        print(
            "✓ Sales revenue PASSED."
        )

    else:

        raise ValueError(
            "Sales revenue mismatch."
        )

    # Purchase quantity

    if abs(
        total_purchase_quantity
        - EXPECTED_PURCHASE_QUANTITY
    ) < 0.01:

        print(
            "✓ Purchase quantity PASSED."
        )

    else:

        raise ValueError(
            "Purchase quantity mismatch."
        )

    # Purchase spending

    if abs(
        total_purchase_spending
        - EXPECTED_PURCHASE_VALUE
    ) < 0.01:

        print(
            "✓ Purchase spending PASSED."
        )

    else:

        raise ValueError(
            "Purchase spending mismatch."
        )

    print(
        "\n✓ Phase 9.5.3 completed successfully."
    )