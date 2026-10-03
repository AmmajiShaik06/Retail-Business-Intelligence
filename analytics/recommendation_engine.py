import os
import pandas as pd


INPUT_FILE = "data/processed/business_recommendation_intelligence.csv"
OUTPUT_DIRECTORY = "data/processed"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIRECTORY,
    "recommendation_engine.csv"
)


def load_recommendation_data():
    df = pd.read_csv(INPUT_FILE)
    return df


def prepare_recommendations(df):
    columns = [
        "product_key",
        "brand",
        "description",
        "size",
        "classification",
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending",
        "end_inventory_quantity",
        "end_inventory_value",
        "risk_category",
        "business_scale_segment",
        "sales_velocity_signal",
        "inventory_exposure_signal",
        "quantity_balance_signal",
        "inventory_movement_signal",
        "opportunity_signal",
        "opportunity_priority",
        "recommendation_category",
        "recommendation_priority",
        "recommendation",
        "recommended_action",
        "recommendation_priority_score"
    ]

    result = df[columns].copy()

    result = result.sort_values(
        by=[
            "recommendation_priority_score",
            "sales_revenue"
        ],
        ascending=[False, False]
    )

    return result


if __name__ == "__main__":

    print("\nRecommendation Engine")
    print("-" * 40)

    df = load_recommendation_data()

    print("Input Shape:", df.shape)

    recommendations = prepare_recommendations(df)

    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

    recommendations.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nRecommendation Output")
    print("-" * 40)

    print("Output Shape:", recommendations.shape)
    print("Output File:", OUTPUT_FILE)

    print("\nPriority Distribution:")
    print(
        recommendations[
            "recommendation_priority"
        ].value_counts()
    )

    print("\nTop 10 Recommendations:")
    print(
        recommendations[
            [
                "product_key",
                "description",
                "recommendation_category",
                "recommendation_priority",
                "recommendation"
            ]
        ].head(10).to_string(index=False)
    )

    print("\nMissing Values:")
    print(
        recommendations.isnull().sum()
    )