"""
Product Union Diagnostic

Purpose:
Determine the complete set of product identities appearing in:

1. Master products
2. Sales
3. Purchases
4. Beginning inventory
5. Ending inventory

This diagnostic does not modify the database.

It determines the correct product population for
product intelligence.
"""

import re

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1


# ============================================================
# 1. NORMALIZE SIZE
# ============================================================

def normalize_product_size(value):

    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if not value:
        return pd.NA

    value_lower = value.lower()

    if value_lower in {
        "liter",
        "liters",
        "litre",
        "litres"
    }:
        return "1000ml"

    if value_lower.endswith("l"):

        number_text = (
            value_lower[:-1]
            .strip()
        )

        try:

            liters = float(
                number_text
            )

            milliliters = round(
                liters * 1000
            )

            return f"{milliliters}ml"

        except ValueError:
            pass

    if value_lower.endswith("ml"):

        number_text = (
            value_lower[:-2]
            .strip()
        )

        try:

            milliliters = round(
                float(number_text)
            )

            return f"{milliliters}ml"

        except ValueError:
            pass

    return value_lower


# ============================================================
# 2. NORMALIZE DESCRIPTION
# ============================================================

def normalize_description(value):

    if pd.isna(value):
        return pd.NA

    value = str(value).lower()

    value = (
        value
        .replace("’", "'")
        .replace("`", "'")
        .replace("´", "'")
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ============================================================
# 3. PREPARE DATAFRAME
# ============================================================

def prepare_product_dataframe(df):

    df = df.copy()

    df["brand"] = pd.to_numeric(
        df["brand"],
        errors="coerce"
    )

    df["description"] = (
        df["description"]
        .astype("string")
        .str.strip()
    )

    df["size"] = (
        df["size"]
        .astype("string")
        .str.strip()
    )

    df["normalized_description"] = (
        df["description"]
        .apply(
            normalize_description
        )
        .astype("string")
    )

    df["normalized_size"] = (
        df["size"]
        .apply(
            normalize_product_size
        )
        .astype("string")
    )

    df["product_key"] = (
        df["brand"].astype("string")
        + "|"
        + df["normalized_description"]
        + "|"
        + df["normalized_size"]
    )

    return df


# ============================================================
# 4. LOAD SOURCE
# ============================================================

def load_products(
    table_name
):

    query = f"""
        SELECT DISTINCT
            brand,
            description,
            size
        FROM {table_name}
        WHERE business_id = %s
    """

    with engine.connect() as connection:

        df = pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )

    return prepare_product_dataframe(
        df
    )


# ============================================================
# 5. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PRODUCT UNION DIAGNOSTIC")
    print("=" * 70)

    tables = [
        "products",
        "sales",
        "purchases",
        "begin_inventory",
        "end_inventory"
    ]

    all_keys = {}

    for table in tables:

        print(
            f"\nLoading {table}..."
        )

        df = load_products(
            table
        )

        keys = set(
            df["product_key"]
            .dropna()
        )

        all_keys[table] = keys

        print(
            f"{table} unique normalized keys: "
            f"{len(keys):,}"
        )

    # --------------------------------------------------------
    # Individual comparisons
    # --------------------------------------------------------

    master_keys = all_keys["products"]
    sales_keys = all_keys["sales"]
    purchase_keys = all_keys["purchases"]
    begin_keys = all_keys["begin_inventory"]
    end_keys = all_keys["end_inventory"]

    # --------------------------------------------------------
    # Complete UNION
    # --------------------------------------------------------

    union_keys = (
        master_keys
        | sales_keys
        | purchase_keys
        | begin_keys
        | end_keys
    )

    print("\n" + "=" * 70)
    print("COMPLETE PRODUCT UNION")
    print("=" * 70)

    print(
        f"\nMaster products: "
        f"{len(master_keys):,}"
    )

    print(
        f"Sales products: "
        f"{len(sales_keys):,}"
    )

    print(
        f"Purchase products: "
        f"{len(purchase_keys):,}"
    )

    print(
        f"Beginning inventory products: "
        f"{len(begin_keys):,}"
    )

    print(
        f"Ending inventory products: "
        f"{len(end_keys):,}"
    )

    print(
        "\nCOMPLETE UNIQUE PRODUCT KEYS:"
    )

    print(
        f"{len(union_keys):,}"
    )

    # --------------------------------------------------------
    # Source-only relative to master
    # --------------------------------------------------------

    sales_only = (
        sales_keys
        - master_keys
    )

    purchase_only = (
        purchase_keys
        - master_keys
    )

    begin_only = (
        begin_keys
        - master_keys
    )

    end_only = (
        end_keys
        - master_keys
    )

    print("\n" + "-" * 70)
    print("SOURCE-ONLY PRODUCT KEYS")
    print("-" * 70)

    print(
        f"Sales only: "
        f"{len(sales_only):,}"
    )

    print(
        f"Purchase only: "
        f"{len(purchase_only):,}"
    )

    print(
        f"Beginning inventory only: "
        f"{len(begin_only):,}"
    )

    print(
        f"Ending inventory only: "
        f"{len(end_only):,}"
    )

    # --------------------------------------------------------
    # Keys appearing in multiple sources
    # --------------------------------------------------------

    source_sets = [
        sales_keys,
        purchase_keys,
        begin_keys,
        end_keys
    ]

    transaction_union = set().union(
        *source_sets
    )

    print("\n" + "-" * 70)
    print("TRANSACTION PRODUCT POPULATION")
    print("-" * 70)

    print(
        f"Unique product keys appearing "
        f"in any transaction/inventory source: "
        f"{len(transaction_union):,}"
    )

    print(
        f"Transaction/inventory products "
        f"not present in master: "
        f"{len(transaction_union - master_keys):,}"
    )

    print("\n" + "=" * 70)
    print(
        "PRODUCT UNION DIAGNOSTIC COMPLETED"
    )
    print("=" * 70)