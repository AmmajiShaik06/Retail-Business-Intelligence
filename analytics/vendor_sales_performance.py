"""
Phase 9.5.1
Vendor Sales Performance

Purpose:
Analyze sales performance by vendor.

Metrics:
1. Sales quantity
2. Sales revenue
3. Average selling value per unit
4. Vendor revenue contribution
5. Top 10 vendors
6. Bottom 10 vendors

Important:
VendorNumber + VendorName is treated as the vendor identity
because the dataset contains vendor-number/name conflicts.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1

CHUNK_SIZE = 250_000

EXPECTED_ROWS = 12_825_363

EXPECTED_QUANTITY = 32_917_876

EXPECTED_SALES = 452_062_952.02


# ============================================================
# 1. LOAD SALES DATA BY VENDOR
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

        # ----------------------------------------------------
        # Clean numeric columns
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Clean vendor name
        # ----------------------------------------------------

        chunk["vendor_name"] = (
            chunk["vendor_name"]
            .astype("string")
            .str.strip()
            .fillna("UNKNOWN")
        )

        # ----------------------------------------------------
        # Remove rows without vendor number
        # ----------------------------------------------------

        chunk = chunk.dropna(
            subset=["vendor_number"]
        )

        # ----------------------------------------------------
        # Aggregate current chunk
        # ----------------------------------------------------

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
                sales_dollars=(
                    "sales_dollars",
                    "sum"
                )
            )
            .reset_index()
        )

        # ----------------------------------------------------
        # Add chunk results to overall vendor totals
        # ----------------------------------------------------

        for _, row in grouped.iterrows():

            key = (
                int(row["vendor_number"]),
                row["vendor_name"]
            )

            if key not in vendor_data:

                vendor_data[key] = {
                    "sales_quantity": 0,
                    "sales_dollars": 0
                }

            vendor_data[key]["sales_quantity"] += (
                row["sales_quantity"]
            )

            vendor_data[key]["sales_dollars"] += (
                row["sales_dollars"]
            )

    print(
        f"Sales rows processed: "
        f"{total_rows:,}"
    )

    return vendor_data


# ============================================================
# 2. BUILD VENDOR DATAFRAME
# ============================================================

def build_vendor_dataframe(vendor_data):

    rows = []

    for (
        vendor_number,
        vendor_name
    ), values in vendor_data.items():

        quantity = values[
            "sales_quantity"
        ]

        sales = values[
            "sales_dollars"
        ]

        # ----------------------------------------------------
        # Average selling value per unit
        # ----------------------------------------------------

        if quantity != 0:

            average_value = (
                sales / quantity
            )

        else:

            average_value = 0

        rows.append(
            {
                "vendor_number":
                    vendor_number,

                "vendor_name":
                    vendor_name,

                "sales_quantity":
                    quantity,

                "sales_dollars":
                    sales,

                "average_selling_value":
                    average_value
            }
        )

    result = pd.DataFrame(rows)

    # --------------------------------------------------------
    # Vendor contribution percentage
    # --------------------------------------------------------

    total_sales = result[
        "sales_dollars"
    ].sum()

    result["sales_contribution_pct"] = (
        result["sales_dollars"]
        / total_sales
        * 100
    )

    return result


# ============================================================
# 3. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 9.5.1")
    print("VENDOR SALES PERFORMANCE")
    print("=" * 70)

    # --------------------------------------------------------
    # Load vendor sales
    # --------------------------------------------------------

    vendor_data = load_vendor_sales()

    # --------------------------------------------------------
    # Build result
    # --------------------------------------------------------

    result = build_vendor_dataframe(
        vendor_data
    )

    pd.set_option(
        "display.max_columns",
        None
    )

    pd.set_option(
        "display.width",
        240
    )

    # ========================================================
    # OVERALL VENDOR SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("OVERALL VENDOR SALES SUMMARY")
    print("=" * 70)

    total_rows = EXPECTED_ROWS

    total_quantity = result[
        "sales_quantity"
    ].sum()

    total_sales = result[
        "sales_dollars"
    ].sum()

    vendor_count = len(result)

    print(
        f"Vendors represented in sales: "
        f"{vendor_count:,}"
    )

    print(
        f"Sales quantity: "
        f"{total_quantity:,.0f}"
    )

    print(
        f"Sales revenue: "
        f"${total_sales:,.2f}"
    )

    # ========================================================
    # TOP 10 VENDORS BY SALES
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 VENDORS BY SALES REVENUE")
    print("=" * 70)

    top_vendors = (
        result
        .sort_values(
            "sales_dollars",
            ascending=False
        )
        .head(10)
    )

    print(
        top_vendors[
            [
                "vendor_number",
                "vendor_name",
                "sales_quantity",
                "sales_dollars",
                "average_selling_value",
                "sales_contribution_pct"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "sales_quantity":
                    "{:,.0f}".format,

                "sales_dollars":
                    "${:,.2f}".format,

                "average_selling_value":
                    "${:,.4f}".format,

                "sales_contribution_pct":
                    "{:.2f}%".format
            }
        )
    )

    # ========================================================
    # BOTTOM 10 VENDORS BY SALES
    # ========================================================

    print("\n" + "=" * 70)
    print("BOTTOM 10 VENDORS BY SALES REVENUE")
    print("=" * 70)

    bottom_vendors = (
        result
        .sort_values(
            "sales_dollars",
            ascending=True
        )
        .head(10)
    )

    print(
        bottom_vendors[
            [
                "vendor_number",
                "vendor_name",
                "sales_quantity",
                "sales_dollars",
                "average_selling_value",
                "sales_contribution_pct"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "sales_quantity":
                    "{:,.0f}".format,

                "sales_dollars":
                    "${:,.2f}".format,

                "average_selling_value":
                    "${:,.4f}".format,

                "sales_contribution_pct":
                    "{:.4f}%".format
            }
        )
    )

    # ========================================================
    # TOP 10 VENDOR CONTRIBUTION
    # ========================================================

    print("\n" + "=" * 70)
    print("VENDOR SALES CONCENTRATION")
    print("=" * 70)

    sorted_vendors = (
        result
        .sort_values(
            "sales_dollars",
            ascending=False
        )
    )

    top_5_sales = (
        sorted_vendors
        .head(5)["sales_dollars"]
        .sum()
    )

    top_10_sales = (
        sorted_vendors
        .head(10)["sales_dollars"]
        .sum()
    )

    top_20_sales = (
        sorted_vendors
        .head(20)["sales_dollars"]
        .sum()
    )

    print(
        f"Top 5 vendors sales: "
        f"${top_5_sales:,.2f}"
    )

    print(
        f"Top 5 contribution: "
        f"{top_5_sales / total_sales * 100:.2f}%"
    )

    print(
        f"Top 10 vendors sales: "
        f"${top_10_sales:,.2f}"
    )

    print(
        f"Top 10 contribution: "
        f"{top_10_sales / total_sales * 100:.2f}%"
    )

    print(
        f"Top 20 vendors sales: "
        f"${top_20_sales:,.2f}"
    )

    print(
        f"Top 20 contribution: "
        f"{top_20_sales / total_sales * 100:.2f}%"
    )

    # ========================================================
    # HIGHEST AVERAGE SELLING VALUE
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 VENDORS BY AVERAGE SELLING VALUE")
    print("=" * 70)

    high_average_value = (
        result[
            result["sales_quantity"] > 0
        ]
        .sort_values(
            "average_selling_value",
            ascending=False
        )
        .head(10)
    )

    print(
        high_average_value[
            [
                "vendor_number",
                "vendor_name",
                "sales_quantity",
                "sales_dollars",
                "average_selling_value"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "sales_quantity":
                    "{:,.0f}".format,

                "sales_dollars":
                    "${:,.2f}".format,

                "average_selling_value":
                    "${:,.4f}".format
            }
        )
    )

    # ========================================================
    # VERIFICATION
    # ========================================================

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Vendor count
    # --------------------------------------------------------

    if vendor_count == 129:

        print(
            "✓ Vendor count PASSED: "
            "129 vendor number + name combinations."
        )

    else:

        raise ValueError(
            f"Vendor count mismatch. "
            f"Expected 129, got {vendor_count}."
        )

    # --------------------------------------------------------
    # Sales quantity
    # --------------------------------------------------------

    if abs(
        total_quantity
        - EXPECTED_QUANTITY
    ) < 0.01:

        print(
            "✓ Sales quantity PASSED."
        )

    else:

        raise ValueError(
            "Sales quantity mismatch."
        )

    # --------------------------------------------------------
    # Sales revenue
    # --------------------------------------------------------

    if abs(
        total_sales
        - EXPECTED_SALES
    ) < 0.01:

        print(
            "✓ Sales revenue PASSED."
        )

    else:

        raise ValueError(
            "Sales revenue mismatch."
        )

    # --------------------------------------------------------
    # Contribution percentage
    # --------------------------------------------------------

    contribution_total = (
        result[
            "sales_contribution_pct"
        ].sum()
    )

    if abs(
        contribution_total - 100
    ) < 0.0001:

        print(
            "✓ Vendor contribution "
            "percentage PASSED."
        )

    else:

        raise ValueError(
            "Vendor contribution percentage "
            "does not equal 100%."
        )

    print(
        "\n✓ Phase 9.5.1 completed successfully."
    )