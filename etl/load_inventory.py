from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database.connection import engine


# ============================================================
# CONFIGURATION
# ============================================================

BUSINESS_ID = 1

EXPECTED_BEGIN_ROWS = 206_529
EXPECTED_END_ROWS = 224_489

READ_CHUNK_SIZE = 50_000
MYSQL_INSERT_CHUNK_SIZE = 5_000

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

BEGIN_FILE = RAW_DIR / "begin_inventory.csv"
END_FILE = RAW_DIR / "end_inventory.csv"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(series):
    """
    Convert values to pandas string type and remove
    unnecessary leading/trailing spaces.
    """
    return series.astype("string").str.strip()


def prepare_begin_chunk(df):
    """
    Prepare one begin_inventory chunk for MySQL.
    """

    required_columns = [
        "InventoryId",
        "Store",
        "City",
        "Brand",
        "Description",
        "Size",
        "onHand",
        "Price",
        "startDate"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in begin_inventory.csv: {missing_columns}"
        )

    df = df[required_columns].copy()

    # InventoryId must remain text
    df["InventoryId"] = clean_text(df["InventoryId"])

    # Numeric fields
    df["Store"] = pd.to_numeric(df["Store"], errors="coerce")
    df["Brand"] = pd.to_numeric(df["Brand"], errors="coerce")
    df["onHand"] = pd.to_numeric(df["onHand"], errors="coerce")
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    # Text fields
    df["City"] = clean_text(df["City"])
    df["Description"] = clean_text(df["Description"])
    df["Size"] = clean_text(df["Size"])

    # Date
    df["startDate"] = pd.to_datetime(
        df["startDate"],
        errors="coerce"
    ).dt.date

    # Add business ID
    df.insert(0, "business_id", BUSINESS_ID)

    # Rename columns to match MySQL
    df = df.rename(
        columns={
            "InventoryId": "inventory_id",
            "Store": "store_number",
            "City": "city",
            "Brand": "brand",
            "Description": "description",
            "Size": "size",
            "onHand": "on_hand",
            "Price": "price",
            "startDate": "start_date"
        }
    )

    return df


def prepare_end_chunk(df):
    """
    Prepare one end_inventory chunk for MySQL.
    """

    required_columns = [
        "InventoryId",
        "Store",
        "City",
        "Brand",
        "Description",
        "Size",
        "onHand",
        "Price",
        "endDate"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in end_inventory.csv: {missing_columns}"
        )

    df = df[required_columns].copy()

    # InventoryId must remain text
    df["InventoryId"] = clean_text(df["InventoryId"])

    # Numeric fields
    df["Store"] = pd.to_numeric(df["Store"], errors="coerce")
    df["Brand"] = pd.to_numeric(df["Brand"], errors="coerce")
    df["onHand"] = pd.to_numeric(df["onHand"], errors="coerce")
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")

    # Text fields
    # City is intentionally allowed to contain NULL values.
    df["City"] = clean_text(df["City"])
    df["Description"] = clean_text(df["Description"])
    df["Size"] = clean_text(df["Size"])

    # Date
    df["endDate"] = pd.to_datetime(
        df["endDate"],
        errors="coerce"
    ).dt.date

    # Add business ID
    df.insert(0, "business_id", BUSINESS_ID)

    # Rename columns to match MySQL
    df = df.rename(
        columns={
            "InventoryId": "inventory_id",
            "Store": "store_number",
            "City": "city",
            "Brand": "brand",
            "Description": "description",
            "Size": "size",
            "onHand": "on_hand",
            "Price": "price",
            "endDate": "end_date"
        }
    )

    return df


# ============================================================
# SOURCE ROW COUNT VALIDATION
# ============================================================

def count_source_rows(file_path):
    """
    Count CSV rows without loading the entire file into memory.
    """

    total_rows = 0

    for chunk in pd.read_csv(
        file_path,
        chunksize=READ_CHUNK_SIZE,
        low_memory=False
    ):
        total_rows += len(chunk)

    return total_rows


# ============================================================
# VALIDATION
# ============================================================

def validate_begin_chunk(df, chunk_number):
    """
    Validate prepared begin inventory chunk.
    """

    required_columns = [
        "business_id",
        "inventory_id",
        "store_number",
        "brand",
        "description",
        "on_hand",
        "price",
        "start_date"
    ]

    for column in required_columns:
        null_count = df[column].isna().sum()

        if null_count > 0:
            raise ValueError(
                f"Begin inventory chunk {chunk_number}: "
                f"column '{column}' contains {null_count} NULL values."
            )

    if not (df["business_id"] == BUSINESS_ID).all():
        raise ValueError(
            f"Begin inventory chunk {chunk_number}: "
            f"invalid business_id found."
        )

    if (df["inventory_id"].str.len() == 0).any():
        raise ValueError(
            f"Begin inventory chunk {chunk_number}: "
            f"empty InventoryId found."
        )


