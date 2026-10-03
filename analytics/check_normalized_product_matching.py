"""
Normalized Product Matching Diagnostic

Purpose:
Identify product matching differences after size normalization.

This diagnostic compares product identities from:

1. Master products
2. Sales
3. Purchases
4. Beginning inventory
5. Ending inventory

It does NOT modify any database table.

It helps identify whether remaining mismatches are caused by:

- description formatting
- capitalization
- punctuation
- spacing
- size representation
- other product identity differences
"""

import re

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1


# ============================================================
# 1. SIZE NORMALIZATION
# ============================================================

def normalize_product_size(value):

    if pd.isna(value):
        return pd.NA

    value = str(value).strip()

    if not value:
        return pd.NA

    value_lower = value.lower()

    # Text representation
    if value_lower in {
        "liter",
        "liters",
        "litre",
        "litres"
    }:
        return "1000ml"

    # L representation
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

    # mL representation
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
# 2. DESCRIPTION NORMALIZATION
# ============================================================

def normalize_description(value):

    if pd.isna(value):

        return pd.NA

    value = str(value)

    # Convert to lowercase
    value = value.lower()

    # Normalize common apostrophes
    value = (
        value
        .replace("’", "'")
        .replace("`", "'")
        .replace("´", "'")
    )

    # Replace punctuation with spaces
    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    # Remove repeated spaces
    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ============================================================
# 3. CREATE PRODUCT KEY
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
# 4. LOAD MASTER PRODUCTS
# ============================================================

def load_master_products():

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

    return prepare_product_dataframe(
        products
    )


# ============================================================
# 5. LOAD DISTINCT SALES PRODUCTS
# ============================================================

def load_sales_products():

    query = """
        SELECT DISTINCT
            brand,
            description,
            size
        FROM sales
        WHERE business_id = %s
    """

    with engine.connect() as connection:

        products = pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )

    return prepare_product_dataframe(
        products
    )


# ============================================================
# 6. LOAD DISTINCT PURCHASE PRODUCTS
# ============================================================

def load_purchase_products():

    query = """
        SELECT DISTINCT
            brand,
            description,
            size
        FROM purchases
        WHERE business_id = %s
    """

    with engine.connect() as connection:

        products = pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )

    return prepare_product_dataframe(
        products
    )


# ============================================================
# 7. LOAD DISTINCT INVENTORY PRODUCTS
# ============================================================

def load_inventory_products(
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

        products = pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )

    return prepare_product_dataframe(
        products
    )


# ============================================================
# 8. COMPARE PRODUCT KEYS
# ============================================================

def compare_products(
    master,
    source,
    source_name
):

    print("\n" + "=" * 70)

    print(
        f"{source_name.upper()} PRODUCT MATCHING"
    )

    print("=" * 70)

    master_keys = set(
        master["product_key"]
        .dropna()
    )

    source_keys = set(
        source["product_key"]
        .dropna()
    )

    matched_keys = (
        master_keys
        & source_keys
    )

    source_only_keys = (
        source_keys
        - master_keys
    )

    master_only_keys = (
        master_keys
        - source_keys
    )

    print(
        f"\nMaster product keys: "
        f"{len(master_keys):,}"
    )

    print(
        f"{source_name} product keys: "
        f"{len(source_keys):,}"
    )

    print(
        f"Matched product keys: "
        f"{len(matched_keys):,}"
    )

    print(
        f"{source_name}-only product keys: "
        f"{len(source_only_keys):,}"
    )

    print(
        f"Master-only product keys: "
        f"{len(master_only_keys):,}"
    )

    # --------------------------------------------------------
    # Source-only products
    # --------------------------------------------------------

    source_only = source[
        source["product_key"].isin(
            source_only_keys
        )
    ].copy()

    print(
        f"\nFIRST 50 {source_name.upper()}-ONLY PRODUCTS"
    )

    print("-" * 70)

    if source_only.empty:

        print(
            "No unmatched products."
        )

    else:

        print(
            source_only[
                [
                    "brand",
                    "description",
                    "size",
                    "normalized_description",
                    "normalized_size"
                ]
            ]
            .head(50)
            .to_string(
                index=False
            )
        )

    return source_only


# ============================================================
# 9. CHECK DESCRIPTION-ONLY MATCHES
# ============================================================

