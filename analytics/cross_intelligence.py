
"""
Phase 10.6 - Cross Intelligence

Creates three cross-dimensional intelligence datasets:

1. Vendor x Store Intelligence
2. Store x Product Intelligence
3. Vendor x Product Intelligence

Important:
- Uses verified MySQL fact tables directly.
- Does NOT modify MySQL.
- Does NOT rerun ETL.
- Does NOT depend on product_intelligence.csv.
- Does NOT depend on inventory_intelligence.csv.
- Uses chunk-based processing to avoid loading the complete
  sales/purchases tables into memory at once.

Outputs:

data/processed/vendor_store_intelligence.csv
data/processed/store_product_intelligence.csv
data/processed/vendor_product_intelligence.csv
"""

import os
import pandas as pd

from database.connection import engine


# ============================================================
# CONFIGURATION
# ============================================================

BUSINESS_ID = 1
CHUNK_SIZE = 250_000

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "data",
    "processed"
)


# ============================================================
# EXPECTED SOURCE TOTALS
# ============================================================

EXPECTED_SALES_ROWS = 12_825_363
EXPECTED_SALES_QUANTITY = 32_917_876
EXPECTED_SALES_REVENUE = 452_062_952.02

EXPECTED_PURCHASE_ROWS = 2_372_474
EXPECTED_PURCHASE_QUANTITY = 33_584_377
EXPECTED_PURCHASE_SPENDING = 321_900_765.53


# ============================================================
# HELPER
# ============================================================

def clean_text(series):

    return (
        series
        .astype("string")
        .str.strip()
    )


# ============================================================
# LOAD SALES - VENDOR x STORE
# ============================================================

def load_vendor_store_sales():

    print("\nLoading sales for Vendor x Store analysis...")

    totals = []

    total_rows = 0
    total_quantity = 0
    total_revenue = 0.0

    query = """
        SELECT
            store_number,
            vendor_number,
            vendor_name,
            sales_quantity,
            sales_dollars
        FROM sales
        WHERE business_id = %s
        ORDER BY sales_id
    """

    last_sales_id = 0

    while True:

        chunk_query = f"""
            SELECT
                sales_id,
                store_number,
                vendor_number,
                vendor_name,
                sales_quantity,
                sales_dollars
            FROM sales
            WHERE business_id = %s
              AND sales_id > {last_sales_id}
            ORDER BY sales_id
            LIMIT {CHUNK_SIZE}
        """

        chunk = pd.read_sql_query(
            chunk_query,
            engine,
            params=(BUSINESS_ID,)
        )

        if chunk.empty:
            break

        last_sales_id = int(
            chunk["sales_id"].max()
        )

        total_rows += len(chunk)

        total_quantity += int(
            chunk["sales_quantity"].sum()
        )

        total_revenue += float(
            chunk["sales_dollars"].sum()
        )

        chunk["vendor_name"] = clean_text(
            chunk["vendor_name"]
        )

        grouped = (
            chunk
            .groupby(
                [
                    "store_number",
                    "vendor_number",
                    "vendor_name"
                ],
                dropna=False
            )
            .agg(
                sales_quantity=(
                    "sales_quantity",
                    "sum"
                ),
                sales_revenue=(
                    "sales_dollars",
                    "sum"
                )
            )
            .reset_index()
        )

        totals.append(grouped)

        print(
            f"Sales rows processed: "
            f"{total_rows:,}",
            end="\r"
        )

    print()

    sales = pd.concat(
        totals,
        ignore_index=True
    )

    sales = (
        sales
        .groupby(
            [
                "store_number",
                "vendor_number",
                "vendor_name"
            ],
            dropna=False
        )
        .agg(
            sales_quantity=(
                "sales_quantity",
                "sum"
            ),
            sales_revenue=(
                "sales_revenue",
                "sum"
            )
        )
        .reset_index()
    )

    return (
        sales,
        total_rows,
        total_quantity,
        total_revenue
    )


# ============================================================
# LOAD PURCHASES - VENDOR x STORE
# ============================================================

