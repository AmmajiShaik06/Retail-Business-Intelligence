
"""
Business Recommendation Intelligence

Phase 10.5.2

Purpose:
Convert verified business opportunity signals into
specific, explainable business recommendations.

Input:
data/processed/business_opportunity_intelligence.csv

Output:
data/processed/business_recommendation_intelligence.csv

Important:
This module does NOT modify MySQL or ETL data.
It only analyzes the verified Business Opportunity
Intelligence output.
"""

import os
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "business_opportunity_intelligence.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "business_recommendation_intelligence.csv"
)


EXPECTED_ROWS = 12_998


# ============================================================
# REQUIRED COLUMNS
# ============================================================

REQUIRED_COLUMNS = [

    # Product identity
    "product_key",
    "brand",
    "description",
    "size",

    # Sales
    "sales_quantity",
    "sales_revenue",

    # Purchases
    "purchase_quantity",
    "purchase_spending",

    # Inventory
    "begin_inventory_quantity",
    "end_inventory_quantity",
    "begin_inventory_value",
    "end_inventory_value",
    "inventory_quantity_change",
    "inventory_value_change",
    "inventory_value_growth_percent",
    "ending_inventory_to_sales_percent",

    # Inventory presence
    "begin_inventory_present",
    "end_inventory_present",
    "inventory_present",

    # Risk
    "zero_ending_inventory",
    "large_quantity_decrease",
    "large_quantity_increase",
    "high_ending_inventory_value",
    "large_value_decrease",
    "large_value_increase",
    "risk_signal_count",
    "risk_category",

    # Business opportunity
    "business_scale_segment",
    "sales_velocity_signal",
    "inventory_exposure_signal",
    "quantity_balance_signal",
    "inventory_movement_signal",
    "opportunity_signal",
    "opportunity_priority"
]


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("\n" + "=" * 70)
    print("BUSINESS RECOMMENDATION INTELLIGENCE")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("LOADING VERIFIED BUSINESS OPPORTUNITY DATA")
    print("=" * 70)

    print("\nReading business opportunity intelligence...")

    if not os.path.exists(INPUT_FILE):

        raise FileNotFoundError(
            f"\nInput file not found:\n{INPUT_FILE}\n\n"
            "Run Phase 10.5.1 first."
        )

    df = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"Business opportunity rows: {len(df):,}"
    )

    return df


# ============================================================
# VALIDATE INPUT
# ============================================================

def validate_input(df):

    print("\n" + "=" * 70)
    print("VALIDATING INPUT DATA")
    print("=" * 70)

    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    assert len(df) == EXPECTED_ROWS, (
        f"Expected {EXPECTED_ROWS:,} rows, "
        f"found {len(df):,}"
    )

    print(
        f"✓ Complete product population: "
        f"{len(df):,}"
    )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    assert not missing_columns, (
        f"Missing required columns: "
        f"{missing_columns}"
    )

    print(
        "✓ Required input columns verified"
    )

    # --------------------------------------------------------
    # Product identity
    # --------------------------------------------------------

    assert df["product_key"].notna().all(), (
        "Missing product keys found."
    )

    print(
        "✓ No missing product keys"
    )

    assert not df["product_key"].duplicated().any(), (
        "Duplicate product identities found."
    )

    print(
        "✓ Product identities are unique"
    )


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(df):

    print("\nPreparing recommendation data...")

    numeric_columns = [

        "sales_quantity",
        "sales_revenue",

        "purchase_quantity",
        "purchase_spending",

        "begin_inventory_quantity",
        "end_inventory_quantity",

        "begin_inventory_value",
        "end_inventory_value",

        "inventory_quantity_change",
        "inventory_value_change",

        "inventory_value_growth_percent",

        "ending_inventory_to_sales_percent",

        "risk_signal_count"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
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
        "large_value_increase"
    ]

    for column in boolean_columns:

        df[column] = (
            df[column]
            .fillna(False)
            .astype(bool)
        )

    # --------------------------------------------------------
    # Numeric NaN handling
    #
    # Missing numeric values in the opportunity dataset
    # represent unavailable activity/evidence.
    # For recommendation calculations, use zero only
    # where the metric itself is an activity amount.
    # Inventory change remains NaN when evidence is incomplete.
    # --------------------------------------------------------

    activity_columns = [

        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending",

        "begin_inventory_quantity",
        "end_inventory_quantity",

        "begin_inventory_value",
        "end_inventory_value",

        "risk_signal_count"
    ]

    for column in activity_columns:

        df[column] = (
            df[column]
            .fillna(0)
        )

    return df


