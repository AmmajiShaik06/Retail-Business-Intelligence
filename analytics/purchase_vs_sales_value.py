"""
Phase 9.3.9
Purchase vs Sales Price / Value Analysis

Purpose:
Compare purchase cost per unit with sales value per unit.

Important:
Sales value - purchase value is NOT treated as profit.
This analysis is used to understand value differences only.

Large-table strategy:
- Purchases: 50,000-row chunks
- Sales: sales_id range queries
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1

PURCHASE_CHUNK_SIZE = 50_000
SALES_RANGE_SIZE = 250_000


# ============================================================
# 1. LOAD PURCHASE VALUE BY VENDOR
# ============================================================

def load_purchase_data():

    print("\nLoading purchase value data...")

    query = """
        SELECT
            vendor_number,
            vendor_name,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = %s
    """

    vendor_data = {}

    total_rows = 0

    for chunk in pd.read_sql_query(
        query,
        engine,
        params=(BUSINESS_ID,),
        chunksize=PURCHASE_CHUNK_SIZE
    ):

        total_rows += len(chunk)

        chunk["vendor_number"] = pd.to_numeric(
            chunk["vendor_number"],
            errors="coerce"
        )

        chunk["vendor_name"] = (
            chunk["vendor_name"]
            .astype("string")
            .str.strip()
        )

        chunk["quantity"] = pd.to_numeric(
            chunk["quantity"],
            errors="coerce"
        ).fillna(0)

        chunk["dollars"] = pd.to_numeric(
            chunk["dollars"],
            errors="coerce"
        ).fillna(0)

        grouped = (
            chunk
            .groupby(
                [
                    "vendor_number",
                    "vendor_name"
                ],
                dropna=False
            )
            .agg(
                purchase_quantity=("quantity", "sum"),
                purchase_amount=("dollars", "sum")
            )
            .reset_index()
        )

        for _, row in grouped.iterrows():

            key = (
                row["vendor_number"],
                row["vendor_name"]
            )

            if key not in vendor_data:

                vendor_data[key] = {
                    "purchase_quantity": 0,
                    "purchase_amount": 0
                }

            vendor_data[key]["purchase_quantity"] += (
                row["purchase_quantity"]
            )

            vendor_data[key]["purchase_amount"] += (
                row["purchase_amount"]
            )

    print(
        f"Purchase rows processed: {total_rows:,}"
    )

    return vendor_data


# ============================================================
# 2. GET SALES ID RANGE
# ============================================================

def get_sales_id_range():

    query = """
        SELECT
            MIN(sales_id),
            MAX(sales_id)
        FROM sales
        WHERE business_id = %s
    """

    with engine.connect() as connection:

        result = connection.exec_driver_sql(
            query,
            (BUSINESS_ID,)
        ).fetchone()

    return result[0], result[1]


# ============================================================
# 3. LOAD SALES VALUE BY VENDOR
# ============================================================

def load_sales_data():

    print("\nLoading sales value data...")

    min_id, max_id = get_sales_id_range()

    print(
        f"Sales ID range: {min_id:,} -> {max_id:,}"
    )

    vendor_data = {}

    current_id = min_id

    total_rows = 0

    while current_id <= max_id:

        end_id = min(
            current_id + SALES_RANGE_SIZE - 1,
            max_id
        )

        query = f"""
            SELECT
                vendor_number,
                vendor_name,
                sales_quantity,
                sales_dollars
            FROM sales
            WHERE business_id = %s
              AND sales_id BETWEEN {current_id}
                              AND {end_id}
        """

        with engine.connect() as connection:

            chunk = pd.read_sql_query(
                query,
                connection,
                params=(BUSINESS_ID,)
            )

        if not chunk.empty:

            total_rows += len(chunk)

            chunk["vendor_number"] = pd.to_numeric(
                chunk["vendor_number"],
                errors="coerce"
            )

            chunk["vendor_name"] = (
                chunk["vendor_name"]
                .astype("string")
                .str.strip()
            )

            chunk["sales_quantity"] = pd.to_numeric(
                chunk["sales_quantity"],
                errors="coerce"
            ).fillna(0)

            chunk["sales_dollars"] = pd.to_numeric(
                chunk["sales_dollars"],
                errors="coerce"
            ).fillna(0)

            grouped = (
                chunk
                .groupby(
                    [
                        "vendor_number",
                        "vendor_name"
                    ],
                    dropna=False
                )
                .agg(
                    sales_quantity=("sales_quantity", "sum"),
                    sales_amount=("sales_dollars", "sum")
                )
                .reset_index()
            )

            for _, row in grouped.iterrows():

                key = (
                    row["vendor_number"],
                    row["vendor_name"]
                )

                if key not in vendor_data:

                    vendor_data[key] = {
                        "sales_quantity": 0,
                        "sales_amount": 0
                    }

                vendor_data[key]["sales_quantity"] += (
                    row["sales_quantity"]
                )

                vendor_data[key]["sales_amount"] += (
                    row["sales_amount"]
                )

        current_id = end_id + 1

        print(
            f"Processed sales IDs through {end_id:,}"
        )

    print(
        f"Sales rows processed: {total_rows:,}"
    )

    return vendor_data


# ============================================================
# 4. BUILD COMPARISON
# ============================================================

def build_comparison(
    purchase_data,
    sales_data
):

    all_vendors = (
        set(purchase_data.keys())
        | set(sales_data.keys())
    )

    rows = []

    for vendor_number, vendor_name in all_vendors:

        purchase = purchase_data.get(
            (vendor_number, vendor_name),
            {}
        )

        sales = sales_data.get(
            (vendor_number, vendor_name),
            {}
        )

        purchase_quantity = purchase.get(
            "purchase_quantity",
            0
        )

        purchase_amount = purchase.get(
            "purchase_amount",
            0
        )

        sales_quantity = sales.get(
            "sales_quantity",
            0
        )

        sales_amount = sales.get(
            "sales_amount",
            0
        )

        if purchase_quantity != 0:

            purchase_unit_cost = (
                purchase_amount
                / purchase_quantity
            )

        else:

            purchase_unit_cost = None

        if sales_quantity != 0:

            sales_unit_value = (
                sales_amount
                / sales_quantity
            )

        else:

            sales_unit_value = None

        if (
            purchase_unit_cost is not None
            and sales_unit_value is not None
            and purchase_unit_cost != 0
        ):

            unit_value_ratio = (
                sales_unit_value
                / purchase_unit_cost
            )

            unit_value_difference = (
                sales_unit_value
                - purchase_unit_cost
            )

        else:

            unit_value_ratio = None
            unit_value_difference = None

        rows.append(
            {
                "vendor_number": vendor_number,
                "vendor_name": vendor_name,
                "purchase_quantity": purchase_quantity,
                "purchase_amount": purchase_amount,
                "purchase_unit_cost": purchase_unit_cost,
                "sales_quantity": sales_quantity,
                "sales_amount": sales_amount,
                "sales_unit_value": sales_unit_value,
                "unit_value_difference": unit_value_difference,
                "unit_value_ratio": unit_value_ratio
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# 5. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 9.3.9")
    print("PURCHASE VS SALES PRICE / VALUE ANALYSIS")
    print("=" * 70)

    purchase_data = load_purchase_data()

    sales_data = load_sales_data()

    result = build_comparison(
        purchase_data,
        sales_data
    )

    result = result.sort_values(
        "sales_amount",
        ascending=False
    )

    pd.set_option(
        "display.max_columns",
        None
    )

    pd.set_option(
        "display.width",
        220
    )

    print("\n" + "=" * 70)
    print("VENDOR PURCHASE VS SALES VALUE")
    print("=" * 70)

    print(
        result.head(20).to_string(
            index=False,
            formatters={
                "purchase_quantity": "{:,.0f}".format,
                "purchase_amount": "${:,.2f}".format,
                "purchase_unit_cost": "${:.4f}".format,
                "sales_quantity": "{:,.0f}".format,
                "sales_amount": "${:,.2f}".format,
                "sales_unit_value": "${:.4f}".format,
                "unit_value_difference": "${:.4f}".format,
                "unit_value_ratio": "{:.4f}".format
            }
        )
    )

    # ========================================================
    # TOP UNIT VALUE RATIOS
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP 10 UNIT VALUE RATIOS")
    print("=" * 70)

    ratio_result = (
        result
        .dropna(
            subset=["unit_value_ratio"]
        )
        .sort_values(
            "unit_value_ratio",
            ascending=False
        )
        .head(10)
    )

    print(
        ratio_result[
            [
                "vendor_number",
                "vendor_name",
                "purchase_quantity",
                "purchase_amount",
                "purchase_unit_cost",
                "sales_quantity",
                "sales_amount",
                "sales_unit_value",
                "unit_value_difference",
                "unit_value_ratio"
            ]
        ].to_string(
            index=False,
            formatters={
                "purchase_quantity": "{:,.0f}".format,
                "purchase_amount": "${:,.2f}".format,
                "purchase_unit_cost": "${:.4f}".format,
                "sales_quantity": "{:,.0f}".format,
                "sales_amount": "${:,.2f}".format,
                "sales_unit_value": "${:.4f}".format,
                "unit_value_difference": "${:.4f}".format,
                "unit_value_ratio": "{:.4f}".format
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
        f"Vendors compared: {len(result):,}"
    )

    print(
        f"Total purchase quantity: "
        f"{result['purchase_quantity'].sum():,.0f}"
    )

    print(
        f"Total sales quantity: "
        f"{result['sales_quantity'].sum():,.0f}"
    )

    print(
        f"Total purchase amount: "
        f"${result['purchase_amount'].sum():,.2f}"
    )

    print(
        f"Total sales amount: "
        f"${result['sales_amount'].sum():,.2f}"
    )

    print(
        "\n✓ Purchase vs sales value analysis completed."
    )