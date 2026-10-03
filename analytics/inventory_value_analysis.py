"""
Phase 9.4.3
Inventory Value Analysis

Purpose:
Analyze the monetary value of beginning and ending inventory.

Inventory Value:
    on_hand * price

This analysis identifies:
1. Overall inventory value
2. Product-level value changes
3. Store-level value changes
4. Highest-value inventory
5. Largest value increases
6. Largest value decreases
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


# ============================================================
# 1. LOAD INVENTORY
# ============================================================

def load_inventory(table_name):

    print(f"\nLoading {table_name}...")

    query = f"""
        SELECT
            inventory_id,
            store_number,
            brand,
            description,
            size,
            on_hand,
            price
        FROM {table_name}
        WHERE business_id = %s
    """

    records = {}

    total_rows = 0

    for chunk in pd.read_sql_query(
        query,
        engine,
        params=(BUSINESS_ID,),
        chunksize=CHUNK_SIZE
    ):

        total_rows += len(chunk)

        chunk["on_hand"] = pd.to_numeric(
            chunk["on_hand"],
            errors="coerce"
        ).fillna(0)

        chunk["price"] = pd.to_numeric(
            chunk["price"],
            errors="coerce"
        ).fillna(0)

        chunk["inventory_value"] = (
            chunk["on_hand"]
            * chunk["price"]
        )

        for _, row in chunk.iterrows():

            inventory_id = row["inventory_id"]

            records[inventory_id] = {
                "store_number": row["store_number"],
                "brand": row["brand"],
                "description": row["description"],
                "size": row["size"],
                "on_hand": row["on_hand"],
                "price": row["price"],
                "inventory_value":
                    row["inventory_value"]
            }

    print(
        f"{table_name} rows processed: "
        f"{total_rows:,}"
    )

    return records


# ============================================================
# 2. BUILD VALUE COMPARISON
# ============================================================

def build_comparison(
    beginning,
    ending
):

    all_ids = (
        set(beginning.keys())
        | set(ending.keys())
    )

    rows = []

    for inventory_id in all_ids:

        begin = beginning.get(
            inventory_id,
            {}
        )

        end = ending.get(
            inventory_id,
            {}
        )

        beginning_quantity = begin.get(
            "on_hand",
            0
        )

        ending_quantity = end.get(
            "on_hand",
            0
        )

        beginning_value = begin.get(
            "inventory_value",
            0
        )

        ending_value = end.get(
            "inventory_value",
            0
        )

        value_change = (
            ending_value
            - beginning_value
        )

        if value_change > 0:

            movement = "Value Increased"

        elif value_change < 0:

            movement = "Value Decreased"

        else:

            movement = "No Value Change"

        rows.append(
            {
                "inventory_id":
                    inventory_id,

                "store_number":
                    end.get(
                        "store_number",
                        begin.get("store_number")
                    ),

                "brand":
                    end.get(
                        "brand",
                        begin.get("brand")
                    ),

                "description":
                    end.get(
                        "description",
                        begin.get("description")
                    ),

                "size":
                    end.get(
                        "size",
                        begin.get("size")
                    ),

                "beginning_quantity":
                    beginning_quantity,

                "ending_quantity":
                    ending_quantity,

                "beginning_value":
                    beginning_value,

                "ending_value":
                    ending_value,

                "value_change":
                    value_change,

                "movement":
                    movement
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# 3. PRODUCT-LEVEL VALUE ANALYSIS
# ============================================================

def analyze_products(result):

    product_analysis = (
        result
        .groupby(
            [
                "brand",
                "description",
                "size"
            ],
            dropna=False
        )
        .agg(
            beginning_quantity=(
                "beginning_quantity",
                "sum"
            ),
            ending_quantity=(
                "ending_quantity",
                "sum"
            ),
            beginning_value=(
                "beginning_value",
                "sum"
            ),
            ending_value=(
                "ending_value",
                "sum"
            ),
            value_change=(
                "value_change",
                "sum"
            )
        )
        .reset_index()
    )

    return product_analysis


# ============================================================
# 4. STORE-LEVEL VALUE ANALYSIS
# ============================================================

def analyze_stores(result):

    store_analysis = (
        result
        .groupby("store_number")
        .agg(
            beginning_quantity=(
                "beginning_quantity",
                "sum"
            ),
            ending_quantity=(
                "ending_quantity",
                "sum"
            ),
            beginning_value=(
                "beginning_value",
                "sum"
            ),
            ending_value=(
                "ending_value",
                "sum"
            ),
            value_change=(
                "value_change",
                "sum"
            )
        )
        .reset_index()
    )

    return store_analysis


# ============================================================
# 5. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 9.4.3")
    print("INVENTORY VALUE ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # Load snapshots
    # --------------------------------------------------------

    beginning = load_inventory(
        "begin_inventory"
    )

    ending = load_inventory(
        "end_inventory"
    )

    # --------------------------------------------------------
    # Build comparison
    # --------------------------------------------------------

    result = build_comparison(
        beginning,
        ending
    )

    pd.set_option(
        "display.max_columns",
        None
    )

    pd.set_option(
        "display.width",
        240
    )

    # ========================================================
    # OVERALL VALUE SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("OVERALL INVENTORY VALUE")
    print("=" * 70)

    beginning_value = (
        result["beginning_value"]
        .sum()
    )

    ending_value = (
        result["ending_value"]
        .sum()
    )

    value_change = (
        ending_value
        - beginning_value
    )

    if beginning_value != 0:

        value_change_pct = (
            value_change
            / beginning_value
        ) * 100

    else:

        value_change_pct = 0

    print(
        f"Beginning inventory value: "
        f"${beginning_value:,.2f}"
    )

    print(
        f"Ending inventory value: "
        f"${ending_value:,.2f}"
    )

    print(
        f"Inventory value change: "
        f"${value_change:,.2f}"
    )

    print(
        f"Inventory value change %: "
        f"{value_change_pct:.2f}%"
    )

    # ========================================================
    # VALUE MOVEMENT COUNTS
    # ========================================================

    print("\n" + "=" * 70)
    print("INVENTORY VALUE MOVEMENT")
    print("=" * 70)

    movement_counts = (
        result["movement"]
        .value_counts()
    )

    print(
        f"Value increased: "
        f"{movement_counts.get('Value Increased', 0):,}"
    )

    print(
        f"Value decreased: "
        f"{movement_counts.get('Value Decreased', 0):,}"
    )

    print(
        f"No value change: "
        f"{movement_counts.get('No Value Change', 0):,}"
    )

    # ========================================================
    # PRODUCT ANALYSIS
    # ========================================================

    product_analysis = analyze_products(
        result
    )

    # --------------------------------------------------------
    # Highest ending inventory value
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 PRODUCTS BY ENDING INVENTORY VALUE")
    print("=" * 70)

    top_ending_products = (
        product_analysis
        .sort_values(
            "ending_value",
            ascending=False
        )
        .head(10)
    )

    print(
        top_ending_products[
            [
                "brand",
                "description",
                "size",
                "ending_quantity",
                "ending_value"
            ]
        ].to_string(
            index=False,
            formatters={
                "ending_quantity":
                    "{:,.0f}".format,

                "ending_value":
                    "${:,.2f}".format
            }
        )
    )

    # --------------------------------------------------------
    # Largest product value increases
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 PRODUCT VALUE INCREASES")
    print("=" * 70)

    top_product_increases = (
        product_analysis
        .sort_values(
            "value_change",
            ascending=False
        )
        .head(10)
    )

    print(
        top_product_increases[
            [
                "brand",
                "description",
                "size",
                "beginning_value",
                "ending_value",
                "value_change"
            ]
        ].to_string(
            index=False,
            formatters={
                "beginning_value":
                    "${:,.2f}".format,

                "ending_value":
                    "${:,.2f}".format,

                "value_change":
                    "${:,.2f}".format
            }
        )
    )

    # --------------------------------------------------------
    # Largest product value decreases
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 PRODUCT VALUE DECREASES")
    print("=" * 70)

    top_product_decreases = (
        product_analysis
        .sort_values(
            "value_change",
            ascending=True
        )
        .head(10)
    )

    print(
        top_product_decreases[
            [
                "brand",
                "description",
                "size",
                "beginning_value",
                "ending_value",
                "value_change"
            ]
        ].to_string(
            index=False,
            formatters={
                "beginning_value":
                    "${:,.2f}".format,

                "ending_value":
                    "${:,.2f}".format,

                "value_change":
                    "${:,.2f}".format
            }
        )
    )

    # ========================================================
    # STORE ANALYSIS
    # ========================================================

    store_analysis = analyze_stores(
        result
    )

    # --------------------------------------------------------
    # Highest ending inventory value stores
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 STORES BY ENDING INVENTORY VALUE")
    print("=" * 70)

    top_ending_stores = (
        store_analysis
        .sort_values(
            "ending_value",
            ascending=False
        )
        .head(10)
    )

    print(
        top_ending_stores[
            [
                "store_number",
                "ending_quantity",
                "ending_value"
            ]
        ].to_string(
            index=False,
            formatters={
                "ending_quantity":
                    "{:,.0f}".format,

                "ending_value":
                    "${:,.2f}".format
            }
        )
    )

    # --------------------------------------------------------
    # Largest store value increases
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 STORE INVENTORY VALUE INCREASES")
    print("=" * 70)

    top_store_increases = (
        store_analysis
        .sort_values(
            "value_change",
            ascending=False
        )
        .head(10)
    )

    print(
        top_store_increases[
            [
                "store_number",
                "beginning_value",
                "ending_value",
                "value_change"
            ]
        ].to_string(
            index=False,
            formatters={
                "beginning_value":
                    "${:,.2f}".format,

                "ending_value":
                    "${:,.2f}".format,

                "value_change":
                    "${:,.2f}".format
            }
        )
    )

    # --------------------------------------------------------
    # Largest store value decreases
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 STORE INVENTORY VALUE DECREASES")
    print("=" * 70)

    top_store_decreases = (
        store_analysis
        .sort_values(
            "value_change",
            ascending=True
        )
        .head(10)
    )

    print(
        top_store_decreases[
            [
                "store_number",
                "beginning_value",
                "ending_value",
                "value_change"
            ]
        ].to_string(
            index=False,
            formatters={
                "beginning_value":
                    "${:,.2f}".format,

                "ending_value":
                    "${:,.2f}".format,

                "value_change":
                    "${:,.2f}".format
            }
        )
    )

    # ========================================================
    # VERIFICATION
    # ========================================================

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    print(
        f"Beginning rows: "
        f"{len(beginning):,}"
    )

    print(
        f"Ending rows: "
        f"{len(ending):,}"
    )

    print(
        f"Unique Inventory IDs compared: "
        f"{len(result):,}"
    )

    # --------------------------------------------------------
    # Verify known overall values
    # --------------------------------------------------------

    expected_beginning_value = 68_053_780.17
    expected_ending_value = 79_704_851.13

    if abs(
        beginning_value
        - expected_beginning_value
    ) < 0.01:

        print(
            "✓ Beginning inventory value PASSED."
        )

    else:

        print(
            "✗ Beginning inventory value FAILED."
        )

        raise ValueError(
            "Beginning inventory value mismatch."
        )

    if abs(
        ending_value
        - expected_ending_value
    ) < 0.01:

        print(
            "✓ Ending inventory value PASSED."
        )

    else:

        print(
            "✗ Ending inventory value FAILED."
        )

        raise ValueError(
            "Ending inventory value mismatch."
        )

    expected_change = (
        expected_ending_value
        - expected_beginning_value
    )

    if abs(
        value_change
        - expected_change
    ) < 0.01:

        print(
            "✓ Inventory value change PASSED."
        )

    else:

        print(
            "✗ Inventory value change FAILED."
        )

        raise ValueError(
            "Inventory value change mismatch."
        )

    if len(result) == 256_042:

        print(
            "✓ Inventory ID count PASSED."
        )

    else:

        print(
            "✗ Inventory ID count FAILED."
        )

        raise ValueError(
            "Unexpected Inventory ID count."
        )

    print(
        "\n✓ Phase 9.4.3 completed successfully."
    )