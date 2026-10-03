
"""
Product Intelligence

Purpose:
Build complete product-level intelligence using product identities
appearing across:

1. Master products
2. Sales
3. Purchases
4. Beginning inventory
5. Ending inventory

Important design decisions:

- Product identity uses:
      brand + normalized description + normalized size

- Size formats are normalized:
      1.75L  -> 1750ml
      1.5L   -> 1500ml
      Liter  -> 1000ml

- Description formatting is normalized only for matching.

- Missing identity fields are represented internally using
  explicit placeholders.

- Source-only products are NOT discarded.

- No fuzzy matching is used.

- Inventory uses the column `price`, not `purchase_price`.

- Sales and purchases are read using database-level keyset
  pagination to avoid MySQL connection problems.

The output is:

data/processed/product_intelligence.csv
"""

import re

import numpy as np
import pandas as pd

from database.connection import engine


BUSINESS_ID = 1

CHUNK_SIZE = 250_000

OUTPUT_FILE = (
    "data/processed/product_intelligence.csv"
)


# ============================================================
# 1. NORMALIZE SIZE
# ============================================================

def normalize_product_size(value):

    if pd.isna(value):

        return "__MISSING_SIZE__"

    value = str(value).strip()

    if not value:

        return "__MISSING_SIZE__"

    value_lower = value.lower()

    # --------------------------------------------------------
    # Liter
    # --------------------------------------------------------

    if value_lower in {
        "liter",
        "liters",
        "litre",
        "litres"
    }:

        return "1000ml"

    # --------------------------------------------------------
    # Liter formats
    #
    # Examples:
    # 1L
    # 1.5L
    # 1.75L
    # 3L
    # 5L
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Milliliter formats
    #
    # Examples:
    # 750mL
    # 1000mL
    # 1750mL
    # --------------------------------------------------------

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

        return "__MISSING_DESCRIPTION__"

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

    value = value.strip()

    if not value:

        return "__MISSING_DESCRIPTION__"

    return value


# ============================================================
# 3. CREATE PRODUCT KEY
# ============================================================

def create_product_key(
    brand,
    description,
    size
):

    if pd.isna(brand):

        brand_key = "__MISSING_BRAND__"

    else:

        brand_key = str(
            int(brand)
        )

    description_key = (
        normalize_description(
            description
        )
    )

    size_key = (
        normalize_product_size(
            size
        )
    )

    return (
        brand_key
        + "|"
        + description_key
        + "|"
        + size_key
    )


# ============================================================
# 4. PREPARE PRODUCT DATAFRAME
# ============================================================

def prepare_product_dataframe(df):

    df = df.copy()

    df["brand"] = pd.to_numeric(
        df["brand"],
        errors="coerce"
    )

    df["product_key"] = [
        create_product_key(
            brand,
            description,
            size
        )
        for brand, description, size
        in zip(
            df["brand"],
            df["description"],
            df["size"]
        )
    ]

    return df


# ============================================================
# 5. READ LARGE TABLE USING KEYSET PAGINATION
# ============================================================

def read_table_in_batches(
    connection,
    base_query,
    id_column,
    business_id
):

    last_id = 0

    while True:

        query = f"""
            {base_query}
              AND {id_column} > %s
            ORDER BY {id_column}
            LIMIT %s
        """

        chunk = pd.read_sql_query(
            query,
            connection,
            params=(
                business_id,
                last_id,
                CHUNK_SIZE
            )
        )

        if chunk.empty:

            break

        yield chunk

        last_id = int(
            chunk[id_column].max()
        )


# ============================================================
# 6. LOAD SALES
# ============================================================

