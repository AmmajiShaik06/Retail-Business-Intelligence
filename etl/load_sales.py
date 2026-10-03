from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database.connection import engine


# ============================================================
# CONFIGURATION
# ============================================================

BUSINESS_ID = 1

EXPECTED_ROWS = 12_825_363

READ_CHUNK_SIZE = 50_000

MYSQL_INSERT_CHUNK_SIZE = 5_000


# ============================================================
# PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SALES_FILE = PROJECT_ROOT / "data" / "raw" / "sales.csv"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(series):
    """
    Convert values to pandas string type,
    remove unnecessary spaces,
    and preserve missing values.
    """
    return (
        series.astype("string")
        .str.strip()
    )


def prepare_sales_chunk(df):
    """
    Prepare one sales dataframe chunk
    before inserting it into MySQL.
    """

    # --------------------------------------------------------
    # Keep only columns required by the database
    # --------------------------------------------------------

    df = df[
        [
            "InventoryId",
            "Store",
            "Brand",
            "Description",
            "Size",
            "SalesQuantity",
            "SalesDollars",
            "SalesPrice",
            "SalesDate",
            "Volume",
            "Classification",
            "ExciseTax",
            "VendorNo",
            "VendorName",
        ]
    ].copy()

    # --------------------------------------------------------
    # Rename CSV columns to database columns
    # --------------------------------------------------------

    df.rename(
        columns={
            "InventoryId": "inventory_id",
            "Store": "store_number",
            "Brand": "brand",
            "Description": "description",
            "Size": "size",
            "SalesQuantity": "sales_quantity",
            "SalesDollars": "sales_dollars",
            "SalesPrice": "sales_price",
            "SalesDate": "sales_date",
            "Volume": "volume",
            "Classification": "classification",
            "ExciseTax": "excise_tax",
            "VendorNo": "vendor_number",
            "VendorName": "vendor_name",
        },
        inplace=True,
    )

    # --------------------------------------------------------
    # Inventory ID
    # --------------------------------------------------------

    # InventoryId must remain text.
    df["inventory_id"] = clean_text(df["inventory_id"])

    # --------------------------------------------------------
    # Text columns
    # --------------------------------------------------------

    text_columns = [
        "description",
        "size",
        "volume",
        "classification",
        "vendor_name",
    ]

    for column in text_columns:
        df[column] = clean_text(df[column])

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "store_number",
        "brand",
        "sales_quantity",
        "sales_dollars",
        "sales_price",
        "excise_tax",
        "vendor_number",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    df["sales_date"] = pd.to_datetime(
        df["sales_date"],
        errors="coerce"
    ).dt.date

    # --------------------------------------------------------
    # Add business ID
    # --------------------------------------------------------

    df.insert(
        0,
        "business_id",
        BUSINESS_ID
    )

    return df


def validate_sales_chunk(df, chunk_number):
    """
    Validate a transformed sales chunk.
    """

    required_columns = [
        "business_id",
        "inventory_id",
        "store_number",
        "brand",
        "sales_quantity",
        "sales_dollars",
        "sales_price",
        "sales_date",
        "vendor_number",
    ]

    # --------------------------------------------------------
    # Check required columns
    # --------------------------------------------------------

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Chunk {chunk_number}: Missing columns: "
            f"{missing_columns}"
        )

    # --------------------------------------------------------
    # Required fields should not be null
    # --------------------------------------------------------

    null_counts = df[required_columns].isna().sum()

    invalid_nulls = null_counts[
        null_counts > 0
    ]

    if not invalid_nulls.empty:
        raise ValueError(
            f"Chunk {chunk_number}: "
            f"Unexpected NULL values:\n"
            f"{invalid_nulls}"
        )

    # --------------------------------------------------------
    # Business ID
    # --------------------------------------------------------

    if not (df["business_id"] == BUSINESS_ID).all():
        raise ValueError(
            f"Chunk {chunk_number}: "
            f"Invalid business_id detected."
        )


# ============================================================
# MAIN ETL
# ============================================================

