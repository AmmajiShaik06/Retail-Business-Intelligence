
"""
Business Opportunity Intelligence.

Phase 10.5.1

Purpose:
Use the verified Inventory Intelligence dataset to identify
business opportunity signals at product level.

IMPORTANT:
- This script does NOT modify MySQL.
- This script does NOT reload sales, purchases, or inventory.
- Inventory Intelligence is the authoritative product-level source
  because it already contains sales, purchase, inventory and risk
  metrics across the complete 12,998-product universe.
- Signals are descriptive indicators, NOT automatic business decisions.
"""

import os
import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INVENTORY_INTELLIGENCE_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "inventory_intelligence.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "business_opportunity_intelligence.csv"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "product_key",
    "brand",
    "description",
    "size",

    "sales_quantity",
    "sales_revenue",

    "purchase_quantity",
    "purchase_spending",

    "quantity_balance",
    "sales_purchase_value_ratio",

    "average_sales_value",
    "average_purchase_cost",

    "begin_inventory_quantity",
    "end_inventory_quantity",

    "inventory_quantity_change",

    "begin_inventory_value",
    "end_inventory_value",

    "inventory_value_change",
    "inventory_value_growth_percent",

    "ending_inventory_to_sales_percent",

    "begin_inventory_present",
    "end_inventory_present",
    "inventory_present",

    "zero_ending_inventory",

    "large_quantity_decrease",
    "large_quantity_increase",

    "high_ending_inventory_value",

    "large_value_decrease",
    "large_value_increase",

    "risk_signal_count",
    "risk_category",
]


# ============================================================
# LOAD VERIFIED INVENTORY INTELLIGENCE
# ============================================================

def load_verified_data():

    print("\n" + "=" * 70)
    print("LOADING VERIFIED INVENTORY INTELLIGENCE")
    print("=" * 70)

    if not os.path.exists(
        INVENTORY_INTELLIGENCE_FILE
    ):

        raise FileNotFoundError(
            "Inventory intelligence file not found:\n"
            f"{INVENTORY_INTELLIGENCE_FILE}"
        )

    print("\nReading inventory intelligence...")

    opportunity = pd.read_csv(
        INVENTORY_INTELLIGENCE_FILE
    )

    print(
        f"Inventory intelligence rows: "
        f"{len(opportunity):,}"
    )

    return opportunity


# ============================================================
# VALIDATE INPUT DATA
# ============================================================

def validate_input_data(
    opportunity
):

    print("\n" + "=" * 70)
    print("VALIDATING INPUT DATA")
    print("=" * 70)

    # --------------------------------------------------------
    # Expected complete product universe
    # --------------------------------------------------------

    expected_rows = 12_998

    assert len(opportunity) == expected_rows

    print(
        f"✓ Complete product population: "
        f"{len(opportunity):,}"
    )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in opportunity.columns
    ]

    assert not missing_columns, (
        "Missing required columns: "
        + str(missing_columns)
    )

    print("✓ Required input columns verified")

    # --------------------------------------------------------
    # Product identity uniqueness
    # --------------------------------------------------------

    duplicate_keys = (
        opportunity["product_key"]
        .duplicated()
        .sum()
    )

    assert duplicate_keys == 0

    print("✓ Product identities are unique")

    # --------------------------------------------------------
    # Product key missing values
    # --------------------------------------------------------

    missing_product_keys = (
        opportunity["product_key"]
        .isna()
        .sum()
    )

    assert missing_product_keys == 0

    print("✓ No missing product keys")


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(opportunity):

    numeric_columns = [
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending",
        "quantity_balance",
        "sales_purchase_value_ratio",
        "average_sales_value",
        "average_purchase_cost",
        "begin_inventory_quantity",
        "end_inventory_quantity",
        "inventory_quantity_change",
        "begin_inventory_value",
        "end_inventory_value",
        "inventory_value_change",
        "inventory_value_growth_percent",
        "ending_inventory_to_sales_percent",
        "risk_signal_count",
    ]

    for column in numeric_columns:

        opportunity[column] = pd.to_numeric(
            opportunity[column],
            errors="coerce"
        )

    boolean_columns = [
        "begin_inventory_present",
        "end_inventory_present",
        "inventory_present",
        "zero_ending_inventory",
        "large_quantity_decrease",
        "large_quantity_increase",
        "high_ending_inventory_value",
        "large_value_decrease",
        "large_value_increase",
    ]

    for column in boolean_columns:

        opportunity[column] = (
            opportunity[column]
            .fillna(False)
            .astype(bool)
        )

    return opportunity


# ============================================================
# BUSINESS SCALE SEGMENT
# ============================================================

