from sqlalchemy import text
from database.connection import engine
from etl.extract import extract_all
from etl.transform import transform_all


# ============================================================
# CONFIGURATION
# ============================================================

BUSINESS_ID = 1


# ============================================================
# PREPARE VENDORS
# ============================================================

def prepare_vendors(data):
    """
    Create vendor master data using unique
    vendor_number + vendor_name combinations.
    """

    purchases = data["purchases"].copy()
    vendor_invoice = data["vendor_invoice"].copy()
    purchase_prices = data["purchase_prices"].copy()

    # Combine vendor information from all relevant sources
    vendors = []

    for df in [purchases, vendor_invoice, purchase_prices]:

        temp = df[["VendorNumber", "VendorName"]].copy()

        temp["VendorNumber"] = temp["VendorNumber"].astype("Int64")
        temp["VendorName"] = temp["VendorName"].astype("string").str.strip()

        temp = temp.dropna(subset=["VendorNumber", "VendorName"])

        vendors.append(temp)

    vendor_master = (
        __import__("pandas")
        .concat(vendors, ignore_index=True)
        .drop_duplicates(
            subset=["VendorNumber", "VendorName"]
        )
        .sort_values(
            by=["VendorNumber", "VendorName"]
        )
        .reset_index(drop=True)
    )

    # Show information about vendor-number conflicts
    conflict_check = (
        vendor_master.groupby("VendorNumber")["VendorName"]
        .nunique()
    )

    conflicts = conflict_check[conflict_check > 1]

    print(
        f"Unique vendor_number + vendor_name combinations: "
        f"{len(vendor_master):,}"
    )

    print(
        f"Vendor numbers with multiple names: "
        f"{len(conflicts):,}"
    )

    if len(conflicts) > 0:
        print("\nVendor-number conflicts:")

        for vendor_number in conflicts.index:
            names = (
                vendor_master[
                    vendor_master["VendorNumber"] == vendor_number
                ]["VendorName"]
                .tolist()
            )

            print(f"{vendor_number}: {names}")

    vendor_master = vendor_master.rename(
        columns={
            "VendorNumber": "vendor_number",
            "VendorName": "vendor_name"
        }
    )

    vendor_master["business_id"] = BUSINESS_ID

    vendor_master = vendor_master[
        [
            "business_id",
            "vendor_number",
            "vendor_name"
        ]
    ]

    return vendor_master


# ============================================================
# PREPARE STORES
# ============================================================

def prepare_stores(data):
    """
    Create store master data using Store -> City relationship.
    """

    import pandas as pd

    begin_inventory = data["begin_inventory"].copy()
    end_inventory = data["end_inventory"].copy()

    stores = pd.concat(
        [
            begin_inventory[["Store", "City"]],
            end_inventory[["Store", "City"]]
        ],
        ignore_index=True
    )

    # Clean values
    stores["Store"] = pd.to_numeric(
        stores["Store"],
        errors="coerce"
    )

    stores["City"] = (
        stores["City"]
        .astype("string")
        .str.strip()
    )

    # Remove rows where Store is missing
    stores = stores.dropna(subset=["Store"])

    # Remove blank cities
    stores["City"] = stores["City"].replace(
        ["", "nan", "None"],
        pd.NA
    )

    # Check Store -> City relationship
    city_counts = (
        stores.dropna(subset=["City"])
        .groupby("Store")["City"]
        .nunique()
    )

    inconsistent_stores = city_counts[
        city_counts > 1
    ]

    if len(inconsistent_stores) > 0:

        print(
            "\nWARNING: Store -> City relationship "
            "has inconsistencies."
        )

        for store in inconsistent_stores.index:

            cities = (
                stores[
                    stores["Store"] == store
                ]["City"]
                .dropna()
                .unique()
                .tolist()
            )

            print(
                f"Store {store}: {cities}"
            )

        raise ValueError(
            "Store -> City relationship is inconsistent. "
            "Master loading stopped."
        )

    print(
        "✓ Store → City relationship is consistent."
    )

    # For each store, select the available city
    stores = (
        stores
        .sort_values(["Store", "City"])
        .drop_duplicates(
            subset=["Store"],
            keep="first"
        )
    )

    stores = stores.rename(
        columns={
            "Store": "store_number",
            "City": "city"
        }
    )

    stores["business_id"] = BUSINESS_ID

    stores = stores[
        [
            "business_id",
            "store_number",
            "city"
        ]
    ]

    return stores


