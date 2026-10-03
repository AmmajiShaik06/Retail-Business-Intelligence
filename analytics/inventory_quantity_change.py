"""
Phase 9.4.2
Inventory Quantity Change Analysis

Purpose:
Analyze inventory quantity movement between
beginning inventory and ending inventory.

Beginning snapshot:
January 1, 2024

Ending snapshot:
December 31, 2024

Quantity change:
ending_quantity - beginning_quantity
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


# ============================================================
# 1. LOAD INVENTORY SNAPSHOT
# ============================================================

def load_inventory(table_name, date_column):

    print(f"\nLoading {table_name}...")

    query = f"""
        SELECT
            inventory_id,
            store_number,
            brand,
            description,
            size,
            on_hand
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

        for _, row in chunk.iterrows():

            inventory_id = row["inventory_id"]

            records[inventory_id] = {
                "store_number": row["store_number"],
                "brand": row["brand"],
                "description": row["description"],
                "size": row["size"],
                "on_hand": row["on_hand"]
            }

    print(
        f"{table_name} rows processed: "
        f"{total_rows:,}"
    )

    return records


# ============================================================
# 2. BUILD QUANTITY CHANGE DATASET
# ============================================================

def build_quantity_change(
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

        quantity_change = (
            ending_quantity
            - beginning_quantity
        )

        if quantity_change > 0:

            movement = "Increased"

        elif quantity_change < 0:

            movement = "Decreased"

        else:

            movement = "No Change"

        rows.append(
            {
                "inventory_id": inventory_id,

                "store_number": end.get(
                    "store_number",
                    begin.get("store_number")
                ),

                "brand": end.get(
                    "brand",
                    begin.get("brand")
                ),

                "description": end.get(
                    "description",
                    begin.get("description")
                ),

                "size": end.get(
                    "size",
                    begin.get("size")
                ),

                "beginning_quantity":
                    beginning_quantity,

                "ending_quantity":
                    ending_quantity,

                "quantity_change":
                    quantity_change,

                "movement":
                    movement
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# 3. STORE-LEVEL ANALYSIS
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
            quantity_change=(
                "quantity_change",
                "sum"
            )
        )
        .reset_index()
    )

    return store_analysis


# ============================================================
# 4. PRODUCT-LEVEL ANALYSIS
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
            quantity_change=(
                "quantity_change",
                "sum"
            )
        )
        .reset_index()
    )

    return product_analysis


# ============================================================
# 5. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 9.4.2")
    print("INVENTORY QUANTITY CHANGE ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # Load snapshots
    # --------------------------------------------------------

    beginning = load_inventory(
        "begin_inventory",
        "start_date"
    )

    ending = load_inventory(
        "end_inventory",
        "end_date"
    )

    # --------------------------------------------------------
    # Build comparison
    # --------------------------------------------------------

    result = build_quantity_change(
        beginning,
        ending
    )

    pd.set_option(
        "display.max_columns",
        None
    )

    pd.set_option(
        "display.width",
        220
    )

    # --------------------------------------------------------
    # Overall movement
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("OVERALL INVENTORY MOVEMENT")
    print("=" * 70)

    movement_counts = (
        result["movement"]
        .value_counts()
    )

    increased = movement_counts.get(
        "Increased",
        0
    )

    decreased = movement_counts.get(
        "Decreased",
        0
    )

    unchanged = movement_counts.get(
        "No Change",
        0
    )

    print(
        f"Inventory records increased: "
        f"{increased:,}"
    )

    print(
        f"Inventory records decreased: "
        f"{decreased:,}"
    )

    print(
        f"Inventory records unchanged: "
        f"{unchanged:,}"
    )

    # --------------------------------------------------------
    # Quantity totals
    # --------------------------------------------------------

    beginning_quantity = (
        result["beginning_quantity"]
        .sum()
    )

    ending_quantity = (
        result["ending_quantity"]
        .sum()
    )

    quantity_change = (
        result["quantity_change"]
        .sum()
    )

    print(
        f"\nBeginning quantity: "
        f"{beginning_quantity:,.0f}"
    )

    print(
        f"Ending quantity: "
        f"{ending_quantity:,.0f}"
    )

    print(
        f"Net quantity change: "
        f"{quantity_change:,.0f}"
    )

    # --------------------------------------------------------
    # TOP PRODUCT INCREASES
    # --------------------------------------------------------

    product_analysis = analyze_products(
        result
    )

    print("\n" + "=" * 70)
    print("TOP 10 PRODUCT QUANTITY INCREASES")
    print("=" * 70)

    top_product_increases = (
        product_analysis
        .sort_values(
            "quantity_change",
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
                "beginning_quantity",
                "ending_quantity",
                "quantity_change"
            ]
        ].to_string(
            index=False,
            formatters={
                "beginning_quantity":
                    "{:,.0f}".format,

                "ending_quantity":
                    "{:,.0f}".format,

                "quantity_change":
                    "{:,.0f}".format
            }
        )
    )

    # --------------------------------------------------------
    # TOP PRODUCT DECREASES
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 PRODUCT QUANTITY DECREASES")
    print("=" * 70)

    top_product_decreases = (
        product_analysis
        .sort_values(
            "quantity_change",
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
                "beginning_quantity",
                "ending_quantity",
                "quantity_change"
            ]
        ].to_string(
            index=False,
            formatters={
                "beginning_quantity":
                    "{:,.0f}".format,

                "ending_quantity":
                    "{:,.0f}".format,

                "quantity_change":
                    "{:,.0f}".format
            }
        )
    )

    # --------------------------------------------------------
    # STORE ANALYSIS
    # --------------------------------------------------------

    store_analysis = analyze_stores(
        result
    )

    # --------------------------------------------------------
    # TOP STORE INCREASES
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 STORE INVENTORY INCREASES")
    print("=" * 70)

    top_store_increases = (
        store_analysis
        .sort_values(
            "quantity_change",
            ascending=False
        )
        .head(10)
    )

    print(
        top_store_increases[
            [
                "store_number",
                "beginning_quantity",
                "ending_quantity",
                "quantity_change"
            ]
        ].to_string(
            index=False,
            formatters={
                "beginning_quantity":
                    "{:,.0f}".format,

                "ending_quantity":
                    "{:,.0f}".format,

                "quantity_change":
                    "{:,.0f}".format
            }
        )
    )

    # --------------------------------------------------------
    # TOP STORE DECREASES
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 STORE INVENTORY DECREASES")
    print("=" * 70)

    top_store_decreases = (
        store_analysis
        .sort_values(
            "quantity_change",
            ascending=True
        )
        .head(10)
    )

    print(
        top_store_decreases[
            [
                "store_number",
                "beginning_quantity",
                "ending_quantity",
                "quantity_change"
            ]
        ].to_string(
            index=False,
            formatters={
                "beginning_quantity":
                    "{:,.0f}".format,

                "ending_quantity":
                    "{:,.0f}".format,

                "quantity_change":
                    "{:,.0f}".format
            }
        )
    )

    # --------------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------------

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

    print(
        f"Movement categories: "
        f"{result['movement'].nunique()}"
    )

    calculated_change = (
        ending_quantity
        - beginning_quantity
    )

    print(
        f"Calculated quantity change: "
        f"{calculated_change:,.0f}"
    )

    if calculated_change == quantity_change:

        print(
            "✓ Quantity reconciliation PASSED."
        )

    else:

        print(
            "✗ Quantity reconciliation FAILED."
        )

        raise ValueError(
            "Inventory quantity reconciliation failed."
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
        "\n✓ Phase 9.4.2 completed successfully."
    )