def check_description_matching(
    master,
    source,
    source_only,
    source_name
):

    print("\n" + "=" * 70)

    print(
        f"{source_name.upper()} DESCRIPTION MATCHING ANALYSIS"
    )

    print("=" * 70)

    if source_only.empty:

        print(
            "No unmatched products to analyze."
        )

        return

    # --------------------------------------------------------
    # Compare by:
    #
    # brand + normalized_size
    #
    # while ignoring description.
    #
    # This helps determine whether the description
    # is the remaining mismatch.
    # --------------------------------------------------------

    master_groups = {}

    for row in master.itertuples(
        index=False
    ):

        key = (
            row.brand,
            row.normalized_size
        )

        if key not in master_groups:

            master_groups[key] = []

        master_groups[key].append(
            {
                "description":
                    row.description,

                "normalized_description":
                    row.normalized_description,

                "size":
                    row.size
            }
        )

    found_candidates = []

    for row in source_only.itertuples(
        index=False
    ):

        key = (
            row.brand,
            row.normalized_size
        )

        candidates = master_groups.get(
            key,
            []
        )

        if candidates:

            for candidate in candidates[:5]:

                found_candidates.append(
                    {
                        "brand":
                            row.brand,

                        "source_description":
                            row.description,

                        "source_size":
                            row.size,

                        "master_description":
                            candidate[
                                "description"
                            ],

                        "master_size":
                            candidate[
                                "size"
                            ],

                        "source_normalized_description":
                            row.normalized_description,

                        "master_normalized_description":
                            candidate[
                                "normalized_description"
                            ]
                    }
                )

    candidates_df = pd.DataFrame(
        found_candidates
    )

    print(
        f"\nUnmatched {source_name} products "
        f"with same brand + normalized size "
        f"as a master product: "
        f"{len(candidates_df):,}"
    )

    if not candidates_df.empty:

        print(
            "\nFIRST 100 POTENTIAL DESCRIPTION MATCHES"
        )

        print("-" * 70)

        print(
            candidates_df
            .head(100)
            .to_string(
                index=False
            )
        )

    else:

        print(
            "\nNo candidates found using "
            "brand + normalized size."
        )


# ============================================================
# 10. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("NORMALIZED PRODUCT MATCHING DIAGNOSTIC")
    print("=" * 70)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    print(
        "\nLoading master products..."
    )

    master = load_master_products()

    print(
        f"Master rows: "
        f"{len(master):,}"
    )

    print(
        "\nLoading distinct sales products..."
    )

    sales = load_sales_products()

    print(
        f"Distinct sales products: "
        f"{len(sales):,}"
    )

    print(
        "\nLoading distinct purchase products..."
    )

    purchases = load_purchase_products()

    print(
        f"Distinct purchase products: "
        f"{len(purchases):,}"
    )

    print(
        "\nLoading beginning inventory products..."
    )

    begin_inventory = load_inventory_products(
        "begin_inventory"
    )

    print(
        f"Beginning inventory products: "
        f"{len(begin_inventory):,}"
    )

    print(
        "\nLoading ending inventory products..."
    )

    end_inventory = load_inventory_products(
        "end_inventory"
    )

    print(
        f"Ending inventory products: "
        f"{len(end_inventory):,}"
    )

    # --------------------------------------------------------
    # Sales
    # --------------------------------------------------------

    sales_only = compare_products(
        master,
        sales,
        "sales"
    )

    check_description_matching(
        master,
        sales,
        sales_only,
        "sales"
    )

    # --------------------------------------------------------
    # Purchases
    # --------------------------------------------------------

    purchase_only = compare_products(
        master,
        purchases,
        "purchase"
    )

    check_description_matching(
        master,
        purchases,
        purchase_only,
        "purchase"
    )

    # --------------------------------------------------------
    # Beginning inventory
    # --------------------------------------------------------

    begin_only = compare_products(
        master,
        begin_inventory,
        "begin inventory"
    )

    check_description_matching(
        master,
        begin_inventory,
        begin_only,
        "begin inventory"
    )

    # --------------------------------------------------------
    # Ending inventory
    # --------------------------------------------------------

    end_only = compare_products(
        master,
        end_inventory,
        "end inventory"
    )

    check_description_matching(
        master,
        end_inventory,
        end_only,
        "end inventory"
    )

    # --------------------------------------------------------
    # Completion
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    print(
        "NORMALIZED PRODUCT MATCHING "
        "DIAGNOSTIC COMPLETED"
    )

    print("=" * 70)