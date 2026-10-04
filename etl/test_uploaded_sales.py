import pandas as pd
from sqlalchemy import text

from database.connection import engine
from etl.load_uploaded_sales import (
    prepare_uploaded_sales,
    validate_uploaded_sales,
)


BUSINESS_ID = 1

UPLOAD_FILE = (
    "data/uploads/valid_sales.csv"
)


def main():

    print("=" * 60)
    print("SAFE UPLOADED SALES ETL TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Read uploaded CSV
    # --------------------------------------------------------

    print("\n1. Reading uploaded CSV...")

    df = pd.read_csv(UPLOAD_FILE)

    print(f"Uploaded rows: {len(df)}")

    # --------------------------------------------------------
    # Prepare data
    # --------------------------------------------------------

    print("\n2. Preparing Sales data...")

    prepared_df = prepare_uploaded_sales(df)

    print(f"Prepared rows: {len(prepared_df)}")

    # --------------------------------------------------------
    # Validate data
    # --------------------------------------------------------

    print("\n3. Validating Sales data...")

    validate_uploaded_sales(prepared_df)

    print("Validation: PASSED")

    # --------------------------------------------------------
    # Start transaction
    # --------------------------------------------------------

    print("\n4. Starting rollback-safe transaction...")

    connection = engine.connect()
    transaction = connection.begin()

    try:

        # ----------------------------------------------------
        # Count before insert
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

        print(f"Sales rows before insert: {before_count}")

        # ----------------------------------------------------
        # Insert test rows
        # ----------------------------------------------------

        print("\n5. Inserting test rows...")

        prepared_df.to_sql(
            name="sales",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=5000,
            method="multi",
        )

        # ----------------------------------------------------
        # Count after insert
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

        print(f"Sales rows after insert: {after_count}")
        print(f"Rows inserted: {inserted_rows}")

        # ----------------------------------------------------
        # Verify insertion
        # ----------------------------------------------------

        if inserted_rows != len(prepared_df):
            raise ValueError(
                f"Expected {len(prepared_df)} rows, "
                f"but {inserted_rows} rows were inserted."
            )

        print("Insertion verification: PASSED")

        # ----------------------------------------------------
        # Rollback
        # ----------------------------------------------------

        print("\n6. Rolling back test transaction...")

        transaction.rollback()

        print("Rollback: COMPLETED")

    except Exception:

        transaction.rollback()

        raise

    finally:

        connection.close()

    # --------------------------------------------------------
    # Verify original count after rollback
    # --------------------------------------------------------

    print("\n7. Verifying database after rollback...")

    with engine.connect() as connection:

        final_count = connection.execute(
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

    print(f"Sales rows after rollback: {final_count}")

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    if final_count != before_count:

        raise ValueError(
            "SAFETY CHECK FAILED: "
            "Sales row count was not restored."
        )

    print("\n" + "=" * 60)
    print("SAFE ETL TEST PASSED")
    print("=" * 60)

    print(
        f"\nOriginal Sales rows preserved: {final_count}"
    )


if __name__ == "__main__":
    main()