def calculate_business_scale_segments(
    opportunity
):

    sales_median = (
        opportunity["sales_revenue"]
        .median()
    )

    purchase_median = (
        opportunity["purchase_spending"]
        .median()
    )

    def classify(row):

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

        if high_sales and not high_purchase:

            return "High Sales / Lower Purchase"

        if not high_sales and high_purchase:

            return "Lower Sales / High Purchase"

        return "Lower Sales / Lower Purchase"

    opportunity[
        "business_scale_segment"
    ] = opportunity.apply(
        classify,
        axis=1
    )

    print("\nBusiness scale thresholds:")

    print(
        f"Sales revenue median: "
        f"${sales_median:,.2f}"
    )

    print(
        f"Purchase spending median: "
        f"${purchase_median:,.2f}"
    )

    return opportunity


# ============================================================
# SALES VELOCITY SIGNAL
# ============================================================

def calculate_sales_velocity_signal(
    opportunity
):

    sales_quantity_median = (
        opportunity["sales_quantity"]
        .median()
    )

    def classify(row):

        if row["sales_quantity"] == 0:

            return "No Sales"

        if (
            row["sales_quantity"]
            >= sales_quantity_median
        ):

            return "Higher Sales Quantity"

        return "Lower Sales Quantity"

    opportunity[
        "sales_velocity_signal"
    ] = opportunity.apply(
        classify,
        axis=1
    )

    return opportunity


# ============================================================
# INVENTORY EXPOSURE SIGNAL
# ============================================================

def calculate_inventory_exposure(
    opportunity
):

    inventory_values = (
        opportunity.loc[
            opportunity["end_inventory_present"],
            "end_inventory_value"
        ]
    )

    inventory_value_median = (
        inventory_values.median()
    )

    def classify(row):

        if not row["end_inventory_present"]:

            return "No Ending Inventory Evidence"

        if row["end_inventory_value"] == 0:

            return "Zero Ending Inventory"

        if (
            row["end_inventory_value"]
            >= inventory_value_median
        ):

            return "Higher Inventory Exposure"

        return "Lower Inventory Exposure"

    opportunity[
        "inventory_exposure_signal"
    ] = opportunity.apply(
        classify,
        axis=1
    )

    print(
        f"\nEnding inventory value median: "
        f"${inventory_value_median:,.2f}"
    )

    return opportunity


# ============================================================
# QUANTITY BALANCE SIGNAL
# ============================================================

def calculate_quantity_balance_signal(
    opportunity
):

    def classify(row):

        if row["purchase_quantity"] == 0:

            if row["sales_quantity"] > 0:

                return "Sales Without Purchase Data"

            return "No Purchase Activity"

        if row["quantity_balance"] > 0:

            return "Purchases Exceed Sales"

        if row["quantity_balance"] < 0:

            return "Sales Exceed Purchases"

        return "Balanced Quantity"

    opportunity[
        "quantity_balance_signal"
    ] = opportunity.apply(
        classify,
        axis=1
    )

    return opportunity


# ============================================================
# INVENTORY MOVEMENT SIGNAL
# ============================================================

def calculate_inventory_movement_signal(
    opportunity
):

    def classify(row):

        if not (
            row["begin_inventory_present"]
            and row["end_inventory_present"]
        ):

            return "Incomplete Inventory History"

        change = (
            row["inventory_quantity_change"]
        )

        if pd.isna(change):

            return "Incomplete Inventory History"

        if change > 0:

            return "Inventory Increased"

        if change < 0:

            return "Inventory Decreased"

        return "Inventory Unchanged"

    opportunity[
        "inventory_movement_signal"
    ] = opportunity.apply(
        classify,
        axis=1
    )

    return opportunity


# ============================================================
# OPPORTUNITY SIGNAL
# ============================================================

