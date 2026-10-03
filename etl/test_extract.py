from etl.extract import extract_all


data = extract_all()


print("\n=== EXTRACTION SUMMARY ===")

for name, df in data.items():
    print(
        f"{name}: "
        f"{df.shape[0]:,} rows × "
        f"{df.shape[1]} columns"
    )