from pathlib import Path

import pandas as pd

from database.connection import engine


# ============================================================
# CONFIGURATION
# ============================================================

BUSINESS_ID = 1

EXPECTED_ROWS = 2_372_474

READ_CHUNK_SIZE = 50_000

MYSQL_INSERT_CHUNK_SIZE = 5_000


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = BASE_DIR / "data" / "raw"

PURCHASES_FILE = RAW_DATA_DIR / "purchases.csv"


# ============================================================
# SOURCE COLUMNS
# ============================================================

SOURCE_COLUMNS = [
    "InventoryId",
    "Store",
    "Brand",
    "Description",
    "Size",
    "VendorNumber",
    "VendorName",
    "PONumber",
    "PODate",
    "ReceivingDate",
    "InvoiceDate",
    "PayDate",
    "PurchasePrice",
    "Quantity",
    "Dollars",
    "Classification",
]


# ============================================================
# DATABASE COLUMNS
# ============================================================

DATABASE_COLUMNS = [
    "business_id",
    "inventory_id",
    "store_number",
    "brand",
    "description",
    "size",
    "vendor_number",
    "vendor_name",
    "po_number",
    "po_date",
    "receiving_date",
    "invoice_date",
    "pay_date",
    "purchase_price",
    "quantity",
    "dollars",
    "classification",
]


# ============================================================
# PREPARE ONE CHUNK
# ============================================================