def load_product_sales():

    print(
        "\nLoading product sales..."
    )

    query = """
        SELECT
            sales_id,
            brand,
            description,
            size,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = %s
    """

    sales_summary = []

    total_rows = 0

    with engine.connect() as connection:

        for chunk in read_table_in_batches(
            connection,
            query,
            "sales_id",
            BUSINESS_ID
        ):

            total_rows += len(chunk)

            chunk = prepare_product_dataframe(
                chunk
            )

            grouped = (
                chunk
                .groupby(
                    "product_key",
                    as_index=False
                )
                .agg(
                    sales_quantity=(
                        "sales_quantity",
                        "sum"
                    ),
                    sales_revenue=(
                        "sales_dollars",
                        "sum"
                    )
                )
            )

            sales_summary.append(
                grouped
            )

    if not sales_summary:

        return pd.DataFrame(
            columns=[
                "product_key",
                "sales_quantity",
                "sales_revenue"
            ]
        )

    result = (
        pd.concat(
            sales_summary,
            ignore_index=True
        )
        .groupby(
            "product_key",
            as_index=False
        )
        .agg(
            sales_quantity=(
                "sales_quantity",
                "sum"
            ),
            sales_revenue=(
                "sales_revenue",
                "sum"
            )
        )
    )

    print(
        f"Sales rows processed: "
        f"{total_rows:,}"
    )

    return result


# ============================================================
# 7. LOAD PURCHASES
# ============================================================

def load_product_purchases():

    print(
        "\nLoading product purchases..."
    )

    query = """
        SELECT
            purchase_id,
            brand,
            description,
            size,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = %s
    """

    purchase_summary = []

    total_rows = 0

    with engine.connect() as connection:

        for chunk in read_table_in_batches(
            connection,
            query,
            "purchase_id",
            BUSINESS_ID
        ):

            total_rows += len(chunk)

            chunk = prepare_product_dataframe(
                chunk
            )

            grouped = (
                chunk
                .groupby(
                    "product_key",
                    as_index=False
                )
                .agg(
                    purchase_quantity=(
                        "quantity",
                        "sum"
                    ),
                    purchase_spending=(
                        "dollars",
                        "sum"
                    )
                )
            )

            purchase_summary.append(
                grouped
            )

    if not purchase_summary:

        return pd.DataFrame(
            columns=[
                "product_key",
                "purchase_quantity",
                "purchase_spending"
            ]
        )

    result = (
        pd.concat(
            purchase_summary,
            ignore_index=True
        )
        .groupby(
            "product_key",
            as_index=False
        )
        .agg(
            purchase_quantity=(
                "purchase_quantity",
                "sum"
            ),
            purchase_spending=(
                "purchase_spending",
                "sum"
            )
        )
    )

    print(
        f"Purchase rows processed: "
        f"{total_rows:,}"
    )

    return result


# ============================================================
# 8. LOAD INVENTORY
# ============================================================

def load_inventory(
    table_name
):

    query = f"""
        SELECT
            brand,
            description,
            size,
            on_hand,
            price
        FROM {table_name}
        WHERE business_id = %s
    """

    with engine.connect() as connection:

        inventory = pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )

    inventory = prepare_product_dataframe(
        inventory
    )

    inventory["inventory_value"] = (
        inventory["on_hand"]
        * inventory["price"]
    )

    result = (
        inventory
        .groupby(
            "product_key",
            as_index=False
        )
        .agg(
            quantity=(
                "on_hand",
                "sum"
            ),
            inventory_value=(
                "inventory_value",
                "sum"
            )
        )
    )

    return result