def load_vendor_store_purchases():

    print("\nLoading purchases for Vendor x Store analysis...")

    totals = []

    total_rows = 0
    total_quantity = 0
    total_spending = 0.0

    last_purchase_id = 0

    while True:

        chunk_query = f"""
            SELECT
                purchase_id,
                store_number,
                vendor_number,
                vendor_name,
                quantity,
                dollars
            FROM purchases
            WHERE business_id = %s
              AND purchase_id > {last_purchase_id}
            ORDER BY purchase_id
            LIMIT {CHUNK_SIZE}
        """

        chunk = pd.read_sql_query(
            chunk_query,
            engine,
            params=(BUSINESS_ID,)
        )

        if chunk.empty:
            break

        last_purchase_id = int(
            chunk["purchase_id"].max()
        )

        total_rows += len(chunk)

        total_quantity += int(
            chunk["quantity"].sum()
        )

        total_spending += float(
            chunk["dollars"].sum()
        )

        chunk["vendor_name"] = clean_text(
            chunk["vendor_name"]
        )

        grouped = (
            chunk
            .groupby(
                [
                    "store_number",
                    "vendor_number",
                    "vendor_name"
                ],
                dropna=False
            )
            .agg(
                purchase_quantity=(
                    "quantity",
                    "sum"
                ),
                purchase_spending=(
                    "dollars",
                    "sum"
                )
            )
            .reset_index()
        )

        totals.append(grouped)

        print(
            f"Purchase rows processed: "
            f"{total_rows:,}",
            end="\r"
        )

    print()

    purchases = pd.concat(
        totals,
        ignore_index=True
    )

    purchases = (
        purchases
        .groupby(
            [
                "store_number",
                "vendor_number",
                "vendor_name"
            ],
            dropna=False
        )
        .agg(
            purchase_quantity=(
                "purchase_quantity",
                "sum"
            ),
            purchase_spending=(
                "purchase_spending",
                "sum"
            )
        )
        .reset_index()
    )

    return (
        purchases,
        total_rows,
        total_quantity,
        total_spending
    )


# ============================================================
# BUILD VENDOR x STORE INTELLIGENCE
# ============================================================

def build_vendor_store_intelligence(
    sales,
    purchases
):

    print(
        "\nBuilding Vendor x Store Intelligence..."
    )

    df = pd.merge(
        sales,
        purchases,
        on=[
            "store_number",
            "vendor_number",
            "vendor_name"
        ],
        how="outer"
    )

    numeric_columns = [
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending"
    ]

    for column in numeric_columns:

        df[column] = (
            df[column]
            .fillna(0)
        )

    df["quantity_balance"] = (
        df["purchase_quantity"]
        - df["sales_quantity"]
    )

    df["value_difference"] = (
        df["sales_revenue"]
        - df["purchase_spending"]
    )

    df["sales_purchase_value_ratio"] = 0.0

    mask = (
        df["purchase_spending"] > 0
    )

    df.loc[
        mask,
        "sales_purchase_value_ratio"
    ] = (
        df.loc[
            mask,
            "sales_revenue"
        ]
        /
        df.loc[
            mask,
            "purchase_spending"
        ]
    )

    df["sales_contribution_percent"] = (
        df["sales_revenue"]
        /
        df["sales_revenue"].sum()
        * 100
    )

    df["purchase_contribution_percent"] = (
        df["purchase_spending"]
        /
        df["purchase_spending"].sum()
        * 100
    )

    df["quantity_balance_percent"] = 0.0

    quantity_mask = (
        df["purchase_quantity"] > 0
    )

    df.loc[
        quantity_mask,
        "quantity_balance_percent"
    ] = (
        df.loc[
            quantity_mask,
            "quantity_balance"
        ]
        /
        df.loc[
            quantity_mask,
            "purchase_quantity"
        ]
        * 100
    )

    df["cross_signal"] = "Balanced Activity"

    df.loc[
        (
            (df["purchase_quantity"] > df["sales_quantity"])
            &
            (df["quantity_balance"] > 0)
        ),
        "cross_signal"
    ] = "Purchases Exceed Sales"

    df.loc[
        (
            (df["sales_quantity"] > df["purchase_quantity"])
            &
            (df["quantity_balance"] < 0)
        ),
        "cross_signal"
    ] = "Sales Exceed Purchases"

    df.loc[
        (
            (df["sales_quantity"] == 0)
            &
            (df["purchase_quantity"] > 0)
        ),
        "cross_signal"
    ] = "Purchase Without Sales"

    df.loc[
        (
            (df["purchase_quantity"] == 0)
            &
            (df["sales_quantity"] > 0)
        ),
        "cross_signal"
    ] = "Sales Without Purchase"

    df = df.sort_values(
        "sales_revenue",
        ascending=False
    ).reset_index(
        drop=True
    )

    return df


