"""
Diagnose product identity matching between:

1. products
2. sales
3. purchases

Product identity:

    brand + description + size

This script does NOT modify the database.
It only identifies unmatched product combinations.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1


# ============================================================
# 1. LOAD MASTER PRODUCTS
# ============================================================

def load_master_products():

    print("\n" + "=" * 70)
    print("LOADING MASTER PRODUCTS")
    print("=" * 70)

    query = """
        SELECT
            brand,
            description,
            size
        FROM products
        WHERE business_id = %s
    """

    with engine.connect() as connection:

        products = pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )

    print(
        f"Master product rows: "
        f"{len(products):,}"
    )

    return products


# ============================================================
# 2. LOAD SALES PRODUCT IDENTITIES
# ============================================================

def load_sales_products():

    print("\n" + "=" * 70)
    print("LOADING SALES PRODUCT IDENTITIES")
    print("=" * 70)

    query = """
        SELECT DISTINCT
            brand,
            description,
            size
        FROM sales
        WHERE business_id = %s
    """

    with engine.connect() as connection:

        sales = pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )

    print(
        f"Distinct sales product combinations: "
        f"{len(sales):,}"
    )

    return sales


# ============================================================
# 3. LOAD PURCHASE PRODUCT IDENTITIES
# ============================================================

def load_purchase_products():

    print("\n" + "=" * 70)
    print("LOADING PURCHASE PRODUCT IDENTITIES")
    print("=" * 70)

    query = """
        SELECT DISTINCT
            brand,
            description,
            size
        FROM purchases
        WHERE business_id = %s
    """

    with engine.connect() as connection:

        purchases = pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )

    print(
        f"Distinct purchase product combinations: "
        f"{len(purchases):,}"
    )

    return purchases


# ============================================================
# 4. NORMALIZE PRODUCT KEYS
# ============================================================

def normalize_product_keys(df):

    df = df.copy()

    # --------------------------------------------------------
    # Brand
    # --------------------------------------------------------

    df["brand"] = pd.to_numeric(
        df["brand"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Text columns
    # --------------------------------------------------------

    for column in [
        "description",
        "size"
    ]:

        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    return df


# ============================================================
# 5. CHECK MASTER vs SALES
# ============================================================

def check_master_vs_sales(
    products,
    sales
):

    print("\n" + "=" * 70)
    print("CHECKING MASTER PRODUCTS vs SALES")
    print("=" * 70)

    products = normalize_product_keys(
        products
    )

    sales = normalize_product_keys(
        sales
    )

    # --------------------------------------------------------
    # Create product keys
    # --------------------------------------------------------

    products["product_key"] = (
        products["brand"].astype("string")
        + "|"
        + products["description"].fillna("<NULL>")
        + "|"
        + products["size"].fillna("<NULL>")
    )

    sales["product_key"] = (
        sales["brand"].astype("string")
        + "|"
        + sales["description"].fillna("<NULL>")
        + "|"
        + sales["size"].fillna("<NULL>")
    )

    master_keys = set(
        products["product_key"]
    )

    sales_keys = set(
        sales["product_key"]
    )

    matched = (
        master_keys
        & sales_keys
    )

    sales_only = (
        sales_keys
        - master_keys
    )

    master_only = (
        master_keys
        - sales_keys
    )

    print(
        f"\nMaster product keys: "
        f"{len(master_keys):,}"
    )

    print(
        f"Sales product keys: "
        f"{len(sales_keys):,}"
    )

    print(
        f"Matched product keys: "
        f"{len(matched):,}"
    )

    print(
        f"Sales-only product keys: "
        f"{len(sales_only):,}"
    )

    print(
        f"Master-only product keys: "
        f"{len(master_only):,}"
    )

    # --------------------------------------------------------
    # Show sales-only examples
    # --------------------------------------------------------

    if sales_only:

        print(
            "\n" + "-" * 70
        )

        print(
            "FIRST 30 SALES-ONLY PRODUCTS"
        )

        print(
            "-" * 70
        )

        sales_only_df = sales[
            sales["product_key"].isin(
                sales_only
            )
        ].copy()

        print(
            sales_only_df[
                [
                    "brand",
                    "description",
                    "size"
                ]
            ]
            .drop_duplicates()
            .head(30)
            .to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # Show master-only examples
    # --------------------------------------------------------

    if master_only:

        print(
            "\n" + "-" * 70
        )

        print(
            "FIRST 30 MASTER-ONLY PRODUCTS"
        )

        print(
            "-" * 70
        )

        master_only_df = products[
            products["product_key"].isin(
                master_only
            )
        ].copy()

        print(
            master_only_df[
                [
                    "brand",
                    "description",
                    "size"
                ]
            ]
            .drop_duplicates()
            .head(30)
            .to_string(
                index=False
            )
        )


# ============================================================
# 6. CHECK MASTER vs PURCHASES
# ============================================================

def check_master_vs_purchases(
    products,
    purchases
):

    print("\n" + "=" * 70)
    print("CHECKING MASTER PRODUCTS vs PURCHASES")
    print("=" * 70)

    products = normalize_product_keys(
        products
    )

    purchases = normalize_product_keys(
        purchases
    )

    # --------------------------------------------------------
    # Create keys
    # --------------------------------------------------------

    products["product_key"] = (
        products["brand"].astype("string")
        + "|"
        + products["description"].fillna("<NULL>")
        + "|"
        + products["size"].fillna("<NULL>")
    )

    purchases["product_key"] = (
        purchases["brand"].astype("string")
        + "|"
        + purchases["description"].fillna("<NULL>")
        + "|"
        + purchases["size"].fillna("<NULL>")
    )

    master_keys = set(
        products["product_key"]
    )

    purchase_keys = set(
        purchases["product_key"]
    )

    matched = (
        master_keys
        & purchase_keys
    )

    purchase_only = (
        purchase_keys
        - master_keys
    )

    master_only = (
        master_keys
        - purchase_keys
    )

    print(
        f"\nMaster product keys: "
        f"{len(master_keys):,}"
    )

    print(
        f"Purchase product keys: "
        f"{len(purchase_keys):,}"
    )

    print(
        f"Matched product keys: "
        f"{len(matched):,}"
    )

    print(
        f"Purchase-only product keys: "
        f"{len(purchase_only):,}"
    )

    print(
        f"Master-only product keys: "
        f"{len(master_only):,}"
    )

    # --------------------------------------------------------
    # Show purchase-only examples
    # --------------------------------------------------------

    if purchase_only:

        print(
            "\n" + "-" * 70
        )

        print(
            "FIRST 30 PURCHASE-ONLY PRODUCTS"
        )

        print(
            "-" * 70
        )

        purchase_only_df = purchases[
            purchases["product_key"].isin(
                purchase_only
            )
        ].copy()

        print(
            purchase_only_df[
                [
                    "brand",
                    "description",
                    "size"
                ]
            ]
            .drop_duplicates()
            .head(30)
            .to_string(
                index=False
            )
        )


# ============================================================
# 7. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PRODUCT MATCHING DIAGNOSTIC")
    print("=" * 70)

    products = load_master_products()

    sales = load_sales_products()

    purchases = load_purchase_products()

    check_master_vs_sales(
        products,
        sales
    )

    check_master_vs_purchases(
        products,
        purchases
    )

    print("\n" + "=" * 70)
    print("PRODUCT MATCHING DIAGNOSTIC COMPLETED")
    print("=" * 70)