# ============================================================
# RECOMMENDATION RULES
# ============================================================

def generate_recommendation(row):

    opportunity = row["opportunity_signal"]

    sales_quantity = row["sales_quantity"]
    sales_revenue = row["sales_revenue"]

    purchase_quantity = row["purchase_quantity"]

    end_inventory_present = (
        row["end_inventory_present"]
    )

    end_inventory_quantity = (
        row["end_inventory_quantity"]
    )

    end_inventory_value = (
        row["end_inventory_value"]
    )

    inventory_quantity_change = (
        row["inventory_quantity_change"]
    )

    risk_signal_count = (
        row["risk_signal_count"]
    )

    # --------------------------------------------------------
    # 1. Potential replenishment
    # --------------------------------------------------------

    if opportunity == "Potential Replenishment Signal":

        return (
            "Review replenishment needs and consider "
            "restocking based on current sales activity."
        )

    # --------------------------------------------------------
    # 2. High sales + declining inventory
    # --------------------------------------------------------

    if opportunity == "High Sales With Declining Inventory":

        return (
            "Prioritize inventory monitoring and review "
            "replenishment timing because sales are strong "
            "while inventory is declining."
        )

    # --------------------------------------------------------
    # 3. Lower sales + higher inventory
    # --------------------------------------------------------

    if opportunity == "Lower Sales With Higher Inventory":

        return (
            "Review inventory levels and consider reducing "
            "future purchasing or using promotions to improve "
            "inventory movement."
        )

    # --------------------------------------------------------
    # 4. Increasing supply exposure
    # --------------------------------------------------------

    if opportunity == "Increasing Supply Exposure":

        return (
            "Review purchasing levels because supply is "
            "increasing faster than sales activity."
        )

    # --------------------------------------------------------
    # 5. Multiple inventory risks
    # --------------------------------------------------------

    if opportunity == "Multiple Inventory Risk Signals":

        return (
            "Conduct a detailed inventory review because "
            "multiple inventory risk indicators are present."
        )

    # --------------------------------------------------------
    # 6. Inventory risk
    # --------------------------------------------------------

    if opportunity == "Inventory Risk Signal":

        return (
            "Monitor inventory closely and investigate the "
            "specific risk signals before making purchasing decisions."
        )

    # --------------------------------------------------------
    # 7. Active product
    # --------------------------------------------------------

    if opportunity == "Active Product":

        if (
            end_inventory_present
            and inventory_quantity_change is not None
            and inventory_quantity_change < 0
        ):

            return (
                "Continue monitoring inventory because the "
                "product has active sales and declining stock."
            )

        return (
            "Continue normal inventory and sales monitoring "
            "for this active product."
        )

    # --------------------------------------------------------
    # 8. Limited activity
    # --------------------------------------------------------

    if opportunity == "Limited Activity":

        return (
            "Review product activity before increasing inventory "
            "or purchasing levels."
        )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    return (
        "Review product performance and inventory activity."
    )


# ============================================================
# RECOMMENDATION CATEGORY
# ============================================================

def generate_recommendation_category(row):

    opportunity = row["opportunity_signal"]

    if opportunity == "Potential Replenishment Signal":

        return "Replenishment"

    if opportunity == "High Sales With Declining Inventory":

        return "Inventory Replenishment"

    if opportunity == "Lower Sales With Higher Inventory":

        return "Inventory Optimization"

    if opportunity == "Increasing Supply Exposure":

        return "Purchasing Review"

    if opportunity == "Multiple Inventory Risk Signals":

        return "Risk Investigation"

    if opportunity == "Inventory Risk Signal":

        return "Risk Monitoring"

    if opportunity == "Active Product":

        return "Performance Monitoring"

    if opportunity == "Limited Activity":

        return "Low Activity Review"

    return "General Review"


# ============================================================
# RECOMMENDATION PRIORITY
# ============================================================

def generate_recommendation_priority(row):

    opportunity = row["opportunity_signal"]

    risk_count = row["risk_signal_count"]

    # --------------------------------------------------------
    # Highest priority
    # --------------------------------------------------------

    if opportunity in [

        "Potential Replenishment Signal",

        "High Sales With Declining Inventory"

    ]:

        return "High"

    # --------------------------------------------------------
    # High risk
    # --------------------------------------------------------

    if opportunity == "Multiple Inventory Risk Signals":

        return "High"

    # --------------------------------------------------------
    # Medium priority
    # --------------------------------------------------------

    if opportunity in [

        "Lower Sales With Higher Inventory",

        "Increasing Supply Exposure",

        "Inventory Risk Signal"

    ]:

        return "Medium"

    # --------------------------------------------------------
    # Risk count fallback
    # --------------------------------------------------------

    if risk_count >= 1:

        return "Medium"

    # --------------------------------------------------------
    # Normal
    # --------------------------------------------------------

    if opportunity == "Active Product":

        return "Normal"

    return "Low"