# ============================================================
# LOAD SALES - STORE x PRODUCT
# ============================================================

def load_store_product_sales():

    print(
        "\nLoading sales for Store x Product analysis..."
    )

    totals = []

    total_rows = 0

    last_sales_id = 0

    while True:

        query = f"""
            SELECT
                sales_id,
                store_number,
                brand,
                description,
                size,
                sales_quantity,
                sales_dollars
            FROM sales
            WHERE business_id = %s
              AND sales_id > {last_sales_id}
            ORDER BY sales_id
            LIMIT {CHUNK_SIZE}
        """

        chunk = pd.read_sql_query(
            query,
            engine,
            params=(BUSINESS_ID,)
        )

        if chunk.empty:
            break

        last_sales_id = int(
            chunk["sales_id"].max()
        )

        total_rows += len(chunk)

        chunk["description"] = clean_text(
            chunk["description"]
        )

        chunk["size"] = clean_text(
            chunk["size"]
        )

        grouped = (
            chunk
            .groupby(
                [
                    "store_number",
                    "brand",
                    "description",
                    "size"
                ],
                dropna=False
            )
            .agg(
                sales_quantity=(
                    "sales_quantity",
                    "sum"
                ),
                sales_revenue=(
                    "sales_dollars",
                    "sum"
                )
            )
            .reset_index()
        )

        totals.append(grouped)

        print(
            f"Sales rows processed: "
            f"{total_rows:,}",
            end="\r"
        )

    print()

    sales = pd.concat(
        totals,
        ignore_index=True
    )

    sales = (
        sales
        .groupby(
            [
                "store_number",
                "brand",
                "description",
                "size"
            ],
            dropna=False
        )
        .agg(
            sales_quantity=(
                "sales_quantity",
                "sum"
            ),
            sales_revenue=(
                "sales_revenue",
                "sum"
            )
        )
        .reset_index()
    )

    return sales


# ============================================================
# LOAD PURCHASES - STORE x PRODUCT
# ============================================================

def load_store_product_purchases():

    print(
        "\nLoading purchases for Store x Product analysis..."
    )

    totals = []

    total_rows = 0

    last_purchase_id = 0

    while True:

        query = f"""
            SELECT
                purchase_id,
                store_number,
                brand,
                description,
                size,
                quantity,
                dollars
            FROM purchases
            WHERE business_id = %s
              AND purchase_id > {last_purchase_id}
            ORDER BY purchase_id
            LIMIT {CHUNK_SIZE}
        """

        chunk = pd.read_sql_query(
            query,
            engine,
            params=(BUSINESS_ID,)
        )

        if chunk.empty:
            break

        last_purchase_id = int(
            chunk["purchase_id"].max()
        )

        total_rows += len(chunk)

        chunk["description"] = clean_text(
            chunk["description"]
        )

        chunk["size"] = clean_text(
            chunk["size"]
        )

        grouped = (
            chunk
            .groupby(
                [
                    "store_number",
                    "brand",
                    "description",
                    "size"
                ],
                dropna=False
            )
            .agg(
                purchase_quantity=(
                    "quantity",
                    "sum"
                ),
                purchase_spending=(
                    "dollars",
                    "sum"
                )
            )
            .reset_index()
        )

        totals.append(grouped)

        print(
            f"Purchase rows processed: "
            f"{total_rows:,}",
            end="\r"
        )

    print()

    purchases = pd.concat(
        totals,
        ignore_index=True
    )

    purchases = (
        purchases
        .groupby(
            [
                "store_number",
                "brand",
                "description",
                "size"
            ],
            dropna=False
        )
        .agg(
            purchase_quantity=(
                "purchase_quantity",
                "sum"
            ),
            purchase_spending=(
                "purchase_spending",
                "sum"
            )
        )
        .reset_index()
    )

    return purchases


# ============================================================
# BUILD STORE x PRODUCT
# ============================================================

