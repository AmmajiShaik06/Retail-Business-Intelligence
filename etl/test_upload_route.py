import requests


URL = "http://127.0.0.1:5000/upload/"

FILE_PATH = "data/sample/upload_test/test_sales.csv"


def main():

    print("=" * 60)
    print("FLASK CSV UPLOAD ROUTE TEST")
    print("=" * 60)

    print("\n1. Sending invalid Sales CSV...")

    with open(FILE_PATH, "rb") as file:

        response = requests.post(
            URL,
            data={
                "dataset": "sales"
            },
            files={
                "file": (
                    "test_sales.csv",
                    file,
                    "text/csv"
                )
            }
        )

    print(f"\nHTTP Status: {response.status_code}")

    print("\nResponse:")
    print(response.text)

    if response.status_code != 400:
        raise ValueError(
            f"Expected HTTP 400, "
            f"but received {response.status_code}"
        )

    if "CSV validation failed." not in response.text:
        raise ValueError(
            "Expected CSV validation error "
            "was not found."
        )

    print("\n" + "=" * 60)
    print("INVALID UPLOAD TEST PASSED")
    print("=" * 60)

    print("\nBad CSV was rejected before Sales ETL.")


if __name__ == "__main__":
    main()