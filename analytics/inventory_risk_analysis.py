"""
Phase 9.4.6
Inventory Risk Analysis

Purpose:
Identify inventory risk signals at product level.

Risk signals:
1. Zero ending inventory
2. Large inventory decrease
3. Large inventory increase
4. High ending inventory value
5. Large inventory value decrease
6. Large inventory value increase

Important:
These are analytical signals, NOT automatic business conclusions.
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
        # Numeric conversion
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
        # Text conversion
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
        # Inventory value
        # ----------------------------------------------------

        chunk["inventory_value"] = (
            chunk["on_hand"]
            * chunk["price"]
        )

        # ----------------------------------------------------
        # Aggregate by product
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
# 2. BUILD PRODUCT INVENTORY COMPARISON
# ============================================================

def build_comparison(
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
    print("PHASE 9.4.6")
    print("INVENTORY RISK ANALYSIS")
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
    # RISK THRESHOLDS
    # ========================================================

    # These thresholds are based on the verified inventory
    # distribution rather than arbitrary business assumptions.

    quantity_decrease_threshold = (
        result["quantity_change"]
        .quantile(0.01)
    )

    quantity_increase_threshold = (
        result["quantity_change"]
        .quantile(0.99)
    )

    value_decrease_threshold = (
        result["value_change"]
        .quantile(0.01)
    )

    value_increase_threshold = (
        result["value_change"]
        .quantile(0.99)
    )

    ending_value_threshold = (
        result["ending_value"]
        .quantile(0.99)
    )

    print("\n" + "=" * 70)
    print("RISK THRESHOLDS")
    print("=" * 70)

    print(
        f"Large quantity decrease threshold: "
        f"{quantity_decrease_threshold:,.0f}"
    )

    print(
        f"Large quantity increase threshold: "
        f"{quantity_increase_threshold:,.0f}"
    )

    print(
        f"Large value decrease threshold: "
        f"${value_decrease_threshold:,.2f}"
    )

    print(
        f"Large value increase threshold: "
        f"${value_increase_threshold:,.2f}"
    )

    print(
        f"High ending inventory value threshold: "
        f"${ending_value_threshold:,.2f}"
    )

    # ========================================================
    # 1. ZERO ENDING INVENTORY
    # ========================================================

    print("\n" + "=" * 70)
    print("ZERO ENDING INVENTORY")
    print("=" * 70)

    zero_ending = (
        result[
            result["ending_quantity"] == 0
        ]
        .sort_values(
            "beginning_quantity",
            ascending=False
        )
    )

    print(
        f"Products with zero ending quantity: "
        f"{len(zero_ending):,}"
    )

    print(
        zero_ending[
            [
                "brand",
                "description",
                "size",
                "beginning_quantity",
                "ending_quantity",
                "quantity_change"
            ]
        ]
        .head(20)
        .to_string(
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
    # 2. LARGE QUANTITY DECREASE
    # ========================================================

    print("\n" + "=" * 70)
    print("LARGE QUANTITY DECREASE")
    print("=" * 70)

    large_quantity_decrease = (
        result[
            result["quantity_change"]
            <= quantity_decrease_threshold
        ]
        .sort_values(
            "quantity_change",
            ascending=True
        )
    )

    print(
        f"Products flagged: "
        f"{len(large_quantity_decrease):,}"
    )

    print(
        large_quantity_decrease[
            [
                "brand",
                "description",
                "size",
                "beginning_quantity",
                "ending_quantity",
                "quantity_change"
            ]
        ]
        .head(20)
        .to_string(
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
    # 3. LARGE QUANTITY INCREASE
    # ========================================================

    print("\n" + "=" * 70)
    print("LARGE QUANTITY INCREASE")
    print("=" * 70)

    large_quantity_increase = (
        result[
            result["quantity_change"]
            >= quantity_increase_threshold
        ]
        .sort_values(
            "quantity_change",
            ascending=False
        )
    )

    print(
        f"Products flagged: "
        f"{len(large_quantity_increase):,}"
    )

    print(
        large_quantity_increase[
            [
                "brand",
                "description",
                "size",
                "beginning_quantity",
                "ending_quantity",
                "quantity_change"
            ]
        ]
        .head(20)
        .to_string(
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
    # 4. HIGH ENDING INVENTORY VALUE
    # ========================================================

    print("\n" + "=" * 70)
    print("HIGH ENDING INVENTORY VALUE")
    print("=" * 70)

    high_ending_value = (
        result[
            result["ending_value"]
            >= ending_value_threshold
        ]
        .sort_values(
            "ending_value",
            ascending=False
        )
    )

    print(
        f"Products flagged: "
        f"{len(high_ending_value):,}"
    )

    print(
        high_ending_value[
            [
                "brand",
                "description",
                "size",
                "ending_quantity",
                "ending_value"
            ]
        ]
        .head(20)
        .to_string(
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
    # 5. LARGE INVENTORY VALUE DECREASE
    # ========================================================

    print("\n" + "=" * 70)
    print("LARGE INVENTORY VALUE DECREASE")
    print("=" * 70)

    large_value_decrease = (
        result[
            result["value_change"]
            <= value_decrease_threshold
        ]
        .sort_values(
            "value_change",
            ascending=True
        )
    )

    print(
        f"Products flagged: "
        f"{len(large_value_decrease):,}"
    )

    print(
        large_value_decrease[
            [
                "brand",
                "description",
                "size",
                "beginning_value",
                "ending_value",
                "value_change"
            ]
        ]
        .head(20)
        .to_string(
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
    # 6. LARGE INVENTORY VALUE INCREASE
    # ========================================================

    print("\n" + "=" * 70)
    print("LARGE INVENTORY VALUE INCREASE")
    print("=" * 70)

    large_value_increase = (
        result[
            result["value_change"]
            >= value_increase_threshold
        ]
        .sort_values(
            "value_change",
            ascending=False
        )
    )

    print(
        f"Products flagged: "
        f"{len(large_value_increase):,}"
    )

    print(
        large_value_increase[
            [
                "brand",
                "description",
                "size",
                "beginning_value",
                "ending_value",
                "value_change"
            ]
        ]
        .head(20)
        .to_string(
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
    # 7. COMBINED HIGH-RISK SIGNALS
    # ========================================================

    result["risk_signal_count"] = 0

    result.loc[
        result["ending_quantity"] == 0,
        "risk_signal_count"
    ] += 1

    result.loc[
        result["quantity_change"]
        <= quantity_decrease_threshold,
        "risk_signal_count"
    ] += 1

    result.loc[
        result["quantity_change"]
        >= quantity_increase_threshold,
        "risk_signal_count"
    ] += 1

    result.loc[
        result["ending_value"]
        >= ending_value_threshold,
        "risk_signal_count"
    ] += 1

    result.loc[
        result["value_change"]
        <= value_decrease_threshold,
        "risk_signal_count"
    ] += 1

    result.loc[
        result["value_change"]
        >= value_increase_threshold,
        "risk_signal_count"
    ] += 1

    print("\n" + "=" * 70)
    print("PRODUCTS WITH MULTIPLE RISK SIGNALS")
    print("=" * 70)

    multiple_signals = (
        result[
            result["risk_signal_count"] >= 2
        ]
        .sort_values(
            [
                "risk_signal_count",
                "ending_value"
            ],
            ascending=[
                False,
                False
            ]
        )
    )

    print(
        f"Products with 2+ signals: "
        f"{len(multiple_signals):,}"
    )

    print(
        multiple_signals[
            [
                "brand",
                "description",
                "size",
                "beginning_quantity",
                "ending_quantity",
                "quantity_change",
                "ending_value",
                "value_change",
                "risk_signal_count"
            ]
        ]
        .head(20)
        .to_string(
            index=False,
            formatters={
                "beginning_quantity":
                    "{:,.0f}".format,

                "ending_quantity":
                    "{:,.0f}".format,

                "quantity_change":
                    "{:,.0f}".format,

                "ending_value":
                    "${:,.2f}".format,

                "value_change":
                    "${:,.2f}".format
            }
        )
    )

    # ========================================================
    # 8. VERIFICATION
    # ========================================================

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Product count
    # --------------------------------------------------------

    if len(result) == 10_878:

        print(
            "✓ Inventory product count PASSED."
        )

    else:

        raise ValueError(
            f"Inventory product count mismatch. "
            f"Expected 10,878, got {len(result)}."
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

    if abs(
        beginning_quantity
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
        ending_quantity
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
    # Inventory values
    # --------------------------------------------------------

    beginning_value = (
        result["beginning_value"]
        .sum()
    )

    ending_value = (
        result["ending_value"]
        .sum()
    )

    if abs(
        beginning_value
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
        ending_value
        - 79_704_851.13
    ) < 0.01:

        print(
            "✓ Ending value PASSED."
        )

    else:

        raise ValueError(
            "Ending value mismatch."
        )

    # --------------------------------------------------------
    # No negative inventory quantities
    # --------------------------------------------------------

    if (
        result["beginning_quantity"] < 0
    ).any():

        raise ValueError(
            "Negative beginning inventory detected."
        )

    print(
        "✓ Beginning inventory non-negative PASSED."
    )

    if (
        result["ending_quantity"] < 0
    ).any():

        raise ValueError(
            "Negative ending inventory detected."
        )

    print(
        "✓ Ending inventory non-negative PASSED."
    )

    print(
        "\n✓ Phase 9.4.6 completed successfully."
    )