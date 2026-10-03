"""
Product Sales Performance Analysis

Calculates:
- Sales quantity
- Sales revenue
- Average selling price
- Sales contribution percentage

Data source:
sales table

Business:
business_id = 1
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1


# ============================================================
# 1. LOAD PRODUCT SALES DATA
# ============================================================

def load_product_sales():

    print("\nLoading product sales data...")

    query = """
        SELECT
            brand,
            description,
            size,
            sales_quantity,
            sales_dollars
        FROM sales
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
                sales_quantity=("sales_quantity", "sum"),
                sales_revenue=("sales_dollars", "sum")
            )
            .reset_index()
        )

        chunks.append(grouped)

    product_sales = pd.concat(
        chunks,
        ignore_index=True
    )

    # --------------------------------------------------------
    # Combine chunk-level results
    # --------------------------------------------------------

    product_sales = (
        product_sales
        .groupby(
            [
                "brand",
                "description",
                "size"
            ],
            dropna=False
        )
        .agg(
            sales_quantity=("sales_quantity", "sum"),
            sales_revenue=("sales_revenue", "sum")
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Average selling price
    # --------------------------------------------------------

    product_sales["average_selling_price"] = (
        product_sales["sales_revenue"]
        / product_sales["sales_quantity"]
    )

    # --------------------------------------------------------
    # Sales contribution
    # --------------------------------------------------------

    total_revenue = (
        product_sales["sales_revenue"].sum()
    )

    product_sales["sales_contribution_pct"] = (
        product_sales["sales_revenue"]
        / total_revenue
        * 100
    )

    print(
        f"Products represented in sales: "
        f"{len(product_sales):,}"
    )

    return product_sales


# ============================================================
# 2. DISPLAY TOP PRODUCTS
# ============================================================

def display_top_products(
    product_sales
):

    print("\n" + "=" * 80)
    print("TOP PRODUCTS BY SALES REVENUE")
    print("=" * 80)

    top_products = (
        product_sales
        .sort_values(
            "sales_revenue",
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
                "sales_quantity",
                "sales_revenue",
                "average_selling_price",
                "sales_contribution_pct"
            ]
        ].to_string(
            index=False,
            formatters={
                "sales_revenue":
                    lambda x: f"${x:,.2f}",

                "average_selling_price":
                    lambda x: f"${x:,.2f}",

                "sales_contribution_pct":
                    lambda x: f"{x:.2f}%"
            }
        )
    )


# ============================================================
# 3. TOP PRODUCTS BY QUANTITY
# ============================================================

def display_top_quantity_products(
    product_sales
):

    print("\n" + "=" * 80)
    print("TOP PRODUCTS BY SALES QUANTITY")
    print("=" * 80)

    top_quantity = (
        product_sales
        .sort_values(
            "sales_quantity",
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
                "sales_quantity",
                "sales_revenue"
            ]
        ].to_string(
            index=False,
            formatters={
                "sales_revenue":
                    lambda x: f"${x:,.2f}"
            }
        )
    )


# ============================================================
# 4. SALES CONCENTRATION
# ============================================================

def calculate_concentration(
    product_sales
):

    print("\n" + "=" * 80)
    print("PRODUCT SALES CONCENTRATION")
    print("=" * 80)

    sorted_products = (
        product_sales
        .sort_values(
            "sales_revenue",
            ascending=False
        )
        .reset_index(drop=True)
    )

    total_revenue = (
        sorted_products["sales_revenue"].sum()
    )

    for n in [5, 10, 20, 50, 100]:

        if n <= len(sorted_products):

            revenue = (
                sorted_products
                .head(n)["sales_revenue"]
                .sum()
            )

            contribution = (
                revenue
                / total_revenue
                * 100
            )

            print(
                f"Top {n} products: "
                f"${revenue:,.2f} "
                f"({contribution:.2f}%)"
            )


# ============================================================
# 5. VERIFY RESULTS
# ============================================================

def verify_results(
    product_sales
):

    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    # --------------------------------------------------------
    # Product count
    # --------------------------------------------------------

    product_count = len(product_sales)

    print(
        f"Products represented in sales: "
        f"{product_count:,}"
    )

    assert product_count > 0

    print(
        "✓ Product sales records found"
    )

    # --------------------------------------------------------
    # Sales quantity
    # --------------------------------------------------------

    total_quantity = (
        product_sales["sales_quantity"]
        .sum()
    )

    expected_quantity = 32_917_876

    assert (
        total_quantity
        == expected_quantity
    )

    print(
        "✓ Sales quantity verified: "
        f"{total_quantity:,}"
    )

    # --------------------------------------------------------
    # Sales revenue
    # --------------------------------------------------------

    total_revenue = (
        product_sales["sales_revenue"]
        .sum()
    )

    expected_revenue = 452_062_952.02

    assert abs(
        total_revenue
        - expected_revenue
    ) < 0.01

    print(
        "✓ Sales revenue verified: "
        f"${total_revenue:,.2f}"
    )

    # --------------------------------------------------------
    # No negative quantities
    # --------------------------------------------------------

    assert (
        product_sales["sales_quantity"]
        >= 0
    ).all()

    print(
        "✓ No negative sales quantities"
    )

    # --------------------------------------------------------
    # No negative revenue
    # --------------------------------------------------------

    assert (
        product_sales["sales_revenue"]
        >= 0
    ).all()

    print(
        "✓ No negative sales revenue"
    )

    # --------------------------------------------------------
    # Contribution percentage
    # --------------------------------------------------------

    contribution_total = (
        product_sales[
            "sales_contribution_pct"
        ].sum()
    )

    assert abs(
        contribution_total - 100
    ) < 0.01

    print(
        "✓ Sales contribution = 100%"
    )

    print(
        "\n✓ ALL PRODUCT SALES "
        "CHECKS PASSED"
    )


# ============================================================
# 6. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 80)
    print("PRODUCT SALES PERFORMANCE")
    print("=" * 80)

    product_sales = load_product_sales()

    display_top_products(
        product_sales
    )

    display_top_quantity_products(
        product_sales
    )

    calculate_concentration(
        product_sales
    )

    verify_results(
        product_sales
    )

    print("\n" + "=" * 80)
    print("PRODUCT SALES PERFORMANCE COMPLETED")
    print("=" * 80)