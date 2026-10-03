
"""
Inventory Intelligence

Purpose:
    Combine sales, purchases, master products, beginning inventory,
    and ending inventory into one product-level intelligence dataset.

Important design decisions:

1. Sales and purchases are processed in chunks.
2. Large tables use keyset pagination instead of OFFSET pagination.
3. Product identity is based on:
       Brand + normalized Description + normalized Size
4. No fuzzy matching is performed.
5. Products that exist only in transactions/inventory are retained.
6. Missing inventory records are NOT treated as zero inventory.
7. Inventory risk signals are calculated only when the required
   inventory evidence exists.
8. Inventory table uses `price`, not `purchase_price`.
9. The source totals are reconciled before the output is accepted.
"""

import os
import re

from matplotlib import text
import numpy as np
import pandas as pd

from database.connection import engine


# ============================================================
# CONFIGURATION
# ============================================================

BUSINESS_ID = 1

CHUNK_SIZE = 250_000

OUTPUT_FILE = (
    "data/processed/inventory_intelligence.csv"
)


# ============================================================
# PRODUCT NORMALIZATION
# ============================================================

def normalize_product_size(value):
    """
    Normalize product size values.

    Examples:

        1.75L
        1.75 L
        1750mL
        1750 ml

    become a consistent representation.

    Missing values remain missing.
    """

    if pd.isna(value):
        return None

    value = str(value).strip().lower()

    if value == "":
        return None

    value = value.replace(" ", "")

    # --------------------------------------------------------
    # Liter values
    # --------------------------------------------------------

    liter_match = re.fullmatch(
        r"(\d+(?:\.\d+)?)l",
        value
    )

    if liter_match:

        liters = float(
            liter_match.group(1)
        )

        milliliters = round(
            liters * 1000
        )

        return f"{milliliters}ml"

    # --------------------------------------------------------
    # Milliliter values
    # --------------------------------------------------------

    ml_match = re.fullmatch(
        r"(\d+(?:\.\d+)?)ml",
        value
    )

    if ml_match:

        milliliters = float(
            ml_match.group(1)
        )

        if milliliters.is_integer():
            return f"{int(milliliters)}ml"

        return f"{milliliters:g}ml"

    # --------------------------------------------------------
    # Other values
    # --------------------------------------------------------

    return value


def normalize_description(value):
    """
    Normalize product descriptions for identity matching.
    """

    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    if value == "":
        return None

    # Normalize repeated whitespace
    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


def create_product_key(
    brand,
    description,
    size
):
    """
    Create normalized product identity.

    Product identity:

        Brand
        +
        normalized Description
        +
        normalized Size

    Explicit placeholders are used only for the internal key.

    Original source columns remain unchanged.
    """

    # --------------------------------------------------------
    # Brand
    # --------------------------------------------------------

    if pd.isna(brand):
        brand_key = "__MISSING_BRAND__"

    else:

        try:
            brand_number = int(float(brand))
            brand_key = str(
                brand_number
            )

        except (
            ValueError,
            TypeError
        ):

            brand_key = str(
                brand
            ).strip().upper()

    # --------------------------------------------------------
    # Description
    # --------------------------------------------------------

    description_key = normalize_description(
        description
    )

    if description_key is None:
        description_key = (
            "__MISSING_DESCRIPTION__"
        )

    # --------------------------------------------------------
    # Size
    # --------------------------------------------------------

    size_key = normalize_product_size(
        size
    )

    if size_key is None:
        size_key = "__MISSING_SIZE__"

    # --------------------------------------------------------
    # Final key
    # --------------------------------------------------------

    return (
        f"{brand_key}"
        f"|{description_key}"
        f"|{size_key}"
    )


def prepare_product_dataframe(df):
    """
    Add normalized product_key to a dataframe.
    """

    df = df.copy()

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
# KEYSET PAGINATION
# ============================================================

def read_table_in_batches(
    query,
    id_column,
    chunk_size=CHUNK_SIZE
):
    """
    Read a large MySQL table using keyset pagination.

    This avoids:

        OFFSET 250000
        OFFSET 500000
        ...

    which becomes increasingly expensive on large tables.
    """

    last_id = 0

    total_rows = 0

    while True:

        batch_query = f"""
            {query}
            AND {id_column} > %s
            ORDER BY {id_column}
            LIMIT %s
        """

        batch = pd.read_sql_query(
            batch_query,
            con=engine,
            params=[
                last_id,
                chunk_size
            ]
        )

        if batch.empty:
            break

        total_rows += len(batch)

        yield batch

        last_id = int(
            batch[id_column].iloc[-1]
        )

    return total_rows


