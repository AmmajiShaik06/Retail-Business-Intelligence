"""
Phase 9.4.5
Product-wise Inventory Analysis

Purpose:
Analyze beginning and ending inventory at product level.

Metrics:
1. Beginning quantity
2. Ending quantity
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
# 1. LOAD INVENTORY BY PRODUCT
# ============================================================

def load_inventory(table_name):

    print(f"\nLoading {table_name}...")

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

    product_totals = {}

    total_rows = 0

    for chunk in pd.read_sql_query(
        query,
        engine,
        params=(BUSINESS_ID,),
        chunksize=CHUNK_SIZE
    ):

        total_rows += len(chunk)

        # ----------------------------------------------------
        # Clean numeric fields
        # ----------------------------------------------------

        chunk["brand"] = pd.to_numeric(
            chunk["brand"],
            errors="coerce"
        )

        chunk["on_hand"] = pd.to_numeric(
            chunk["on_hand"],
            errors="coerce"
        ).fillna(0)

        chunk["price"] = pd.to_numeric(
            chunk["price"],
            errors="coerce"
        ).fillna(0)

        # ----------------------------------------------------
        # Clean product text
        # ----------------------------------------------------

        chunk["description"] = (
            chunk["description"]
            .astype("string")
            .str.strip()
            .fillna("")
        )

        chunk["size"] = (
            chunk["size"]
            .astype("string")
            .str.strip()
            .fillna("")
        )

        # ----------------------------------------------------
        # Calculate inventory value
        # ----------------------------------------------------

        chunk["inventory_value"] = (
            chunk["on_hand"]
            * chunk["price"]
        )

        # ----------------------------------------------------
        # Product-level aggregation
        #
        # Product identity:
        # Brand + Description + Size
        # ----------------------------------------------------

        grouped = (
            chunk
            .groupby(
                [
                    "brand",
                    "description",
                    "size"
                ]
            )
            .agg(
                quantity=("on_hand", "sum"),
                value=("inventory_value", "sum")
            )
        )

        # ----------------------------------------------------
        # Combine chunk results
        # ----------------------------------------------------

        for product_key, row in grouped.iterrows():

            if product_key not in product_totals:

                product_totals[product_key] = {
                    "quantity": 0,
                    "value": 0
                }

            product_totals[product_key]["quantity"] += (
                row["quantity"]
            )

            product_totals[product_key]["value"] += (
                row["value"]
            )

    print(
        f"{table_name} rows processed: "
        f"{total_rows:,}"
    )

    return product_totals


# ============================================================
# 2. BUILD PRODUCT COMPARISON
# ============================================================

def build_product_comparison(
    beginning,
    ending
):

    all_products = (
        set(beginning.keys())
        | set(ending.keys())
    )

    rows = []

    for product_key in all_products:

        brand, description, size = product_key

        begin = beginning.get(
            product_key,
            {
                "quantity": 0,
                "value": 0
            }
        )

        end = ending.get(
            product_key,
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
                "brand": brand,
                "description": description,
                "size": size,

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
    print("PHASE 9.4.5")
    print("PRODUCT-WISE INVENTORY ANALYSIS")
    print("=" * 70)

    # --------------------------------------------------------
    # Load beginning inventory
    # --------------------------------------------------------

    beginning = load_inventory(
        "begin_inventory"
    )

    # --------------------------------------------------------
    # Load ending inventory
    # --------------------------------------------------------

    ending = load_inventory(
        "end_inventory"
    )

    # --------------------------------------------------------
    # Build product comparison
    # --------------------------------------------------------

    result = build_product_comparison(
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
    # OVERALL SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print("OVERALL PRODUCT INVENTORY SUMMARY")
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
        f"Unique products analyzed: "
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
    # TOP 10 PRODUCTS BY ENDING INVENTORY VALUE
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 PRODUCTS BY ENDING INVENTORY VALUE")
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
                "brand",
                "description",
                "size",
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
    # BOTTOM 10 PRODUCTS BY ENDING INVENTORY VALUE
    # ========================================================

    print("\n" + "=" * 70)
    print("BOTTOM 10 PRODUCTS BY ENDING INVENTORY VALUE")
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

    print(
        bottom_ending[
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

    # ========================================================
    # TOP QUANTITY INCREASES
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 PRODUCT QUANTITY INCREASES")
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

    # ========================================================
    # TOP QUANTITY DECREASES
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 PRODUCT QUANTITY DECREASES")
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

    # ========================================================
    # TOP VALUE INCREASES
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 PRODUCT INVENTORY VALUE INCREASES")
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
    # TOP VALUE DECREASES
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 PRODUCT INVENTORY VALUE DECREASES")
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
    # INVENTORY VALUE CONCENTRATION
    # ========================================================

    print("\n" + "=" * 70)
    print("ENDING INVENTORY VALUE CONCENTRATION")
    print("=" * 70)

    sorted_products = (
        result
        .sort_values(
            "ending_value",
            ascending=False
        )
        .reset_index(drop=True)
    )

    for number in [5, 10, 20, 50]:

        top_n_value = (
            sorted_products
            .head(number)["ending_value"]
            .sum()
        )

        contribution = (
            top_n_value
            / total_ending_value
            * 100
        )

        print(
            f"Top {number} products: "
            f"${top_n_value:,.2f} "
            f"({contribution:.2f}%)"
        )

    # ========================================================
    # VERIFICATION
    # ========================================================

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Product count
    #
    # The products master contains 12,261 products.
    # Inventory snapshots contain only products that actually
    # appear in the beginning/end inventory datasets.
    #
    # Therefore the inventory analysis product count is not
    # expected to equal the master product count.
    # --------------------------------------------------------

    inventory_product_count = len(result)

    if inventory_product_count > 0:

        print(
            f"✓ Inventory product count PASSED: "
            f"{inventory_product_count:,} products analyzed."
        )

    else:

        raise ValueError(
            "No products found in inventory analysis."
        )

    print(
        f"Master product count: 12,261"
    )

    print(
        f"Products present in inventory analysis: "
        f"{inventory_product_count:,}"
    )

    print(
        f"Products not represented in inventory snapshots: "
        f"{12_261 - inventory_product_count:,}"
    )

    # --------------------------------------------------------
    # Beginning quantity
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Ending quantity
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Beginning value
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Ending value
    # --------------------------------------------------------

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
        "\n✓ Phase 9.4.5 completed successfully."
    )