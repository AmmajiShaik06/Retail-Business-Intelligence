from flask import Blueprint, render_template, request
from pathlib import Path
import pandas as pd

from etl.validate import REQUIRED_COLUMNS
from etl.load_uploaded_sales import load_uploaded_sales


upload = Blueprint(
    "upload",
    __name__,
    url_prefix="/upload"
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"


@upload.route("/", methods=["GET", "POST"])
def upload_page():

    # ========================================================
    # GET REQUEST
    # ========================================================

    if request.method == "GET":
        return render_template("upload.html")

    # ========================================================
    # GET SELECTED DATASET AND FILE
    # ========================================================

    dataset = request.form.get("dataset")
    file = request.files.get("file")

    # ========================================================
    # VALIDATE DATASET SELECTION
    # ========================================================

    if not dataset:
        return {
            "status": "error",
            "message": "Please select a dataset."
        }, 400

    # ========================================================
    # VALIDATE DATASET NAME
    # ========================================================

    if dataset not in REQUIRED_COLUMNS:
        return {
            "status": "error",
            "message": f"Invalid dataset: {dataset}"
        }, 400

    # ========================================================
    # VALIDATE FILE SELECTION
    # ========================================================

    if file is None or file.filename == "":
        return {
            "status": "error",
            "message": "Please select a CSV file."
        }, 400

    # ========================================================
    # VALIDATE FILE EXTENSION
    # ========================================================

    if not file.filename.lower().endswith(".csv"):
        return {
            "status": "error",
            "message": "Only CSV files are allowed."
        }, 400

    # ========================================================
    # READ CSV
    # ========================================================

    try:

        df = pd.read_csv(file)

    except Exception as e:

        return {
            "status": "error",
            "message": f"Could not read CSV file: {str(e)}"
        }, 400

    # ========================================================
    # VALIDATE REQUIRED COLUMNS
    # ========================================================

    required_columns = REQUIRED_COLUMNS[dataset]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        return {
            "status": "error",
            "message": "CSV validation failed.",
            "dataset": dataset,
            "missing_columns": missing_columns,
            "uploaded_columns": list(df.columns)
        }, 400

    # ========================================================
    # VALIDATE ROW COUNT
    # ========================================================

    if df.empty:

        return {
            "status": "error",
            "message": "CSV validation failed: file contains 0 rows."
        }, 400

    # ========================================================
    # CREATE UPLOAD DIRECTORY
    # ========================================================

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # SAVE UPLOADED CSV
    # ========================================================

    filename = Path(file.filename).name

    save_path = UPLOAD_DIR / filename

    df.to_csv(
        save_path,
        index=False
    )

    # ========================================================
    # SALES ETL
    # ========================================================

    if dataset == "sales":

        try:

            result = load_uploaded_sales(df)

        except Exception as e:

            return {
                "status": "error",
                "message": "Sales ETL failed.",
                "details": str(e),
                "dataset": dataset,
                "filename": filename
            }, 400

        return {
            "status": "success",
            "message": (
                "Sales CSV uploaded, validated, "
                "and loaded into MySQL successfully."
            ),
            "dataset": dataset,
            "filename": filename,
            "uploaded_rows": result["uploaded_rows"],
            "inserted_rows": result["inserted_rows"],
            "total_sales_rows": result["total_rows_after"],
            "path": str(save_path)
        }

    # ========================================================
    # OTHER DATASETS
    # ========================================================

    return {
        "status": "success",
        "message": (
            "CSV uploaded and validated successfully. "
            "ETL loading for this dataset is not connected yet."
        ),
        "dataset": dataset,
        "filename": filename,
        "rows": len(df),
        "columns": list(df.columns),
        "path": str(save_path)
    }