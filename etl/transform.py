import pandas as pd


# ============================================================
# BEGIN INVENTORY
# ============================================================

def transform_begin_inventory(df):
    df = df.copy()

    # Convert date
    df["startDate"] = pd.to_datetime(
        df["startDate"],
        errors="coerce"
    )

    # Convert numeric columns
    df["Store"] = pd.to_numeric(
        df["Store"],
        errors="coerce"
    )

    df["Brand"] = pd.to_numeric(
        df["Brand"],
        errors="coerce"
    )

    df["onHand"] = pd.to_numeric(
        df["onHand"],
        errors="coerce"
    )

    df["Price"] = pd.to_numeric(
        df["Price"],
        errors="coerce"
    )

    # Keep InventoryId as STRING
    df["InventoryId"] = df["InventoryId"].astype("string")

    # Clean text columns
    for column in ["City", "Description", "Size"]:
        df[column] = df[column].astype("string").str.strip()

    return df


# ============================================================
# END INVENTORY
# ============================================================

def transform_end_inventory(df):
    df = df.copy()

    # Convert date
    df["endDate"] = pd.to_datetime(
        df["endDate"],
        errors="coerce"
    )

    # Convert numeric columns
    df["Store"] = pd.to_numeric(
        df["Store"],
        errors="coerce"
    )

    df["Brand"] = pd.to_numeric(
        df["Brand"],
        errors="coerce"
    )

    df["onHand"] = pd.to_numeric(
        df["onHand"],
        errors="coerce"
    )

    df["Price"] = pd.to_numeric(
        df["Price"],
        errors="coerce"
    )

    # Keep InventoryId as STRING
    df["InventoryId"] = df["InventoryId"].astype("string")

    # Clean text columns
    for column in ["City", "Description", "Size"]:
        df[column] = df[column].astype("string").str.strip()

    return df


# ============================================================
# PURCHASE PRICES
# ============================================================

def transform_purchase_prices(df):
    df = df.copy()

    # Numeric columns
    df["Brand"] = pd.to_numeric(
        df["Brand"],
        errors="coerce"
    )

    df["Price"] = pd.to_numeric(
        df["Price"],
        errors="coerce"
    )

    df["PurchasePrice"] = pd.to_numeric(
        df["PurchasePrice"],
        errors="coerce"
    )

    df["VendorNumber"] = pd.to_numeric(
        df["VendorNumber"],
        errors="coerce"
    )

    # Clean text columns
    for column in [
        "Description",
        "Size",
        "Volume",
        "Classification",
        "VendorName"
    ]:
        df[column] = df[column].astype("string").str.strip()

    return df


# ============================================================
# PURCHASES
# ============================================================

def transform_purchases(df):
    df = df.copy()

    # Keep InventoryId as STRING
    df["InventoryId"] = df["InventoryId"].astype("string")

    # Numeric columns
    for column in [
        "Store",
        "Brand",
        "VendorNumber",
        "PONumber",
        "Quantity"
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Decimal/numeric columns
    for column in [
        "PurchasePrice",
        "Dollars"
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Date columns
    for column in [
        "PODate",
        "ReceivingDate",
        "InvoiceDate",
        "PayDate"
    ]:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        )

    # Clean text columns
    for column in [
        "Description",
        "Size",
        "VendorName",
        "Classification"
    ]:
        df[column] = df[column].astype("string").str.strip()

    return df


# ============================================================
# SALES
# ============================================================

def transform_sales(df):
    df = df.copy()

    # Keep InventoryId as STRING
    df["InventoryId"] = df["InventoryId"].astype("string")

    # Numeric columns
    for column in [
        "Store",
        "Brand",
        "SalesQuantity",
        "VendorNo"
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Decimal columns
    for column in [
        "SalesDollars",
        "SalesPrice",
        "ExciseTax"
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Date
    df["SalesDate"] = pd.to_datetime(
        df["SalesDate"],
        errors="coerce"
    )

    # Clean text
    for column in [
        "Description",
        "Size",
        "Volume",
        "Classification",
        "VendorName"
    ]:
        df[column] = df[column].astype("string").str.strip()

    return df


# ============================================================
# VENDOR INVOICE
# ============================================================

def transform_vendor_invoice(df):
    df = df.copy()

    # Numeric columns
    for column in [
        "VendorNumber",
        "PONumber",
        "Quantity"
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Decimal columns
    for column in [
        "Dollars",
        "Freight"
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Date columns
    for column in [
        "InvoiceDate",
        "PODate",
        "PayDate"
    ]:
        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        )

    # Clean text
    for column in [
        "VendorName",
        "Approval"
    ]:
        df[column] = df[column].astype("string").str.strip()

    return df


# ============================================================
# TRANSFORM ALL DATASETS
# ============================================================

def transform_all(data):

    transformed = {}

    transformed["begin_inventory"] = transform_begin_inventory(
        data["begin_inventory"]
    )

    transformed["end_inventory"] = transform_end_inventory(
        data["end_inventory"]
    )

    transformed["purchase_prices"] = transform_purchase_prices(
        data["purchase_prices"]
    )

    transformed["purchases"] = transform_purchases(
        data["purchases"]
    )

    transformed["sales"] = transform_sales(
        data["sales"]
    )

    transformed["vendor_invoice"] = transform_vendor_invoice(
        data["vendor_invoice"]
    )

    return transformed