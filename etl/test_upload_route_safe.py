import io
import pandas as pd

from app import create_app
from etl.load_uploaded_sales import load_uploaded_sales


def main():

    print("=" * 60)
    print("SAFE FLASK CSV UPLOAD + ETL TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Read valid test CSV
    # --------------------------------------------------------

    file_path = "data/uploads/valid_sales.csv"

    print("\n1. Reading valid Sales CSV...")

    df = pd.read_csv(file_path)

    print(f"Uploaded rows: {len(df)}")

    # --------------------------------------------------------
    # Create Flask application
    # --------------------------------------------------------

    print("\n2. Creating Flask test client...")

    app = create_app()

    # --------------------------------------------------------
    # Replace normal loader temporarily with rollback mode
    # --------------------------------------------------------

    import app.routes.upload as upload_module

    original_loader = upload_module.load_uploaded_sales

    upload_module.load_uploaded_sales = (
        lambda data: load_uploaded_sales(
            data,
            test_mode=True
        )
    )

    try:

        # ----------------------------------------------------
        # Send CSV through actual Flask upload route
        # ----------------------------------------------------

        print("\n3. Sending CSV to /upload/...")

        csv_bytes = open(
            file_path,
            "rb"
        ).read()

        response = app.test_client().post(
            "/upload/",
            data={
                "dataset": "sales",
                "file": (
                    io.BytesIO(csv_bytes),
                    "valid_sales.csv"
                )
            },
            content_type="multipart/form-data"
        )

        print(f"\nHTTP Status: {response.status_code}")

        print("\nResponse:")
        print(response.text)

        # ----------------------------------------------------
        # Verify response
        # ----------------------------------------------------

        if response.status_code != 200:
            raise ValueError(
                f"Expected HTTP 200, "
                f"but received {response.status_code}"
            )

        result = response.get_json()

        if result["status"] != "success":
            raise ValueError(
                "Upload route did not return success."
            )

        if result["uploaded_rows"] != 2:
            raise ValueError(
                "Expected 2 uploaded rows."
            )

        if result["inserted_rows"] != 2:
            raise ValueError(
                "Expected 2 inserted rows."
            )

        if result["total_sales_rows"] != 12825363:
            raise ValueError(
                "Database row count changed unexpectedly."
            )

        print("\n" + "=" * 60)
        print("SAFE FLASK UPLOAD + ETL TEST PASSED")
        print("=" * 60)

        print(
            "\n2 test rows were processed through the actual "
            "Flask upload route."
        )

        print(
            "Database transaction was rolled back."
        )

        print(
            "Original Sales rows preserved: 12825363"
        )

    finally:

        # ----------------------------------------------------
        # Restore original loader
        # ----------------------------------------------------

        upload_module.load_uploaded_sales = original_loader


if __name__ == "__main__":
    main()
