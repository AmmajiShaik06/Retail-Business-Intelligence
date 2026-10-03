import pandas as pd
from sqlalchemy import text
from database.connection import engine


BUSINESS_ID = 1
CHUNK_SIZE = 50_000


def calculate_purchase_kpis():
    query = """
        SELECT
            quantity,
            dollars
        FROM purchases
        WHERE business_id = :business_id
    """

    total_rows = 0
    total_quantity = 0
    total_dollars = 0.0

    print("Starting Purchase KPI calculation...")
    print(f"Chunk size: {CHUNK_SIZE:,}")

    with engine.connect() as connection:

        for chunk_number, chunk in enumerate(
            pd.read_sql(
                text(query),
                connection,
                params={"business_id": BUSINESS_ID},
                chunksize=CHUNK_SIZE
            ),
            start=1
        ):

            chunk["quantity"] = pd.to_numeric(
                chunk["quantity"],
                errors="coerce"
            )

            chunk["dollars"] = pd.to_numeric(
                chunk["dollars"],
                errors="coerce"
            )

            total_rows += len(chunk)

            total_quantity += chunk["quantity"].sum()
            total_dollars += chunk["dollars"].sum()

            print(
                f"Chunk {chunk_number}: "
                f"{len(chunk):,} rows processed | "
                f"Total rows: {total_rows:,}"
            )

    print("\n" + "=" * 60)
    print("PURCHASE KPI RESULTS")
    print("=" * 60)

    print(f"Total Purchase Rows : {total_rows:,}")
    print(f"Total Purchase Qty  : {total_quantity:,.2f}")
    print(f"Total Purchase $    : {total_dollars:,.2f}")

    print("=" * 60)


if __name__ == "__main__":
    calculate_purchase_kpis()