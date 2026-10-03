import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"

PURCHASES_FILE = RAW_DATA_PATH / "purchases.csv"
PURCHASE_PRICES_FILE = RAW_DATA_PATH / "purchase_prices.csv"

CHUNK_SIZE = 50_000


# ============================================================
# LOAD PURCHASE-PRICE MASTER
# ============================================================

def load_purchase_price_master():

    print("\nLoading purchase_prices.csv...")

    purchase_prices = pd.read_csv(
        PURCHASE_PRICES_FILE
    )

    purchase_prices["Brand"] = pd.to_numeric(
        purchase_prices["Brand"],
        errors="coerce"
    )

    purchase_prices["VendorNumber"] = pd.to_numeric(
        purchase_prices["VendorNumber"],
        errors="coerce"
    )

    purchase_prices = purchase_prices.dropna(
        subset=[
            "Brand",
            "VendorNumber"
        ]
    )

    purchase_prices["Brand"] = (
        purchase_prices["Brand"]
        .astype(int)
    )

    purchase_prices["VendorNumber"] = (
        purchase_prices["VendorNumber"]
        .astype(int)
    )

    purchase_prices["VendorName"] = (
        purchase_prices["VendorName"]
        .astype("string")
        .str.strip()
    )

    purchase_prices["Description"] = (
        purchase_prices["Description"]
        .astype("string")
        .str.strip()
    )

    print(
        f"Purchase-price rows loaded: "
        f"{len(purchase_prices):,}"
    )

    return purchase_prices


# ============================================================
# EXTRACT UNIQUE PURCHASE COMBINATIONS
# ============================================================

def load_purchase_combinations():

    print("\nReading purchases.csv in chunks...")

    purchase_combinations = []

    total_rows = 0

    for chunk in pd.read_csv(
        PURCHASES_FILE,
        usecols=[
            "Brand",
            "VendorNumber",
            "VendorName"
        ],
        chunksize=CHUNK_SIZE
    ):

        chunk["Brand"] = pd.to_numeric(
            chunk["Brand"],
            errors="coerce"
        )

        chunk["VendorNumber"] = pd.to_numeric(
            chunk["VendorNumber"],
            errors="coerce"
        )

        chunk = chunk.dropna(
            subset=[
                "Brand",
                "VendorNumber"
            ]
        )

        chunk["Brand"] = (
            chunk["Brand"]
            .astype(int)
        )

        chunk["VendorNumber"] = (
            chunk["VendorNumber"]
            .astype(int)
        )

        chunk["VendorName"] = (
            chunk["VendorName"]
            .astype("string")
            .str.strip()
        )

        combinations = chunk[
            [
                "Brand",
                "VendorNumber",
                "VendorName"
            ]
        ].drop_duplicates()

        purchase_combinations.append(
            combinations
        )

        total_rows += len(chunk)

        print(
            f"Processed purchase rows: "
            f"{total_rows:,}"
        )

    purchases = pd.concat(
        purchase_combinations,
        ignore_index=True
    )

    purchases = purchases.drop_duplicates(
        subset=[
            "Brand",
            "VendorNumber"
        ]
    )

    print(
        f"\nUnique purchase Brand + Vendor combinations: "
        f"{len(purchases):,}"
    )

    return purchases


# ============================================================
# MATCH PURCHASES WITH PURCHASE-PRICE MASTER
# ============================================================

def verify_matching():

    print("\n" + "=" * 70)
    print("PURCHASE PRICE MASTER MATCHING")
    print("=" * 70)

    purchase_prices = load_purchase_price_master()

    purchases = load_purchase_combinations()

    # --------------------------------------------------------
    # Unique Brand + Vendor combinations in master
    # --------------------------------------------------------

    price_master_combinations = (
        purchase_prices[
            [
                "Brand",
                "VendorNumber"
            ]
        ]
        .drop_duplicates()
    )

    print(
        f"\nUnique purchase-price Brand + Vendor combinations: "
        f"{len(price_master_combinations):,}"
    )

    # --------------------------------------------------------
    # LEFT JOIN
    #
    # Every purchase combination must be preserved.
    # --------------------------------------------------------

    matched = purchases.merge(
        price_master_combinations,
        on=[
            "Brand",
            "VendorNumber"
        ],
        how="left",
        indicator=True
    )

    matched_count = (
        matched["_merge"] == "both"
    ).sum()

    unmatched_count = (
        matched["_merge"] == "left_only"
    ).sum()

    # --------------------------------------------------------
    # DISPLAY SUMMARY
    # --------------------------------------------------------

    print("\nMatching Summary:")
    print(
        f"Purchase combinations: "
        f"{len(purchases):,}"
    )

    print(
        f"Matched combinations: "
        f"{matched_count:,}"
    )

    print(
        f"Unmatched combinations: "
        f"{unmatched_count:,}"
    )

    match_percentage = (
        matched_count
        / len(purchases)
        * 100
    )

    print(
        f"Match percentage: "
        f"{match_percentage:.2f}%"
    )

    # --------------------------------------------------------
    # DISPLAY UNMATCHED COMBINATIONS
    # --------------------------------------------------------

    unmatched = (
        matched[
            matched["_merge"] == "left_only"
        ]
        [
            [
                "Brand",
                "VendorNumber",
                "VendorName"
            ]
        ]
        .sort_values(
            [
                "VendorNumber",
                "Brand"
            ]
        )
    )

    print("\n" + "=" * 70)
    print("UNMATCHED PURCHASE BRAND + VENDOR COMBINATIONS")
    print("=" * 70)

    if len(unmatched) > 0:

        print(
            unmatched.to_string(
                index=False
            )
        )

    else:

        print(
            "No unmatched combinations found."
        )

    # --------------------------------------------------------
    # VERIFY EXPECTED RESULT
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("VERIFICATION")
    print("=" * 70)

    expected_purchase_combinations = 10_693
    expected_matched = 10_649
    expected_unmatched = 44

    if len(purchases) == expected_purchase_combinations:
        print(
            "Purchase combination count: PASSED"
        )
    else:
        print(
            "Purchase combination count: FAILED"
        )

    if matched_count == expected_matched:
        print(
            "Matched combination count: PASSED"
        )
    else:
        print(
            "Matched combination count: FAILED"
        )

    if unmatched_count == expected_unmatched:
        print(
            "Unmatched combination count: PASSED"
        )
    else:
        print(
            "Unmatched combination count: FAILED"
        )

    print("\n" + "=" * 70)
    print("PURCHASE PRICE MATCHING VERIFICATION COMPLETE")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    verify_matching()