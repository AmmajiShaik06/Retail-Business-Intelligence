
import pandas as pd
from sqlalchemy import text

from database.connection import engine
from etl.extract import load_csv
from etl.transform import transform_all


# ============================================================
# CONFIGURATION
# ============================================================

BUSINESS_ID = 1

EXPECTED_ROWS = 5543


# ============================================================
# PREPARE VENDOR INVOICES
# ============================================================

def prepare_vendor_invoices(df):
    """
    Prepare vendor invoice data for MySQL loading.
    """

    df = df.copy()

    print("\nPreparing vendor invoice data...")

    # --------------------------------------------------------
    # Clean column names
    # --------------------------------------------------------

    df.columns = df.columns.str.strip()

    # --------------------------------------------------------
    # Rename source columns to database columns
    # --------------------------------------------------------

    df = df.rename(
        columns={
            "VendorNumber": "vendor_number",
            "VendorName": "vendor_name",
            "InvoiceDate": "invoice_date",
            "PONumber": "po_number",
            "PODate": "po_date",
            "PayDate": "pay_date",
            "Quantity": "quantity",
            "Dollars": "dollars",
            "Freight": "freight",
            "Approval": "approval"
        }
    )

    # --------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "vendor_number",
        "po_number",
        "quantity",
        "dollars",
        "freight"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Date columns
    # --------------------------------------------------------

    date_columns = [
        "invoice_date",
        "po_date",
        "pay_date"
    ]

    for column in date_columns:

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Text columns
    # --------------------------------------------------------

    df["vendor_name"] = (
        df["vendor_name"]
        .astype("string")
        .str.strip()
    )

    df["approval"] = (
        df["approval"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------------
    # Add business ID
    # --------------------------------------------------------

    df["business_id"] = BUSINESS_ID

    # --------------------------------------------------------
    # Select exact database columns
    # --------------------------------------------------------

    df = df[
        [
            "business_id",
            "vendor_number",
            "vendor_name",
            "invoice_date",
            "po_number",
            "po_date",
            "pay_date",
            "quantity",
            "dollars",
            "freight",
            "approval"
        ]
    ]

    return df


# ============================================================
# VALIDATE VENDOR INVOICES
# ============================================================

def validate_vendor_invoices(df):
    """
    Validate vendor invoice data before loading.
    """

    print("\nValidating vendor invoice data...")

    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    print(
        f"Rows prepared: {len(df):,}"
    )

    if len(df) != EXPECTED_ROWS:

        raise ValueError(
            f"Expected {EXPECTED_ROWS:,} rows, "
            f"but received {len(df):,} rows."
        )

    # --------------------------------------------------------
    # PO number should be unique in vendor_invoice
    # --------------------------------------------------------

    duplicate_po = (
        df["po_number"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate PO numbers: {duplicate_po:,}"
    )

    if duplicate_po != 0:

        raise ValueError(
            "Duplicate PO numbers found in "
            "vendor invoice data."
        )

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    required_columns = [
        "vendor_number",
        "vendor_name",
        "invoice_date",
        "po_number",
        "po_date",
        "pay_date",
        "quantity",
        "dollars",
        "freight"
    ]

    for column in required_columns:

        null_count = df[column].isna().sum()

        print(
            f"{column}: {null_count:,} null values"
        )

    # PO number must not be null
    if df["po_number"].isna().any():

        raise ValueError(
            "PO number contains NULL values."
        )

    print(
        "\n✓ Vendor invoice validation passed."
    )


# ============================================================
# CLEAR EXISTING VENDOR INVOICES
# ============================================================

def clear_existing_vendor_invoices(connection):
    """
    Delete existing vendor invoices for this business.

    This is executed inside the database transaction.
    """

    print("\n" + "=" * 60)
    print("CLEARING EXISTING VENDOR INVOICES")
    print("=" * 60)

    result = connection.execute(
        text(
            """
            DELETE FROM vendor_invoices
            WHERE business_id = :business_id
            """
        ),
        {
            "business_id": BUSINESS_ID
        }
    )

    print(
        f"✓ Old vendor invoice rows removed: "
        f"{result.rowcount:,}"
    )


# ============================================================
# LOAD VENDOR INVOICES
# ============================================================

def load_vendor_invoices(
    connection,
    df
):
    """
    Insert vendor invoices into MySQL.
    """

    print("\n" + "=" * 60)
    print("LOADING VENDOR INVOICES")
    print("=" * 60)

    df.to_sql(
        "vendor_invoices",
        con=connection,
        if_exists="append",
        index=False,
        method="multi"
    )

    print(
        f"✓ Vendor invoices loaded: "
        f"{len(df):,}"
    )


# ============================================================
# VERIFY DATABASE
# ============================================================

def verify_vendor_invoices(connection):

    print("\n" + "=" * 60)
    print("VERIFYING VENDOR INVOICES")
    print("=" * 60)

    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    result = connection.execute(
        text(
            """
            SELECT COUNT(*)
            FROM vendor_invoices
            WHERE business_id = :business_id
            """
        ),
        {
            "business_id": BUSINESS_ID
        }
    )

    count = result.scalar()

    print(
        f"vendor_invoices: {count:,}"
    )

    if count != EXPECTED_ROWS:

        raise ValueError(
            f"Database contains {count:,} rows. "
            f"Expected {EXPECTED_ROWS:,}."
        )

    # --------------------------------------------------------
    # Duplicate PO numbers
    # --------------------------------------------------------

    duplicate_result = connection.execute(
        text(
            """
            SELECT
                po_number,
                COUNT(*) AS row_count
            FROM vendor_invoices
            WHERE business_id = :business_id
            GROUP BY po_number
            HAVING COUNT(*) > 1
            """
        ),
        {
            "business_id": BUSINESS_ID
        }
    ).fetchall()

    if duplicate_result:

        raise ValueError(
            "Duplicate PO numbers found in "
            "vendor_invoices table."
        )

    print(
        "✓ PO number uniqueness verified."
    )

    # --------------------------------------------------------
    # Business ID verification
    # --------------------------------------------------------

    business_result = connection.execute(
        text(
            """
            SELECT
                COUNT(DISTINCT business_id)
            FROM vendor_invoices
            WHERE business_id = :business_id
            """
        ),
        {
            "business_id": BUSINESS_ID
        }
    )

    business_count = business_result.scalar()

    if business_count != 1:

        raise ValueError(
            "Unexpected business_id found."
        )

    print(
        "✓ Business ID verified."
    )

    print(
        "\n✓ Vendor invoice database "
        "verification passed."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("VENDOR INVOICE FACT ETL")
    print("=" * 60)

    try:

        # ----------------------------------------------------
        # EXTRACT
        # ----------------------------------------------------

        print(
            "\nExtracting vendor invoice data..."
        )

        df = load_csv(
            "vendor_invoice.csv"
        )

        # ----------------------------------------------------
        # TRANSFORM
        # ----------------------------------------------------
        print(
            "\nTransforming vendor invoice data..."
        )

        # Vendor invoice transformation is handled
        # inside prepare_vendor_invoices().
        # We do not call transform_all() here because
        # transform_all() expects all six datasets.

        print(
            "Vendor invoice transformation will be "
            "completed during preparation."
        )

        # ----------------------------------------------------
        # PREPARE
        # ----------------------------------------------------

        df = prepare_vendor_invoices(
            df
        )

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        validate_vendor_invoices(
            df
        )

        # ----------------------------------------------------
        # DATABASE TRANSACTION
        # ----------------------------------------------------

        print(
            "\nStarting database transaction..."
        )

        with engine.begin() as connection:

            clear_existing_vendor_invoices(
                connection
            )

            load_vendor_invoices(
                connection,
                df
            )

            verify_vendor_invoices(
                connection
            )

            print(
                "\n✓ All vendor invoice checks passed."
            )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        print("\n" + "=" * 60)
        print("TRANSACTION COMMITTED SUCCESSFULLY")
        print("=" * 60)

        print(
            "\nVENDOR INVOICE ETL COMPLETED SUCCESSFULLY"
        )

        print(
            f"\nFinal row count: {len(df):,}"
        )

        print(
            "\nNext fact table will be loaded "
            "only after this ETL is verified."
        )

    except Exception as e:

        print("\n" + "=" * 60)
        print("VENDOR INVOICE ETL FAILED")
        print("=" * 60)

        print(
            "\nError:"
        )

        print(e)

        print(
            "\nThe database transaction was rolled back."
        )

        raise


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()