def build_store_product_intelligence(
    sales,
    purchases
):

    print(
        "\nBuilding Store x Product Intelligence..."
    )

    keys = [
        "store_number",
        "brand",
        "description",
        "size"
    ]

    df = pd.merge(
        sales,
        purchases,
        on=keys,
        how="outer"
    )

    for column in [
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending"
    ]:

        df[column] = (
            df[column]
            .fillna(0)
        )

    df["quantity_balance"] = (
        df["purchase_quantity"]
        - df["sales_quantity"]
    )

    df["value_difference"] = (
        df["sales_revenue"]
        - df["purchase_spending"]
    )

    df["sales_purchase_value_ratio"] = 0.0

    mask = (
        df["purchase_spending"] > 0
    )

    df.loc[
        mask,
        "sales_purchase_value_ratio"
    ] = (
        df.loc[
            mask,
            "sales_revenue"
        ]
        /
        df.loc[
            mask,
            "purchase_spending"
        ]
    )

    df["cross_signal"] = "Balanced Activity"

    df.loc[
        df["quantity_balance"] > 0,
        "cross_signal"
    ] = "Purchases Exceed Sales"

    df.loc[
        df["quantity_balance"] < 0,
        "cross_signal"
    ] = "Sales Exceed Purchases"

    df.loc[
        (
            (df["sales_quantity"] == 0)
            &
            (df["purchase_quantity"] > 0)
        ),
        "cross_signal"
    ] = "Purchase Without Sales"

    df.loc[
        (
            (df["purchase_quantity"] == 0)
            &
            (df["sales_quantity"] > 0)
        ),
        "cross_signal"
    ] = "Sales Without Purchase"

    df = df.sort_values(
        "sales_revenue",
        ascending=False
    ).reset_index(
        drop=True
    )

    return df


# ============================================================
# LOAD SALES - VENDOR x PRODUCT
# ============================================================

def load_vendor_product_sales():

    print(
        "\nLoading sales for Vendor x Product analysis..."
    )

    totals = []

    last_sales_id = 0

    while True:

        query = f"""
            SELECT
                sales_id,
                vendor_number,
                vendor_name,
                brand,
                description,
                size,
                sales_quantity,
                sales_dollars
            FROM sales
            WHERE business_id = %s
              AND sales_id > {last_sales_id}
            ORDER BY sales_id
            LIMIT {CHUNK_SIZE}
        """

        chunk = pd.read_sql_query(
            query,
            engine,
            params=(BUSINESS_ID,)
        )

        if chunk.empty:
            break

        last_sales_id = int(
            chunk["sales_id"].max()
        )

        chunk["vendor_name"] = clean_text(
            chunk["vendor_name"]
        )

        chunk["description"] = clean_text(
            chunk["description"]
        )

        chunk["size"] = clean_text(
            chunk["size"]
        )

        grouped = (
            chunk
            .groupby(
                [
                    "vendor_number",
                    "vendor_name",
                    "brand",
                    "description",
                    "size"
                ],
                dropna=False
            )
            .agg(
                sales_quantity=(
                    "sales_quantity",
                    "sum"
                ),
                sales_revenue=(
                    "sales_dollars",
                    "sum"
                )
            )
            .reset_index()
        )

        totals.append(grouped)

    sales = pd.concat(
        totals,
        ignore_index=True
    )

    keys = [
        "vendor_number",
        "vendor_name",
        "brand",
        "description",
        "size"
    ]

    sales = (
        sales
        .groupby(
            keys,
            dropna=False
        )
        .agg(
            sales_quantity=(
                "sales_quantity",
                "sum"
            ),
            sales_revenue=(
                "sales_revenue",
                "sum"
            )
        )
        .reset_index()
    )

    return sales


# ============================================================
# LOAD PURCHASES - VENDOR x PRODUCT
# ============================================================

def load_vendor_product_purchases():

    print(
        "\nLoading purchases for Vendor x Product analysis..."
    )

    totals = []

    last_purchase_id = 0

    while True:

        query = f"""
            SELECT
                purchase_id,
                vendor_number,
                vendor_name,
                brand,
                description,
                size,
                quantity,
                dollars
            FROM purchases
            WHERE business_id = %s
              AND purchase_id > {last_purchase_id}
            ORDER BY purchase_id
            LIMIT {CHUNK_SIZE}
        """

        chunk = pd.read_sql_query(
            query,
            engine,
            params=(BUSINESS_ID,)
        )

        if chunk.empty:
            break

        last_purchase_id = int(
            chunk["purchase_id"].max()
        )

        chunk["vendor_name"] = clean_text(
            chunk["vendor_name"]
        )

        chunk["description"] = clean_text(
            chunk["description"]
        )

        chunk["size"] = clean_text(
            chunk["size"]
        )

        grouped = (
            chunk
            .groupby(
                [
                    "vendor_number",
                    "vendor_name",
                    "brand",
                    "description",
                    "size"
                ],
                dropna=False
            )
            .agg(
                purchase_quantity=(
                    "quantity",
                    "sum"
                ),
                purchase_spending=(
                    "dollars",
                    "sum"
                )
            )
            .reset_index()
        )

        totals.append(grouped)

    purchases = pd.concat(
        totals,
        ignore_index=True
    )

    keys = [
        "vendor_number",
        "vendor_name",
        "brand",
        "description",
        "size"
    ]

    purchases = (
        purchases
        .groupby(
            keys,
            dropna=False
        )
        .agg(
            purchase_quantity=(
                "purchase_quantity",
                "sum"
            ),
            purchase_spending=(
                "purchase_spending",
                "sum"
            )
        )
        .reset_index()
    )

    return purchases


