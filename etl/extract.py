from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"


def load_csv(filename):
    """
    Read a CSV file from the raw data directory.
    """
    file_path = RAW_DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    print(f"Reading: {filename}")

    df = pd.read_csv(file_path)

    print(
        f"Loaded {filename}: "
        f"{df.shape[0]:,} rows × {df.shape[1]} columns"
    )

    return df


def extract_all():
    """
    Extract all raw datasets.
    """

    data = {}

    data["begin_inventory"] = load_csv(
        "begin_inventory.csv"
    )

    data["end_inventory"] = load_csv(
        "end_inventory.csv"
    )

    data["purchase_prices"] = load_csv(
        "purchase_prices.csv"
    )

    data["purchases"] = load_csv(
        "purchases.csv"
    )

    data["sales"] = load_csv(
        "sales.csv"
    )

    data["vendor_invoice"] = load_csv(
        "vendor_invoice.csv"
    )

    return data