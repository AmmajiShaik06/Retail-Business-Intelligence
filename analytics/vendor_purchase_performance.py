
"""
Phase 9.5.2
Vendor Purchase Performance

Purpose:
Analyze purchase performance by vendor.

Metrics:
1. Purchase quantity
2. Purchase spending
3. Average purchase cost per unit
4. Vendor purchase contribution
5. Top 10 vendors
6. Bottom 10 vendors
7. Purchase concentration

Important:
VendorNumber + VendorName is treated as the vendor identity
because the dataset contains vendor-number/name conflicts.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1

CHUNK_SIZE = 50_000

EXPECTED_ROWS = 2_372_474

EXPECTED_QUANTITY = 33_584_377

EXPECTED_PURCHASES = 321_900_765.53


# ============================================================
# 1. LOAD PURCHASE DATA BY VENDOR
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

        # ----------------------------------------------------
        # Clean numeric columns
        # ----------------------------------------------------

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
                purchase_quantity=(
                    "quantity",
                    "sum"
                ),
                purchase_dollars=(
                    "dollars",
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
                    "purchase_quantity": 0,
                    "purchase_dollars": 0
                }

            vendor_data[key]["purchase_quantity"] += (
                row["purchase_quantity"]
            )

            vendor_data[key]["purchase_dollars"] += (
                row["purchase_dollars"]
            )

    print(
        f"Purchase rows processed: "
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
            "purchase_quantity"
        ]

        purchases = values[
            "purchase_dollars"
        ]

        # ----------------------------------------------------
        # Average purchase cost per unit
        # ----------------------------------------------------

        if quantity != 0:

            average_cost = (
                purchases / quantity
            )

        else:

            average_cost = 0

        rows.append(
            {
                "vendor_number":
                    vendor_number,

                "vendor_name":
                    vendor_name,

                "purchase_quantity":
                    quantity,

                "purchase_dollars":
                    purchases,

                "average_purchase_cost":
                    average_cost
            }
        )

    result = pd.DataFrame(rows)

    # --------------------------------------------------------
    # Vendor purchase contribution percentage
    # --------------------------------------------------------

    total_purchases = result[
        "purchase_dollars"
    ].sum()

    result["purchase_contribution_pct"] = (
        result["purchase_dollars"]
        / total_purchases
        * 100
    )

    return result


# ============================================================
# 3. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 9.5.2")
    print("VENDOR PURCHASE PERFORMANCE")
    print("=" * 70)

    # --------------------------------------------------------
    # Load vendor purchases
    # --------------------------------------------------------

    vendor_data = load_vendor_purchases()

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
    # OVERALL VENDOR PURCHASE SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("OVERALL VENDOR PURCHASE SUMMARY")
    print("=" * 70)

    total_quantity = result[
        "purchase_quantity"
    ].sum()

    total_purchases = result[
        "purchase_dollars"
    ].sum()

    vendor_count = len(result)

    print(
        f"Vendors represented in purchases: "
        f"{vendor_count:,}"
    )

    print(
        f"Purchase quantity: "
        f"{total_quantity:,.0f}"
    )

    print(
        f"Purchase spending: "
        f"${total_purchases:,.2f}"
    )

    # ========================================================
    # TOP 10 VENDORS BY PURCHASE SPENDING
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 VENDORS BY PURCHASE SPENDING")
    print("=" * 70)

    top_vendors = (
        result
        .sort_values(
            "purchase_dollars",
            ascending=False
        )
        .head(10)
    )

    print(
        top_vendors[
            [
                "vendor_number",
                "vendor_name",
                "purchase_quantity",
                "purchase_dollars",
                "average_purchase_cost",
                "purchase_contribution_pct"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "purchase_quantity":
                    "{:,.0f}".format,

                "purchase_dollars":
                    "${:,.2f}".format,

                "average_purchase_cost":
                    "${:,.4f}".format,

                "purchase_contribution_pct":
                    "{:.2f}%".format
            }
        )
    )

    # ========================================================
    # BOTTOM 10 VENDORS BY PURCHASE SPENDING
    # ========================================================

    print("\n" + "=" * 70)
    print("BOTTOM 10 VENDORS BY PURCHASE SPENDING")
    print("=" * 70)

    bottom_vendors = (
        result
        .sort_values(
            "purchase_dollars",
            ascending=True
        )
        .head(10)
    )

    print(
        bottom_vendors[
            [
                "vendor_number",
                "vendor_name",
                "purchase_quantity",
                "purchase_dollars",
                "average_purchase_cost",
                "purchase_contribution_pct"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "purchase_quantity":
                    "{:,.0f}".format,

                "purchase_dollars":
                    "${:,.2f}".format,

                "average_purchase_cost":
                    "${:,.4f}".format,

                "purchase_contribution_pct":
                    "{:.4f}%".format
            }
        )
    )

    # ========================================================
    # VENDOR PURCHASE CONCENTRATION
    # ========================================================

    print("\n" + "=" * 70)
    print("VENDOR PURCHASE CONCENTRATION")
    print("=" * 70)

    sorted_vendors = (
        result
        .sort_values(
            "purchase_dollars",
            ascending=False
        )
    )

    top_5_purchases = (
        sorted_vendors
        .head(5)["purchase_dollars"]
        .sum()
    )

    top_10_purchases = (
        sorted_vendors
        .head(10)["purchase_dollars"]
        .sum()
    )

    top_20_purchases = (
        sorted_vendors
        .head(20)["purchase_dollars"]
        .sum()
    )

    print(
        f"Top 5 vendors purchase spending: "
        f"${top_5_purchases:,.2f}"
    )

    print(
        f"Top 5 contribution: "
        f"{top_5_purchases / total_purchases * 100:.2f}%"
    )

    print(
        f"Top 10 vendors purchase spending: "
        f"${top_10_purchases:,.2f}"
    )

    print(
        f"Top 10 contribution: "
        f"{top_10_purchases / total_purchases * 100:.2f}%"
    )

    print(
        f"Top 20 vendors purchase spending: "
        f"${top_20_purchases:,.2f}"
    )

    print(
        f"Top 20 contribution: "
        f"{top_20_purchases / total_purchases * 100:.2f}%"
    )

    # ========================================================
    # HIGHEST AVERAGE PURCHASE COST
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 VENDORS BY AVERAGE PURCHASE COST")
    print("=" * 70)

    high_average_cost = (
        result[
            result["purchase_quantity"] > 0
        ]
        .sort_values(
            "average_purchase_cost",
            ascending=False
        )
        .head(10)
    )

    print(
        high_average_cost[
            [
                "vendor_number",
                "vendor_name",
                "purchase_quantity",
                "purchase_dollars",
                "average_purchase_cost"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "purchase_quantity":
                    "{:,.0f}".format,

                "purchase_dollars":
                    "${:,.2f}".format,

                "average_purchase_cost":
                    "${:,.4f}".format
            }
        )
    )

    # ========================================================
    # LOWEST AVERAGE PURCHASE COST
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 VENDORS BY LOWEST AVERAGE PURCHASE COST")
    print("=" * 70)

    low_average_cost = (
        result[
            result["purchase_quantity"] > 0
        ]
        .sort_values(
            "average_purchase_cost",
            ascending=True
        )
        .head(10)
    )

    print(
        low_average_cost[
            [
                "vendor_number",
                "vendor_name",
                "purchase_quantity",
                "purchase_dollars",
                "average_purchase_cost"
            ]
        ]
        .to_string(
            index=False,
            formatters={
                "purchase_quantity":
                    "{:,.0f}".format,

                "purchase_dollars":
                    "${:,.2f}".format,

                "average_purchase_cost":
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
    #
    # Purchases contain 128 vendor number + name combinations.
    # --------------------------------------------------------

    if vendor_count == 128:

        print(
            "✓ Vendor count PASSED: "
            "128 vendor number + name combinations."
        )

    else:

        raise ValueError(
            f"Vendor count mismatch. "
            f"Expected 128, got {vendor_count}."
        )

    # --------------------------------------------------------
    # Purchase quantity
    # --------------------------------------------------------

    if abs(
        total_quantity
        - EXPECTED_QUANTITY
    ) < 0.01:

        print(
            "✓ Purchase quantity PASSED."
        )

    else:

        raise ValueError(
            "Purchase quantity mismatch."
        )

    # --------------------------------------------------------
    # Purchase spending
    # --------------------------------------------------------

    if abs(
        total_purchases
        - EXPECTED_PURCHASES
    ) < 0.01:

        print(
            "✓ Purchase spending PASSED."
        )

    else:

        raise ValueError(
            "Purchase spending mismatch."
        )

    # --------------------------------------------------------
    # Contribution percentage
    # --------------------------------------------------------

    contribution_total = (
        result[
            "purchase_contribution_pct"
        ].sum()
    )

    if abs(
        contribution_total - 100
    ) < 0.0001:

        print(
            "✓ Vendor purchase contribution "
            "percentage PASSED."
        )

    else:

        raise ValueError(
            "Vendor purchase contribution "
            "percentage does not equal 100%."
        )

    print(
        "\n✓ Phase 9.5.2 completed successfully."
    )