# ============================================================
# ACTION
# ============================================================

def generate_action(row):

    category = row["recommendation_category"]

    if category == "Replenishment":

        return (
            "Check current stock and evaluate whether "
            "replenishment should be scheduled."
        )

    if category == "Inventory Replenishment":

        return (
            "Monitor stock closely and evaluate the next "
            "purchase order timing."
        )

    if category == "Inventory Optimization":

        return (
            "Review stock levels, sales velocity and possible "
            "promotional or purchasing adjustments."
        )

    if category == "Purchasing Review":

        return (
            "Compare purchasing quantities with sales movement "
            "before increasing future orders."
        )

    if category == "Risk Investigation":

        return (
            "Investigate the underlying inventory risk signals "
            "before making purchasing decisions."
        )

    if category == "Risk Monitoring":

        return (
            "Monitor the product and investigate the identified "
            "inventory risk."
        )

    if category == "Performance Monitoring":

        return (
            "Continue monitoring sales and inventory performance."
        )

    if category == "Low Activity Review":

        return (
            "Review demand before committing additional "
            "inventory."
        )

    return (
        "Review product performance and inventory position."
    )


# ============================================================
# BUILD RECOMMENDATIONS
# ============================================================

def build_recommendations(df):

    print("\n" + "=" * 70)
    print("GENERATING BUSINESS RECOMMENDATIONS")
    print("=" * 70)

    df["recommendation_category"] = df.apply(
        generate_recommendation_category,
        axis=1
    )

    df["recommendation_priority"] = df.apply(
        generate_recommendation_priority,
        axis=1
    )

    df["recommendation"] = df.apply(
        generate_recommendation,
        axis=1
    )

    df["recommended_action"] = df.apply(
        generate_action,
        axis=1
    )

    # --------------------------------------------------------
    # Recommendation score
    #
    # This is NOT a business profitability score.
    # It only helps order the recommendation review queue.
    # --------------------------------------------------------

    priority_score = {

        "High": 3,
        "Medium": 2,
        "Normal": 1,
        "Low": 0

    }

    df["recommendation_priority_score"] = (
        df["recommendation_priority"]
        .map(priority_score)
        .fillna(0)
        .astype(int)
    )

    # --------------------------------------------------------
    # Sort review queue
    # --------------------------------------------------------

    df = df.sort_values(
        [
            "recommendation_priority_score",
            "risk_signal_count",
            "sales_revenue",
            "end_inventory_value"
        ],
        ascending=[
            False,
            False,
            False,
            False
        ]
    ).reset_index(
        drop=True
    )

    return df


# ============================================================
# VERIFY RECOMMENDATIONS
# ============================================================

