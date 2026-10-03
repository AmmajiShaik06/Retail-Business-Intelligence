
"""
Phase 9.9.2 - Business Health Indicators

Purpose:
Derive executive-level business indicators from the
already verified overall KPIs.

This script does NOT reload data.
It does NOT modify the database.

It uses the verified totals from Phase 9.9.1.
"""


# ============================================================
# VERIFIED BUSINESS KPIs
# ============================================================

SALES_QUANTITY = 32_917_876
SALES_REVENUE = 452_062_952.02

PURCHASE_QUANTITY = 33_584_377
PURCHASE_SPENDING = 321_900_765.53

BEGIN_INVENTORY_QUANTITY = 4_219_275
END_INVENTORY_QUANTITY = 4_885_776

BEGIN_INVENTORY_VALUE = 68_053_780.17
END_INVENTORY_VALUE = 79_704_851.13

VENDOR_COUNT = 134
STORE_COUNT = 80
PRODUCT_COUNT = 12_261


# ============================================================
# CALCULATE BUSINESS HEALTH INDICATORS
# ============================================================

def calculate_indicators():

    # --------------------------------------------------------
    # 1. Sales-to-purchase value ratio
    # --------------------------------------------------------

    sales_to_purchase_value_ratio = (
        SALES_REVENUE
        / PURCHASE_SPENDING
    )

    # --------------------------------------------------------
    # 2. Purchase-to-sales quantity ratio
    # --------------------------------------------------------

    purchase_to_sales_quantity_ratio = (
        PURCHASE_QUANTITY
        / SALES_QUANTITY
    )

    # --------------------------------------------------------
    # 3. Inventory quantity change
    # --------------------------------------------------------

    inventory_quantity_change = (
        END_INVENTORY_QUANTITY
        - BEGIN_INVENTORY_QUANTITY
    )

    inventory_quantity_change_percent = (
        inventory_quantity_change
        / BEGIN_INVENTORY_QUANTITY
        * 100
    )

    # --------------------------------------------------------
    # 4. Inventory value change
    # --------------------------------------------------------

    inventory_value_change = (
        END_INVENTORY_VALUE
        - BEGIN_INVENTORY_VALUE
    )

    inventory_value_growth_percent = (
        inventory_value_change
        / BEGIN_INVENTORY_VALUE
        * 100
    )

    # --------------------------------------------------------
    # 5. Average sales value per unit
    # --------------------------------------------------------

    average_sales_value_per_unit = (
        SALES_REVENUE
        / SALES_QUANTITY
    )

    # --------------------------------------------------------
    # 6. Average purchase cost per unit
    # --------------------------------------------------------

    average_purchase_cost_per_unit = (
        PURCHASE_SPENDING
        / PURCHASE_QUANTITY
    )

    # --------------------------------------------------------
    # 7. Sales-purchase value difference
    # --------------------------------------------------------

    sales_purchase_value_difference = (
        SALES_REVENUE
        - PURCHASE_SPENDING
    )

    # --------------------------------------------------------
    # 8. Ending inventory value as percentage of
    #    annual sales revenue
    # --------------------------------------------------------

    ending_inventory_to_sales_percent = (
        END_INVENTORY_VALUE
        / SALES_REVENUE
        * 100
    )

    # --------------------------------------------------------
    # 9. Sales revenue per store
    # --------------------------------------------------------

    sales_revenue_per_store = (
        SALES_REVENUE
        / STORE_COUNT
    )

    # --------------------------------------------------------
    # 10. Ending inventory value per store
    # --------------------------------------------------------

    inventory_value_per_store = (
        END_INVENTORY_VALUE
        / STORE_COUNT
    )

    return {
        "sales_to_purchase_value_ratio":
            sales_to_purchase_value_ratio,

        "purchase_to_sales_quantity_ratio":
            purchase_to_sales_quantity_ratio,

        "inventory_quantity_change":
            inventory_quantity_change,

        "inventory_quantity_change_percent":
            inventory_quantity_change_percent,

        "inventory_value_change":
            inventory_value_change,

        "inventory_value_growth_percent":
            inventory_value_growth_percent,

        "average_sales_value_per_unit":
            average_sales_value_per_unit,

        "average_purchase_cost_per_unit":
            average_purchase_cost_per_unit,

        "sales_purchase_value_difference":
            sales_purchase_value_difference,

        "ending_inventory_to_sales_percent":
            ending_inventory_to_sales_percent,

        "sales_revenue_per_store":
            sales_revenue_per_store,

        "inventory_value_per_store":
            inventory_value_per_store
    }


# ============================================================
# DISPLAY RESULTS
# ============================================================