def calculate_opportunity_signal(
    opportunity
):

    """
    Generate descriptive business signals.

    These signals do NOT represent profitability,
    quality or automatic business decisions.
    """

    sales_median = (
        opportunity["sales_revenue"]
        .median()
    )

    inventory_values = (
        opportunity.loc[
            opportunity["end_inventory_present"],
            "end_inventory_value"
        ]
    )

    inventory_median = (
        inventory_values.median()
    )

    def classify(row):

        sales = row["sales_revenue"]
        sales_quantity = row["sales_quantity"]
        purchase_quantity = row["purchase_quantity"]
        inventory_value = row["end_inventory_value"]

        # ----------------------------------------------------
        # Potential replenishment
        # ----------------------------------------------------

        if (
            sales_quantity > 0
            and row["end_inventory_present"]
            and inventory_value == 0
        ):

            return "Potential Replenishment Signal"

        # ----------------------------------------------------
        # High sales with declining inventory
        # ----------------------------------------------------

        if (
            sales >= sales_median
            and sales_quantity > 0
            and row["begin_inventory_present"]
            and row["end_inventory_present"]
            and row["inventory_quantity_change"] < 0
        ):

            return (
                "High Sales With Declining Inventory"
            )

        # ----------------------------------------------------
        # Low sales + high inventory
        # ----------------------------------------------------

        if (
            sales < sales_median
            and row["end_inventory_present"]
            and inventory_value >= inventory_median
        ):

            return (
                "Lower Sales With Higher Inventory"
            )

        # ----------------------------------------------------
        # Purchases exceed sales and inventory increased
        # ----------------------------------------------------

        if (
            purchase_quantity > sales_quantity
            and row["inventory_quantity_change"]
            > 0
        ):

            return "Increasing Supply Exposure"

        # ----------------------------------------------------
        # Multiple inventory risk signals
        # ----------------------------------------------------

        if row["risk_signal_count"] >= 3:

            return "Multiple Inventory Risk Signals"

        # ----------------------------------------------------
        # Other inventory risk
        # ----------------------------------------------------

        if row["risk_signal_count"] > 0:

            return "Inventory Risk Signal"

        # ----------------------------------------------------
        # Active product
        # ----------------------------------------------------

        if sales > 0:

            return "Active Product"

        # ----------------------------------------------------
        # No sales
        # ----------------------------------------------------

        return "Limited Activity"

    opportunity[
        "opportunity_signal"
    ] = opportunity.apply(
        classify,
        axis=1
    )

    return opportunity


# ============================================================
# OPPORTUNITY PRIORITY
# ============================================================

def calculate_opportunity_priority(
    opportunity
):

    """
    Screening priority based on observable signals.

    This is NOT a profitability score.
    """

    def classify(row):

        signal = (
            row["opportunity_signal"]
        )

        risk_count = (
            row["risk_signal_count"]
        )

        if signal in [
            "Potential Replenishment Signal",
            "High Sales With Declining Inventory",
        ]:

            return "Review First"

        if signal in [
            "Lower Sales With Higher Inventory",
            "Increasing Supply Exposure",
            "Multiple Inventory Risk Signals",
        ]:

            return "Review"

        if risk_count > 0:

            return "Monitor"

        if row["sales_revenue"] > 0:

            return "Normal Monitoring"

        return "Low Activity"

    opportunity[
        "opportunity_priority"
    ] = opportunity.apply(
        classify,
        axis=1
    )

    return opportunity


# ============================================================
# VERIFICATION
# ============================================================

def verify_opportunity_intelligence(
    opportunity
):

    print("\n" + "=" * 70)
    print("VERIFYING BUSINESS OPPORTUNITY INTELLIGENCE")
    print("=" * 70)

    # --------------------------------------------------------
    # Product population
    # --------------------------------------------------------

    assert len(opportunity) == 12_998

    print(
        f"Products analyzed: "
        f"{len(opportunity):,}"
    )

    # --------------------------------------------------------
    # Product identity uniqueness
    # --------------------------------------------------------

    assert (
        opportunity["product_key"]
        .duplicated()
        .sum()
        == 0
    )

    print(
        "✓ No duplicate product identities"
    )

    # --------------------------------------------------------
    # Sales totals
    # --------------------------------------------------------

    sales_quantity = int(
        opportunity["sales_quantity"].sum()
    )

    sales_revenue = round(
        opportunity["sales_revenue"].sum(),
        2
    )

    assert sales_quantity == 32_917_876

    assert sales_revenue == 452_062_952.02

    print(
        "✓ Sales quantity reconciled"
    )

    print(
        "✓ Sales revenue reconciled"
    )

    # --------------------------------------------------------
    # Purchase totals
    # --------------------------------------------------------

    purchase_quantity = int(
        opportunity[
            "purchase_quantity"
        ].sum()
    )

    purchase_spending = round(
        opportunity[
            "purchase_spending"
        ].sum(),
        2
    )

    assert purchase_quantity == 33_584_377

    assert purchase_spending == 321_900_765.53

    print(
        "✓ Purchase quantity reconciled"
    )

    print(
        "✓ Purchase spending reconciled"
    )

    # --------------------------------------------------------
    # Beginning inventory
    # --------------------------------------------------------

    begin_quantity = int(
        opportunity[
            "begin_inventory_quantity"
        ].sum()
    )

    begin_value = round(
        opportunity[
            "begin_inventory_value"
        ].sum(),
        2
    )

    assert begin_quantity == 4_219_275

    assert begin_value == 68_053_780.17

    print(
        "✓ Beginning inventory quantity reconciled"
    )

    print(
        "✓ Beginning inventory value reconciled"
    )

    # --------------------------------------------------------
    # Ending inventory
    # --------------------------------------------------------

    end_quantity = int(
        opportunity[
            "end_inventory_quantity"
        ].sum()
    )

    end_value = round(
        opportunity[
            "end_inventory_value"
        ].sum(),
        2
    )

    assert end_quantity == 4_885_776

    assert end_value == 79_704_851.13

    print(
        "✓ Ending inventory quantity reconciled"
    )

    print(
        "✓ Ending inventory value reconciled"
    )

    # --------------------------------------------------------
    # Inventory presence
    # --------------------------------------------------------

    expected_presence = (
        opportunity[
            "begin_inventory_present"
        ]
        |
        opportunity[
            "end_inventory_present"
        ]
    )

    assert (
        opportunity["inventory_present"]
        == expected_presence
    ).all()

    print(
        "✓ Inventory presence flags are consistent"
    )

    # --------------------------------------------------------
    # Opportunity signals
    # --------------------------------------------------------

    assert (
        opportunity[
            "opportunity_signal"
        ]
        .notna()
        .all()
    )

    assert (
        opportunity[
            "opportunity_priority"
        ]
        .notna()
        .all()
    )

    print(
        "✓ Opportunity signals generated"
    )

    print(
        "✓ Opportunity priorities generated"
    )

    # --------------------------------------------------------
    # Risk evidence
    # --------------------------------------------------------

    invalid_zero_inventory = (
        opportunity[
            "zero_ending_inventory"
        ]
        &
        ~opportunity[
            "end_inventory_present"
        ]
    )

    assert not invalid_zero_inventory.any()

    print(
        "✓ Zero-inventory signals have valid evidence"
    )

    # --------------------------------------------------------
    # Signal counts
    # --------------------------------------------------------

    print(
        "\nOpportunity signal count:"
    )

    signal_counts = (
        opportunity[
            "opportunity_signal"
        ]
        .value_counts()
    )

    for signal, count in signal_counts.items():

        print(
            f"{signal}: {count:,}"
        )

    print(
        "\nOpportunity priority count:"
    )

    priority_counts = (
        opportunity[
            "opportunity_priority"
        ]
        .value_counts()
    )

    for priority, count in priority_counts.items():

        print(
            f"{priority}: {count:,}"
        )

    print(
        "\n✓ ALL BUSINESS OPPORTUNITY "
        "VERIFICATION CHECKS PASSED"
    )


