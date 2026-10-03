
"""
Phase 9.9.1 - Overall KPI Summary

Purpose:
Create one consolidated KPI summary for the Retail Business
Intelligence project.

This script summarizes:
1. Sales
2. Purchases
3. Inventory
4. Vendors
5. Stores
6. Products

Important:
- Uses exec_driver_sql(), therefore MySQL %s placeholders are used.
- Inventory tables use the column `price`, NOT `purchase_price`.
- This script only analyzes existing MySQL data.
- It does NOT modify any database tables.
"""

from database.connection import engine


BUSINESS_ID = 1


# ============================================================
# GET OVERALL KPIs
# ============================================================

def get_overall_kpis():

    print("\n" + "=" * 70)
    print("PHASE 9.9.1 - OVERALL KPI SUMMARY")
    print("=" * 70)

    query = """
        SELECT

            -- ==================================================
            -- SALES KPIs
            -- ==================================================

            (
                SELECT COUNT(*)
                FROM sales
                WHERE business_id = %s
            ) AS sales_rows,

            (
                SELECT COALESCE(
                    SUM(sales_quantity),
                    0
                )
                FROM sales
                WHERE business_id = %s
            ) AS sales_quantity,

            (
                SELECT COALESCE(
                    SUM(sales_dollars),
                    0
                )
                FROM sales
                WHERE business_id = %s
            ) AS sales_revenue,


            -- ==================================================
            -- PURCHASE KPIs
            -- ==================================================

            (
                SELECT COUNT(*)
                FROM purchases
                WHERE business_id = %s
            ) AS purchase_rows,

            (
                SELECT COALESCE(
                    SUM(quantity),
                    0
                )
                FROM purchases
                WHERE business_id = %s
            ) AS purchase_quantity,

            (
                SELECT COALESCE(
                    SUM(dollars),
                    0
                )
                FROM purchases
                WHERE business_id = %s
            ) AS purchase_spending,


            -- ==================================================
            -- INVENTORY KPIs
            --
            -- IMPORTANT:
            -- Inventory tables use `price`.
            -- They do NOT use `purchase_price`.
            -- ==================================================

            (
                SELECT COALESCE(
                    SUM(on_hand),
                    0
                )
                FROM begin_inventory
                WHERE business_id = %s
            ) AS begin_inventory_quantity,

            (
                SELECT COALESCE(
                    SUM(on_hand),
                    0
                )
                FROM end_inventory
                WHERE business_id = %s
            ) AS end_inventory_quantity,

            (
                SELECT COALESCE(
                    SUM(on_hand * price),
                    0
                )
                FROM begin_inventory
                WHERE business_id = %s
            ) AS begin_inventory_value,

            (
                SELECT COALESCE(
                    SUM(on_hand * price),
                    0
                )
                FROM end_inventory
                WHERE business_id = %s
            ) AS end_inventory_value,


            -- ==================================================
            -- MASTER DATA COUNTS
            -- ==================================================

            (
                SELECT COUNT(*)
                FROM vendors
                WHERE business_id = %s
            ) AS vendor_count,

            (
                SELECT COUNT(*)
                FROM stores
                WHERE business_id = %s
            ) AS store_count,

            (
                SELECT COUNT(*)
                FROM products
                WHERE business_id = %s
            ) AS product_count

    """

    # --------------------------------------------------------
    # IMPORTANT:
    # There are 13 %s placeholders above.
    # Therefore we provide BUSINESS_ID 13 times.
    # --------------------------------------------------------

    parameters = (
        BUSINESS_ID,   # sales_rows
        BUSINESS_ID,   # sales_quantity
        BUSINESS_ID,   # sales_revenue

        BUSINESS_ID,   # purchase_rows
        BUSINESS_ID,   # purchase_quantity
        BUSINESS_ID,   # purchase_spending

        BUSINESS_ID,   # begin_inventory_quantity
        BUSINESS_ID,   # end_inventory_quantity
        BUSINESS_ID,   # begin_inventory_value
        BUSINESS_ID,   # end_inventory_value

        BUSINESS_ID,   # vendor_count
        BUSINESS_ID,   # store_count
        BUSINESS_ID    # product_count
    )

    # --------------------------------------------------------
    # Execute query
    # --------------------------------------------------------

    with engine.connect() as connection:

        result = connection.exec_driver_sql(
            query,
            parameters
        )

        row = result.fetchone()

    # --------------------------------------------------------
    # Convert result to dictionary
    # --------------------------------------------------------

    kpis = {
        "sales_rows": int(row.sales_rows),
        "sales_quantity": int(row.sales_quantity),
        "sales_revenue": float(row.sales_revenue),

        "purchase_rows": int(row.purchase_rows),
        "purchase_quantity": int(row.purchase_quantity),
        "purchase_spending": float(row.purchase_spending),

        "begin_inventory_quantity": int(
            row.begin_inventory_quantity
        ),

        "end_inventory_quantity": int(
            row.end_inventory_quantity
        ),

        "begin_inventory_value": float(
            row.begin_inventory_value
        ),

        "end_inventory_value": float(
            row.end_inventory_value
        ),

        "vendor_count": int(row.vendor_count),
        "store_count": int(row.store_count),
        "product_count": int(row.product_count)
    }

    return kpis