def validate_end_chunk(df, chunk_number):
    """
    Validate prepared end inventory chunk.

    City is intentionally NOT required because
    the source contains 1,284 missing City values.
    """

    required_columns = [
        "business_id",
        "inventory_id",
        "store_number",
        "brand",
        "description",
        "on_hand",
        "price",
        "end_date"
    ]

    for column in required_columns:
        null_count = df[column].isna().sum()

        if null_count > 0:
            raise ValueError(
                f"End inventory chunk {chunk_number}: "
                f"column '{column}' contains {null_count} NULL values."
            )

    if not (df["business_id"] == BUSINESS_ID).all():
        raise ValueError(
            f"End inventory chunk {chunk_number}: "
            f"invalid business_id found."
        )

    if (df["inventory_id"].str.len() == 0).any():
        raise ValueError(
            f"End inventory chunk {chunk_number}: "
            f"empty InventoryId found."
        )


# ============================================================
# LOAD BEGIN INVENTORY
# ============================================================

def load_begin_inventory(connection):
    print("\n" + "=" * 70)
    print("LOADING BEGIN INVENTORY")
    print("=" * 70)

    print(f"Source file: {BEGIN_FILE}")

    if not BEGIN_FILE.exists():
        raise FileNotFoundError(
            f"Begin inventory file not found: {BEGIN_FILE}"
        )

    print("Checking source row count...")

    source_rows = count_source_rows(BEGIN_FILE)

    print(f"Source rows: {source_rows:,}")

    if source_rows != EXPECTED_BEGIN_ROWS:
        raise ValueError(
            f"Unexpected begin inventory row count. "
            f"Expected {EXPECTED_BEGIN_ROWS:,}, "
            f"found {source_rows:,}."
        )

    print("Source row count verified.")

    # Clear previous data
    print("\nClearing existing begin inventory data...")

    result = connection.execute(
        text(
            """
            DELETE FROM begin_inventory
            WHERE business_id = :business_id
            """
        ),
        {"business_id": BUSINESS_ID}
    )

    print(
        f"Old begin inventory rows removed: "
        f"{result.rowcount:,}"
    )

    # Load chunks
    total_loaded = 0
    chunk_number = 0

    print("\nLoading begin inventory in chunks...")

    for chunk in pd.read_csv(
        BEGIN_FILE,
        chunksize=READ_CHUNK_SIZE,
        low_memory=False
    ):
        chunk_number += 1

        prepared = prepare_begin_chunk(chunk)

        validate_begin_chunk(
            prepared,
            chunk_number
        )

        prepared.to_sql(
            "begin_inventory",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=MYSQL_INSERT_CHUNK_SIZE,
            method="multi"
        )

        total_loaded += len(prepared)

        print(
            f"Chunk {chunk_number}: "
            f"{len(prepared):,} rows loaded | "
            f"Total: {total_loaded:,}"
        )

    if total_loaded != EXPECTED_BEGIN_ROWS:
        raise ValueError(
            f"Begin inventory load mismatch. "
            f"Expected {EXPECTED_BEGIN_ROWS:,}, "
            f"loaded {total_loaded:,}."
        )

    print(
        f"\nBegin inventory loading completed: "
        f"{total_loaded:,} rows."
    )


# ============================================================
# LOAD END INVENTORY
# ============================================================

def load_end_inventory(connection):
    print("\n" + "=" * 70)
    print("LOADING END INVENTORY")
    print("=" * 70)

    print(f"Source file: {END_FILE}")

    if not END_FILE.exists():
        raise FileNotFoundError(
            f"End inventory file not found: {END_FILE}"
        )

    print("Checking source row count...")

    source_rows = count_source_rows(END_FILE)

    print(f"Source rows: {source_rows:,}")

    if source_rows != EXPECTED_END_ROWS:
        raise ValueError(
            f"Unexpected end inventory row count. "
            f"Expected {EXPECTED_END_ROWS:,}, "
            f"found {source_rows:,}."
        )

    print("Source row count verified.")

    # Clear previous data
    print("\nClearing existing end inventory data...")

    result = connection.execute(
        text(
            """
            DELETE FROM end_inventory
            WHERE business_id = :business_id
            """
        ),
        {"business_id": BUSINESS_ID}
    )

    print(
        f"Old end inventory rows removed: "
        f"{result.rowcount:,}"
    )

    # Load chunks
    total_loaded = 0
    chunk_number = 0

    print("\nLoading end inventory in chunks...")

    for chunk in pd.read_csv(
        END_FILE,
        chunksize=READ_CHUNK_SIZE,
        low_memory=False
    ):
        chunk_number += 1

        prepared = prepare_end_chunk(chunk)

        validate_end_chunk(
            prepared,
            chunk_number
        )

        prepared.to_sql(
            "end_inventory",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=MYSQL_INSERT_CHUNK_SIZE,
            method="multi"
        )

        total_loaded += len(prepared)

        print(
            f"Chunk {chunk_number}: "
            f"{len(prepared):,} rows loaded | "
            f"Total: {total_loaded:,}"
        )

    if total_loaded != EXPECTED_END_ROWS:
        raise ValueError(
            f"End inventory load mismatch. "
            f"Expected {EXPECTED_END_ROWS:,}, "
            f"loaded {total_loaded:,}."
        )

    print(
        f"\nEnd inventory loading completed: "
        f"{total_loaded:,} rows."
    )