# ============================================================
# PREPARE PRODUCTS
# ============================================================

def prepare_products(data):
    """
    Create product master data from purchase_prices.
    """

    products = data["purchase_prices"].copy()

    products = products[
        [
            "Brand",
            "Description",
            "Size",
            "Volume",
            "Classification"
        ]
    ].copy()

    # Clean values
    products["Brand"] = pd_to_numeric(
        products["Brand"]
    )

    products["Description"] = (
        products["Description"]
        .astype("string")
        .str.strip()
    )

    products["Size"] = (
        products["Size"]
        .astype("string")
        .str.strip()
    )

    products["Volume"] = (
        products["Volume"]
        .astype("string")
        .str.strip()
    )

    products["Classification"] = (
        products["Classification"]
        .astype("string")
        .str.strip()
    )

    # Remove exact duplicate product combinations
    before = len(products)

    products = products.drop_duplicates(
        subset=[
            "Brand",
            "Description",
            "Size"
        ]
    )

    duplicates_removed = before - len(products)

    print(
        f"Duplicate product combinations removed: "
        f"{duplicates_removed:,}"
    )

    products = products.rename(
        columns={
            "Brand": "brand",
            "Description": "description",
            "Size": "size",
            "Volume": "volume",
            "Classification": "classification"
        }
    )

    products["business_id"] = BUSINESS_ID

    products = products[
        [
            "business_id",
            "brand",
            "description",
            "size",
            "volume",
            "classification"
        ]
    ]

    return products


# ============================================================
# NUMERIC HELPER
# ============================================================

def pd_to_numeric(series):
    """
    Safely convert a pandas Series to numeric.
    """

    import pandas as pd

    return pd.to_numeric(
        series,
        errors="coerce"
    ).astype("Int64")


# ============================================================
# CLEAR OLD MASTER DATA
# ============================================================

def clear_existing_masters(connection):
    """
    Delete only the current business's master records.

    This happens inside the transaction.
    If anything fails later, the deletion is rolled back.
    """

    print("\n" + "=" * 60)
    print("CLEARING EXISTING MASTER DATA")
    print("=" * 60)

    tables = [
        "vendors",
        "stores",
        "products"
    ]

    for table in tables:

        result = connection.execute(
            text(
                f"""
                DELETE FROM {table}
                WHERE business_id = :business_id
                """
            ),
            {
                "business_id": BUSINESS_ID
            }
        )

        print(
            f"✓ {table}: "
            f"{result.rowcount:,} old rows removed"
        )


# ============================================================
# LOAD MASTER DATA
# ============================================================

def load_master_data(
    connection,
    vendors,
    stores,
    products
):
    """
    Insert prepared master data into MySQL.
    """

    print("\n" + "=" * 60)
    print("LOADING VENDORS")
    print("=" * 60)

    vendors.to_sql(
        "vendors",
        con=connection,
        if_exists="append",
        index=False,
        method="multi"
    )

    print(
        f"✓ Vendors loaded: {len(vendors):,}"
    )

    print("\n" + "=" * 60)
    print("LOADING STORES")
    print("=" * 60)

    stores.to_sql(
        "stores",
        con=connection,
        if_exists="append",
        index=False,
        method="multi"
    )

    print(
        f"✓ Stores loaded: {len(stores):,}"
    )

    print("\n" + "=" * 60)
    print("LOADING PRODUCTS")
    print("=" * 60)

    products.to_sql(
        "products",
        con=connection,
        if_exists="append",
        index=False,
        method="multi"
    )

    print(
        f"✓ Products loaded: {len(products):,}"
    )


# ============================================================
# VERIFY MASTER DATA
# ============================================================

