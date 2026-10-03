
"""
Master Product Missing-Key Diagnostic

Purpose:
Identify master product rows that cannot form a complete
normalized product key.

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

        number_text = value_lower[:-1].strip()

        try:
            liters = float(number_text)

            milliliters = round(
                liters * 1000
            )

            return f"{milliliters}ml"

        except ValueError:
            pass

    if value_lower.endswith("ml"):

        number_text = value_lower[:-2].strip()

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
# 3. LOAD PRODUCTS
# ============================================================

def load_products():

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

        return pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )


# ============================================================
# 4. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("MASTER PRODUCT MISSING-KEY DIAGNOSTIC")
    print("=" * 70)

    products = load_products()

    print(
        f"\nMaster product rows: "
        f"{len(products):,}"
    )

    # --------------------------------------------------------
    # Normalize fields
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
    # Find incomplete keys
    # --------------------------------------------------------

    missing_key_rows = products[
        products["product_key"].isna()
        | products["brand"].isna()
        | products["normalized_description"].isna()
        | products["normalized_size"].isna()
    ].copy()

    print(
        f"\nRows with incomplete product key: "
        f"{len(missing_key_rows):,}"
    )

    if missing_key_rows.empty:

        print(
            "\nNo incomplete product keys found."
        )

    else:

        print(
            "\nMaster rows with incomplete product identity:"
        )

        print(
            missing_key_rows[
                [
                    "brand",
                    "description",
                    "size",
                    "volume",
                    "classification",
                    "normalized_description",
                    "normalized_size"
                ]
            ].to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # Individual missing fields
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("MISSING FIELD COUNTS")
    print("-" * 70)

    print(
        f"Missing brand: "
        f"{products['brand'].isna().sum():,}"
    )

    print(
        f"Missing description: "
        f"{products['description'].isna().sum():,}"
    )

    print(
        f"Missing size: "
        f"{products['size'].isna().sum():,}"
    )

    print(
        f"Missing normalized description: "
        f"{products['normalized_description'].isna().sum():,}"
    )

    print(
        f"Missing normalized size: "
        f"{products['normalized_size'].isna().sum():,}"
    )

    print("\n" + "=" * 70)
    print(
        "MASTER PRODUCT MISSING-KEY DIAGNOSTIC COMPLETED"
    )
    print("=" * 70)