# ============================================================
# FINAL VERIFICATION
# ============================================================

def verify_inventory(connection):
    print("\n" + "=" * 70)
    print("FINAL INVENTORY VERIFICATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Begin inventory count
    # --------------------------------------------------------

    begin_count = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM begin_inventory
            WHERE business_id = :business_id
            """
        ),
        {"business_id": BUSINESS_ID}
    ).scalar()

    print(
        f"Begin inventory rows: "
        f"{begin_count:,}"
    )

    if begin_count != EXPECTED_BEGIN_ROWS:
        raise ValueError(
            f"Begin inventory verification failed. "
            f"Expected {EXPECTED_BEGIN_ROWS:,}, "
            f"found {begin_count:,}."
        )

    # --------------------------------------------------------
    # End inventory count
    # --------------------------------------------------------

    end_count = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM end_inventory
            WHERE business_id = :business_id
            """
        ),
        {"business_id": BUSINESS_ID}
    ).scalar()

    print(
        f"End inventory rows: "
        f"{end_count:,}"
    )

    if end_count != EXPECTED_END_ROWS:
        raise ValueError(
            f"End inventory verification failed. "
            f"Expected {EXPECTED_END_ROWS:,}, "
            f"found {end_count:,}."
        )

    # --------------------------------------------------------
    # Inventory ID uniqueness
    # --------------------------------------------------------

    begin_ids = connection.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT inventory_id) AS unique_ids
            FROM begin_inventory
            WHERE business_id = :business_id
            """
        ),
        {"business_id": BUSINESS_ID}
    ).mappings().one()

    print(
        f"Begin Inventory IDs: "
        f"{begin_ids['unique_ids']:,} unique / "
        f"{begin_ids['total_rows']:,} total"
    )

    if begin_ids["unique_ids"] != begin_ids["total_rows"]:
        raise ValueError(
            "Duplicate InventoryId values found "
            "in begin_inventory."
        )

    end_ids = connection.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT inventory_id) AS unique_ids
            FROM end_inventory
            WHERE business_id = :business_id
            """
        ),
        {"business_id": BUSINESS_ID}
    ).mappings().one()

    print(
        f"End Inventory IDs: "
        f"{end_ids['unique_ids']:,} unique / "
        f"{end_ids['total_rows']:,} total"
    )

    if end_ids["unique_ids"] != end_ids["total_rows"]:
        raise ValueError(
            "Duplicate InventoryId values found "
            "in end_inventory."
        )

    # --------------------------------------------------------
    # Required NULL verification
    # --------------------------------------------------------

    begin_nulls = connection.execute(
        text(
            """
            SELECT
                COUNT(*) - COUNT(inventory_id) AS inventory_id_nulls,
                COUNT(*) - COUNT(store_number) AS store_nulls,
                COUNT(*) - COUNT(brand) AS brand_nulls,
                COUNT(*) - COUNT(description) AS description_nulls,
                COUNT(*) - COUNT(on_hand) AS on_hand_nulls,
                COUNT(*) - COUNT(price) AS price_nulls,
                COUNT(*) - COUNT(start_date) AS start_date_nulls
            FROM begin_inventory
            WHERE business_id = :business_id
            """
        ),
        {"business_id": BUSINESS_ID}
    ).mappings().one()

    print("\nBegin inventory required NULL counts:")

    for column, value in begin_nulls.items():
        print(f"  {column}: {value:,}")

    if any(value != 0 for value in begin_nulls.values()):
        raise ValueError(
            "NULL values found in required begin inventory fields."
        )

    end_nulls = connection.execute(
        text(
            """
            SELECT
                COUNT(*) - COUNT(inventory_id) AS inventory_id_nulls,
                COUNT(*) - COUNT(store_number) AS store_nulls,
                COUNT(*) - COUNT(brand) AS brand_nulls,
                COUNT(*) - COUNT(description) AS description_nulls,
                COUNT(*) - COUNT(on_hand) AS on_hand_nulls,
                COUNT(*) - COUNT(price) AS price_nulls,
                COUNT(*) - COUNT(end_date) AS end_date_nulls
            FROM end_inventory
            WHERE business_id = :business_id
            """
        ),
        {"business_id": BUSINESS_ID}
    ).mappings().one()

    print("\nEnd inventory required NULL counts:")

    for column, value in end_nulls.items():
        print(f"  {column}: {value:,}")

    if any(value != 0 for value in end_nulls.values()):
        raise ValueError(
            "NULL values found in required end inventory fields."
        )

    # --------------------------------------------------------
    # City NULL verification
    # --------------------------------------------------------

    end_city_nulls = connection.execute(
        text(
            """
            SELECT COUNT(*) - COUNT(city)
            FROM end_inventory
            WHERE business_id = :business_id
            """
        ),
        {"business_id": BUSINESS_ID}
    ).scalar()

    print(
        f"\nEnd inventory City NULL rows: "
        f"{end_city_nulls:,}"
    )

    if end_city_nulls != 1_284:
        raise ValueError(
            f"Unexpected End Inventory City NULL count. "
            f"Expected 1,284, found {end_city_nulls:,}."
        )

    # --------------------------------------------------------
    # Date verification
    # --------------------------------------------------------

    begin_dates = connection.execute(
        text(
            """
            SELECT
                MIN(start_date) AS min_date,
                MAX(start_date) AS max_date
            FROM begin_inventory
            WHERE business_id = :business_id
            """
        ),
        {"business_id": BUSINESS_ID}
    ).mappings().one()

    print(
        f"Begin inventory date range: "
        f"{begin_dates['min_date']} -> "
        f"{begin_dates['max_date']}"
    )

    end_dates = connection.execute(
        text(
            """
            SELECT
                MIN(end_date) AS min_date,
                MAX(end_date) AS max_date
            FROM end_inventory
            WHERE business_id = :business_id
            """
        ),
        {"business_id": BUSINESS_ID}
    ).mappings().one()

    print(
        f"End inventory date range: "
        f"{end_dates['min_date']} -> "
        f"{end_dates['max_date']}"
    )

    if str(begin_dates["min_date"]) != "2024-01-01":
        raise ValueError(
            "Unexpected begin inventory start date."
        )

    if str(begin_dates["max_date"]) != "2024-01-01":
        raise ValueError(
            "Unexpected begin inventory end date."
        )

    if str(end_dates["min_date"]) != "2024-12-31":
        raise ValueError(
            "Unexpected end inventory start date."
        )

    if str(end_dates["max_date"]) != "2024-12-31":
        raise ValueError(
            "Unexpected end inventory end date."
        )

    # --------------------------------------------------------
    # Business ID verification
    # --------------------------------------------------------

    invalid_begin_business_ids = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM begin_inventory
            WHERE business_id <> :business_id
               OR business_id IS NULL
            """
        ),
        {"business_id": BUSINESS_ID}
    ).scalar()

    invalid_end_business_ids = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM end_inventory
            WHERE business_id <> :business_id
               OR business_id IS NULL
            """
        ),
        {"business_id": BUSINESS_ID}
    ).scalar()

    print(
        f"Invalid begin business_id rows: "
        f"{invalid_begin_business_ids:,}"
    )

    print(
        f"Invalid end business_id rows: "
        f"{invalid_end_business_ids:,}"
    )

    if invalid_begin_business_ids != 0:
        raise ValueError(
            "Invalid business_id found in begin_inventory."
        )

    if invalid_end_business_ids != 0:
        raise ValueError(
            "Invalid business_id found in end_inventory."
        )

    print("\nInventory verification PASSED.")


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "#" * 70)
    print("PHASE 6.4 - INVENTORY FACT LOADING")
    print("#" * 70)

    try:

        # One transaction for the complete inventory load.
        with engine.begin() as connection:

            load_begin_inventory(connection)

            load_end_inventory(connection)

            verify_inventory(connection)

            print(
                "\nTransaction committed successfully."
            )

        print("\n" + "#" * 70)
        print("PHASE 6.4 INVENTORY LOAD COMPLETED SUCCESSFULLY")
        print("#" * 70)

    except Exception as error:

        print("\n" + "!" * 70)
        print("INVENTORY LOAD FAILED")
        print("!" * 70)

        print(f"\nError: {error}")

        print(
            "\nNo successful commit was made for this run."
        )

        raise


if __name__ == "__main__":
    main()