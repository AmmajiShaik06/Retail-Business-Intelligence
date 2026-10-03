"""
Phase 9.3.8
Monthly Purchase Quantity vs Sales Quantity

Purpose:
Compare monthly purchases and sales for the same 2024 period.

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
# 1. LOAD MONTHLY PURCHASE DATA
# ============================================================

def load_monthly_purchases():

    print("\nLoading monthly purchase data...")

    query = """
        SELECT
            po_date,
            quantity,
            dollars
        FROM purchases
        WHERE business_id = %s
          AND po_date >= '2024-01-01'
          AND po_date < '2025-01-01'
    """

    monthly = {}

    total_rows = 0

    for chunk in pd.read_sql_query(
        query,
        engine,
        params=(BUSINESS_ID,),
        chunksize=PURCHASE_CHUNK_SIZE
    ):

        total_rows += len(chunk)

        chunk["po_date"] = pd.to_datetime(
            chunk["po_date"],
            errors="coerce"
        )

        chunk["quantity"] = pd.to_numeric(
            chunk["quantity"],
            errors="coerce"
        ).fillna(0)

        chunk["dollars"] = pd.to_numeric(
            chunk["dollars"],
            errors="coerce"
        ).fillna(0)

        chunk["month"] = (
            chunk["po_date"]
            .dt.to_period("M")
            .astype(str)
        )

        grouped = (
            chunk
            .groupby("month")
            .agg(
                purchase_quantity=("quantity", "sum"),
                purchase_amount=("dollars", "sum")
            )
        )

        for month, row in grouped.iterrows():

            if month not in monthly:

                monthly[month] = {
                    "purchase_quantity": 0,
                    "purchase_amount": 0
                }

            monthly[month]["purchase_quantity"] += (
                row["purchase_quantity"]
            )

            monthly[month]["purchase_amount"] += (
                row["purchase_amount"]
            )

    print(
        f"Purchase rows processed: {total_rows:,}"
    )

    return monthly


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
# 3. LOAD MONTHLY SALES DATA
# ============================================================

def load_monthly_sales():

    print("\nLoading monthly sales data...")

    min_id, max_id = get_sales_id_range()

    print(
        f"Sales ID range: {min_id:,} -> {max_id:,}"
    )

    monthly = {}

    current_id = min_id

    total_rows = 0

    while current_id <= max_id:

        end_id = min(
            current_id + SALES_RANGE_SIZE - 1,
            max_id
        )

        query = f"""
            SELECT
                sales_date,
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

            chunk["sales_date"] = pd.to_datetime(
                chunk["sales_date"],
                errors="coerce"
            )

            chunk["sales_quantity"] = pd.to_numeric(
                chunk["sales_quantity"],
                errors="coerce"
            ).fillna(0)

            chunk["sales_dollars"] = pd.to_numeric(
                chunk["sales_dollars"],
                errors="coerce"
            ).fillna(0)

            chunk["month"] = (
                chunk["sales_date"]
                .dt.to_period("M")
                .astype(str)
            )

            grouped = (
                chunk
                .groupby("month")
                .agg(
                    sales_quantity=("sales_quantity", "sum"),
                    sales_amount=("sales_dollars", "sum")
                )
            )

            for month, row in grouped.iterrows():

                if month not in monthly:

                    monthly[month] = {
                        "sales_quantity": 0,
                        "sales_amount": 0
                    }

                monthly[month]["sales_quantity"] += (
                    row["sales_quantity"]
                )

                monthly[month]["sales_amount"] += (
                    row["sales_amount"]
                )

        current_id = end_id + 1

        print(
            f"Processed sales IDs through {end_id:,}"
        )

    print(
        f"Sales rows processed: {total_rows:,}"
    )

    return monthly


# ============================================================
# 4. COMBINE PURCHASE + SALES
# ============================================================

def build_comparison(
    purchase_data,
    sales_data
):

    months = sorted(
        set(purchase_data.keys())
        | set(sales_data.keys())
    )

    rows = []

    for month in months:

        purchase_quantity = purchase_data.get(
            month,
            {}
        ).get(
            "purchase_quantity",
            0
        )

        purchase_amount = purchase_data.get(
            month,
            {}
        ).get(
            "purchase_amount",
            0
        )

        sales_quantity = sales_data.get(
            month,
            {}
        ).get(
            "sales_quantity",
            0
        )

        sales_amount = sales_data.get(
            month,
            {}
        ).get(
            "sales_amount",
            0
        )

        quantity_difference = (
            sales_quantity
            - purchase_quantity
        )

        amount_difference = (
            sales_amount
            - purchase_amount
        )

        if purchase_quantity != 0:

            quantity_ratio = (
                sales_quantity
                / purchase_quantity
            )

        else:

            quantity_ratio = None

        if purchase_amount != 0:

            amount_ratio = (
                sales_amount
                / purchase_amount
            )

        else:

            amount_ratio = None

        rows.append(
            {
                "month": month,
                "purchase_quantity": purchase_quantity,
                "sales_quantity": sales_quantity,
                "quantity_difference": quantity_difference,
                "quantity_ratio": quantity_ratio,
                "purchase_amount": purchase_amount,
                "sales_amount": sales_amount,
                "amount_difference": amount_difference,
                "amount_ratio": amount_ratio
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# 5. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 9.3.8")
    print("MONTHLY PURCHASE VS SALES ANALYSIS")
    print("=" * 70)

    purchase_data = load_monthly_purchases()

    sales_data = load_monthly_sales()

    result = build_comparison(
        purchase_data,
        sales_data
    )

    pd.set_option(
        "display.max_columns",
        None
    )

    pd.set_option(
        "display.width",
        200
    )

    print("\n" + "=" * 70)
    print("MONTHLY PURCHASE VS SALES")
    print("=" * 70)

    print(
        result.to_string(
            index=False,
            formatters={
                "purchase_quantity": "{:,.0f}".format,
                "sales_quantity": "{:,.0f}".format,
                "quantity_difference": "{:,.0f}".format,
                "quantity_ratio": "{:.4f}".format,
                "purchase_amount": "${:,.2f}".format,
                "sales_amount": "${:,.2f}".format,
                "amount_difference": "${:,.2f}".format,
                "amount_ratio": "{:.4f}".format
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
        f"Months analyzed: {len(result)}"
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
        f"Total quantity difference: "
        f"{result['quantity_difference'].sum():,.0f}"
    )

    print(
        f"Total amount difference: "
        f"${result['amount_difference'].sum():,.2f}"
    )

    print(
        "\n✓ Monthly purchase vs sales analysis completed."
    )