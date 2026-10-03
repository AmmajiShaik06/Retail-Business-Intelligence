"""
Product Purchase Performance Analysis

Calculates:
- Purchase quantity
- Purchase spending
- Average purchase price
- Purchase contribution percentage

Data source:
purchases table

Business:
business_id = 1
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1


# ============================================================
# 1. LOAD PRODUCT PURCHASE DATA
# ============================================================

def load_product_purchases():

    print("\nLoading product purchase data...")

    query = """
        SELECT
            brand,
            description,
            size,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = %s
    """

    chunks = []

    for chunk in pd.read_sql(
        query,
        con=engine,
        params=(BUSINESS_ID,),
        chunksize=100_000
    ):

        grouped = (
            chunk
            .groupby(
                [
                    "brand",
                    "description",
                    "size"
                ],
                dropna=False
            )
            .agg(
                purchase_quantity=("quantity", "sum"),
                purchase_spending=("dollars", "sum")
            )
            .reset_index()
        )

        chunks.append(grouped)

    product_purchases = pd.concat(
        chunks,
        ignore_index=True
    )

    # --------------------------------------------------------
    # Combine chunk-level results
    # --------------------------------------------------------

    product_purchases = (
        product_purchases
        .groupby(
            [
                "brand",
                "description",
                "size"
            ],
            dropna=False
        )
        .agg(
            purchase_quantity=("purchase_quantity", "sum"),
            purchase_spending=("purchase_spending", "sum")
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Average purchase price
    # --------------------------------------------------------

    product_purchases["average_purchase_price"] = (
        product_purchases["purchase_spending"]
        / product_purchases["purchase_quantity"]
    )

    # --------------------------------------------------------
    # Purchase contribution
    # --------------------------------------------------------

    total_spending = (
        product_purchases["purchase_spending"].sum()
    )

    product_purchases["purchase_contribution_pct"] = (
        product_purchases["purchase_spending"]
        / total_spending
        * 100
    )

    print(
        f"Products represented in purchases: "
        f"{len(product_purchases):,}"
    )

    return product_purchases


# ============================================================
# 2. DISPLAY TOP PRODUCTS BY PURCHASE SPENDING
# ============================================================

def display_top_products(
    product_purchases
):

    print("\n" + "=" * 80)
    print("TOP PRODUCTS BY PURCHASE SPENDING")
    print("=" * 80)

    top_products = (
        product_purchases
        .sort_values(
            "purchase_spending",
            ascending=False
        )
        .head(20)
    )

    print(
        top_products[
            [
                "brand",
                "description",
                "size",
                "purchase_quantity",
                "purchase_spending",
                "average_purchase_price",
                "purchase_contribution_pct"
            ]
        ].to_string(
            index=False,
            formatters={
                "purchase_spending":
                    lambda x: f"${x:,.2f}",

                "average_purchase_price":
                    lambda x: f"${x:,.2f}",

                "purchase_contribution_pct":
                    lambda x: f"{x:.2f}%"
            }
        )
    )


# ============================================================
# 3. TOP PRODUCTS BY PURCHASE QUANTITY
# ============================================================

def display_top_quantity_products(
    product_purchases
):

    print("\n" + "=" * 80)
    print("TOP PRODUCTS BY PURCHASE QUANTITY")
    print("=" * 80)

    top_quantity = (
        product_purchases
        .sort_values(
            "purchase_quantity",
            ascending=False
        )
        .head(10)
    )

    print(
        top_quantity[
            [
                "brand",
                "description",
                "size",
                "purchase_quantity",
                "purchase_spending"
            ]
        ].to_string(
            index=False,
            formatters={
                "purchase_spending":
                    lambda x: f"${x:,.2f}"
            }
        )
    )


# ============================================================
# 4. PURCHASE SPENDING CONCENTRATION
# ============================================================

def calculate_concentration(
    product_purchases
):

    print("\n" + "=" * 80)
    print("PRODUCT PURCHASE CONCENTRATION")
    print("=" * 80)

    sorted_products = (
        product_purchases
        .sort_values(
            "purchase_spending",
            ascending=False
        )
        .reset_index(drop=True)
    )

    total_spending = (
        sorted_products["purchase_spending"].sum()
    )

    for n in [5, 10, 20, 50, 100]:

        if n <= len(sorted_products):

            spending = (
                sorted_products
                .head(n)["purchase_spending"]
                .sum()
            )

            contribution = (
                spending
                / total_spending
                * 100
            )

            print(
                f"Top {n} products: "
                f"${spending:,.2f} "
                f"({contribution:.2f}%)"
            )


# ============================================================
# 5. VERIFY RESULTS
# ============================================================

def verify_results(
    product_purchases
):

    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    # --------------------------------------------------------
    # Product count
    # --------------------------------------------------------

    product_count = len(product_purchases)

    print(
        f"Products represented in purchases: "
        f"{product_count:,}"
    )

    assert product_count > 0

    print(
        "✓ Product purchase records found"
    )

    # --------------------------------------------------------
    # Purchase quantity
    # --------------------------------------------------------

    total_quantity = (
        product_purchases["purchase_quantity"]
        .sum()
    )

    expected_quantity = 33_584_377

    assert (
        total_quantity
        == expected_quantity
    )

    print(
        "✓ Purchase quantity verified: "
        f"{total_quantity:,}"
    )

    # --------------------------------------------------------
    # Purchase spending
    # --------------------------------------------------------

    total_spending = (
        product_purchases["purchase_spending"]
        .sum()
    )

    expected_spending = 321_900_765.53

    assert abs(
        total_spending
        - expected_spending
    ) < 0.01

    print(
        "✓ Purchase spending verified: "
        f"${total_spending:,.2f}"
    )

    # --------------------------------------------------------
    # No negative quantities
    # --------------------------------------------------------

    assert (
        product_purchases["purchase_quantity"]
        >= 0
    ).all()

    print(
        "✓ No negative purchase quantities"
    )

    # --------------------------------------------------------
    # No negative spending
    # --------------------------------------------------------

    assert (
        product_purchases["purchase_spending"]
        >= 0
    ).all()

    print(
        "✓ No negative purchase spending"
    )

    # --------------------------------------------------------
    # Contribution percentage
    # --------------------------------------------------------

    contribution_total = (
        product_purchases[
            "purchase_contribution_pct"
        ].sum()
    )

    assert abs(
        contribution_total - 100
    ) < 0.01

    print(
        "✓ Purchase contribution = 100%"
    )

    print(
        "\n✓ ALL PRODUCT PURCHASE "
        "CHECKS PASSED"
    )


# ============================================================
# 6. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 80)
    print("PRODUCT PURCHASE PERFORMANCE")
    print("=" * 80)

    product_purchases = (
        load_product_purchases()
    )

    display_top_products(
        product_purchases
    )

    display_top_quantity_products(
        product_purchases
    )

    calculate_concentration(
        product_purchases
    )

    verify_results(
        product_purchases
    )

    print("\n" + "=" * 80)
    print("PRODUCT PURCHASE PERFORMANCE COMPLETED")
    print("=" * 80)