def verify_recommendations(df):

    print("\n" + "=" * 70)
    print("VERIFYING BUSINESS RECOMMENDATIONS")
    print("=" * 70)

    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    assert len(df) == EXPECTED_ROWS

    print(
        f"Products analyzed: {len(df):,}"
    )

    # --------------------------------------------------------
    # Product identity
    # --------------------------------------------------------

    assert not df["product_key"].duplicated().any()

    print(
        "✓ No duplicate product identities"
    )

    # --------------------------------------------------------
    # Source totals
    # --------------------------------------------------------

    expected_sales_quantity = 32_917_876
    expected_sales_revenue = 452_062_952.02

    expected_purchase_quantity = 33_584_377
    expected_purchase_spending = 321_900_765.53

    expected_begin_quantity = 4_219_275
    expected_begin_value = 68_053_780.17

    expected_end_quantity = 4_885_776
    expected_end_value = 79_704_851.13

    assert (
        int(df["sales_quantity"].sum())
        == expected_sales_quantity
    )

    print(
        "✓ Sales quantity reconciled"
    )

    assert round(
        df["sales_revenue"].sum(),
        2
    ) == expected_sales_revenue

    print(
        "✓ Sales revenue reconciled"
    )

    assert (
        int(df["purchase_quantity"].sum())
        == expected_purchase_quantity
    )

    print(
        "✓ Purchase quantity reconciled"
    )

    assert round(
        df["purchase_spending"].sum(),
        2
    ) == expected_purchase_spending

    print(
        "✓ Purchase spending reconciled"
    )

    assert (
        int(df["begin_inventory_quantity"].sum())
        == expected_begin_quantity
    )

    print(
        "✓ Beginning inventory quantity reconciled"
    )

    assert round(
        df["begin_inventory_value"].sum(),
        2
    ) == expected_begin_value

    print(
        "✓ Beginning inventory value reconciled"
    )

    assert (
        int(df["end_inventory_quantity"].sum())
        == expected_end_quantity
    )

    print(
        "✓ Ending inventory quantity reconciled"
    )

    assert round(
        df["end_inventory_value"].sum(),
        2
    ) == expected_end_value

    print(
        "✓ Ending inventory value reconciled"
    )

    # --------------------------------------------------------
    # Recommendation columns
    # --------------------------------------------------------

    recommendation_columns = [

        "recommendation_category",
        "recommendation_priority",
        "recommendation",
        "recommended_action",
        "recommendation_priority_score"

    ]

    for column in recommendation_columns:

        assert df[column].notna().all(), (
            f"Missing recommendation values "
            f"in {column}"
        )

    print(
        "✓ Recommendation fields generated"
    )

    # --------------------------------------------------------
    # Valid priorities
    # --------------------------------------------------------

    valid_priorities = {

        "High",
        "Medium",
        "Normal",
        "Low"

    }

    actual_priorities = set(
        df["recommendation_priority"]
        .unique()
    )

    assert actual_priorities.issubset(
        valid_priorities
    )

    print(
        "✓ Recommendation priorities are valid"
    )

    # --------------------------------------------------------
    # Valid categories
    # --------------------------------------------------------

    valid_categories = {

        "Replenishment",
        "Inventory Replenishment",
        "Inventory Optimization",
        "Purchasing Review",
        "Risk Investigation",
        "Risk Monitoring",
        "Performance Monitoring",
        "Low Activity Review",
        "General Review"

    }

    actual_categories = set(
        df["recommendation_category"]
        .unique()
    )

    assert actual_categories.issubset(
        valid_categories
    )

    print(
        "✓ Recommendation categories are valid"
    )

    # --------------------------------------------------------
    # Recommendation consistency
    # --------------------------------------------------------

    high_priority = df[
        df["recommendation_priority"] == "High"
    ]

    assert len(high_priority) > 0

    print(
        "✓ High-priority recommendations generated"
    )

    # --------------------------------------------------------
    # Zero inventory evidence
    # --------------------------------------------------------

    invalid_zero_inventory = df[
        df["zero_ending_inventory"]
        & ~df["end_inventory_present"]
    ]

    assert len(invalid_zero_inventory) == 0

    print(
        "✓ Zero-inventory recommendations have valid evidence"
    )

    # --------------------------------------------------------
    # Print summaries
    # --------------------------------------------------------

    print(
        "\nRecommendation category count:"
    )

    print(
        df["recommendation_category"]
        .value_counts()
        .to_string()
    )

    print(
        "\nRecommendation priority count:"
    )

    print(
        df["recommendation_priority"]
        .value_counts()
        .to_string()
    )

    print(
        "\n✓ ALL BUSINESS RECOMMENDATION "
        "VERIFICATION CHECKS PASSED"
    )


# ============================================================
# DISPLAY TOP RECOMMENDATIONS
# ============================================================

def display_top_recommendations(df):

    print("\n" + "=" * 70)
    print("TOP BUSINESS RECOMMENDATIONS")
    print("=" * 70)

    display_columns = [

        "brand",
        "description",
        "size",

        "sales_quantity",
        "sales_revenue",

        "purchase_quantity",

        "end_inventory_quantity",
        "end_inventory_value",

        "risk_signal_count",

        "opportunity_signal",

        "recommendation_priority",

        "recommendation_category",

        "recommendation"

    ]

    top = df[
        display_columns
    ].head(15)

    print(
        top.to_string(
            index=False
        )
    )


# ============================================================
# SAVE OUTPUT
# ============================================================

def save_output(df):

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    df.to_csv(
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
        OUTPUT_FILE.replace(
            BASE_DIR + os.sep,
            ""
        )
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    df = load_data()

    validate_input(
        df
    )

    df = prepare_data(
        df
    )

    df = build_recommendations(
        df
    )

    verify_recommendations(
        df
    )

    display_top_recommendations(
        df
    )

    save_output(
        df
    )

    print("\n" + "=" * 70)
    print(
        "BUSINESS RECOMMENDATION INTELLIGENCE COMPLETED"
    )
    print("=" * 70)