# ============================================================
# BUILD VENDOR x PRODUCT
# ============================================================

def build_vendor_product_intelligence(
    sales,
    purchases
):

    print(
        "\nBuilding Vendor x Product Intelligence..."
    )

    keys = [
        "vendor_number",
        "vendor_name",
        "brand",
        "description",
        "size"
    ]

    df = pd.merge(
        sales,
        purchases,
        on=keys,
        how="outer"
    )

    for column in [
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending"
    ]:

        df[column] = (
            df[column]
            .fillna(0)
        )

    df["quantity_balance"] = (
        df["purchase_quantity"]
        - df["sales_quantity"]
    )

    df["value_difference"] = (
        df["sales_revenue"]
        - df["purchase_spending"]
    )

    df["sales_purchase_value_ratio"] = 0.0

    mask = (
        df["purchase_spending"] > 0
    )

    df.loc[
        mask,
        "sales_purchase_value_ratio"
    ] = (
        df.loc[
            mask,
            "sales_revenue"
        ]
        /
        df.loc[
            mask,
            "purchase_spending"
        ]
    )

    df["cross_signal"] = "Balanced Activity"

    df.loc[
        df["quantity_balance"] > 0,
        "cross_signal"
    ] = "Purchases Exceed Sales"

    df.loc[
        df["quantity_balance"] < 0,
        "cross_signal"
    ] = "Sales Exceed Purchases"

    df.loc[
        (
            (df["sales_quantity"] == 0)
            &
            (df["purchase_quantity"] > 0)
        ),
        "cross_signal"
    ] = "Purchase Without Sales"

    df.loc[
        (
            (df["purchase_quantity"] == 0)
            &
            (df["sales_quantity"] > 0)
        ),
        "cross_signal"
    ] = "Sales Without Purchase"

    df = df.sort_values(
        "sales_revenue",
        ascending=False
    ).reset_index(
        drop=True
    )

    return df


# ============================================================
# VERIFY SOURCE TOTALS
# ============================================================

def verify_source_totals(
    sales_rows,
    sales_quantity,
    sales_revenue,
    purchase_rows,
    purchase_quantity,
    purchase_spending
):

    print("\n" + "=" * 70)
    print("VERIFYING SOURCE TOTALS")
    print("=" * 70)

    assert sales_rows == EXPECTED_SALES_ROWS

    print(
        "✓ Sales row count reconciled"
    )

    assert sales_quantity == EXPECTED_SALES_QUANTITY

    print(
        "✓ Sales quantity reconciled"
    )

    assert round(
        sales_revenue,
        2
    ) == EXPECTED_SALES_REVENUE

    print(
        "✓ Sales revenue reconciled"
    )

    assert purchase_rows == EXPECTED_PURCHASE_ROWS

    print(
        "✓ Purchase row count reconciled"
    )

    assert purchase_quantity == EXPECTED_PURCHASE_QUANTITY

    print(
        "✓ Purchase quantity reconciled"
    )

    assert round(
        purchase_spending,
        2
    ) == EXPECTED_PURCHASE_SPENDING

    print(
        "✓ Purchase spending reconciled"
    )


# ============================================================
# VERIFY CROSS DATASET
# ============================================================

