import pandas as pd
from sqlalchemy import text

from database.connection import engine
from etl.transform import transform_sales


BUSINESS_ID = 1


# ============================================================
# PREPARE UPLOADED SALES
# ============================================================

def prepare_uploaded_sales(df):
    """
    Transform and prepare uploaded Sales data
    for insertion into the MySQL sales table.
    """

    df = transform_sales(df)

    # Keep only columns required by the database
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

    # Rename CSV columns to database columns
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

    # Add business ID
    df.insert(
        0,
        "business_id",
        BUSINESS_ID
    )

    return df


# ============================================================
# VALIDATE UPLOADED SALES
# ============================================================

def validate_uploaded_sales(df):
    """
    Validate required fields before inserting
    uploaded Sales records into MySQL.
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

    # Check required columns
    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing database columns: {missing_columns}"
        )

    # Check required fields for NULL values
    null_counts = df[required_columns].isna().sum()

    invalid_nulls = null_counts[
        null_counts > 0
    ]

    if not invalid_nulls.empty:
        raise ValueError(
            "Uploaded Sales contains NULL values "
            "in required fields:\n"
            f"{invalid_nulls}"
        )

    # Verify business ID
    if not (df["business_id"] == BUSINESS_ID).all():
        raise ValueError(
            "Invalid business_id detected."
        )

    # Verify uploaded data is not empty
    if df.empty:
        raise ValueError(
            "Uploaded Sales dataframe contains 0 rows."
        )


# ============================================================
# LOAD UPLOADED SALES
# ============================================================

def load_uploaded_sales(df, test_mode=False):
    """
    Safely append uploaded Sales rows to MySQL.

    test_mode=False:
        Insert rows and commit the transaction.

    test_mode=True:
        Insert rows, verify them, and then rollback.
        This is used for safe testing.

    IMPORTANT:
    This function never deletes existing Sales data.
    """

    prepared_df = prepare_uploaded_sales(df)

    validate_uploaded_sales(prepared_df)

    uploaded_rows = len(prepared_df)

    connection = engine.connect()
    transaction = connection.begin()

    try:

        # ----------------------------------------------------
        # Get existing row count
        # ----------------------------------------------------

        before_count = connection.execute(
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

        # ----------------------------------------------------
        # Insert uploaded rows
        # ----------------------------------------------------

        prepared_df.to_sql(
            name="sales",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=5000,
            method="multi",
        )

        # ----------------------------------------------------
        # Get row count after insertion
        # ----------------------------------------------------

        after_count = connection.execute(
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

        inserted_rows = after_count - before_count

        # ----------------------------------------------------
        # Verify insertion
        # ----------------------------------------------------

        if inserted_rows != uploaded_rows:
            raise ValueError(
                "Upload verification failed. "
                f"Expected {uploaded_rows} rows to be inserted, "
                f"but {inserted_rows} rows were inserted."
            )

        # ----------------------------------------------------
        # Test mode
        # ----------------------------------------------------

        if test_mode:

            transaction.rollback()

            final_count = before_count

        # ----------------------------------------------------
        # Normal mode
        # ----------------------------------------------------

        else:

            transaction.commit()

            final_count = after_count

    except Exception:

        transaction.rollback()

        raise

    finally:

        connection.close()

    return {
        "uploaded_rows": uploaded_rows,
        "inserted_rows": inserted_rows,
        "total_rows_after": final_count,
        "test_mode": test_mode,
    }