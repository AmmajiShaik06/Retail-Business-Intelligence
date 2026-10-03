"""
Classification Sales vs Purchase Analysis

Compares sales and purchases by product classification.

This script:
1. Aggregates sales by classification in chunks.
2. Aggregates purchases by classification in chunks.
3. Combines both datasets.
4. Calculates quantity differences.
5. Calculates sales-to-purchase quantity ratios.
6. Calculates sales-to-purchase value ratios.
7. Compares sales and purchase contribution.
8. Verifies all totals against MySQL.

Important:
Sales-to-purchase value ratio is NOT profit margin.
It is only a comparison of sales revenue to purchase spending.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 250_000


# ============================================================
# 1. SALES BY CLASSIFICATION
# ============================================================

def load_sales_by_classification():

    print("\n" + "=" * 70)
    print("LOADING SALES BY CLASSIFICATION")
    print("=" * 70)

    query = """
        SELECT
            classification,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = 1
    """

    results = []

    total_rows = 0

    for chunk_number, chunk in enumerate(
        pd.read_sql(
            query,
            con=engine,
            chunksize=CHUNK_SIZE
        ),
        start=1
    ):

        total_rows += len(chunk)

        print(
            f"Sales chunk {chunk_number}: "
            f"{len(chunk):,} rows"
        )

        chunk["classification"] = (
            chunk["classification"]
            .astype("string")
            .str.strip()
        )

        chunk = chunk.dropna(
            subset=["classification"]
        )

        grouped = (
            chunk
            .groupby("classification", as_index=False)
            .agg(
                sales_quantity=("sales_quantity", "sum"),
                sales_revenue=("sales_dollars", "sum")
            )
        )

        results.append(grouped)

    combined = pd.concat(
        results,
        ignore_index=True
    )

    final = (
        combined
        .groupby("classification", as_index=False)
        .agg(
            sales_quantity=("sales_quantity", "sum"),
            sales_revenue=("sales_revenue", "sum")
        )
    )

    print(
        f"\nTotal sales rows processed: "
        f"{total_rows:,}"
    )

    return final


# ============================================================
# 2. PURCHASES BY CLASSIFICATION
# ============================================================

def load_purchases_by_classification():

    print("\n" + "=" * 70)
    print("LOADING PURCHASES BY CLASSIFICATION")
    print("=" * 70)

    query = """
        SELECT
            classification,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = 1
    """

    results = []

    total_rows = 0

    for chunk_number, chunk in enumerate(
        pd.read_sql(
            query,
            con=engine,
            chunksize=CHUNK_SIZE
        ),
        start=1
    ):

        total_rows += len(chunk)

        print(
            f"Purchase chunk {chunk_number}: "
            f"{len(chunk):,} rows"
        )

        chunk["classification"] = (
            chunk["classification"]
            .astype("string")
            .str.strip()
        )

        chunk = chunk.dropna(
            subset=["classification"]
        )

        grouped = (
            chunk
            .groupby("classification", as_index=False)
            .agg(
                purchase_quantity=("quantity", "sum"),
                purchase_spending=("dollars", "sum")
            )
        )

        results.append(grouped)

    combined = pd.concat(
        results,
        ignore_index=True
    )

    final = (
        combined
        .groupby("classification", as_index=False)
        .agg(
            purchase_quantity=("purchase_quantity", "sum"),
            purchase_spending=("purchase_spending", "sum")
        )
    )

    print(
        f"\nTotal purchase rows processed: "
        f"{total_rows:,}"
    )

    return final


# ============================================================
# 3. COMBINE SALES AND PURCHASES
# ============================================================

def combine_results(
    sales,
    purchases
):

    print("\n" + "=" * 70)
    print("COMBINING SALES AND PURCHASE DATA")
    print("=" * 70)

    final = pd.merge(
        sales,
        purchases,
        on="classification",
        how="outer"
    )

    # --------------------------------------------------------
    # Replace missing numeric values with zero
    # --------------------------------------------------------

    numeric_columns = [
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending"
    ]

    for column in numeric_columns:

        final[column] = (
            final[column]
            .fillna(0)
        )

    # --------------------------------------------------------
    # Quantity difference
    #
    # Positive = sales quantity > purchase quantity
    # Negative = purchase quantity > sales quantity
    # --------------------------------------------------------

    final["quantity_difference"] = (
        final["sales_quantity"]
        - final["purchase_quantity"]
    )

    # --------------------------------------------------------
    # Sales-to-purchase quantity ratio
    # --------------------------------------------------------

    final["quantity_ratio"] = (
        final["sales_quantity"]
        / final["purchase_quantity"]
        .replace(0, pd.NA)
    )

    # --------------------------------------------------------
    # Sales-to-purchase value ratio
    #
    # IMPORTANT:
    # This is NOT profit margin.
    # --------------------------------------------------------

    final["value_ratio"] = (
        final["sales_revenue"]
        / final["purchase_spending"]
        .replace(0, pd.NA)
    )

    # --------------------------------------------------------
    # Contribution percentages
    # --------------------------------------------------------

    total_sales = final["sales_revenue"].sum()

    total_purchase = final["purchase_spending"].sum()

    final["sales_contribution_pct"] = (
        final["sales_revenue"]
        / total_sales
        * 100
    )

    final["purchase_contribution_pct"] = (
        final["purchase_spending"]
        / total_purchase
        * 100
    )

    # --------------------------------------------------------
    # Contribution difference
    # --------------------------------------------------------

    final["contribution_difference_pct"] = (
        final["sales_contribution_pct"]
        - final["purchase_contribution_pct"]
    )

    # --------------------------------------------------------
    # Sort by sales revenue
    # --------------------------------------------------------

    final = final.sort_values(
        "sales_revenue",
        ascending=False
    ).reset_index(drop=True)

    return final


# ============================================================
# 4. DISPLAY SUMMARY
# ============================================================

def display_summary(final):

    print("\n" + "=" * 70)
    print("CLASSIFICATION SALES VS PURCHASE SUMMARY")
    print("=" * 70)

    print(
        f"\nClassifications compared: "
        f"{len(final):,}"
    )

    print(
        f"Total sales quantity: "
        f"{final['sales_quantity'].sum():,.0f}"
    )

    print(
        f"Total purchase quantity: "
        f"{final['purchase_quantity'].sum():,.0f}"
    )

    print(
        f"Quantity difference: "
        f"{final['quantity_difference'].sum():,.0f}"
    )

    print(
        f"Total sales revenue: "
        f"${final['sales_revenue'].sum():,.2f}"
    )

    print(
        f"Total purchase spending: "
        f"${final['purchase_spending'].sum():,.2f}"
    )


# ============================================================
# 5. DISPLAY CLASSIFICATION DETAILS
# ============================================================

def display_classification_details(final):

    print("\n" + "-" * 70)
    print("CLASSIFICATION COMPARISON")
    print("-" * 70)

    for index, row in final.iterrows():

        print(
            f"\nClassification {row['classification']}"
        )

        print(
            f"Sales quantity: "
            f"{row['sales_quantity']:,.0f}"
        )

        print(
            f"Purchase quantity: "
            f"{row['purchase_quantity']:,.0f}"
        )

        print(
            f"Quantity difference: "
            f"{row['quantity_difference']:,.0f}"
        )

        print(
            f"Quantity ratio: "
            f"{row['quantity_ratio']:.4f}"
        )

        print(
            f"Sales revenue: "
            f"${row['sales_revenue']:,.2f}"
        )

        print(
            f"Purchase spending: "
            f"${row['purchase_spending']:,.2f}"
        )

        print(
            f"Sales-to-purchase value ratio: "
            f"{row['value_ratio']:.4f}"
        )

        print(
            f"Sales contribution: "
            f"{row['sales_contribution_pct']:.2f}%"
        )

        print(
            f"Purchase contribution: "
            f"{row['purchase_contribution_pct']:.2f}%"
        )

        print(
            f"Contribution difference: "
            f"{row['contribution_difference_pct']:+.2f} percentage points"
        )


# ============================================================
# 6. QUANTITY DIFFERENCE ANALYSIS
# ============================================================

def quantity_difference_analysis(final):

    print("\n" + "=" * 70)
    print("QUANTITY DIFFERENCE ANALYSIS")
    print("=" * 70)

    sales_higher = final[
        final["quantity_difference"] > 0
    ]

    purchase_higher = final[
        final["quantity_difference"] < 0
    ]

    equal = final[
        final["quantity_difference"] == 0
    ]

    print(
        f"\nClassifications where "
        f"sales quantity > purchase quantity: "
        f"{len(sales_higher)}"
    )

    print(
        f"Classifications where "
        f"purchase quantity > sales quantity: "
        f"{len(purchase_higher)}"
    )

    print(
        f"Classifications with equal quantities: "
        f"{len(equal)}"
    )

    # --------------------------------------------------------
    # Largest positive difference
    # --------------------------------------------------------

    print("\nLargest positive quantity differences:")

    top_positive = (
        final
        .sort_values(
            "quantity_difference",
            ascending=False
        )
        .head(10)
    )

    for _, row in top_positive.iterrows():

        print(
            f"Classification {row['classification']} | "
            f"Difference: "
            f"{row['quantity_difference']:,.0f}"
        )

    # --------------------------------------------------------
    # Largest negative difference
    # --------------------------------------------------------

    print("\nLargest negative quantity differences:")

    top_negative = (
        final
        .sort_values(
            "quantity_difference",
            ascending=True
        )
        .head(10)
    )

    for _, row in top_negative.iterrows():

        print(
            f"Classification {row['classification']} | "
            f"Difference: "
            f"{row['quantity_difference']:,.0f}"
        )


# ============================================================
# 7. CONTRIBUTION COMPARISON
# ============================================================

def contribution_analysis(final):

    print("\n" + "=" * 70)
    print("SALES VS PURCHASE CONTRIBUTION")
    print("=" * 70)

    contribution = (
        final[
            [
                "classification",
                "sales_contribution_pct",
                "purchase_contribution_pct",
                "contribution_difference_pct"
            ]
        ]
        .sort_values(
            "contribution_difference_pct",
            ascending=False
        )
    )

    for _, row in contribution.iterrows():

        print(
            f"Classification {row['classification']} | "
            f"Sales: {row['sales_contribution_pct']:.2f}% | "
            f"Purchase: {row['purchase_contribution_pct']:.2f}% | "
            f"Difference: "
            f"{row['contribution_difference_pct']:+.2f} pp"
        )


# ============================================================
# 8. VERIFICATION
# ============================================================

def verify_results(final):

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    verification_query = """
        SELECT
            COUNT(*) AS total_rows,
            SUM(quantity) AS total_quantity,
            SUM(dollars) AS total_spending
        FROM purchases
        WHERE business_id = 1
    """

    sales_verification_query = """
        SELECT
            COUNT(*) AS total_rows,
            SUM(sales_quantity) AS total_quantity,
            SUM(sales_dollars) AS total_revenue
        FROM sales
        WHERE business_id = 1
    """

    with engine.connect() as connection:

        purchase_result = connection.exec_driver_sql(
            verification_query
        ).fetchone()

        sales_result = connection.exec_driver_sql(
            sales_verification_query
        ).fetchone()

    # --------------------------------------------------------
    # Expected values
    # --------------------------------------------------------

    expected_purchase_rows = purchase_result[0]
    expected_purchase_quantity = purchase_result[1]
    expected_purchase_spending = float(
        purchase_result[2]
    )

    expected_sales_rows = sales_result[0]
    expected_sales_quantity = sales_result[1]
    expected_sales_revenue = float(
        sales_result[2]
    )

    # --------------------------------------------------------
    # Actual values
    # --------------------------------------------------------

    actual_purchase_quantity = (
        final["purchase_quantity"].sum()
    )

    actual_purchase_spending = (
        final["purchase_spending"].sum()
    )

    actual_sales_quantity = (
        final["sales_quantity"].sum()
    )

    actual_sales_revenue = (
        final["sales_revenue"].sum()
    )

    # --------------------------------------------------------
    # Verify purchase quantity
    # --------------------------------------------------------

    purchase_quantity_passed = (
        actual_purchase_quantity
        == expected_purchase_quantity
    )

    print(
        "Purchase quantity verification: "
        f"{'PASSED' if purchase_quantity_passed else 'FAILED'}"
    )

    # --------------------------------------------------------
    # Verify purchase spending
    # --------------------------------------------------------

    purchase_spending_passed = (
        abs(
            actual_purchase_spending
            - expected_purchase_spending
        )
        < 0.01
    )

    print(
        "Purchase spending verification: "
        f"{'PASSED' if purchase_spending_passed else 'FAILED'}"
    )

    # --------------------------------------------------------
    # Verify sales quantity
    # --------------------------------------------------------

    sales_quantity_passed = (
        actual_sales_quantity
        == expected_sales_quantity
    )

    print(
        "Sales quantity verification: "
        f"{'PASSED' if sales_quantity_passed else 'FAILED'}"
    )

    # --------------------------------------------------------
    # Verify sales revenue
    # --------------------------------------------------------

    sales_revenue_passed = (
        abs(
            actual_sales_revenue
            - expected_sales_revenue
        )
        < 0.01
    )

    print(
        "Sales revenue verification: "
        f"{'PASSED' if sales_revenue_passed else 'FAILED'}"
    )

    # --------------------------------------------------------
    # Verify classifications
    # --------------------------------------------------------

    classification_count_passed = (
        len(final) == 2
    )

    print(
        "Classification count verification: "
        f"{'PASSED' if classification_count_passed else 'FAILED'}"
    )

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    if (
        purchase_quantity_passed
        and purchase_spending_passed
        and sales_quantity_passed
        and sales_revenue_passed
        and classification_count_passed
    ):

        print(
            "\n✓ ALL CLASSIFICATION SALES VS PURCHASE "
            "VERIFICATION CHECKS PASSED"
        )

    else:

        raise ValueError(
            "\n✗ CLASSIFICATION SALES VS PURCHASE "
            "VERIFICATION FAILED"
        )


# ============================================================
# 9. MAIN
# ============================================================

if __name__ == "__main__":

    sales = load_sales_by_classification()

    purchases = load_purchases_by_classification()

    final = combine_results(
        sales,
        purchases
    )

    display_summary(
        final
    )

    display_classification_details(
        final
    )

    quantity_difference_analysis(
        final
    )

    contribution_analysis(
        final
    )

    verify_results(
        final
    )

    print("\n" + "=" * 70)
    print(
        "CLASSIFICATION SALES VS PURCHASE "
        "ANALYSIS COMPLETED"
    )
    print("=" * 70)