def verify_cross_dataset(
    df,
    required_keys,
    dataset_name
):

    print(
        f"\nVerifying {dataset_name}..."
    )

    assert len(df) > 0

    print(
        f"✓ {dataset_name} contains "
        f"{len(df):,} cross-dimensional rows"
    )

    assert not df.duplicated(
        subset=required_keys
    ).any()

    print(
        f"✓ No duplicate {dataset_name} identities"
    )

    required_columns = [
        "sales_quantity",
        "sales_revenue",
        "purchase_quantity",
        "purchase_spending",
        "quantity_balance",
        "value_difference",
        "sales_purchase_value_ratio",
        "cross_signal"
    ]

    for column in required_columns:

        assert column in df.columns

    print(
        f"✓ Required {dataset_name} columns present"
    )

    assert df["cross_signal"].notna().all()

    print(
        f"✓ {dataset_name} signals generated"
    )


# ============================================================
# SAVE
# ============================================================

def save_output(
    df,
    filename
):

    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    df.to_csv(
        path,
        index=False
    )

    print(
        f"✓ Saved: "
        f"data/processed/{filename}"
    )


# ============================================================
# DISPLAY TOP RESULTS
# ============================================================

def display_results(
    vendor_store,
    store_product,
    vendor_product
):

    print("\n" + "=" * 70)
    print("TOP CROSS-INTELLIGENCE RESULTS")
    print("=" * 70)

    print("\nTop Vendor x Store combinations:")

    print(
        vendor_store[
            [
                "store_number",
                "vendor_number",
                "vendor_name",
                "sales_quantity",
                "sales_revenue",
                "purchase_quantity",
                "purchase_spending",
                "quantity_balance",
                "cross_signal"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\nTop Store x Product combinations:")

    print(
        store_product[
            [
                "store_number",
                "brand",
                "description",
                "size",
                "sales_quantity",
                "sales_revenue",
                "purchase_quantity",
                "purchase_spending",
                "quantity_balance",
                "cross_signal"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    print("\nTop Vendor x Product combinations:")

    print(
        vendor_product[
            [
                "vendor_number",
                "vendor_name",
                "brand",
                "description",
                "size",
                "sales_quantity",
                "sales_revenue",
                "purchase_quantity",
                "purchase_spending",
                "quantity_balance",
                "cross_signal"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("PHASE 10.6 - CROSS INTELLIGENCE")
    print("=" * 70)

    # --------------------------------------------------------
    # Vendor x Store
    # --------------------------------------------------------

    (
        vendor_store_sales,
        sales_rows,
        sales_quantity,
        sales_revenue
    ) = load_vendor_store_sales()

    (
        vendor_store_purchases,
        purchase_rows,
        purchase_quantity,
        purchase_spending
    ) = load_vendor_store_purchases()

    verify_source_totals(
        sales_rows,
        sales_quantity,
        sales_revenue,
        purchase_rows,
        purchase_quantity,
        purchase_spending
    )

    vendor_store = build_vendor_store_intelligence(
        vendor_store_sales,
        vendor_store_purchases
    )

    # --------------------------------------------------------
    # Store x Product
    # --------------------------------------------------------

    store_product_sales = load_store_product_sales()

    store_product_purchases = load_store_product_purchases()

    store_product = build_store_product_intelligence(
        store_product_sales,
        store_product_purchases
    )

    # --------------------------------------------------------
    # Vendor x Product
    # --------------------------------------------------------

    vendor_product_sales = load_vendor_product_sales()

    vendor_product_purchases = load_vendor_product_purchases()

    vendor_product = build_vendor_product_intelligence(
        vendor_product_sales,
        vendor_product_purchases
    )

    # --------------------------------------------------------
    # Verify datasets
    # --------------------------------------------------------

    verify_cross_dataset(
        vendor_store,
        [
            "store_number",
            "vendor_number",
            "vendor_name"
        ],
        "Vendor x Store Intelligence"
    )

    verify_cross_dataset(
        store_product,
        [
            "store_number",
            "brand",
            "description",
            "size"
        ],
        "Store x Product Intelligence"
    )

    verify_cross_dataset(
        vendor_product,
        [
            "vendor_number",
            "vendor_name",
            "brand",
            "description",
            "size"
        ],
        "Vendor x Product Intelligence"
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    save_output(
        vendor_store,
        "vendor_store_intelligence.csv"
    )

    save_output(
        store_product,
        "store_product_intelligence.csv"
    )

    save_output(
        vendor_product,
        "vendor_product_intelligence.csv"
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    display_results(
        vendor_store,
        store_product,
        vendor_product
    )

    print("\n" + "=" * 70)
    print(
        "PHASE 10.6 CROSS INTELLIGENCE COMPLETED"
    )
    print("=" * 70)