# ============================================================
# DISPLAY TOP REVIEW PRODUCTS
# ============================================================

def display_review_products(
    opportunity
):

    print("\n" + "=" * 70)
    print("TOP REVIEW-FIRST PRODUCTS")
    print("=" * 70)

    review_first = (
        opportunity[
            opportunity[
                "opportunity_priority"
            ]
            == "Review First"
        ]
        .sort_values(
            [
                "sales_revenue",
                "end_inventory_value"
            ],
            ascending=False
        )
        .head(10)
    )

    if review_first.empty:

        print(
            "No products currently meet "
            "Review First conditions."
        )

        return

    display_columns = [
        "brand",
        "description",
        "size",
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "end_inventory_quantity",
        "end_inventory_value",
        "inventory_quantity_change",
        "risk_signal_count",
        "opportunity_signal",
    ]

    print(
        review_first[
            display_columns
        ].to_string(
            index=False
        )
    )


# ============================================================
# SAVE OUTPUT
# ============================================================

def save_output(
    opportunity
):

    os.makedirs(
        os.path.dirname(
            OUTPUT_FILE
        ),
        exist_ok=True
    )

    opportunity.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 70)
    print("OUTPUT")
    print("=" * 70)

    print(
        "\n✓ Output saved to:"
    )

    print(
        "data/processed/"
        "business_opportunity_intelligence.csv"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("BUSINESS OPPORTUNITY INTELLIGENCE")
    print("=" * 70)

    # --------------------------------------------------------
    # Load verified Inventory Intelligence
    # --------------------------------------------------------

    opportunity = load_verified_data()

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_input_data(
        opportunity
    )

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    opportunity = prepare_data(
        opportunity
    )

    # --------------------------------------------------------
    # Business intelligence signals
    # --------------------------------------------------------

    opportunity = (
        calculate_business_scale_segments(
            opportunity
        )
    )

    opportunity = (
        calculate_sales_velocity_signal(
            opportunity
        )
    )

    opportunity = (
        calculate_inventory_exposure(
            opportunity
        )
    )

    opportunity = (
        calculate_quantity_balance_signal(
            opportunity
        )
    )

    opportunity = (
        calculate_inventory_movement_signal(
            opportunity
        )
    )

    opportunity = (
        calculate_opportunity_signal(
            opportunity
        )
    )

    opportunity = (
        calculate_opportunity_priority(
            opportunity
        )
    )

    # --------------------------------------------------------
    # Verify
    # --------------------------------------------------------

    verify_opportunity_intelligence(
        opportunity
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_output(
        opportunity
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    display_review_products(
        opportunity
    )

    print("\n" + "=" * 70)
    print(
        "BUSINESS OPPORTUNITY "
        "INTELLIGENCE COMPLETED"
    )
    print("=" * 70)
