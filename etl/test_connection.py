from database.connection import engine


try:
    with engine.connect() as connection:
        print("Database connection successful!")
        print("Connected to retail_business_intelligence")

except Exception as e:
    print("Database connection failed.")
    print("Error:", e)