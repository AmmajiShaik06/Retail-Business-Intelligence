
"""
Master Product Normalized-Key Collision Diagnostic

Purpose:
Find master product rows that become identical after
description and size normalization.

This script does NOT modify the database.
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

            liters = float(number_text)

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
# 3. LOAD MASTER PRODUCTS
# ============================================================

def load_master_products():

    query = """
        SELECT
            brand,
            description,
            size,
            volume,
            classification
        FROM products
        WHERE business_id = %s
    """

    with engine.connect() as connection:

        products = pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )

    return products


# ============================================================
# 4. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("MASTER PRODUCT NORMALIZED-KEY COLLISION DIAGNOSTIC")
    print("=" * 70)

    products = load_master_products()

    print(
        f"\nMaster product rows: "
        f"{len(products):,}"
    )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    products["normalized_description"] = (
        products["description"]
        .apply(normalize_description)
        .astype("string")
    )

    products["normalized_size"] = (
        products["size"]
        .apply(normalize_product_size)
        .astype("string")
    )

    products["product_key"] = (
        products["brand"].astype("string")
        + "|"
        + products["normalized_description"]
        + "|"
        + products["normalized_size"]
    )

    # --------------------------------------------------------
    # Find collisions
    # --------------------------------------------------------

    key_counts = (
        products
        .groupby("product_key", dropna=False)
        .size()
        .reset_index(name="row_count")
    )

    collisions = key_counts[
        key_counts["row_count"] > 1
    ]

    print(
        f"\nNormalized product keys: "
        f"{products['product_key'].nunique(dropna=True):,}"
    )

    print(
        f"Normalized keys with multiple "
        f"master rows: "
        f"{len(collisions):,}"
    )

    # --------------------------------------------------------
    # Display collisions
    # --------------------------------------------------------

    if collisions.empty:

        print(
            "\n✓ No normalized-key collisions found."
        )

    else:

        print(
            "\nWARNING: Normalized-key collisions found."
        )

        for product_key in collisions[
            "product_key"
        ]:

            print("\n" + "-" * 70)

            print(
                f"Product key: {product_key}"
            )

            matching_rows = products[
                products["product_key"] == product_key
            ]

            print(
                matching_rows[
                    [
                        "brand",
                        "description",
                        "size",
                        "volume",
                        "classification"
                    ]
                ].to_string(
                    index=False
                )
            )

    print("\n" + "=" * 70)
    print(
        "MASTER PRODUCT COLLISION DIAGNOSTIC COMPLETED"
    )
    print("=" * 70)