# ============================================================
# LOAD SALES
# ============================================================

def load_sales():

    print("\nLoading sales...")

    aggregated = {}

    base_query = """
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

    total_rows = 0

    last_id = 0

    while True:

        query = f"""
            SELECT
                sales_id,
                brand,
                description,
                size,
                sales_quantity,
                sales_dollars
            FROM sales
            WHERE business_id = %s
              AND sales_id > %s
            ORDER BY sales_id
            LIMIT %s
        """

        batch = pd.read_sql_query(
        query,
        con=engine,
        params=(
            BUSINESS_ID,
            last_id,
            CHUNK_SIZE
        )
    )

        if batch.empty:
            break

        total_rows += len(batch)

        batch = prepare_product_dataframe(
            batch
        )

        grouped = (
            batch
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

        for row in grouped.itertuples(
            index=False
        ):

            key = row.product_key

            if key not in aggregated:

                aggregated[key] = {
                    "sales_quantity": 0,
                    "sales_revenue": 0.0
                }

            aggregated[key][
                "sales_quantity"
            ] += int(
                row.sales_quantity
            )

            aggregated[key][
                "sales_revenue"
            ] += float(
                row.sales_revenue
            )

        last_id = int(
            batch["sales_id"].iloc[-1]
        )

    result = pd.DataFrame.from_dict(
        aggregated,
        orient="index"
    )

    result.index.name = "product_key"

    result = result.reset_index()

    if result.empty:

        result = pd.DataFrame(
            columns=[
                "product_key",
                "sales_quantity",
                "sales_revenue"
            ]
        )

    print(
        f"Sales rows processed: "
        f"{total_rows:,}"
    )

    return result


# ============================================================
# LOAD PURCHASES
# ============================================================

def load_purchases():

    print("\nLoading purchases...")

    aggregated = {}

    total_rows = 0

    last_id = 0

    while True:

        query = f"""
            SELECT
                purchase_id,
                brand,
                description,
                size,
                quantity,
                dollars
            FROM purchases
            WHERE business_id = %s
              AND purchase_id > %s
            ORDER BY purchase_id
            LIMIT %s
        """

        batch = pd.read_sql_query(
            query,
            con=engine,
            params=(
                BUSINESS_ID,
                last_id,
                CHUNK_SIZE
            )
        )
        if batch.empty:
            break

        total_rows += len(batch)

        batch = prepare_product_dataframe(
            batch
        )

        grouped = (
            batch
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

        for row in grouped.itertuples(
            index=False
        ):

            key = row.product_key

            if key not in aggregated:

                aggregated[key] = {
                    "purchase_quantity": 0,
                    "purchase_spending": 0.0
                }

            aggregated[key][
                "purchase_quantity"
            ] += int(
                row.purchase_quantity
            )

            aggregated[key][
                "purchase_spending"
            ] += float(
                row.purchase_spending
            )

        last_id = int(
            batch["purchase_id"].iloc[-1]
        )

    result = pd.DataFrame.from_dict(
        aggregated,
        orient="index"
    )

    result.index.name = "product_key"

    result = result.reset_index()

    if result.empty:

        result = pd.DataFrame(
            columns=[
                "product_key",
                "purchase_quantity",
                "purchase_spending"
            ]
        )

    print(
        f"Purchase rows processed: "
        f"{total_rows:,}"
    )

    return result


# ============================================================
# LOAD INVENTORY
# ============================================================

def load_inventory(
    table_name
):
    """
    Load either:

        begin_inventory

    or:

        end_inventory

    Inventory identity is based on normalized product identity.

    IMPORTANT:
    Missing inventory rows are not interpreted as zero.

    A presence flag is maintained.
    """

    print(
        f"\nLoading {table_name}..."
    )

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

    chunks = []

    total_rows = 0

    for batch in pd.read_sql_query(
        query,
        con=engine,
        params=(BUSINESS_ID,),
        chunksize=CHUNK_SIZE
    ):
        total_rows += len(batch)

        batch = prepare_product_dataframe(
            batch
        )

        batch["on_hand"] = pd.to_numeric(
            batch["on_hand"],
            errors="coerce"
        ).fillna(0)

        batch["price"] = pd.to_numeric(
            batch["price"],
            errors="coerce"
        ).fillna(0)

        batch["inventory_value"] = (
            batch["on_hand"]
            * batch["price"]
        )

        grouped = (
            batch
            .groupby(
                "product_key",
                as_index=False
            )
            .agg(
                inventory_quantity=(
                    "on_hand",
                    "sum"
                ),
                inventory_value=(
                    "inventory_value",
                    "sum"
                )
            )
        )

        grouped["inventory_present"] = True

        chunks.append(
            grouped
        )

    if not chunks:

        return pd.DataFrame(
            columns=[
                "product_key",
                "inventory_quantity",
                "inventory_value",
                "inventory_present"
            ]
        )

    result = pd.concat(
        chunks,
        ignore_index=True
    )

    result = (
        result
        .groupby(
            "product_key",
            as_index=False
        )
        .agg(
            inventory_quantity=(
                "inventory_quantity",
                "sum"
            ),
            inventory_value=(
                "inventory_value",
                "sum"
            ),
            inventory_present=(
                "inventory_present",
                "max"
            )
        )
    )

    print(
        f"{table_name} rows processed: "
        f"{total_rows:,}"
    )

    return result


# ============================================================
# LOAD PRODUCT MASTER ATTRIBUTES
# ============================================================

def load_product_attributes():

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

    products = pd.read_sql_query(
        query,
        con=engine,
        params=(BUSINESS_ID,)
    )

    products = prepare_product_dataframe(
        products
    )

    # --------------------------------------------------------
    # Product master should already be unique after Phase 7.
    # --------------------------------------------------------

    products = (
        products
        .drop_duplicates(
            subset=[
                "product_key"
            ]
        )
    )

    return products[
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
# BUILD PRODUCT UNIVERSE
# ============================================================

def build_inventory_intelligence(
    product_attributes,
    sales,
    purchases,
    begin_inventory,
    end_inventory
):

    # --------------------------------------------------------
    # Create complete product universe.
    #
    # We intentionally use an OUTER union so products that
    # exist only in transactions or inventory are retained.
    # --------------------------------------------------------

    product_keys = set()

    for dataframe in [
        product_attributes,
        sales,
        purchases,
        begin_inventory,
        end_inventory
    ]:

        product_keys.update(
            dataframe[
                "product_key"
            ].dropna().tolist()
        )

    complete_products = pd.DataFrame(
        {
            "product_key": sorted(
                product_keys
            )
        }
    )

    # --------------------------------------------------------
    # Master attributes
    # --------------------------------------------------------

    result = complete_products.merge(
        product_attributes,
        on="product_key",
        how="left"
    )

    # --------------------------------------------------------
    # Sales
    # --------------------------------------------------------

    result = result.merge(
        sales,
        on="product_key",
        how="left"
    )

    # --------------------------------------------------------
    # Purchases
    # --------------------------------------------------------

    result = result.merge(
        purchases,
        on="product_key",
        how="left"
    )

    # --------------------------------------------------------
    # Beginning inventory
    # --------------------------------------------------------

    begin_inventory = (
        begin_inventory
        .rename(
            columns={
                "inventory_quantity":
                    "begin_inventory_quantity",

                "inventory_value":
                    "begin_inventory_value",

                "inventory_present":
                    "begin_inventory_present"
            }
        )
    )

    result = result.merge(
        begin_inventory,
        on="product_key",
        how="left"
    )

    # --------------------------------------------------------
    # Ending inventory
    # --------------------------------------------------------

    end_inventory = (
        end_inventory
        .rename(
            columns={
                "inventory_quantity":
                    "end_inventory_quantity",

                "inventory_value":
                    "end_inventory_value",

                "inventory_present":
                    "end_inventory_present"
            }
        )
    )

    result = result.merge(
        end_inventory,
        on="product_key",
        how="left"
    )

    # --------------------------------------------------------
    # Numeric missing values
    #
    # Missing transaction data means no transaction for that
    # product, therefore numeric transaction values can be zero.
    #
    # Inventory presence is different:
    #
    # missing inventory record != zero inventory.
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

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce"
        ).fillna(0)

    # --------------------------------------------------------
    # Presence flags
    # --------------------------------------------------------

    result[
        "begin_inventory_present"
    ] = result[
        "begin_inventory_present"
    ].fillna(False).astype(bool)

    result[
        "end_inventory_present"
    ] = result[
        "end_inventory_present"
    ].fillna(False).astype(bool)

    result[
        "inventory_present"
    ] = (
        result[
            "begin_inventory_present"
        ]
        |
        result[
            "end_inventory_present"
        ]
    )

    return result


# ============================================================
# CALCULATE INVENTORY INTELLIGENCE
# ============================================================

def calculate_inventory_intelligence(
    dataframe
):

    df = dataframe.copy()

    # --------------------------------------------------------
    # Quantity balance
    #
    # Positive value:
    #     purchases > sales
    #
    # Negative value:
    #     sales > purchases
    # --------------------------------------------------------

    df[
        "quantity_balance"
    ] = (
        df[
            "purchase_quantity"
        ]
        -
        df[
            "sales_quantity"
        ]
    )

    # --------------------------------------------------------
    # Quantity balance %
    # --------------------------------------------------------

    df[
        "quantity_balance_percent"
    ] = np.where(
        df["purchase_quantity"] > 0,

        (
            df["quantity_balance"]
            /
            df["purchase_quantity"]
            * 100
        ),

        np.nan
    )

    # --------------------------------------------------------
    # Sales / purchase value ratio
    #
    # IMPORTANT:
    # This is NOT profit margin.
    #
    # It compares:
    #
    # sales revenue / purchase spending
    # --------------------------------------------------------

    df[
        "sales_purchase_value_ratio"
    ] = np.where(
        df["purchase_spending"] > 0,

        (
            df["sales_revenue"]
            /
            df["purchase_spending"]
        ),

        np.nan
    )

    # --------------------------------------------------------
    # Average sales value
    # --------------------------------------------------------

    df[
        "average_sales_value"
    ] = np.where(
        df["sales_quantity"] > 0,

        (
            df["sales_revenue"]
            /
            df["sales_quantity"]
        ),

        np.nan
    )

    # --------------------------------------------------------
    # Average purchase cost
    # --------------------------------------------------------

    df[
        "average_purchase_cost"
    ] = np.where(
        df["purchase_quantity"] > 0,

        (
            df["purchase_spending"]
            /
            df["purchase_quantity"]
        ),

        np.nan
    )

    # --------------------------------------------------------
    # Inventory quantity change
    #
    # Only calculated when BOTH snapshots exist.
    #
    # A missing snapshot is not treated as zero.
    # --------------------------------------------------------

    both_inventory_present = (
        df[
            "begin_inventory_present"
        ]
        &
        df[
            "end_inventory_present"
        ]
    )

    df[
        "inventory_quantity_change"
    ] = np.where(
        both_inventory_present,

        (
            df[
                "end_inventory_quantity"
            ]
            -
            df[
                "begin_inventory_quantity"
            ]
        ),

        np.nan
    )

    # --------------------------------------------------------
    # Inventory value change
    # --------------------------------------------------------

    df[
        "inventory_value_change"
    ] = np.where(
        both_inventory_present,

        (
            df[
                "end_inventory_value"
            ]
            -
            df[
                "begin_inventory_value"
            ]
        ),

        np.nan
    )

    # --------------------------------------------------------
    # Inventory value growth %
    # --------------------------------------------------------

    df[
        "inventory_value_growth_percent"
    ] = np.where(
        (
            both_inventory_present
            &
            (df[
                "begin_inventory_value"
            ] > 0)
        ),

        (
            (
                df[
                    "inventory_value_change"
                ]
                /
                df[
                    "begin_inventory_value"
                ]
            )
            * 100
        ),

        np.nan
    )

    # --------------------------------------------------------
    # Ending inventory / annual sales %
    #
    # Only calculated where ending inventory exists.
    # --------------------------------------------------------

    df[
        "ending_inventory_to_sales_percent"
    ] = np.where(
        (
            df[
                "end_inventory_present"
            ]
            &
            (df[
                "sales_revenue"
            ] > 0)
        ),

        (
            df[
                "end_inventory_value"
            ]
            /
            df[
                "sales_revenue"
            ]
            * 100
        ),

        np.nan
    )

    # ========================================================
    # INVENTORY RISK THRESHOLDS
    #
    # These thresholds were calculated during Phase 9.4 using
    # the verified inventory distribution.
    # ========================================================

    LARGE_QUANTITY_DECREASE = -1174

    LARGE_QUANTITY_INCREASE = 1876

    LARGE_VALUE_DECREASE = -17226.41

    LARGE_VALUE_INCREASE = 29500.03

    HIGH_ENDING_INVENTORY_VALUE = 76636.53

    # --------------------------------------------------------
    # Zero ending inventory
    #
    # ONLY actual ending-inventory records are considered.
    #
    # A product absent from end_inventory is NOT zero inventory.
    # --------------------------------------------------------

    df[
        "zero_ending_inventory"
    ] = (
        df[
            "end_inventory_present"
        ]
        &
        (
            df[
                "end_inventory_quantity"
            ]
            == 0
        )
    )

    # --------------------------------------------------------
    # Large quantity decrease
    # --------------------------------------------------------

    df[
        "large_quantity_decrease"
    ] = (
        both_inventory_present
        &
        (
            df[
                "inventory_quantity_change"
            ]
            <= LARGE_QUANTITY_DECREASE
        )
    )

    # --------------------------------------------------------
    # Large quantity increase
    # --------------------------------------------------------

    df[
        "large_quantity_increase"
    ] = (
        both_inventory_present
        &
        (
            df[
                "inventory_quantity_change"
            ]
            >= LARGE_QUANTITY_INCREASE
        )
    )

    # --------------------------------------------------------
    # High ending inventory value
    # --------------------------------------------------------

    df[
        "high_ending_inventory_value"
    ] = (
        df[
            "end_inventory_present"
        ]
        &
        (
            df[
                "end_inventory_value"
            ]
            >= HIGH_ENDING_INVENTORY_VALUE
        )
    )

    # --------------------------------------------------------
    # Large inventory value decrease
    # --------------------------------------------------------

    df[
        "large_value_decrease"
    ] = (
        both_inventory_present
        &
        (
            df[
                "inventory_value_change"
            ]
            <= LARGE_VALUE_DECREASE
        )
    )

    # --------------------------------------------------------
    # Large inventory value increase
    # --------------------------------------------------------

    df[
        "large_value_increase"
    ] = (
        both_inventory_present
        &
        (
            df[
                "inventory_value_change"
            ]
            >= LARGE_VALUE_INCREASE
        )
    )

    # --------------------------------------------------------
    # Risk signal count
    # --------------------------------------------------------

    risk_columns = [

        "zero_ending_inventory",

        "large_quantity_decrease",

        "large_quantity_increase",

        "high_ending_inventory_value",

        "large_value_decrease",

        "large_value_increase"
    ]

    df[
        "risk_signal_count"
    ] = df[
        risk_columns
    ].sum(
        axis=1
    )

    # --------------------------------------------------------
    # Risk category
    #
    # This is descriptive, not a business ranking.
    # --------------------------------------------------------

    def classify_risk(row):

        count = row[
            "risk_signal_count"
        ]

        if count >= 3:
            return "Multiple Risk Signals"

        if row[
            "zero_ending_inventory"
        ]:
            return "Zero Ending Inventory"

        if row[
            "large_quantity_decrease"
        ]:
            return "Large Quantity Decrease"

        if row[
            "large_quantity_increase"
        ]:
            return "Large Quantity Increase"

        if row[
            "large_value_decrease"
        ]:
            return "Large Value Decrease"

        if row[
            "large_value_increase"
        ]:
            return "Large Value Increase"

        if row[
            "high_ending_inventory_value"
        ]:
            return "High Inventory Value"

        return "No Major Risk Signal"

    df[
        "risk_category"
    ] = df.apply(
        classify_risk,
        axis=1
    )

    # --------------------------------------------------------
    # Sort by risk importance for display.
    # --------------------------------------------------------

    df = df.sort_values(
        [
            "risk_signal_count",
            "end_inventory_value"
        ],
        ascending=[
            False,
            False
        ]
    )

    return df


# ============================================================
# VERIFY INVENTORY INTELLIGENCE
# ============================================================

def verify_inventory_intelligence(
    inventory_intelligence
):

    print("\n" + "=" * 70)
    print("VERIFYING INVENTORY INTELLIGENCE")
    print("=" * 70)

    # --------------------------------------------------------
    # Expected source totals
    # --------------------------------------------------------

    expected_sales_quantity = 32_917_876

    expected_purchase_quantity = 33_584_377

    expected_begin_inventory_quantity = 4_219_275

    expected_end_inventory_quantity = 4_885_776

    expected_begin_inventory_value = 68_053_780.17

    expected_end_inventory_value = 79_704_851.13

    # --------------------------------------------------------
    # Actual totals
    # --------------------------------------------------------

    actual_sales_quantity = int(
        inventory_intelligence[
            "sales_quantity"
        ].sum()
    )

    actual_purchase_quantity = int(
        inventory_intelligence[
            "purchase_quantity"
        ].sum()
    )

    actual_begin_inventory_quantity = int(
        inventory_intelligence[
            "begin_inventory_quantity"
        ].sum()
    )

    actual_end_inventory_quantity = int(
        inventory_intelligence[
            "end_inventory_quantity"
        ].sum()
    )

    actual_begin_inventory_value = float(
        inventory_intelligence[
            "begin_inventory_value"
        ].sum()
    )

    actual_end_inventory_value = float(
        inventory_intelligence[
            "end_inventory_value"
        ].sum()
    )

    # --------------------------------------------------------
    # Product population
    # --------------------------------------------------------

    actual_product_count = len(
        inventory_intelligence
    )

    actual_inventory_products = int(
        inventory_intelligence[
            "inventory_present"
        ].sum()
    )

    actual_begin_inventory_products = int(
        inventory_intelligence[
            "begin_inventory_present"
        ].sum()
    )

    actual_end_inventory_products = int(
        inventory_intelligence[
            "end_inventory_present"
        ].sum()
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print(
        f"Products analyzed: "
        f"{actual_product_count:,}"
    )

    print(
        f"Products with inventory evidence: "
        f"{actual_inventory_products:,}"
    )

    print(
        f"Products with beginning inventory: "
        f"{actual_begin_inventory_products:,}"
    )

    print(
        f"Products with ending inventory: "
        f"{actual_end_inventory_products:,}"
    )

    print()

    print(
        f"Sales quantity: "
        f"{actual_sales_quantity:,}"
    )

    print(
        f"Purchase quantity: "
        f"{actual_purchase_quantity:,}"
    )

    print(
        f"Beginning inventory quantity: "
        f"{actual_begin_inventory_quantity:,}"
    )

    print(
        f"Ending inventory quantity: "
        f"{actual_end_inventory_quantity:,}"
    )

    print(
        f"Beginning inventory value: "
        f"${actual_begin_inventory_value:,.2f}"
    )

    print(
        f"Ending inventory value: "
        f"${actual_end_inventory_value:,.2f}"
    )

    # ========================================================
    # SOURCE RECONCILIATION
    # ========================================================

    assert (
        actual_sales_quantity
        == expected_sales_quantity
    ), (
        "Sales quantity mismatch."
    )

    print(
        "✓ Sales quantity reconciled"
    )

    assert (
        actual_purchase_quantity
        == expected_purchase_quantity
    ), (
        "Purchase quantity mismatch."
    )

    print(
        "✓ Purchase quantity reconciled"
    )

    assert (
        actual_begin_inventory_quantity
        == expected_begin_inventory_quantity
    ), (
        "Beginning inventory quantity mismatch."
    )

    print(
        "✓ Beginning inventory quantity reconciled"
    )

    assert (
        actual_end_inventory_quantity
        == expected_end_inventory_quantity
    ), (
        "Ending inventory quantity mismatch."
    )

    print(
        "✓ Ending inventory quantity reconciled"
    )

    assert np.isclose(
        actual_begin_inventory_value,
        expected_begin_inventory_value,
        atol=0.01
    ), (
        "Beginning inventory value mismatch."
    )

    print(
        "✓ Beginning inventory value reconciled"
    )

    assert np.isclose(
        actual_end_inventory_value,
        expected_end_inventory_value,
        atol=0.01
    ), (
        "Ending inventory value mismatch."
    )

    print(
        "✓ Ending inventory value reconciled"
    )

    # ========================================================
    # INVENTORY PRODUCT POPULATION
    # ========================================================

    expected_inventory_products = int(
        (
            inventory_intelligence[
                "begin_inventory_present"
            ]
            |
            inventory_intelligence[
                "end_inventory_present"
            ]
        ).sum()
    )

    print(
        f"Expected inventory-product identities: "
        f"{expected_inventory_products:,}"
    )

    print(
        f"Actual inventory-product identities: "
        f"{actual_inventory_products:,}"
    )

    assert (
        actual_inventory_products
        == expected_inventory_products
    ), (
        "Inventory-product identity count mismatch."
    )

    print(
        "✓ Inventory-product population reconciled"
    )

    # ========================================================
    # INVENTORY PRESENCE FLAG
    # ========================================================

    calculated_inventory_present = (
        inventory_intelligence[
            "begin_inventory_present"
        ]
        |
        inventory_intelligence[
            "end_inventory_present"
        ]
    )

    assert (
        inventory_intelligence[
            "inventory_present"
        ]
        == calculated_inventory_present
    ).all(), (
        "inventory_present flag is inconsistent."
    )

    print(
        "✓ Inventory presence flags are consistent"
    )

    # ========================================================
    # REQUIRED COLUMNS
    # ========================================================

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

        "begin_inventory_present",

        "end_inventory_present",

        "inventory_present",

        "inventory_quantity_change",

        "inventory_value_change",

        "inventory_value_growth_percent",

        "quantity_balance",

        "quantity_balance_percent",

        "sales_purchase_value_ratio",

        "average_sales_value",

        "average_purchase_cost",

        "ending_inventory_to_sales_percent",

        "zero_ending_inventory",

        "large_quantity_decrease",

        "large_quantity_increase",

        "high_ending_inventory_value",

        "large_value_decrease",

        "large_value_increase",

        "risk_signal_count",

        "risk_category"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in inventory_intelligence.columns
    ]

    assert not missing_columns, (
        f"Missing required columns: "
        f"{missing_columns}"
    )

    print(
        "✓ Required columns present"
    )

    # ========================================================
    # DUPLICATE PRODUCT IDENTITY
    # ========================================================

    duplicate_product_keys = int(
        inventory_intelligence[
            "product_key"
        ].duplicated().sum()
    )

    assert (
        duplicate_product_keys == 0
    ), (
        "Duplicate product identities found."
    )

    print(
        "✓ No duplicate product identities"
    )

    # ========================================================
    # RISK FLAG VALIDATION
    # ========================================================

    invalid_zero_inventory_flags = int(
        (
            inventory_intelligence[
                "zero_ending_inventory"
            ]
            &
            ~inventory_intelligence[
                "end_inventory_present"
            ]
        ).sum()
    )

    assert (
        invalid_zero_inventory_flags == 0
    ), (
        "Zero-inventory risk assigned without "
        "ending inventory evidence."
    )

    invalid_high_inventory_flags = int(
        (
            inventory_intelligence[
                "high_ending_inventory_value"
            ]
            &
            ~inventory_intelligence[
                "end_inventory_present"
            ]
        ).sum()
    )

    assert (
        invalid_high_inventory_flags == 0
    ), (
        "High inventory-value risk assigned without "
        "ending inventory evidence."
    )

    invalid_quantity_decrease_flags = int(
        (
            inventory_intelligence[
                "large_quantity_decrease"
            ]
            &
            ~inventory_intelligence[
                "inventory_present"
            ]
        ).sum()
    )

    assert (
        invalid_quantity_decrease_flags == 0
    ), (
        "Large quantity decrease risk assigned "
        "without inventory evidence."
    )

    invalid_quantity_increase_flags = int(
        (
            inventory_intelligence[
                "large_quantity_increase"
            ]
            &
            ~inventory_intelligence[
                "inventory_present"
            ]
        ).sum()
    )

    assert (
        invalid_quantity_increase_flags == 0
    ), (
        "Large quantity increase risk assigned "
        "without inventory evidence."
    )

    invalid_value_decrease_flags = int(
        (
            inventory_intelligence[
                "large_value_decrease"
            ]
            &
            ~inventory_intelligence[
                "inventory_present"
            ]
        ).sum()
    )

    assert (
        invalid_value_decrease_flags == 0
    ), (
        "Large value decrease risk assigned "
        "without inventory evidence."
    )

    invalid_value_increase_flags = int(
        (
            inventory_intelligence[
                "large_value_increase"
            ]
            &
            ~inventory_intelligence[
                "inventory_present"
            ]
        ).sum()
    )

    assert (
        invalid_value_increase_flags == 0
    ), (
        "Large value increase risk assigned "
        "without inventory evidence."
    )

    print(
        "✓ Inventory risk flags have valid evidence"
    )

    # ========================================================
    # RISK SUMMARY
    # ========================================================

    print("\nInventory risk summary:")

    print(
        "Zero ending inventory: "
        f"{int(inventory_intelligence['zero_ending_inventory'].sum()):,}"
    )

    print(
        "Large quantity decrease: "
        f"{int(inventory_intelligence['large_quantity_decrease'].sum()):,}"
    )

    print(
        "Large quantity increase: "
        f"{int(inventory_intelligence['large_quantity_increase'].sum()):,}"
    )

    print(
        "High ending inventory value: "
        f"{int(inventory_intelligence['high_ending_inventory_value'].sum()):,}"
    )

    print(
        "Large value decrease: "
        f"{int(inventory_intelligence['large_value_decrease'].sum()):,}"
    )

    print(
        "Large value increase: "
        f"{int(inventory_intelligence['large_value_increase'].sum()):,}"
    )

    print(
        "Multiple risk signals: "
        f"{int((inventory_intelligence['risk_signal_count'] >= 3).sum()):,}"
    )

    # ========================================================
    # FINAL VERIFICATION
    # ========================================================

    print("\n" + "=" * 70)

    print(
        "✓ ALL INVENTORY INTELLIGENCE VERIFICATION CHECKS PASSED"
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("INVENTORY INTELLIGENCE")
    print("=" * 70)

    print(
        "\nLoading inventory intelligence data..."
    )

    # --------------------------------------------------------
    # Load master product attributes
    # --------------------------------------------------------

    product_attributes = (
        load_product_attributes()
    )

    # --------------------------------------------------------
    # Load sales
    # --------------------------------------------------------

    sales = load_sales()

    # --------------------------------------------------------
    # Load purchases
    # --------------------------------------------------------

    purchases = load_purchases()

    # --------------------------------------------------------
    # Load beginning inventory
    # --------------------------------------------------------

    begin_inventory = load_inventory(
        "begin_inventory"
    )

    # --------------------------------------------------------
    # Load ending inventory
    # --------------------------------------------------------

    end_inventory = load_inventory(
        "end_inventory"
    )

    # --------------------------------------------------------
    # Build complete product universe
    # --------------------------------------------------------

    inventory_intelligence = (
        build_inventory_intelligence(
            product_attributes,
            sales,
            purchases,
            begin_inventory,
            end_inventory
        )
    )

    print(
        f"\nComplete product identities: "
        f"{len(inventory_intelligence):,}"
    )

    # --------------------------------------------------------
    # Calculate intelligence
    # --------------------------------------------------------

    inventory_intelligence = (
        calculate_inventory_intelligence(
            inventory_intelligence
        )
    )

    # --------------------------------------------------------
    # Verify
    # --------------------------------------------------------

    verify_inventory_intelligence(
        inventory_intelligence
    )

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    output_directory = os.path.dirname(
        OUTPUT_FILE
    )

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    inventory_intelligence.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"\n✓ Output saved to:"
    )

    print(
        OUTPUT_FILE
    )

    # ========================================================
    # DISPLAY TOP RISK PRODUCTS
    # ========================================================

    print(
        "\n" + "=" * 70
    )

    print(
        "TOP INVENTORY RISK PRODUCTS"
    )

    print(
        "=" * 70
    )

    display_columns = [

        "brand",

        "description",

        "size",

        "sales_quantity",

        "purchase_quantity",

        "begin_inventory_quantity",

        "end_inventory_quantity",

        "inventory_quantity_change",

        "begin_inventory_value",

        "end_inventory_value",

        "inventory_value_change",

        "risk_signal_count",

        "risk_category"
    ]

    available_display_columns = [
        column
        for column in display_columns
        if column in inventory_intelligence.columns
    ]

    print(
        inventory_intelligence[
            available_display_columns
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "INVENTORY INTELLIGENCE COMPLETED"
    )

    print(
        "=" * 70
    )
