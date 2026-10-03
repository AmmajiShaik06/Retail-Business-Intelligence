REQUIRED_COLUMNS = {
    "begin_inventory": [
        "InventoryId",
        "Store",
        "City",
        "Brand",
        "Description",
        "Size",
        "onHand",
        "Price",
        "startDate"
    ],

    "end_inventory": [
        "InventoryId",
        "Store",
        "City",
        "Brand",
        "Description",
        "Size",
        "onHand",
        "Price",
        "endDate"
    ],

    "purchase_prices": [
        "Brand",
        "Description",
        "Price",
        "Size",
        "Volume",
        "Classification",
        "PurchasePrice",
        "VendorNumber",
        "VendorName"
    ],

    "purchases": [
        "InventoryId",
        "Store",
        "Brand",
        "Description",
        "Size",
        "VendorNumber",
        "VendorName",
        "PONumber",
        "PODate",
        "ReceivingDate",
        "InvoiceDate",
        "PayDate",
        "PurchasePrice",
        "Quantity",
        "Dollars",
        "Classification"
    ],

    "sales": [
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
        "VendorName"
    ],

    "vendor_invoice": [
        "VendorNumber",
        "VendorName",
        "InvoiceDate",
        "PONumber",
        "PODate",
        "PayDate",
        "Quantity",
        "Dollars",
        "Freight",
        "Approval"
    ]
}


def validate_columns(data):
    """
    Verify that every dataset contains
    the expected source columns.
    """

    for dataset_name, required_columns in REQUIRED_COLUMNS.items():

        if dataset_name not in data:
            raise ValueError(
                f"Missing dataset: {dataset_name}"
            )

        actual_columns = set(
            data[dataset_name].columns
        )

        missing_columns = [
            column
            for column in required_columns
            if column not in actual_columns
        ]

        if missing_columns:
            raise ValueError(
                f"{dataset_name} is missing columns: "
                f"{missing_columns}"
            )

        print(
            f"✓ {dataset_name}: "
            f"all required columns present"
        )


def validate_row_counts(data):

    for dataset_name, df in data.items():

        if df.empty:
            raise ValueError(
                f"{dataset_name} contains 0 rows!"
            )

        print(
            f"✓ {dataset_name}: "
            f"{len(df):,} rows"
        )