def verify_master_data(connection):
    """
    Verify the master tables after loading.
    """

    print("\n" + "=" * 60)
    print("VERIFYING MASTER TABLES")
    print("=" * 60)

    expected_counts = {
        "vendors": None,
        "stores": None,
        "products": None
    }

    for table in expected_counts:

        result = connection.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE business_id = :business_id
                """
            ),
            {
                "business_id": BUSINESS_ID
            }
        )

        count = result.scalar()

        expected_counts[table] = count

        print(
            f"{table}: {count:,}"
        )

    # Basic validation
    if expected_counts["vendors"] == 0:
        raise ValueError(
            "Vendor table is empty."
        )

    if expected_counts["stores"] == 0:
        raise ValueError(
            "Store table is empty."
        )

    if expected_counts["products"] == 0:
        raise ValueError(
            "Product table is empty."
        )

    # Check duplicate vendor combinations
    duplicate_vendors = connection.execute(
        text(
            """
            SELECT
                vendor_number,
                vendor_name,
                COUNT(*) AS row_count
            FROM vendors
            WHERE business_id = :business_id
            GROUP BY
                vendor_number,
                vendor_name
            HAVING COUNT(*) > 1
            """
        ),
        {
            "business_id": BUSINESS_ID
        }
    ).fetchall()

    if duplicate_vendors:

        raise ValueError(
            "Duplicate vendor_number + vendor_name "
            "combinations found."
        )

    # Check duplicate stores
    duplicate_stores = connection.execute(
        text(
            """
            SELECT
                store_number,
                COUNT(*) AS row_count
            FROM stores
            WHERE business_id = :business_id
            GROUP BY store_number
            HAVING COUNT(*) > 1
            """
        ),
        {
            "business_id": BUSINESS_ID
        }
    ).fetchall()

    if duplicate_stores:

        raise ValueError(
            "Duplicate store numbers found."
        )

    # Check duplicate products
    duplicate_products = connection.execute(
        text(
            """
            SELECT
                brand,
                description,
                size,
                COUNT(*) AS row_count
            FROM products
            WHERE business_id = :business_id
            GROUP BY
                brand,
                description,
                size
            HAVING COUNT(*) > 1
            """
        ),
        {
            "business_id": BUSINESS_ID
        }
    ).fetchall()

    if duplicate_products:

        raise ValueError(
            "Duplicate product combinations found."
        )

    print("\n✓ Master-table verification passed.")


# ============================================================
# MAIN ETL
# ============================================================

def main():

    print("=" * 60)
    print("MASTER DATA ETL - SAFE / RERUNNABLE VERSION")
    print("=" * 60)

    try:

        # ----------------------------------------------------
        # EXTRACT
        # ----------------------------------------------------

        print("\nExtracting required master-data files...")

        data = extract_all()

        # ----------------------------------------------------
        # TRANSFORM
        # ----------------------------------------------------

        print("\nTransforming required master-data files...")

        data = transform_all(data)

        print("\nTransformation completed.")

        # ----------------------------------------------------
        # PREPARE MASTER DATA
        # ----------------------------------------------------

        print("\nPreparing master tables...")

        vendors = prepare_vendors(data)
        stores = prepare_stores(data)
        products = prepare_products(data)

        # ----------------------------------------------------
        # DATABASE TRANSACTION
        # ----------------------------------------------------

        print("\nStarting database transaction...")

        with engine.begin() as connection:

            # Delete old master data
            clear_existing_masters(connection)

            # Insert new master data
            load_master_data(
                connection,
                vendors,
                stores,
                products
            )

            # Verify before commit
            verify_master_data(connection)

            print(
                "\n✓ All master-data checks passed."
            )

        # ----------------------------------------------------
        # COMMIT SUCCESS
        # ----------------------------------------------------

        print("\n" + "=" * 60)
        print("TRANSACTION COMMITTED SUCCESSFULLY")
        print("=" * 60)

        print("\nMASTER DATA ETL COMPLETED SUCCESSFULLY")

        print("\nFinal master counts:")
        print(
            f"Vendors  : {len(vendors):,}"
        )
        print(
            f"Stores   : {len(stores):,}"
        )
        print(
            f"Products : {len(products):,}"
        )

        print(
            "\nSales data was intentionally NOT processed."
        )

        print(
            "Sales will be loaded separately using "
            "chunk-based ETL."
        )

    except Exception as e:

        print("\n" + "=" * 60)
        print("MASTER DATA ETL FAILED")
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
# RUN SCRIPT
# ============================================================

if __name__ == "__main__":
    main()