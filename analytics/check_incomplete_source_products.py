
"""
Incomplete Source Product Diagnostic

Purpose:
Identify source rows with missing fields required to construct
a product identity.

This script does NOT modify the database.
"""

import pandas as pd

from database.connection import engine


BUSINESS_ID = 1


# ============================================================
# 1. TABLE-SPECIFIC QUERIES
# ============================================================

QUERIES = {

    "sales": """
        SELECT
            brand,
            description,
            size,
            SUM(sales_quantity) AS quantity_total,
            SUM(sales_dollars) AS value_total
        FROM sales
        WHERE business_id = %s
          AND (
                brand IS NULL
                OR description IS NULL
                OR size IS NULL
              )
        GROUP BY
            brand,
            description,
            size
        ORDER BY
            brand,
            description,
            size
    """,

    "purchases": """
        SELECT
            brand,
            description,
            size,
            SUM(quantity) AS quantity_total,
            SUM(dollars) AS value_total
        FROM purchases
        WHERE business_id = %s
          AND (
                brand IS NULL
                OR description IS NULL
                OR size IS NULL
              )
        GROUP BY
            brand,
            description,
            size
        ORDER BY
            brand,
            description,
            size
    """,

    "begin_inventory": """
        SELECT
            brand,
            description,
            size,
            SUM(on_hand) AS quantity_total,
            SUM(on_hand * price) AS value_total
        FROM begin_inventory
        WHERE business_id = %s
          AND (
                brand IS NULL
                OR description IS NULL
                OR size IS NULL
              )
        GROUP BY
            brand,
            description,
            size
        ORDER BY
            brand,
            description,
            size
    """,

    "end_inventory": """
        SELECT
            brand,
            description,
            size,
            SUM(on_hand) AS quantity_total,
            SUM(on_hand * price) AS value_total
        FROM end_inventory
        WHERE business_id = %s
          AND (
                brand IS NULL
                OR description IS NULL
                OR size IS NULL
              )
        GROUP BY
            brand,
            description,
            size
        ORDER BY
            brand,
            description,
            size
    """
}


# ============================================================
# 2. CHECK TABLE
# ============================================================

def check_table(table_name):

    query = QUERIES[table_name]

    with engine.connect() as connection:

        return pd.read_sql_query(
            query,
            connection,
            params=(BUSINESS_ID,)
        )


# ============================================================
# 3. MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("INCOMPLETE SOURCE PRODUCT DIAGNOSTIC")
    print("=" * 70)

    for table_name in QUERIES:

        print("\n" + "-" * 70)
        print(table_name.upper())
        print("-" * 70)

        result = check_table(
            table_name
        )

        if result.empty:

            print(
                "✓ No incomplete product identities found."
            )

        else:

            print(
                f"Incomplete product groups: "
                f"{len(result):,}"
            )

            print()

            print(
                result.to_string(
                    index=False
                )
            )

    print("\n" + "=" * 70)
    print(
        "INCOMPLETE SOURCE PRODUCT DIAGNOSTIC COMPLETED"
    )
    print("=" * 70)