def main():

    print("=" * 60)
    print("SALES FACT ETL")
    print("=" * 60)

    print()
    print("Source file:")
    print(SALES_FILE)

    print()
    print(f"Expected source rows: {EXPECTED_ROWS:,}")

    # --------------------------------------------------------
    # Check file
    # --------------------------------------------------------

    if not SALES_FILE.exists():
        raise FileNotFoundError(
            f"Sales file not found:\n{SALES_FILE}"
        )

    # --------------------------------------------------------
    # Verify source row count
    # --------------------------------------------------------

    print()
    print("Checking source row count...")

    source_rows = 0

    for chunk in pd.read_csv(
        SALES_FILE,
        chunksize=READ_CHUNK_SIZE,
        low_memory=False
    ):
        source_rows += len(chunk)

    print(
        f"Source rows found: {source_rows:,}"
    )

    if source_rows != EXPECTED_ROWS:
        raise ValueError(
            f"Source row count mismatch. "
            f"Expected {EXPECTED_ROWS:,}, "
            f"found {source_rows:,}."
        )

    print("✓ Source row count verified.")

    # --------------------------------------------------------
    # Start database transaction
    # --------------------------------------------------------

    print()
    print("Starting database transaction...")

    with engine.begin() as connection:

        # ====================================================
        # CLEAR EXISTING DATA
        # ====================================================

        print()
        print("=" * 60)
        print("CLEARING EXISTING SALES DATA")
        print("=" * 60)

        old_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM sales
                WHERE business_id = :business_id
                """
            ),
            {
                "business_id": BUSINESS_ID
            }
        ).scalar()

        connection.execute(
            text(
                """
                DELETE FROM sales
                WHERE business_id = :business_id
                """
            ),
            {
                "business_id": BUSINESS_ID
            }
        )

        print(
            f"✓ Old sales rows removed: {old_rows:,}"
        )

        # ====================================================
        # LOAD DATA
        # ====================================================

        print()
        print("=" * 60)
        print("LOADING SALES DATA")
        print("=" * 60)

        total_loaded = 0
        chunk_number = 0

        for chunk in pd.read_csv(
            SALES_FILE,
            chunksize=READ_CHUNK_SIZE,
            low_memory=False
        ):

            chunk_number += 1

            print()
            print(
                f"Processing chunk {chunk_number}..."
            )

            print(
                f"Rows in chunk: {len(chunk):,}"
            )

            # ------------------------------------------------
            # Transform
            # ------------------------------------------------

            chunk = prepare_sales_chunk(chunk)

            # ------------------------------------------------
            # Validate
            # ------------------------------------------------

            validate_sales_chunk(
                chunk,
                chunk_number
            )

            # ------------------------------------------------
            # Insert
            # ------------------------------------------------

            chunk.to_sql(
                name="sales",
                con=connection,
                if_exists="append",
                index=False,
                chunksize=MYSQL_INSERT_CHUNK_SIZE,
                method="multi",
            )

            total_loaded += len(chunk)

            print(
                f"✓ Chunk {chunk_number} loaded."
            )

            print(
                f"Total loaded so far: "
                f"{total_loaded:,}"
            )

        # ====================================================
        # VERIFY DATABASE
        # ====================================================

        print()
        print("=" * 60)
        print("VERIFYING SALES DATA")
        print("=" * 60)

        # ----------------------------------------------------
        # Row count
        # ----------------------------------------------------

        db_rows = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM sales
                WHERE business_id = :business_id
                """
            ),
            {
                "business_id": BUSINESS_ID
            }
        ).scalar()

        print(
            f"sales: {db_rows:,}"
        )

        if db_rows != EXPECTED_ROWS:
            raise ValueError(
                f"Database row count mismatch. "
                f"Expected {EXPECTED_ROWS:,}, "
                f"found {db_rows:,}."
            )

        # ----------------------------------------------------
        # Business ID
        # ----------------------------------------------------

        invalid_business_ids = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM sales
                WHERE business_id <> :business_id
                """
            ),
            {
                "business_id": BUSINESS_ID
            }
        ).scalar()

        if invalid_business_ids != 0:
            raise ValueError(
                "Invalid business_id values found."
            )

        print("✓ Business ID verified.")

        # ----------------------------------------------------
        # Sales ID uniqueness
        # ----------------------------------------------------

        total_sales_ids = connection.execute(
            text(
                """
                SELECT COUNT(sales_id)
                FROM sales
                WHERE business_id = :business_id
                """
            ),
            {
                "business_id": BUSINESS_ID
            }
        ).scalar()

        unique_sales_ids = connection.execute(
            text(
                """
                SELECT COUNT(DISTINCT sales_id)
                FROM sales
                WHERE business_id = :business_id
                """
            ),
            {
                "business_id": BUSINESS_ID
            }
        ).scalar()

        print(
            f"Sales IDs: "
            f"{unique_sales_ids:,} unique / "
            f"{total_sales_ids:,} total"
        )

        if total_sales_ids != unique_sales_ids:
            raise ValueError(
                "Sales ID uniqueness verification failed."
            )

        print(
            "✓ Sales ID uniqueness verified."
        )

        # ----------------------------------------------------
        # Missing required fields
        # ----------------------------------------------------

        null_check = connection.execute(
            text(
                """
                SELECT
                    SUM(inventory_id IS NULL) AS inventory_id_nulls,
                    SUM(store_number IS NULL) AS store_nulls,
                    SUM(brand IS NULL) AS brand_nulls,
                    SUM(sales_quantity IS NULL) AS quantity_nulls,
                    SUM(sales_dollars IS NULL) AS dollars_nulls,
                    SUM(sales_price IS NULL) AS price_nulls,
                    SUM(sales_date IS NULL) AS date_nulls,
                    SUM(vendor_number IS NULL) AS vendor_nulls
                FROM sales
                WHERE business_id = :business_id
                """
            ),
            {
                "business_id": BUSINESS_ID
            }
        ).mappings().one()

        print()
        print("Required field NULL counts:")

        for column, value in null_check.items():
            print(
                f"  {column}: {value}"
            )

        if any(
            (value or 0) != 0
            for value in null_check.values()
        ):
            raise ValueError(
                "Unexpected NULL values found "
                "in required sales fields."
            )

        print(
            "✓ Required field validation passed."
        )

        # ----------------------------------------------------
        # Sales date range
        # ----------------------------------------------------

        date_range = connection.execute(
            text(
                """
                SELECT
                    MIN(sales_date) AS min_date,
                    MAX(sales_date) AS max_date
                FROM sales
                WHERE business_id = :business_id
                """
            ),
            {
                "business_id": BUSINESS_ID
            }
        ).mappings().one()

        print()
        print(
            f"Sales date range: "
            f"{date_range['min_date']} → "
            f"{date_range['max_date']}"
        )

        if (
            str(date_range["min_date"]) != "2024-01-01"
            or str(date_range["max_date"]) != "2024-12-31"
        ):
            raise ValueError(
                "Unexpected SalesDate range."
            )

        print(
            "✓ Sales date range verified."
        )

        # ----------------------------------------------------
        # Basic numeric validation
        # ----------------------------------------------------

        numeric_check = connection.execute(
            text(
                """
                SELECT
                    SUM(sales_quantity) AS total_quantity,
                    SUM(sales_dollars) AS total_sales,
                    MIN(sales_quantity) AS min_quantity,
                    MIN(sales_dollars) AS min_sales
                FROM sales
                WHERE business_id = :business_id
                """
            ),
            {
                "business_id": BUSINESS_ID
            }
        ).mappings().one()

        print()
        print("Sales numeric verification:")

        print(
            f"Total Sales Quantity: "
            f"{numeric_check['total_quantity']}"
        )

        print(
            f"Total Sales Dollars: "
            f"{numeric_check['total_sales']}"
        )

        print(
            f"Minimum Sales Quantity: "
            f"{numeric_check['min_quantity']}"
        )

        print(
            f"Minimum Sales Dollars: "
            f"{numeric_check['min_sales']}"
        )

        if (
            numeric_check["total_quantity"] is None
            or numeric_check["total_sales"] is None
        ):
            raise ValueError(
                "Sales numeric totals are NULL."
            )

        print(
            "✓ Sales numeric verification passed."
        )

        print()
        print("✓ Sales database verification passed.")
        print("✓ All sales ETL checks passed.")

    # ========================================================
    # COMMIT
    # ========================================================

    print()
    print("=" * 60)
    print("TRANSACTION COMMITTED SUCCESSFULLY")
    print("=" * 60)

    print()
    print("SALES ETL COMPLETED SUCCESSFULLY")

    print(
        f"Final row count: {EXPECTED_ROWS:,}"
    )


if __name__ == "__main__":
    main()