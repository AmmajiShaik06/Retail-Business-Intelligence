from flask import Flask, render_template
from dotenv import load_dotenv
from sqlalchemy import text
from database.connection import engine
import pandas as pd
import os
from app.routes.api import api
from app.routes.auth import auth
from app.auth import login_required
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY")

    # --------------------------------------------------
    # HOME ROUTE
    # --------------------------------------------------
    @app.route("/")
    def home():
        return "Retail Business Intelligence Platform - Flask Backend"
    
    @app.route("/login")
    def login_page():
        return render_template("login.html")
    
    
    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html")

    # # --------------------------------------------------
    # # DATABASE TEST ROUTE
    # # --------------------------------------------------
    # @app.route("/api/db-test")
    # def db_test():
    #     try:
    #         with engine.connect() as connection:
    #             result = connection.execute(
    #                 text("SELECT DATABASE()")
    #             )
    #             database_name = result.scalar()

    #         return {
    #             "status": "success",
    #             "database": database_name
    #         }

    #     except Exception as e:
    #         return {
    #             "status": "error",
    #             "message": str(e)
    #         }, 500

    # # --------------------------------------------------
    # # KPI API
    # # --------------------------------------------------
    # @app.route("/api/kpis")
    # def kpis():
    #     try:
    #         query = text("""
    #             SELECT
    #                 (SELECT COALESCE(SUM(sales_dollars), 0)
    #                  FROM sales) AS total_sales_revenue,

    #                 (SELECT COALESCE(SUM(sales_quantity), 0)
    #                  FROM sales) AS total_sales_quantity,

    #                 (SELECT COALESCE(SUM(dollars), 0)
    #                  FROM purchases) AS total_purchase_spending,

    #                 (SELECT COALESCE(SUM(quantity), 0)
    #                  FROM purchases) AS total_purchase_quantity,

    #                 (SELECT COALESCE(SUM(on_hand), 0)
    #                  FROM begin_inventory) AS beginning_inventory_quantity,

    #                 (SELECT COALESCE(SUM(on_hand), 0)
    #                  FROM end_inventory) AS ending_inventory_quantity
    #         """)

    #         with engine.connect() as connection:
    #             result = connection.execute(query)
    #             row = result.mappings().first()

    #         return {
    #             "status": "success",
    #             "kpis": dict(row)
    #         }

    #     except Exception as e:
    #         return {
    #             "status": "error",
    #             "message": str(e)
    #         }, 500

    # # --------------------------------------------------
    # # SALES API
    # # --------------------------------------------------
    # @app.route("/api/sales")
    # def sales():
    #     try:
    #         query = text("""
    #             SELECT
    #                 DATE_FORMAT(sales_date, '%Y-%m') AS month,
    #                 SUM(sales_quantity) AS sales_quantity,
    #                 SUM(sales_dollars) AS sales_revenue
    #             FROM sales
    #             GROUP BY DATE_FORMAT(sales_date, '%Y-%m')
    #             ORDER BY month
    #         """)

    #         with engine.connect() as connection:
    #             result = connection.execute(query)
    #             rows = result.mappings().all()

    #         return {
    #             "status": "success",
    #             "count": len(rows),
    #             "sales": [dict(row) for row in rows]
    #         }

    #     except Exception as e:
    #         return {
    #             "status": "error",
    #             "message": str(e)
    #         }, 500

    # # --------------------------------------------------
    # # PURCHASE API
    # # --------------------------------------------------
    # @app.route("/api/purchases")
    # def purchases():
    #     try:
    #         query = text("""
    #             SELECT
    #                 DATE_FORMAT(po_date, '%Y-%m') AS month,
    #                 SUM(quantity) AS purchase_quantity,
    #                 SUM(dollars) AS purchase_spending
    #             FROM purchases
    #             GROUP BY DATE_FORMAT(po_date, '%Y-%m')
    #             ORDER BY month
    #         """)

    #         with engine.connect() as connection:
    #             result = connection.execute(query)
    #             rows = result.mappings().all()

    #         return {
    #             "status": "success",
    #             "count": len(rows),
    #             "purchases": [dict(row) for row in rows]
    #         }

    #     except Exception as e:
    #         return {
    #             "status": "error",
    #             "message": str(e)
    #         }, 500

    # # --------------------------------------------------
    # # VENDOR API
    # # --------------------------------------------------
    # @app.route("/api/vendors")
    # def vendors():
    #     try:
    #         file_path = os.path.join(
    #             "data",
    #             "processed",
    #             "vendor_intelligence.csv"
    #         )

    #         df = pd.read_csv(file_path)

    #         columns = [
    #             "vendor_number",
    #             "vendor_name",
    #             "sales_quantity",
    #             "sales_revenue",
    #             "purchase_quantity",
    #             "purchase_spending"
    #         ]

    #         result = df[columns].copy()

    #         result = result.sort_values(
    #             by="sales_revenue",
    #             ascending=False
    #         )

    #         result = result.fillna("")

    #         return {
    #             "status": "success",
    #             "count": len(result),
    #             "vendors": result.to_dict(orient="records")
    #         }

    #     except Exception as e:
    #         return {
    #             "status": "error",
    #             "message": str(e)
    #         }, 500

    # # --------------------------------------------------
    # # STORE API
    # # --------------------------------------------------
    # @app.route("/api/stores")
    # def stores():
    #     try:
    #         file_path = os.path.join(
    #             "data",
    #             "processed",
    #             "store_intelligence.csv"
    #         )

    #         df = pd.read_csv(file_path)

    #         columns = [
    #             "store_number",
    #             "sales_quantity",
    #             "sales_revenue",
    #             "purchase_quantity",
    #             "purchase_spending",
    #             "sales_purchase_value_ratio",
    #             "store_segment"
    #         ]

    #         result = df[columns].copy()

    #         result = result.sort_values(
    #             by="sales_revenue",
    #             ascending=False
    #         )

    #         result = result.fillna("")

    #         return {
    #             "status": "success",
    #             "count": len(result),
    #             "stores": result.to_dict(orient="records")
    #         }

    #     except Exception as e:
    #         return {
    #             "status": "error",
    #             "message": str(e)
    #         }, 500
    # PRODUCT API
    # @app.route("/api/products")
    # def products():
    #     try:
    #         file_path = os.path.join(
    #             "data",
    #             "processed",
    #             "product_intelligence.csv"
    #         )

    #         df = pd.read_csv(file_path)

    #         columns = [
    #             "product_key",
    #             "brand",
    #             "description",
    #             "size",
    #             "classification",
    #             "sales_quantity",
    #             "sales_revenue",
    #             "purchase_quantity",
    #             "purchase_spending",
    #             "end_inventory_quantity",
    #             "end_inventory_value",
    #             "product_segment"
    #         ]

    #         result = df[columns].copy()

    #         result = result.sort_values(
    #             by="sales_revenue",
    #             ascending=False
    #         )

    #         result = result.fillna("")

    #         return {
    #             "status": "success",
    #             "count": len(result),
    #             "products": result.to_dict(orient="records")
    #         }

    #     except Exception as e:
    #         return {
    #             "status": "error",
    #             "message": str(e)
    #         }, 500


    #     # INVENTORY API
    # @app.route("/api/inventory")
    # def inventory():
    #     try:
    #         file_path = os.path.join(
    #             "data",
    #             "processed",
    #             "inventory_intelligence.csv"
    #         )

    #         df = pd.read_csv(file_path)

    #         columns = [
    #             "product_key",
    #             "brand",
    #             "description",
    #             "classification",
    #             "begin_inventory_quantity",
    #             "end_inventory_quantity",
    #             "begin_inventory_value",
    #             "end_inventory_value",
    #             "inventory_quantity_change",
    #             "inventory_value_change",
    #             "inventory_value_growth_percent",
    #             "ending_inventory_to_sales_percent",
    #             "risk_category"
    #         ]

    #         result = df[columns].copy()

    #         result = result.sort_values(
    #             by="end_inventory_value",
    #             ascending=False
    #         )

    #         result = result.fillna("")

    #         return {
    #             "status": "success",
    #             "count": len(result),
    #             "inventory": result.to_dict(orient="records")
    #         }

    #     except Exception as e:
    #         return {
    #             "status": "error",
    #             "message": str(e)
    #         }, 500
    #     # RECOMMENDATION API
    # @app.route("/api/recommendations")
    # def recommendations():
    #     try:
    #         file_path = os.path.join(
    #             "data",
    #             "processed",
    #             "recommendation_engine.csv"
    #         )

    #         df = pd.read_csv(file_path)

    #         columns = [
    #             "product_key",
    #             "brand",
    #             "description",
    #             "classification",
    #             "sales_quantity",
    #             "sales_revenue",
    #             "purchase_quantity",
    #             "purchase_spending",
    #             "end_inventory_quantity",
    #             "end_inventory_value",
    #             "risk_category",
    #             "recommendation_category",
    #             "recommendation_priority",
    #             "recommendation",
    #             "recommended_action",
    #             "recommendation_priority_score"
    #         ]

    #         result = df[columns].copy()

    #         result = result.sort_values(
    #             by=[
    #                 "recommendation_priority_score",
    #                 "sales_revenue"
    #             ],
    #             ascending=[False, False]
    #         )

    #         result = result.fillna("")

    #         return {
    #             "status": "success",
    #             "count": len(result),
    #             "recommendations": result.to_dict(
    #                 orient="records"
    #             )
    #         }

    #     except Exception as e:
    #         return {
    #             "status": "error",
    #             "message": str(e)
    #         }, 500
    #     # SALES FORECAST API
    # @app.route("/api/forecast")
    # def forecast():
    #     try:
    #         file_path = os.path.join(
    #             "data",
    #             "processed",
    #             "sales_forecast.csv"
    #         )

    #         df = pd.read_csv(file_path)

    #         columns = [
    #             "date",
    #             "forecast_month",
    #             "forecast_sales_revenue"
    #         ]

    #         result = df[columns].copy()

    #         result = result.sort_values(
    #             by="date",
    #             ascending=True
    #         )

    #         result = result.fillna("")

    #         return {
    #             "status": "success",
    #             "count": len(result),
    #             "forecast": result.to_dict(
    #                 orient="records"
    #             )
    #         }

    #     except Exception as e:
    #         return {
    #             "status": "error",
    #             "message": str(e)
    #         }, 500
    app.register_blueprint(api)
    app.register_blueprint(auth)
    return app