def prepare_purchase_chunk(df):
    """
    Transform one purchases CSV chunk into the
    format required by the MySQL purchases table.
    """

    df = df.copy()

    # --------------------------------------------------------
    # Clean column names
    # --------------------------------------------------------

    df.columns = df.columns.str.strip()

    # --------------------------------------------------------
    # Inventory ID
    # --------------------------------------------------------

    df["InventoryId"] = (
        df["InventoryId"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "Store",
        "Brand",
        "VendorNumber",
        "PONumber",
        "PurchasePrice",
        "Quantity",
        "Dollars",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    date_columns = [
        "PODate",
        "ReceivingDate",
        "InvoiceDate",
        "PayDate",
    ]

    for column in date_columns:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        ).dt.date

    # --------------------------------------------------------
    # Text columns
    # --------------------------------------------------------

    text_columns = [
        "Description",
        "Size",
        "VendorName",
        "Classification",
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )

    # --------------------------------------------------------
    # Add business ID
    # --------------------------------------------------------

    df["business_id"] = BUSINESS_ID

    # --------------------------------------------------------
    # Rename columns
    # --------------------------------------------------------

    df = df.rename(
        columns={
            "InventoryId": "inventory_id",
            "Store": "store_number",
            "Brand": "brand",
            "Description": "description",
            "Size": "size",
            "VendorNumber": "vendor_number",
            "VendorName": "vendor_name",
            "PONumber": "po_number",
            "PODate": "po_date",
            "ReceivingDate": "receiving_date",
            "InvoiceDate": "invoice_date",
            "PayDate": "pay_date",
            "PurchasePrice": "purchase_price",
            "Quantity": "quantity",
            "Dollars": "dollars",
            "Classification": "classification",
        }
    )

    # --------------------------------------------------------
    # Select exact database columns
    # --------------------------------------------------------

    df = df[DATABASE_COLUMNS]

    return df


# ============================================================
# VALIDATE ONE CHUNK
# ============================================================

def validate_purchase_chunk(df, chunk_number):
    """
    Validate one prepared purchase chunk.
    """

    if df.empty:
        raise ValueError(
            f"Chunk {chunk_number} is empty."
        )

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    required_columns = [
        "business_id",
        "inventory_id",
        "store_number",
        "brand",
        "vendor_number",
        "vendor_name",
        "po_number",
        "po_date",
        "receiving_date",
        "invoice_date",
        "pay_date",
        "purchase_price",
        "quantity",
        "dollars",
        "classification",
    ]

    for column in required_columns:

        null_count = df[column].isna().sum()

        if null_count > 0:

            raise ValueError(
                f"Chunk {chunk_number}: "
                f"{column} contains {null_count:,} null values."
            )

    # --------------------------------------------------------
    # Inventory ID must not be empty
    # --------------------------------------------------------

    empty_inventory_ids = (
        df["inventory_id"]
        .astype("string")
        .str.strip()
        .eq("")
        .sum()
    )

    if empty_inventory_ids > 0:

        raise ValueError(
            f"Chunk {chunk_number}: "
            f"{empty_inventory_ids:,} empty InventoryId values."
        )

    # --------------------------------------------------------
    # Business ID
    # --------------------------------------------------------

    invalid_business_ids = (
        df["business_id"] != BUSINESS_ID
    ).sum()

    if invalid_business_ids > 0:

        raise ValueError(
            f"Chunk {chunk_number}: "
            f"invalid business_id values found."
        )


# ============================================================
# CLEAR EXISTING PURCHASE DATA
# ============================================================

def clear_existing_purchases(connection):

    print("\n" + "=" * 60)
    print("CLEARING EXISTING PURCHASE DATA")
    print("=" * 60)

    result = connection.exec_driver_sql(
        "DELETE FROM purchases WHERE business_id = %s",
        (BUSINESS_ID,)
    )

    deleted_rows = result.rowcount

    print(
        f"✓ Old purchase rows removed: "
        f"{deleted_rows:,}"
    )


# ============================================================
# LOAD PURCHASE DATA
# ============================================================

def load_purchases(connection):

    print("\n" + "=" * 60)
    print("LOADING PURCHASE DATA")
    print("=" * 60)

    total_loaded = 0
    chunk_number = 0

    for raw_chunk in pd.read_csv(
        PURCHASES_FILE,
        chunksize=READ_CHUNK_SIZE,
        low_memory=False,
    ):

        chunk_number += 1

        print(
            f"\nProcessing chunk {chunk_number}..."
        )

        print(
            f"Rows in chunk: "
            f"{len(raw_chunk):,}"
        )

        # ----------------------------------------------------
        # Prepare
        # ----------------------------------------------------

        prepared_chunk = prepare_purchase_chunk(
            raw_chunk
        )

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        validate_purchase_chunk(
            prepared_chunk,
            chunk_number
        )

        # ----------------------------------------------------
        # Insert
        # ----------------------------------------------------

        prepared_chunk.to_sql(
            name="purchases",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=MYSQL_INSERT_CHUNK_SIZE,
            method="multi",
        )

        total_loaded += len(prepared_chunk)

        print(
            f"✓ Chunk {chunk_number} loaded."
        )

        print(
            f"Total loaded so far: "
            f"{total_loaded:,}"
        )

    return total_loaded


# ============================================================
# VERIFY DATABASE
# ============================================================

def verify_purchases(connection, expected_rows):

    print("\n" + "=" * 60)
    print("VERIFYING PURCHASE DATA")
    print("=" * 60)

    # --------------------------------------------------------
    # Total rows
    # --------------------------------------------------------

    result = connection.exec_driver_sql(
        """
        SELECT COUNT(*)
        FROM purchases
        WHERE business_id = %s
        """,
        (BUSINESS_ID,)
    )

    database_count = result.scalar()

    print(
        f"purchases: {database_count:,}"
    )

    if database_count != expected_rows:

        raise ValueError(
            f"Row count mismatch. "
            f"Expected {expected_rows:,}, "
            f"found {database_count:,}."
        )

    # --------------------------------------------------------
    # Business ID check
    # --------------------------------------------------------

    result = connection.exec_driver_sql(
        """
        SELECT COUNT(*)
        FROM purchases
        WHERE business_id = %s
        """,
        (BUSINESS_ID,)
    )

    business_count = result.scalar()

    if business_count != expected_rows:

        raise ValueError(
            "Business ID verification failed."
        )

    print(
        "✓ Business ID verified."
    )

    # --------------------------------------------------------
    # Purchase ID check
    # --------------------------------------------------------

    result = connection.exec_driver_sql(
        """
        SELECT
            COUNT(*) AS total_rows,
            COUNT(DISTINCT purchase_id) AS unique_ids
        FROM purchases
        WHERE business_id = %s
        """,
        (BUSINESS_ID,)
    )

    row = result.fetchone()

    total_rows = row[0]
    unique_ids = row[1]

    print(
        f"Purchase IDs: "
        f"{unique_ids:,} unique / "
        f"{total_rows:,} total"
    )

    if total_rows != unique_ids:

        raise ValueError(
            "Duplicate purchase_id values detected."
        )

    print(
        "✓ Purchase ID uniqueness verified."
    )

    # --------------------------------------------------------
    # PO number check
    # --------------------------------------------------------

    result = connection.exec_driver_sql(
        """
        SELECT COUNT(DISTINCT po_number)
        FROM purchases
        WHERE business_id = %s
        """,
        (BUSINESS_ID,)
    )

    unique_po_numbers = result.scalar()

    print(
        f"Unique PO numbers: "
        f"{unique_po_numbers:,}"
    )

    if unique_po_numbers != 5543:

        raise ValueError(
            f"Expected 5,543 unique PO numbers, "
            f"found {unique_po_numbers:,}."
        )

    print(
        "✓ PO number relationship verified."
    )

    # --------------------------------------------------------
    # Missing size check
    # --------------------------------------------------------

    result = connection.exec_driver_sql(
        """
        SELECT COUNT(*)
        FROM purchases
        WHERE business_id = %s
          AND size IS NULL
        """,
        (BUSINESS_ID,)
    )

    missing_size = result.scalar()

    print(
        f"Rows with missing size: "
        f"{missing_size:,}"
    )

    if missing_size != 3:

        raise ValueError(
            f"Expected 3 missing Size values, "
            f"found {missing_size:,}."
        )

    print(
        "✓ Expected Size null count verified."
    )

    print(
        "\n✓ Purchase database verification passed."
    )


# ============================================================
# MAIN ETL
# ============================================================

def main():

    print("=" * 60)
    print("PURCHASE FACT ETL")
    print("=" * 60)

    # --------------------------------------------------------
    # Check source file
    # --------------------------------------------------------

    if not PURCHASES_FILE.exists():

        raise FileNotFoundError(
            f"Purchases file not found:\n"
            f"{PURCHASES_FILE}"
        )

    print("\nSource file:")
    print(PURCHASES_FILE)

    print(
        f"\nExpected source rows: "
        f"{EXPECTED_ROWS:,}"
    )

    # --------------------------------------------------------
    # Check source row count before modifying database
    # --------------------------------------------------------

    print(
        "\nChecking source row count..."
    )

    source_row_count = sum(
        len(chunk)
        for chunk in pd.read_csv(
            PURCHASES_FILE,
            chunksize=READ_CHUNK_SIZE,
            usecols=SOURCE_COLUMNS,
        )
    )

    print(
        f"Source rows found: "
        f"{source_row_count:,}"
    )

    if source_row_count != EXPECTED_ROWS:

        raise ValueError(
            f"Source row count mismatch. "
            f"Expected {EXPECTED_ROWS:,}, "
            f"found {source_row_count:,}."
        )

    print(
        "✓ Source row count verified."
    )

    # --------------------------------------------------------
    # Database transaction
    # --------------------------------------------------------

    print(
        "\nStarting database transaction..."
    )

    with engine.begin() as connection:

        # ----------------------------------------------------
        # Clear old data
        # ----------------------------------------------------

        clear_existing_purchases(
            connection
        )

        # ----------------------------------------------------
        # Load new data
        # ----------------------------------------------------

        total_loaded = load_purchases(
            connection
        )

        # ----------------------------------------------------
        # Verify
        # ----------------------------------------------------

        if total_loaded != EXPECTED_ROWS:

            raise ValueError(
                f"Loaded row count mismatch. "
                f"Expected {EXPECTED_ROWS:,}, "
                f"loaded {total_loaded:,}."
            )

        verify_purchases(
            connection,
            EXPECTED_ROWS
        )

        print(
            "\n✓ All purchase ETL checks passed."
        )

    # --------------------------------------------------------
    # Transaction committed
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("TRANSACTION COMMITTED SUCCESSFULLY")
    print("=" * 60)

    print(
        "\nPURCHASE ETL COMPLETED SUCCESSFULLY"
    )

    print(
        f"\nFinal row count: "
        f"{EXPECTED_ROWS:,}"
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()