# ============================================================
# DISPLAY KPI SUMMARY
# ============================================================

def display_kpis(kpis):

    print("\n" + "-" * 70)
    print("SALES KPIs")
    print("-" * 70)

    print(
        f"Sales rows: "
        f"{kpis['sales_rows']:,}"
    )

    print(
        f"Sales quantity: "
        f"{kpis['sales_quantity']:,}"
    )

    print(
        f"Sales revenue: "
        f"${kpis['sales_revenue']:,.2f}"
    )


    print("\n" + "-" * 70)
    print("PURCHASE KPIs")
    print("-" * 70)

    print(
        f"Purchase rows: "
        f"{kpis['purchase_rows']:,}"
    )

    print(
        f"Purchase quantity: "
        f"{kpis['purchase_quantity']:,}"
    )

    print(
        f"Purchase spending: "
        f"${kpis['purchase_spending']:,.2f}"
    )

    # --------------------------------------------------------
    # Inventory change calculations
    # --------------------------------------------------------

    inventory_quantity_change = (
        kpis["end_inventory_quantity"]
        - kpis["begin_inventory_quantity"]
    )

    inventory_value_change = (
        kpis["end_inventory_value"]
        - kpis["begin_inventory_value"]
    )

    inventory_value_growth = (
        inventory_value_change
        / kpis["begin_inventory_value"]
        * 100
    )

    print("\n" + "-" * 70)
    print("INVENTORY KPIs")
    print("-" * 70)

    print(
        f"Beginning inventory quantity: "
        f"{kpis['begin_inventory_quantity']:,}"
    )

    print(
        f"Ending inventory quantity: "
        f"{kpis['end_inventory_quantity']:,}"
    )

    print(
        f"Inventory quantity change: "
        f"{inventory_quantity_change:+,}"
    )

    print(
        f"Beginning inventory value: "
        f"${kpis['begin_inventory_value']:,.2f}"
    )

    print(
        f"Ending inventory value: "
        f"${kpis['end_inventory_value']:,.2f}"
    )

    print(
        f"Inventory value change: "
        f"${inventory_value_change:+,.2f}"
    )

    print(
        f"Inventory value growth: "
        f"{inventory_value_growth:+.2f}%"
    )

    print("\n" + "-" * 70)
    print("MASTER DATA KPIs")
    print("-" * 70)

    print(
        f"Vendors: "
        f"{kpis['vendor_count']:,}"
    )

    print(
        f"Stores: "
        f"{kpis['store_count']:,}"
    )

    print(
        f"Products: "
        f"{kpis['product_count']:,}"
    )


