"""
Phase 9.4.1
Beginning vs Ending Inventory Analysis

Purpose:
Compare beginning inventory and ending inventory
for the retail business.

Beginning inventory:
    January 1, 2024

Ending inventory:
    December 31, 2024

Inventory value:
    on_hand * price

Large-table strategy:
    Process inventory tables in chunks.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


# ============================================================
# 1. LOAD BEGINNING INVENTORY
# ============================================================

def load_beginning_inventory():

    print("\nLoading beginning inventory...")

    query = """
        SELECT
            inventory_id,
            store_number,
            brand,
            description,
            size,
            on_hand,
            price,
            start_date
        FROM begin_inventory
        WHERE business_id = %s
    """

    inventory = {}

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

            inventory[inventory_id] = {
                "store_number": row["store_number"],
                "brand": row["brand"],
                "description": row["description"],
                "size": row["size"],
                "on_hand": row["on_hand"],
                "price": row["price"],
                "inventory_value": row["inventory_value"]
            }

    print(
        f"Beginning inventory rows processed: "
        f"{total_rows:,}"
    )

    return inventory


# ============================================================
# 2. LOAD ENDING INVENTORY
# ============================================================

def load_ending_inventory():

    print("\nLoading ending inventory...")

    query = """
        SELECT
            inventory_id,
            store_number,
            brand,
            description,
            size,
            on_hand,
            price,
            end_date
        FROM end_inventory
        WHERE business_id = %s
    """

    inventory = {}

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

            inventory[inventory_id] = {
                "store_number": row["store_number"],
                "brand": row["brand"],
                "description": row["description"],
                "size": row["size"],
                "on_hand": row["on_hand"],
                "price": row["price"],
                "inventory_value": row["inventory_value"]
            }

    print(
        f"Ending inventory rows processed: "
        f"{total_rows:,}"
    )

    return inventory


# ============================================================
# 3. BUILD BEGINNING VS ENDING COMPARISON
# ============================================================

def build_comparison(
    beginning,
    ending
):

    all_inventory_ids = (
        set(beginning.keys())
        | set(ending.keys())
    )

    rows = []

    for inventory_id in all_inventory_ids:

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

        quantity_change = (
            ending_quantity
            - beginning_quantity
        )

        value_change = (
            ending_value
            - beginning_value
        )

        if inventory_id in beginning and inventory_id in ending:

            status = "Present in both"

        elif inventory_id in beginning:

            status = "Beginning only"

        else:

            status = "Ending only"

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
                "beginning_quantity": beginning_quantity,
                "ending_quantity": ending_quantity,
                "quantity_change": quantity_change,
                "beginning_value": beginning_value,
                "ending_value": ending_value,
                "value_change": value_change,
                "status": status
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# 4. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 9.4.1")
    print("BEGINNING VS ENDING INVENTORY ANALYSIS")
    print("=" * 70)

    beginning = load_beginning_inventory()

    ending = load_ending_inventory()

    result = build_comparison(
        beginning,
        ending
    )

    # --------------------------------------------------------
    # Basic display settings
    # --------------------------------------------------------

    pd.set_option(
        "display.max_columns",
        None
    )

    pd.set_option(
        "display.width",
        220
    )

    # --------------------------------------------------------
    # Overall summary
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("OVERALL INVENTORY SUMMARY")
    print("=" * 70)

    beginning_quantity = result[
        "beginning_quantity"
    ].sum()

    ending_quantity = result[
        "ending_quantity"
    ].sum()

    beginning_value = result[
        "beginning_value"
    ].sum()

    ending_value = result[
        "ending_value"
    ].sum()

    quantity_change = (
        ending_quantity
        - beginning_quantity
    )

    value_change = (
        ending_value
        - beginning_value
    )

    print(
        f"Beginning inventory quantity: "
        f"{beginning_quantity:,.0f}"
    )

    print(
        f"Ending inventory quantity: "
        f"{ending_quantity:,.0f}"
    )

    print(
        f"Inventory quantity change: "
        f"{quantity_change:,.0f}"
    )

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

    # --------------------------------------------------------
    # Inventory ID comparison
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("INVENTORY ID COMPARISON")
    print("=" * 70)

    status_counts = (
        result["status"]
        .value_counts()
    )

    print(
        f"Present in both: "
        f"{status_counts.get('Present in both', 0):,}"
    )

    print(
        f"Beginning only: "
        f"{status_counts.get('Beginning only', 0):,}"
    )

    print(
        f"Ending only: "
        f"{status_counts.get('Ending only', 0):,}"
    )

    # --------------------------------------------------------
    # Quantity increase
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 INVENTORY QUANTITY INCREASES")
    print("=" * 70)

    top_increases = (
        result
        .sort_values(
            "quantity_change",
            ascending=False
        )
        .head(10)
    )

    print(
        top_increases[
            [
                "inventory_id",
                "store_number",
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
                "beginning_quantity": "{:,.0f}".format,
                "ending_quantity": "{:,.0f}".format,
                "quantity_change": "{:,.0f}".format
            }
        )
    )

    # --------------------------------------------------------
    # Quantity decrease
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 INVENTORY QUANTITY DECREASES")
    print("=" * 70)

    top_decreases = (
        result
        .sort_values(
            "quantity_change",
            ascending=True
        )
        .head(10)
    )

    print(
        top_decreases[
            [
                "inventory_id",
                "store_number",
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
                "beginning_quantity": "{:,.0f}".format,
                "ending_quantity": "{:,.0f}".format,
                "quantity_change": "{:,.0f}".format
            }
        )
    )

    # --------------------------------------------------------
    # Value increase
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 INVENTORY VALUE INCREASES")
    print("=" * 70)

    top_value_increases = (
        result
        .sort_values(
            "value_change",
            ascending=False
        )
        .head(10)
    )

    print(
        top_value_increases[
            [
                "inventory_id",
                "store_number",
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
                "beginning_value": "${:,.2f}".format,
                "ending_value": "${:,.2f}".format,
                "value_change": "${:,.2f}".format
            }
        )
    )

    # --------------------------------------------------------
    # Value decrease
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("TOP 10 INVENTORY VALUE DECREASES")
    print("=" * 70)

    top_value_decreases = (
        result
        .sort_values(
            "value_change",
            ascending=True
        )
        .head(10)
    )

    print(
        top_value_decreases[
            [
                "inventory_id",
                "store_number",
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
                "beginning_value": "${:,.2f}".format,
                "ending_value": "${:,.2f}".format,
                "value_change": "${:,.2f}".format
            }
        )
    )

    # --------------------------------------------------------
    # Verification
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
        f"Unique inventory IDs compared: "
        f"{len(result):,}"
    )

    print(
        f"Beginning-only IDs: "
        f"{(result['status'] == 'Beginning only').sum():,}"
    )

    print(
        f"Ending-only IDs: "
        f"{(result['status'] == 'Ending only').sum():,}"
    )

    print(
        f"IDs present in both: "
        f"{(result['status'] == 'Present in both').sum():,}"
    )

    print(
        "\n✓ Beginning vs ending inventory analysis completed."
    )