def display_indicators(indicators):

    print("\n" + "=" * 70)
    print("PHASE 9.9.2 - BUSINESS HEALTH INDICATORS")
    print("=" * 70)

    print("\n" + "-" * 70)
    print("VALUE INDICATORS")
    print("-" * 70)

    print(
        f"Sales-to-purchase value ratio: "
        f"{indicators['sales_to_purchase_value_ratio']:.4f}"
    )

    print(
        f"Sales-purchase value difference: "
        f"${indicators['sales_purchase_value_difference']:,.2f}"
    )

    print(
        f"Average sales value per unit: "
        f"${indicators['average_sales_value_per_unit']:.4f}"
    )

    print(
        f"Average purchase cost per unit: "
        f"${indicators['average_purchase_cost_per_unit']:.4f}"
    )

    print("\n" + "-" * 70)
    print("QUANTITY INDICATORS")
    print("-" * 70)

    print(
        f"Purchase-to-sales quantity ratio: "
        f"{indicators['purchase_to_sales_quantity_ratio']:.4f}"
    )

    print(
        f"Inventory quantity change: "
        f"{indicators['inventory_quantity_change']:+,}"
    )

    print(
        f"Inventory quantity change: "
        f"{indicators['inventory_quantity_change_percent']:+.2f}%"
    )

    print("\n" + "-" * 70)
    print("INVENTORY VALUE INDICATORS")
    print("-" * 70)

    print(
        f"Inventory value change: "
        f"${indicators['inventory_value_change']:+,.2f}"
    )

    print(
        f"Inventory value growth: "
        f"{indicators['inventory_value_growth_percent']:+.2f}%"
    )

    print(
        f"Ending inventory value / annual sales: "
        f"{indicators['ending_inventory_to_sales_percent']:.2f}%"
    )

    print("\n" + "-" * 70)
    print("STORE-LEVEL BUSINESS INDICATORS")
    print("-" * 70)

    print(
        f"Average sales revenue per store: "
        f"${indicators['sales_revenue_per_store']:,.2f}"
    )

    print(
        f"Average ending inventory value per store: "
        f"${indicators['inventory_value_per_store']:,.2f}"
    )

    print("\n" + "-" * 70)
    print("MASTER DATA")
    print("-" * 70)

    print(
        f"Vendors: {VENDOR_COUNT:,}"
    )

    print(
        f"Stores: {STORE_COUNT:,}"
    )

    print(
        f"Products: {PRODUCT_COUNT:,}"
    )


# ============================================================
# VERIFY RESULTS
# ============================================================

def verify_indicators(indicators):

    print("\n" + "=" * 70)
    print("VERIFYING BUSINESS HEALTH INDICATORS")
    print("=" * 70)

    # --------------------------------------------------------
    # Expected calculations
    # --------------------------------------------------------

    expected_sales_purchase_ratio = (
        SALES_REVENUE
        / PURCHASE_SPENDING
    )

    expected_quantity_ratio = (
        PURCHASE_QUANTITY
        / SALES_QUANTITY
    )

    expected_quantity_change = (
        END_INVENTORY_QUANTITY
        - BEGIN_INVENTORY_QUANTITY
    )

    expected_quantity_change_percent = (
        expected_quantity_change
        / BEGIN_INVENTORY_QUANTITY
        * 100
    )

    expected_value_change = (
        END_INVENTORY_VALUE
        - BEGIN_INVENTORY_VALUE
    )

    expected_value_growth = (
        expected_value_change
        / BEGIN_INVENTORY_VALUE
        * 100
    )

    expected_sales_unit_value = (
        SALES_REVENUE
        / SALES_QUANTITY
    )

    expected_purchase_unit_cost = (
        PURCHASE_SPENDING
        / PURCHASE_QUANTITY
    )

    expected_value_difference = (
        SALES_REVENUE
        - PURCHASE_SPENDING
    )

    expected_inventory_sales_percent = (
        END_INVENTORY_VALUE
        / SALES_REVENUE
        * 100
    )

    expected_sales_per_store = (
        SALES_REVENUE
        / STORE_COUNT
    )

    expected_inventory_per_store = (
        END_INVENTORY_VALUE
        / STORE_COUNT
    )

    expected = {
        "sales_to_purchase_value_ratio":
            expected_sales_purchase_ratio,

        "purchase_to_sales_quantity_ratio":
            expected_quantity_ratio,

        "inventory_quantity_change":
            expected_quantity_change,

        "inventory_quantity_change_percent":
            expected_quantity_change_percent,

        "inventory_value_change":
            expected_value_change,

        "inventory_value_growth_percent":
            expected_value_growth,

        "average_sales_value_per_unit":
            expected_sales_unit_value,

        "average_purchase_cost_per_unit":
            expected_purchase_unit_cost,

        "sales_purchase_value_difference":
            expected_value_difference,

        "ending_inventory_to_sales_percent":
            expected_inventory_sales_percent,

        "sales_revenue_per_store":
            expected_sales_per_store,

        "inventory_value_per_store":
            expected_inventory_per_store
    }

    # --------------------------------------------------------
    # Verify every calculated indicator
    # --------------------------------------------------------

    for key, expected_value in expected.items():

        actual_value = indicators[key]

        if abs(actual_value - expected_value) <= 0.01:

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
                f"  Expected: {expected_value}"
            )

            print(
                f"  Actual:   {actual_value}"
            )

            raise ValueError(
                f"Verification failed for {key}"
            )

    print(
        "\n✓ ALL BUSINESS HEALTH INDICATOR "
        "VERIFICATION CHECKS PASSED"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    indicators = calculate_indicators()

    display_indicators(indicators)

    verify_indicators(indicators)

    print("\n" + "=" * 70)
    print("PHASE 9.9.2 COMPLETED SUCCESSFULLY")
    print("=" * 70)
