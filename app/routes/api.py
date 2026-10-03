from flask import Blueprint
from sqlalchemy import text
from database.connection import engine
import pandas as pd

api = Blueprint("api", __name__)


@api.route("/api/db-test")
def db_test():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT DATABASE()")
            )
            database_name = result.scalar()

        return {
            "status": "success",
            "database": database_name
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
@api.route("/api/kpis")
def kpis():
    try:
        query = text("""
            SELECT
                (SELECT COALESCE(SUM(sales_dollars), 0)
                 FROM sales) AS total_sales_revenue,

                (SELECT COALESCE(SUM(sales_quantity), 0)
                 FROM sales) AS total_sales_quantity,

                (SELECT COALESCE(SUM(dollars), 0)
                 FROM purchases) AS total_purchase_spending,

                (SELECT COALESCE(SUM(quantity), 0)
                 FROM purchases) AS total_purchase_quantity,

                (SELECT COALESCE(SUM(on_hand), 0)
                 FROM begin_inventory) AS beginning_inventory_quantity,

                (SELECT COALESCE(SUM(on_hand), 0)
                 FROM end_inventory) AS ending_inventory_quantity
        """)

        with engine.connect() as connection:
            result = connection.execute(query)
            row = result.mappings().first()

        return {
            "status": "success",
            "kpis": dict(row)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
@api.route("/api/sales")
def sales():
    try:
        query = text("""
            SELECT
                DATE_FORMAT(sales_date, '%Y-%m') AS month,
                SUM(sales_quantity) AS sales_quantity,
                SUM(sales_dollars) AS sales_revenue
            FROM sales
            GROUP BY DATE_FORMAT(sales_date, '%Y-%m')
            ORDER BY month
        """)

        with engine.connect() as connection:
            result = connection.execute(query)
            rows = result.mappings().all()

        return {
            "status": "success",
            "count": len(rows),
            "sales": [dict(row) for row in rows]
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
@api.route("/api/purchases")
def purchases():
    try:
        query = text("""
            SELECT
                DATE_FORMAT(po_date, '%Y-%m') AS month,
                SUM(quantity) AS purchase_quantity,
                SUM(dollars) AS purchase_spending
            FROM purchases
            GROUP BY DATE_FORMAT(po_date, '%Y-%m')
            ORDER BY month
        """)

        with engine.connect() as connection:
            result = connection.execute(query)
            rows = result.mappings().all()

        return {
            "status": "success",
            "count": len(rows),
            "purchases": [dict(row) for row in rows]
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
@api.route("/api/vendors")
def vendors():
    try:
        file_path = "data/processed/vendor_intelligence.csv"

        columns = [
            "vendor_number",
            "vendor_name",
            "sales_quantity",
            "sales_revenue",
            "purchase_quantity",
            "purchase_spending"
        ]

        df = pd.read_csv(file_path, usecols=columns)

        df = df.sort_values(
            by="sales_revenue",
            ascending=False
        )

        df = df.fillna("")

        return {
            "status": "success",
            "count": len(df),
            "vendors": df.to_dict(orient="records")
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
@api.route("/api/stores")
def stores():
    try:
        file_path = "data/processed/store_intelligence.csv"

        columns = [
            "store_number",
            "sales_quantity",
            "sales_revenue",
            "purchase_quantity",
            "purchase_spending",
            "sales_purchase_value_ratio",
            "store_segment"
        ]

        df = pd.read_csv(file_path, usecols=columns)

        df = df.sort_values(
            by="sales_revenue",
            ascending=False
        )

        df = df.fillna("")

        return {
            "status": "success",
            "count": len(df),
            "stores": df.to_dict(orient="records")
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
@api.route("/api/products")
def products():
    try:
        file_path = "data/processed/product_intelligence.csv"

        columns = [
            "product_key",
            "brand",
            "description",
            "size",
            "classification",
            "sales_quantity",
            "sales_revenue",
            "purchase_quantity",
            "purchase_spending",
            "end_inventory_quantity",
            "end_inventory_value",
            "product_segment"
        ]

        df = pd.read_csv(file_path, usecols=columns)

        df = df.sort_values(
            by="sales_revenue",
            ascending=False
        )

        df = df.fillna("")

        return {
            "status": "success",
            "count": len(df),
            "products": df.to_dict(orient="records")
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
@api.route("/api/inventory")
def inventory():
    try:
        file_path = "data/processed/inventory_intelligence.csv"

        columns = [
            "product_key",
            "brand",
            "description",
            "classification",
            "begin_inventory_quantity",
            "end_inventory_quantity",
            "begin_inventory_value",
            "end_inventory_value",
            "inventory_quantity_change",
            "inventory_value_change",
            "inventory_value_growth_percent",
            "ending_inventory_to_sales_percent",
            "risk_category"
        ]

        df = pd.read_csv(file_path, usecols=columns)

        df = df.sort_values(
            by="end_inventory_value",
            ascending=False
        )

        df = df.fillna("")

        return {
            "status": "success",
            "count": len(df),
            "inventory": df.to_dict(orient="records")
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
@api.route("/api/recommendations")
def recommendations():
    try:
        file_path = "data/processed/recommendation_engine.csv"

        columns = [
            "product_key",
            "brand",
            "description",
            "classification",
            "sales_quantity",
            "sales_revenue",
            "purchase_quantity",
            "purchase_spending",
            "end_inventory_quantity",
            "end_inventory_value",
            "risk_category",
            "recommendation_category",
            "recommendation_priority",
            "recommendation",
            "recommended_action",
            "recommendation_priority_score"
        ]

        df = pd.read_csv(file_path, usecols=columns)

        df = df.sort_values(
            by=["recommendation_priority_score", "sales_revenue"],
            ascending=[False, False]
        )

        df = df.fillna("")

        return {
            "status": "success",
            "count": len(df),
            "recommendations": df.to_dict(orient="records")
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
@api.route("/api/forecast")
def forecast():
    try:
        file_path = "data/processed/sales_forecast.csv"

        columns = [
            "date",
            "forecast_month",
            "forecast_sales_revenue"
        ]

        df = pd.read_csv(file_path, usecols=columns)

        df = df.sort_values(
            by="date",
            ascending=True
        )

        df = df.fillna("")

        return {
            "status": "success",
            "count": len(df),
            "forecast": df.to_dict(orient="records")
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
@api.route("/api/my-vendor")
def my_vendor():
    from flask import session

    if "user_id" not in session:
        return {
            "status": "error",
            "message": "Login required"
        }, 401

    if session.get("role") != "vendor":
        return {
            "status": "error",
            "message": "Vendor access required"
        }, 403

    try:
        file_path = "data/processed/vendor_intelligence.csv"

        df = pd.read_csv(file_path)

        vendor_number = session.get("vendor_number")

        vendor = df[
            df["vendor_number"] == vendor_number
        ]

        if vendor.empty:
            return {
                "status": "error",
                "message": "Vendor data not found"
            }, 404

        row = vendor.iloc[0]

        return {
            "status": "success",
            "vendor": {
                "vendor_number": int(row["vendor_number"]),
                "vendor_name": row["vendor_name"],
                "purchase_quantity": float(row["purchase_quantity"]),
                "purchase_spending": float(row["purchase_spending"]),
                "sales_quantity": float(row["sales_quantity"]),
                "sales_revenue": float(row["sales_revenue"])
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500
@api.route("/api/my-vendor/recommendations")
def my_vendor_recommendations():
    from flask import session

    if "user_id" not in session:
        return {
            "status": "error",
            "message": "Login required"
        }, 401

    if session.get("role") != "vendor":
        return {
            "status": "error",
            "message": "Vendor access required"
        }, 403

    try:
        vendor_number = session.get("vendor_number")

        query = text("""
            SELECT DISTINCT
                brand,
                description,
                size
            FROM sales
            WHERE vendor_number = :vendor_number
        """)

        with engine.connect() as connection:
            result = connection.execute(
                query,
                {"vendor_number": vendor_number}
            )
            vendor_products = pd.DataFrame(
                result.mappings().all()
            )

        if vendor_products.empty:
            return {
                "status": "error",
                "message": "No products found for vendor"
            }, 404

        recommendation_file = (
            "data/processed/recommendation_engine.csv"
        )

        recommendations = pd.read_csv(
            recommendation_file
        )

        merged = vendor_products.merge(
            recommendations[
                [
                    "brand",
                    "description",
                    "size",
                    "recommendation",
                    "recommendation_category",
                    "recommendation_priority"
                ]
            ],
            on=["brand", "description", "size"],
            how="inner"
        )

        return {
            "status": "success",
            "vendor_number": vendor_number,
            "count": len(merged),
            "recommendations": merged.to_dict(
                orient="records"
            )
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }, 500