# ============================================================
# 9. LOAD MASTER PRODUCTS
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

        master = pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )

    master = prepare_product_dataframe(
        master
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # Master has one incomplete row:
    #
    # Brand = 4202
    # Description = NULL
    # Size = NULL
    #
    # We preserve it using the explicit missing-value key.
    # --------------------------------------------------------

    # No rows are dropped here.

    # --------------------------------------------------------
    # If multiple physical master rows somehow map to the same
    # product key, retain the first record.
    #
    # Our diagnostics showed no normalized collisions.
    # --------------------------------------------------------

    master = (
        master
        .drop_duplicates(
            subset=["product_key"],
            keep="first"
        )
    )

    return master[
        [
            "product_key",
            "brand",
            "description",
            "size",
            "volume",
            "classification"
        ]
    ]


# ============================================================
# 10. BUILD COMPLETE PRODUCT UNION
# ============================================================

def build_product_union(
    master,
    sales,
    purchases,
    begin_inventory,
    end_inventory
):

    # --------------------------------------------------------
    # Collect every product identity
    # --------------------------------------------------------

    product_keys = pd.DataFrame(
        {
            "product_key": pd.unique(
                pd.concat(
                    [
                        master["product_key"],
                        sales["product_key"],
                        purchases["product_key"],
                        begin_inventory["product_key"],
                        end_inventory["product_key"]
                    ],
                    ignore_index=True
                )
            )
        }
    )

    print(
        f"\nComplete product identities: "
        f"{len(product_keys):,}"
    )

    # --------------------------------------------------------
    # Attach master attributes
    # --------------------------------------------------------

    result = product_keys.merge(
        master,
        on="product_key",
        how="left"
    )

    # --------------------------------------------------------
    # Attach source attributes for products that do not exist
    # in the master table.
    #
    # Sales are used first because they contain volume and
    # classification.
    # --------------------------------------------------------

    sales_attribute_query = """
        SELECT
            brand,
            description,
            size,
            volume,
            classification
        FROM sales
        WHERE business_id = %s
          AND brand IS NOT NULL
    """

    with engine.connect() as connection:

        sales_attributes = pd.read_sql_query(
            sales_attribute_query,
            connection,
            params=(BUSINESS_ID,)
        )

    sales_attributes = prepare_product_dataframe(
        sales_attributes
    )

    sales_attributes = (
        sales_attributes[
            [
                "product_key",
                "brand",
                "description",
                "size",
                "volume",
                "classification"
            ]
        ]
        .drop_duplicates(
            subset=["product_key"],
            keep="first"
        )
    )

    # --------------------------------------------------------
    # Fill only missing master attributes.
    # --------------------------------------------------------

    for column in [
        "brand",
        "description",
        "size",
        "volume",
        "classification"
    ]:

        source_column = (
            f"{column}_source"
        )

        result = result.merge(
            sales_attributes[
                [
                    "product_key",
                    column
                ]
            ].rename(
                columns={
                    column: source_column
                }
            ),
            on="product_key",
            how="left"
        )

        result[column] = (
            result[column]
            .combine_first(
                result[source_column]
            )
        )

        result = result.drop(
            columns=[source_column]
        )

    # --------------------------------------------------------
    # Attach sales
    # --------------------------------------------------------

    result = result.merge(
        sales,
        on="product_key",
        how="left"
    )

    # --------------------------------------------------------
    # Attach purchases
    # --------------------------------------------------------

    result = result.merge(
        purchases,
        on="product_key",
        how="left"
    )

    # --------------------------------------------------------
    # Attach beginning inventory
    # --------------------------------------------------------

    begin = begin_inventory.rename(
        columns={
            "quantity":
                "begin_inventory_quantity",
            "inventory_value":
                "begin_inventory_value"
        }
    )

    result = result.merge(
        begin,
        on="product_key",
        how="left"
    )

    # --------------------------------------------------------
    # Attach ending inventory
    # --------------------------------------------------------

    end = end_inventory.rename(
        columns={
            "quantity":
                "end_inventory_quantity",
            "inventory_value":
                "end_inventory_value"
        }
    )

    result = result.merge(
        end,
        on="product_key",
        how="left"
    )

    # --------------------------------------------------------
    # Fill metrics for products absent from a particular
    # source.
    # --------------------------------------------------------

    numeric_columns = [
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending",
        "begin_inventory_quantity",
        "begin_inventory_value",
        "end_inventory_quantity",
        "end_inventory_value"
    ]

    for column in numeric_columns:

        result[column] = (
            result[column]
            .fillna(0)
        )

    return result


# ============================================================
# 11. CALCULATE PRODUCT INTELLIGENCE
# ============================================================

def calculate_product_intelligence(
    df
):

    total_sales_revenue = (
        df["sales_revenue"].sum()
    )

    total_purchase_spending = (
        df["purchase_spending"].sum()
    )

    total_inventory_value = (
        df["end_inventory_value"].sum()
    )

    # --------------------------------------------------------
    # Contributions
    # --------------------------------------------------------

    if total_sales_revenue != 0:

        df["sales_contribution_percent"] = (
            df["sales_revenue"]
            / total_sales_revenue
            * 100
        )

    else:

        df["sales_contribution_percent"] = 0

    if total_purchase_spending != 0:

        df["purchase_contribution_percent"] = (
            df["purchase_spending"]
            / total_purchase_spending
            * 100
        )

    else:

        df["purchase_contribution_percent"] = 0

    if total_inventory_value != 0:

        df["inventory_value_contribution_percent"] = (
            df["end_inventory_value"]
            / total_inventory_value
            * 100
        )

    else:

        df["inventory_value_contribution_percent"] = 0

    # --------------------------------------------------------
    # Quantity balance
    #
    # Positive = more purchased than sold
    # Negative = more sold than purchased
    # --------------------------------------------------------

    df["quantity_balance"] = (
        df["purchase_quantity"]
        - df["sales_quantity"]
    )

    # --------------------------------------------------------
    # Sales / purchase value ratio
    #
    # IMPORTANT:
    # This is NOT profit margin.
    # --------------------------------------------------------

    df["sales_purchase_value_ratio"] = (
        np.where(
            df["purchase_spending"] > 0,
            df["sales_revenue"]
            / df["purchase_spending"],
            np.nan
        )
    )

    # --------------------------------------------------------
    # Average sales value
    # --------------------------------------------------------

    df["average_sales_value"] = (
        np.where(
            df["sales_quantity"] > 0,
            df["sales_revenue"]
            / df["sales_quantity"],
            np.nan
        )
    )

    # --------------------------------------------------------
    # Average purchase cost
    # --------------------------------------------------------

    df["average_purchase_cost"] = (
        np.where(
            df["purchase_quantity"] > 0,
            df["purchase_spending"]
            / df["purchase_quantity"],
            np.nan
        )
    )

    # --------------------------------------------------------
    # Quantity balance percentage
    # --------------------------------------------------------

    df["quantity_balance_percent"] = (
        np.where(
            df["sales_quantity"] > 0,
            df["quantity_balance"]
            / df["sales_quantity"]
            * 100,
            np.nan
        )
    )

    # --------------------------------------------------------
    # Inventory changes
    # --------------------------------------------------------

    df["inventory_quantity_change"] = (
        df["end_inventory_quantity"]
        - df["begin_inventory_quantity"]
    )

    df["inventory_value_change"] = (
        df["end_inventory_value"]
        - df["begin_inventory_value"]
    )

    df["inventory_value_growth_percent"] = (
        np.where(
            df["begin_inventory_value"] > 0,
            (
                (
                    df["end_inventory_value"]
                    - df["begin_inventory_value"]
                )
                / df["begin_inventory_value"]
                * 100
            ),
            np.nan
        )
    )

    # --------------------------------------------------------
    # Inventory relative to annual sales
    # --------------------------------------------------------

    df["inventory_to_sales_percent"] = (
        np.where(
            df["sales_revenue"] > 0,
            df["end_inventory_value"]
            / df["sales_revenue"]
            * 100,
            np.nan
        )
    )

    # --------------------------------------------------------
    # Product segmentation
    #
    # Median-based descriptive segmentation.
    # This is NOT a good/bad ranking.
    # --------------------------------------------------------

    sales_median = (
        df["sales_revenue"]
        .median()
    )

    purchase_median = (
        df["purchase_spending"]
        .median()
    )

    def assign_segment(row):

        high_sales = (
            row["sales_revenue"]
            >= sales_median
        )

        high_purchase = (
            row["purchase_spending"]
            >= purchase_median
        )

        if high_sales and high_purchase:

            return "High Sales / High Purchase"

        if high_sales and not high_purchase:

            return "High Sales / Lower Purchase"

        if not high_sales and high_purchase:

            return "Lower Sales / High Purchase"

        return "Lower Sales / Lower Purchase"

    df["product_segment"] = (
        df.apply(
            assign_segment,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    df = (
        df
        .sort_values(
            [
                "sales_revenue",
                "purchase_spending"
            ],
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    return df


# ============================================================
# 12. VERIFY
# ============================================================

def verify_product_intelligence(
    df,
    expected_sales_quantity,
    expected_sales_revenue,
    expected_purchase_quantity,
    expected_purchase_spending,
    expected_begin_quantity,
    expected_end_quantity,
    expected_begin_value,
    expected_end_value
):

    print("\n" + "=" * 70)
    print("VERIFYING PRODUCT INTELLIGENCE")
    print("=" * 70)

    actual_sales_quantity = (
        df["sales_quantity"].sum()
    )

    actual_sales_revenue = (
        df["sales_revenue"].sum()
    )

    actual_purchase_quantity = (
        df["purchase_quantity"].sum()
    )

    actual_purchase_spending = (
        df["purchase_spending"].sum()
    )

    actual_begin_quantity = (
        df["begin_inventory_quantity"].sum()
    )

    actual_end_quantity = (
        df["end_inventory_quantity"].sum()
    )

    actual_begin_value = (
        df["begin_inventory_value"].sum()
    )

    actual_end_value = (
        df["end_inventory_value"].sum()
    )

    print(
        f"\nProducts analyzed: "
        f"{len(df):,}"
    )

    print(
        f"Sales quantity: "
        f"{actual_sales_quantity:,.0f}"
    )

    print(
        f"Expected sales quantity: "
        f"{expected_sales_quantity:,.0f}"
    )

    print(
        f"Sales revenue: "
        f"${actual_sales_revenue:,.2f}"
    )

    print(
        f"Expected sales revenue: "
        f"${expected_sales_revenue:,.2f}"
    )

    print(
        f"\nPurchase quantity: "
        f"{actual_purchase_quantity:,.0f}"
    )

    print(
        f"Expected purchase quantity: "
        f"{expected_purchase_quantity:,.0f}"
    )

    print(
        f"Purchase spending: "
        f"${actual_purchase_spending:,.2f}"
    )

    print(
        f"Expected purchase spending: "
        f"${expected_purchase_spending:,.2f}"
    )

    print(
        f"\nBeginning inventory quantity: "
        f"{actual_begin_quantity:,.0f}"
    )

    print(
        f"Expected beginning inventory quantity: "
        f"{expected_begin_quantity:,.0f}"
    )

    print(
        f"Ending inventory quantity: "
        f"{actual_end_quantity:,.0f}"
    )

    print(
        f"Expected ending inventory quantity: "
        f"{expected_end_quantity:,.0f}"
    )

    print(
        f"\nBeginning inventory value: "
        f"${actual_begin_value:,.2f}"
    )

    print(
        f"Expected beginning inventory value: "
        f"${expected_begin_value:,.2f}"
    )

    print(
        f"Ending inventory value: "
        f"${actual_end_value:,.2f}"
    )

    print(
        f"Expected ending inventory value: "
        f"${expected_end_value:,.2f}"
    )

    # --------------------------------------------------------
    # Exact reconciliation
    # --------------------------------------------------------

    assert np.isclose(
        actual_sales_quantity,
        expected_sales_quantity
    )

    assert np.isclose(
        actual_sales_revenue,
        expected_sales_revenue
    )

    assert np.isclose(
        actual_purchase_quantity,
        expected_purchase_quantity
    )

    assert np.isclose(
        actual_purchase_spending,
        expected_purchase_spending
    )

    assert np.isclose(
        actual_begin_quantity,
        expected_begin_quantity
    )

    assert np.isclose(
        actual_end_quantity,
        expected_end_quantity
    )

    assert np.isclose(
        actual_begin_value,
        expected_begin_value
    )

    assert np.isclose(
        actual_end_value,
        expected_end_value
    )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "product_key",
        "brand",
        "description",
        "size",
        "volume",
        "classification",
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending",
        "begin_inventory_quantity",
        "begin_inventory_value",
        "end_inventory_quantity",
        "end_inventory_value",
        "sales_contribution_percent",
        "purchase_contribution_percent",
        "inventory_value_contribution_percent",
        "quantity_balance",
        "sales_purchase_value_ratio",
        "average_sales_value",
        "average_purchase_cost",
        "quantity_balance_percent",
        "inventory_quantity_change",
        "inventory_value_change",
        "inventory_value_growth_percent",
        "inventory_to_sales_percent",
        "product_segment"
    ]

    for column in required_columns:

        assert column in df.columns

    # --------------------------------------------------------
    # Duplicate product identities
    # --------------------------------------------------------

    assert (
        df["product_key"]
        .duplicated()
        .sum()
        == 0
    )

    print(
        "\n✓ Sales quantity reconciled"
    )

    print(
        "✓ Sales revenue reconciled"
    )

    print(
        "✓ Purchase quantity reconciled"
    )

    print(
        "✓ Purchase spending reconciled"
    )

    print(
        "✓ Beginning inventory quantity reconciled"
    )

    print(
        "✓ Ending inventory quantity reconciled"
    )

    print(
        "✓ Beginning inventory value reconciled"
    )

    print(
        "✓ Ending inventory value reconciled"
    )

    print(
        "✓ Required columns present"
    )

    print(
        "✓ No duplicate product identities"
    )

    print(
        "\n✓ ALL PRODUCT INTELLIGENCE "
        "VERIFICATION CHECKS PASSED"
    )


# ============================================================
# 13. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PRODUCT INTELLIGENCE")
    print("=" * 70)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    print(
        "\nLoading product data..."
    )

    master = load_master_products()

    sales = load_product_sales()

    purchases = load_product_purchases()

    begin_inventory_raw = load_inventory(
        "begin_inventory"
    )

    end_inventory_raw = load_inventory(
        "end_inventory"
    )

    # --------------------------------------------------------
    # Add product_key to inventory summaries
    # --------------------------------------------------------

    # load_inventory already returns product_key.

    begin_inventory = (
        begin_inventory_raw
    )

    end_inventory = (
        end_inventory_raw
    )

    print(
        f"\nMaster product rows retained: "
        f"{len(master):,}"
    )

    print(
        f"Sales product identities: "
        f"{len(sales):,}"
    )

    print(
        f"Purchase product identities: "
        f"{len(purchases):,}"
    )

    print(
        f"Beginning inventory identities: "
        f"{len(begin_inventory):,}"
    )

    print(
        f"Ending inventory identities: "
        f"{len(end_inventory):,}"
    )

    # --------------------------------------------------------
    # Build complete union
    # --------------------------------------------------------

    product_intelligence = build_product_union(
        master,
        sales,
        purchases,
        begin_inventory,
        end_inventory
    )

    # --------------------------------------------------------
    # Calculate intelligence
    # --------------------------------------------------------

    product_intelligence = (
        calculate_product_intelligence(
            product_intelligence
        )
    )

    # --------------------------------------------------------
    # Expected totals
    #
    # These come from the already verified Phase 9 results.
    # --------------------------------------------------------

    EXPECTED_SALES_QUANTITY = 32_917_876

    EXPECTED_SALES_REVENUE = 452_062_952.02

    EXPECTED_PURCHASE_QUANTITY = 33_584_377

    EXPECTED_PURCHASE_SPENDING = 321_900_765.53

    EXPECTED_BEGIN_QUANTITY = 4_219_275

    EXPECTED_END_QUANTITY = 4_885_776

    EXPECTED_BEGIN_VALUE = 68_053_780.17

    EXPECTED_END_VALUE = 79_704_851.13

    # --------------------------------------------------------
    # Verify
    # --------------------------------------------------------

    verify_product_intelligence(
        product_intelligence,
        EXPECTED_SALES_QUANTITY,
        EXPECTED_SALES_REVENUE,
        EXPECTED_PURCHASE_QUANTITY,
        EXPECTED_PURCHASE_SPENDING,
        EXPECTED_BEGIN_QUANTITY,
        EXPECTED_END_QUANTITY,
        EXPECTED_BEGIN_VALUE,
        EXPECTED_END_VALUE
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    product_intelligence.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"\n✓ Output saved to:"
        f"\n{OUTPUT_FILE}"
    )

    # --------------------------------------------------------
    # Display top products
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 PRODUCTS BY SALES REVENUE")
    print("=" * 70)

    print(
        product_intelligence[
            [
                "brand",
                "description",
                "size",
                "sales_quantity",
                "sales_revenue",
                "purchase_spending",
                "end_inventory_value",
                "product_segment"
            ]
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)
    print(
        "PRODUCT INTELLIGENCE COMPLETED SUCCESSFULLY"
    )
    print("=" * 70)
