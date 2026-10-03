"""
Phase 9.4.4
Store-wise Inventory Analysis

Purpose:
Analyze inventory quantity and inventory value
at the store level.

Metrics:
1. Beginning inventory quantity
2. Ending inventory quantity
3. Quantity change
4. Beginning inventory value
5. Ending inventory value
6. Inventory value change
7. Ending inventory value contribution
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


# ============================================================
# 1. LOAD INVENTORY BY STORE
# ============================================================

def load_inventory(table_name):

    print(f"\nLoading {table_name}...")

    query = f"""
        SELECT
            store_number,
            on_hand,
            price
        FROM {table_name}
        WHERE business_id = %s
    """

    store_totals = {}

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

        grouped = (
            chunk
            .groupby("store_number")
            .agg(
                quantity=("on_hand", "sum"),
                value=("inventory_value", "sum")
            )
        )

        for store_number, row in grouped.iterrows():

            if store_number not in store_totals:

                store_totals[store_number] = {
                    "quantity": 0,
                    "value": 0
                }

            store_totals[store_number]["quantity"] += (
                row["quantity"]
            )

            store_totals[store_number]["value"] += (
                row["value"]
            )

    print(
        f"{table_name} rows processed: "
        f"{total_rows:,}"
    )

    return store_totals


# ============================================================
# 2. BUILD STORE COMPARISON
# ============================================================

def build_store_comparison(
    beginning,
    ending
):

    all_stores = (
        set(beginning.keys())
        | set(ending.keys())
    )

    rows = []

    for store_number in all_stores:

        begin = beginning.get(
            store_number,
            {
                "quantity": 0,
                "value": 0
            }
        )

        end = ending.get(
            store_number,
            {
                "quantity": 0,
                "value": 0
            }
        )

        beginning_quantity = begin["quantity"]
        ending_quantity = end["quantity"]

        beginning_value = begin["value"]
        ending_value = end["value"]

        quantity_change = (
            ending_quantity
            - beginning_quantity
        )

        value_change = (
            ending_value
            - beginning_value
        )

        rows.append(
            {
                "store_number": store_number,

                "beginning_quantity":
                    beginning_quantity,

                "ending_quantity":
                    ending_quantity,

                "quantity_change":
                    quantity_change,

                "beginning_value":
                    beginning_value,

                "ending_value":
                    ending_value,

                "value_change":
                    value_change
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# 3. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 9.4.4")
    print("STORE-WISE INVENTORY ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # Load inventory
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

    result = build_store_comparison(
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

    # ========================================================
    # OVERALL SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("OVERALL STORE INVENTORY SUMMARY")
    print("=" * 70)

    total_beginning_quantity = (
        result["beginning_quantity"]
        .sum()
    )

    total_ending_quantity = (
        result["ending_quantity"]
        .sum()
    )

    total_beginning_value = (
        result["beginning_value"]
        .sum()
    )

    total_ending_value = (
        result["ending_value"]
        .sum()
    )

    print(
        f"Total stores analyzed: "
        f"{len(result):,}"
    )

    print(
        f"Beginning inventory quantity: "
        f"{total_beginning_quantity:,.0f}"
    )

    print(
        f"Ending inventory quantity: "
        f"{total_ending_quantity:,.0f}"
    )

    print(
        f"Beginning inventory value: "
        f"${total_beginning_value:,.2f}"
    )

    print(
        f"Ending inventory value: "
        f"${total_ending_value:,.2f}"
    )

    # ========================================================
    # TOP STORES BY ENDING VALUE
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 STORES BY ENDING INVENTORY VALUE")
    print("=" * 70)

    top_ending = (
        result
        .sort_values(
            "ending_value",
            ascending=False
        )
        .head(10)
        .copy()
    )

    top_ending["value_contribution_pct"] = (
        top_ending["ending_value"]
        / total_ending_value
        * 100
    )

    print(
        top_ending[
            [
                "store_number",
                "ending_quantity",
                "ending_value",
                "value_contribution_pct"
            ]
        ].to_string(
            index=False,
            formatters={
                "ending_quantity":
                    "{:,.0f}".format,

                "ending_value":
                    "${:,.2f}".format,

                "value_contribution_pct":
                    "{:.2f}%".format
            }
        )
    )

    # ========================================================
    # LOWEST STORES BY ENDING VALUE
    # ========================================================

    print("\n" + "=" * 70)
    print("BOTTOM 10 STORES BY ENDING INVENTORY VALUE")
    print("=" * 70)

    bottom_ending = (
        result
        .sort_values(
            "ending_value",
            ascending=True
        )
        .head(10)
        .copy()
    )

    bottom_ending["value_contribution_pct"] = (
        bottom_ending["ending_value"]
        / total_ending_value
        * 100
    )

    print(
        bottom_ending[
            [
                "store_number",
                "ending_quantity",
                "ending_value",
                "value_contribution_pct"
            ]
        ].to_string(
            index=False,
            formatters={
                "ending_quantity":
                    "{:,.0f}".format,

                "ending_value":
                    "${:,.2f}".format,

                "value_contribution_pct":
                    "{:.2f}%".format
            }
        )
    )

    # ========================================================
    # TOP STORE QUANTITY INCREASES
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 STORE QUANTITY INCREASES")
    print("=" * 70)

    top_quantity_increases = (
        result
        .sort_values(
            "quantity_change",
            ascending=False
        )
        .head(10)
    )

    print(
        top_quantity_increases[
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

    # ========================================================
    # TOP STORE QUANTITY DECREASES
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 STORE QUANTITY DECREASES")
    print("=" * 70)

    top_quantity_decreases = (
        result
        .sort_values(
            "quantity_change",
            ascending=True
        )
        .head(10)
    )

    print(
        top_quantity_decreases[
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

    # ========================================================
    # TOP STORE VALUE INCREASES
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 STORE VALUE INCREASES")
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
    # TOP STORE VALUE DECREASES
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 STORE VALUE DECREASES")
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
    # CONCENTRATION ANALYSIS
    # ========================================================

    print("\n" + "=" * 70)
    print("ENDING INVENTORY VALUE CONCENTRATION")
    print("=" * 70)

    sorted_stores = (
        result
        .sort_values(
            "ending_value",
            ascending=False
        )
        .reset_index(drop=True)
    )

    for number in [5, 10, 20]:

        top_n_value = (
            sorted_stores
            .head(number)["ending_value"]
            .sum()
        )

        contribution = (
            top_n_value
            / total_ending_value
            * 100
        )

        print(
            f"Top {number} stores: "
            f"${top_n_value:,.2f} "
            f"({contribution:.2f}%)"
        )

    # ========================================================
    # VERIFICATION
    # ========================================================

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    expected_stores = 80

    if len(result) == expected_stores:

        print(
            "✓ Store count PASSED."
        )

    else:

        print(
            f"✗ Store count FAILED. "
            f"Expected {expected_stores}, "
            f"got {len(result)}."
        )

        raise ValueError(
            "Unexpected store count."
        )

    if abs(
        total_beginning_quantity
        - 4_219_275
    ) < 0.01:

        print(
            "✓ Beginning quantity PASSED."
        )

    else:

        raise ValueError(
            "Beginning quantity mismatch."
        )

    if abs(
        total_ending_quantity
        - 4_885_776
    ) < 0.01:

        print(
            "✓ Ending quantity PASSED."
        )

    else:

        raise ValueError(
            "Ending quantity mismatch."
        )

    if abs(
        total_beginning_value
        - 68_053_780.17
    ) < 0.01:

        print(
            "✓ Beginning value PASSED."
        )

    else:

        raise ValueError(
            "Beginning value mismatch."
        )

    if abs(
        total_ending_value
        - 79_704_851.13
    ) < 0.01:

        print(
            "✓ Ending value PASSED."
        )

    else:

        raise ValueError(
            "Ending value mismatch."
        )

    print(
        "\n✓ Phase 9.4.4 completed successfully."
    )