# ============================================================
# VERIFY KPIs
# ============================================================

def verify_kpis(kpis):

    print("\n" + "=" * 70)
    print("VERIFYING OVERALL KPIs")
    print("=" * 70)

    expected = {

        "sales_rows": 12_825_363,

        "sales_quantity": 32_917_876,

        "sales_revenue": 452_062_952.02,

        "purchase_rows": 2_372_474,

        "purchase_quantity": 33_584_377,

        "purchase_spending": 321_900_765.53,

        "begin_inventory_quantity": 4_219_275,

        "end_inventory_quantity": 4_885_776,

        "begin_inventory_value": 68_053_780.17,

        "end_inventory_value": 79_704_851.13,

        "vendor_count": 134,

        "store_count": 80,

        "product_count": 12_261
    }

    # --------------------------------------------------------
    # Verify integer KPIs
    # --------------------------------------------------------

    integer_keys = [
        "sales_rows",
        "sales_quantity",
        "purchase_rows",
        "purchase_quantity",
        "begin_inventory_quantity",
        "end_inventory_quantity",
        "vendor_count",
        "store_count",
        "product_count"
    ]

    for key in integer_keys:

        if kpis[key] == expected[key]:

            print(
                f"✓ {key.replace('_', ' ').title()}: "
                f"PASSED"
            )

        else:

            print(
                f"✗ {key.replace('_', ' ').title()}: "
                f"FAILED"
            )

            print(
                f"  Expected: {expected[key]:,}"
            )

            print(
                f"  Actual:   {kpis[key]:,}"
            )

            raise ValueError(
                f"Verification failed for {key}"
            )

    # --------------------------------------------------------
    # Verify monetary KPIs
    # --------------------------------------------------------

    float_keys = [
        "sales_revenue",
        "purchase_spending",
        "begin_inventory_value",
        "end_inventory_value"
    ]

    tolerance = 0.01

    for key in float_keys:

        if abs(
            kpis[key] - expected[key]
        ) <= tolerance:

            print(
                f"✓ {key.replace('_', ' ').title()}: "
                f"PASSED"
            )

        else:

            print(
                f"✗ {key.replace('_', ' ').title()}: "
                f"FAILED"
            )

            print(
                f"  Expected: "
                f"${expected[key]:,.2f}"
            )

            print(
                f"  Actual:   "
                f"${kpis[key]:,.2f}"
            )

            raise ValueError(
                f"Verification failed for {key}"
            )

    # --------------------------------------------------------
    # Inventory reconciliation
    #
    # Beginning Inventory
    # + Purchase Quantity
    # - Sales Quantity
    # = Ending Inventory
    # --------------------------------------------------------

    calculated_end_inventory = (
        kpis["begin_inventory_quantity"]
        + kpis["purchase_quantity"]
        - kpis["sales_quantity"]
    )

    if (
        calculated_end_inventory
        == kpis["end_inventory_quantity"]
    ):

        print(
            "✓ Inventory reconciliation: PASSED"
        )

    else:

        print(
            "✗ Inventory reconciliation: FAILED"
        )

        print(
            f"  Calculated ending inventory: "
            f"{calculated_end_inventory:,}"
        )

        print(
            f"  Actual ending inventory: "
            f"{kpis['end_inventory_quantity']:,}"
        )

        raise ValueError(
            "Inventory reconciliation failed."
        )

    print(
        "\n✓ ALL OVERALL KPI VERIFICATION CHECKS PASSED"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("STARTING OVERALL KPI ANALYSIS")
    print("=" * 70)

    kpis = get_overall_kpis()

    display_kpis(kpis)

    verify_kpis(kpis)

    print("\n" + "=" * 70)
    print("PHASE 9.9.1 COMPLETED SUCCESSFULLY")
    print("=" * 70)
