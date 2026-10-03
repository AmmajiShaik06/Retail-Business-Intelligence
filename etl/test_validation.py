from etl.extract import extract_all
from etl.validate import (
    validate_columns,
    validate_row_counts
)


data = extract_all()

print("\n=== COLUMN VALIDATION ===")

validate_columns(data)

print("\n=== ROW COUNT VALIDATION ===")

validate_row_counts(data)

print("\nETL validation successful!")