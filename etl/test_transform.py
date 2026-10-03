from etl.extract import extract_all
from etl.transform import transform_all


print("=== STARTING EXTRACTION ===")

data = extract_all()


print("\n=== STARTING TRANSFORMATION ===")

transformed_data = transform_all(data)


print("\n=== TRANSFORMATION SUMMARY ===")

for name, df in transformed_data.items():

    print(f"\n{name}")
    print(f"Rows: {df.shape[0]:,}")
    print(f"Columns: {df.shape[1]}")

    print("Null values:")
    print(df.isnull().sum().sum())

print("\n=== DATE VALIDATION ===")

print(
    "Begin inventory startDate:",
    transformed_data["begin_inventory"]["startDate"].min(),
    "to",
    transformed_data["begin_inventory"]["startDate"].max()
)

print(
    "End inventory endDate:",
    transformed_data["end_inventory"]["endDate"].min(),
    "to",
    transformed_data["end_inventory"]["endDate"].max()
)

print(
    "Purchases PODate:",
    transformed_data["purchases"]["PODate"].min(),
    "to",
    transformed_data["purchases"]["PODate"].max()
)

print(
    "Sales SalesDate:",
    transformed_data["sales"]["SalesDate"].min(),
    "to",
    transformed_data["sales"]["SalesDate"].max()
)

print("\n=== DATA TYPE VALIDATION ===")

print(
    "Begin InventoryId type:",
    transformed_data["begin_inventory"]["InventoryId"].dtype
)

print(
    "End InventoryId type:",
    transformed_data["end_inventory"]["InventoryId"].dtype
)

print(
    "Purchases InventoryId type:",
    transformed_data["purchases"]["InventoryId"].dtype
)

print(
    "Sales InventoryId type:",
    transformed_data["sales"]["InventoryId"].dtype
)

print("\nTransformation completed successfully!")