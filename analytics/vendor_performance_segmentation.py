"""
Phase 9.5.4
Vendor Performance Segmentation

Purpose:
Segment vendors using sales and purchase performance.

Segmentation dimensions:
1. Sales scale
2. Purchase scale
3. Quantity balance

Important:
The segmentation is descriptive.
It does not claim that one segment is inherently
"good" or "bad".

Vendor identity:
VendorNumber + VendorName
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
# 1. LOAD VENDOR SALES
# ============================================================

def load_vendor_sales():

    print("\n" + "=" * 70)
    print("LOADING SALES DATA")
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
# 2. LOAD VENDOR PURCHASES
# ============================================================

def load_vendor_purchases():

    print("\n" + "=" * 70)
    print("LOADING PURCHASE DATA")
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
# 3. BUILD VENDOR METRICS
# ============================================================

def build_vendor_metrics(
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
        # Quantity ratio
        # ----------------------------------------------------

        if purchase_quantity != 0:

            quantity_ratio = (
                sales_quantity
                / purchase_quantity
            )

        else:

            quantity_ratio = None

        # ----------------------------------------------------
        # Value ratio
        # ----------------------------------------------------

        if purchase_spending != 0:

            value_ratio = (
                sales_revenue
                / purchase_spending
            )

        else:

            value_ratio = None

        # ----------------------------------------------------
        # Average sales value
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

                "sales_revenue":
                    sales_revenue,

                "purchase_spending":
                    purchase_spending,

                "quantity_difference":
                    sales_quantity
                    - purchase_quantity,

                "quantity_ratio":
                    quantity_ratio,

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
    # Contribution percentages
    # --------------------------------------------------------

    total_sales = result[
        "sales_revenue"
    ].sum()

    total_purchases = result[
        "purchase_spending"
    ].sum()

    result["sales_contribution_pct"] = (
        result["sales_revenue"]
        / total_sales
        * 100
    )

    result["purchase_contribution_pct"] = (
        result["purchase_spending"]
        / total_purchases
        * 100
    )

    return result


# ============================================================
# 4. ASSIGN SALES SCALE
# ============================================================

def assign_sales_scale(
    result
):

    sales_median = result[
        "sales_revenue"
    ].median()

    result["sales_scale"] = result[
        "sales_revenue"
    ].apply(
        lambda x:
            "High Sales"
            if x >= sales_median
            else "Lower Sales"
    )

    print(
        f"\nSales revenue median: "
        f"${sales_median:,.2f}"
    )

    return result


# ============================================================
# 5. ASSIGN PURCHASE SCALE
# ============================================================

def assign_purchase_scale(
    result
):

    purchase_median = result[
        "purchase_spending"
    ].median()

    result["purchase_scale"] = result[
        "purchase_spending"
    ].apply(
        lambda x:
            "High Purchase"
            if x >= purchase_median
            else "Lower Purchase"
    )

    print(
        f"Purchase spending median: "
        f"${purchase_median:,.2f}"
    )

    return result


# ============================================================
# 6. ASSIGN QUANTITY BALANCE
# ============================================================

def assign_quantity_balance(
    result
):

    result["quantity_balance"] = result[
        "quantity_ratio"
    ].apply(
        lambda x:
            "Sales > Purchases"
            if x > 1
            else (
                "Sales < Purchases"
                if x < 1
                else "Sales = Purchases"
            )
            if pd.notna(x)
            else "No Purchase Data"
    )

    return result


# ============================================================
# 7. ASSIGN PERFORMANCE SEGMENT
# ============================================================

def assign_segment(
    row
):

    sales_scale = row[
        "sales_scale"
    ]

    purchase_scale = row[
        "purchase_scale"
    ]

    if (
        sales_scale == "High Sales"
        and
        purchase_scale == "High Purchase"
    ):

        return "High Sales / High Purchase"

    elif (
        sales_scale == "High Sales"
        and
        purchase_scale == "Lower Purchase"
    ):

        return "High Sales / Lower Purchase"

    elif (
        sales_scale == "Lower Sales"
        and
        purchase_scale == "High Purchase"
    ):

        return "Lower Sales / High Purchase"

    else:

        return "Lower Sales / Lower Purchase"


# ============================================================
# 8. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 9.5.4")
    print("VENDOR PERFORMANCE SEGMENTATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    sales_data = load_vendor_sales()

    purchase_data = load_vendor_purchases()

    # --------------------------------------------------------
    # Build metrics
    # --------------------------------------------------------

    result = build_vendor_metrics(
        sales_data,
        purchase_data
    )

    # --------------------------------------------------------
    # Assign segmentation
    # --------------------------------------------------------

    result = assign_sales_scale(
        result
    )

    result = assign_purchase_scale(
        result
    )

    result = assign_quantity_balance(
        result
    )

    result["performance_segment"] = (
        result.apply(
            assign_segment,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Display settings
    # --------------------------------------------------------

    pd.set_option(
        "display.max_columns",
        None
    )

    pd.set_option(
        "display.width",
        280
    )

    # ========================================================
    # SEGMENT SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("VENDOR PERFORMANCE SEGMENT SUMMARY")
    print("=" * 70)

    segment_summary = (
        result
        .groupby(
            "performance_segment"
        )
        .agg(
            vendor_count=(
                "vendor_number",
                "count"
            ),
            sales_revenue=(
                "sales_revenue",
                "sum"
            ),
            purchase_spending=(
                "purchase_spending",
                "sum"
            ),
            sales_quantity=(
                "sales_quantity",
                "sum"
            ),
            purchase_quantity=(
                "purchase_quantity",
                "sum"
            )
        )
        .reset_index()
    )

    segment_summary[
        "sales_contribution_pct"
    ] = (
        segment_summary[
            "sales_revenue"
        ]
        / result["sales_revenue"].sum()
        * 100
    )

    segment_summary[
        "purchase_contribution_pct"
    ] = (
        segment_summary[
            "purchase_spending"
        ]
        / result["purchase_spending"].sum()
        * 100
    )

    print(
        segment_summary.to_string(
            index=False,
            formatters={
                "sales_revenue":
                    "${:,.2f}".format,

                "purchase_spending":
                    "${:,.2f}".format,

                "sales_quantity":
                    "{:,.0f}".format,

                "purchase_quantity":
                    "{:,.0f}".format,

                "sales_contribution_pct":
                    "{:.2f}%".format,

                "purchase_contribution_pct":
                    "{:.2f}%".format
            }
        )
    )

    # ========================================================
    # VENDOR COUNT BY SEGMENT
    # ========================================================

    print("\n" + "=" * 70)
    print("VENDOR COUNT BY SEGMENT")
    print("=" * 70)

    segment_counts = (
        result[
            "performance_segment"
        ]
        .value_counts()
        .sort_index()
    )

    for segment, count in segment_counts.items():

        print(
            f"{segment}: {count}"
        )

    # ========================================================
    # TOP VENDORS IN EACH SEGMENT
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP VENDORS WITHIN EACH SEGMENT")
    print("=" * 70)

    for segment in sorted(
        result[
            "performance_segment"
        ].unique()
    ):

        print(
            f"\n--- {segment} ---"
        )

        segment_vendors = (
            result[
                result[
                    "performance_segment"
                ] == segment
            ]
            .sort_values(
                "sales_revenue",
                ascending=False
            )
            .head(5)
        )

        print(
            segment_vendors[
                [
                    "vendor_number",
                    "vendor_name",
                    "sales_revenue",
                    "purchase_spending",
                    "quantity_difference",
                    "quantity_ratio"
                ]
            ]
            .to_string(
                index=False,
                formatters={
                    "sales_revenue":
                        "${:,.2f}".format,

                    "purchase_spending":
                        "${:,.2f}".format,

                    "quantity_difference":
                        "{:,.0f}".format,

                    "quantity_ratio":
                        "{:.4f}".format
                }
            )
        )

    # ========================================================
    # QUANTITY BALANCE SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("QUANTITY BALANCE SUMMARY")
    print("=" * 70)

    balance_summary = (
        result[
            "quantity_balance"
        ]
        .value_counts()
    )

    for balance, count in balance_summary.items():

        print(
            f"{balance}: {count}"
        )

    # ========================================================
    # HIGH SALES / LOWER PURCHASE VENDORS
    # ========================================================

    print("\n" + "=" * 70)
    print("HIGH SALES / LOWER PURCHASE VENDORS")
    print("=" * 70)

    high_sales_lower_purchase = (
        result[
            result[
                "performance_segment"
            ]
            == "High Sales / Lower Purchase"
        ]
        .sort_values(
            "sales_revenue",
            ascending=False
        )
        .head(10)
    )

    print(
        high_sales_lower_purchase[
            [
                "vendor_number",
                "vendor_name",
                "sales_revenue",
                "purchase_spending",
                "sales_contribution_pct",
                "purchase_contribution_pct",
                "quantity_difference",
                "quantity_ratio"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "sales_revenue":
                    "${:,.2f}".format,

                "purchase_spending":
                    "${:,.2f}".format,

                "sales_contribution_pct":
                    "{:.2f}%".format,

                "purchase_contribution_pct":
                    "{:.2f}%".format,

                "quantity_difference":
                    "{:,.0f}".format,

                "quantity_ratio":
                    "{:.4f}".format
            }
        )
    )

    # ========================================================
    # LOWER SALES / HIGH PURCHASE VENDORS
    # ========================================================

    print("\n" + "=" * 70)
    print("LOWER SALES / HIGH PURCHASE VENDORS")
    print("=" * 70)

    lower_sales_high_purchase = (
        result[
            result[
                "performance_segment"
            ]
            == "Lower Sales / High Purchase"
        ]
        .sort_values(
            "purchase_spending",
            ascending=False
        )
        .head(10)
    )

    print(
        lower_sales_high_purchase[
            [
                "vendor_number",
                "vendor_name",
                "sales_revenue",
                "purchase_spending",
                "sales_contribution_pct",
                "purchase_contribution_pct",
                "quantity_difference",
                "quantity_ratio"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "sales_revenue":
                    "${:,.2f}".format,

                "purchase_spending":
                    "${:,.2f}".format,

                "sales_contribution_pct":
                    "{:.2f}%".format,

                "purchase_contribution_pct":
                    "{:.2f}%".format,

                "quantity_difference":
                    "{:,.0f}".format,

                "quantity_ratio":
                    "{:.4f}".format
            }
        )
    )

    # ========================================================
    # VERIFICATION
    # ========================================================

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    total_sales_quantity = result[
        "sales_quantity"
    ].sum()

    total_sales_revenue = result[
        "sales_revenue"
    ].sum()

    total_purchase_quantity = result[
        "purchase_quantity"
    ].sum()

    total_purchase_spending = result[
        "purchase_spending"
    ].sum()

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

    # Segment count

    total_segment_vendors = (
        result[
            "performance_segment"
        ]
        .notna()
        .sum()
    )

    if total_segment_vendors == len(result):

        print(
            "✓ Every vendor assigned to "
            "a performance segment."
        )

    else:

        raise ValueError(
            "Some vendors were not assigned "
            "to a performance segment."
        )

    print(
        "\n✓ Phase 9.5.4 completed successfully."
    )