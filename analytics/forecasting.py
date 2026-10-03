import os

import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    mean_squared_error
)

from database.connection import engine


def load_monthly_sales():
    query = """
        SELECT
            date,
            sales_revenue,
            sales_quantity
        FROM monthly_sales_forecast
        ORDER BY date
    """

    df = pd.read_sql(query, engine)

    return df


def build_sales_forecast_model(df):
    # Create a copy
    df = df.copy()

    # Create sequential month numbers
    df["month_number"] = range(1, len(df) + 1)

    # Input variable
    X = df[["month_number"]]

    # Target variable
    y = df["sales_revenue"]

    # Create Linear Regression model
    model = LinearRegression()

    # Train model
    model.fit(X, y)

    # Historical predictions
    df["predicted_sales"] = model.predict(X)

    # Evaluation metrics
    r2 = r2_score(y, df["predicted_sales"])

    mae = mean_absolute_error(
        y,
        df["predicted_sales"]
    )

    rmse = mean_squared_error(
        y,
        df["predicted_sales"]
    ) ** 0.5

    return model, df, r2, mae, rmse


def generate_future_forecast(
    model,
    last_month_number,
    last_date,
    periods=3
):
    # Create future month numbers
    future_month_numbers = list(
        range(
            last_month_number + 1,
            last_month_number + periods + 1
        )
    )

    # Predict future sales
    future_predictions = model.predict(
        pd.DataFrame(
            {"month_number": future_month_numbers}
        )
    )

    # Create future dates
    future_dates = pd.date_range(
        start=last_date + pd.DateOffset(months=1),
        periods=periods,
        freq="MS"
    )

    # Create forecast DataFrame
    forecast_df = pd.DataFrame({
        "date": future_dates,
        "forecast_month": future_dates.strftime("%B %Y"),
        "forecast_sales_revenue": future_predictions
    })

    return forecast_df


if __name__ == "__main__":

    # ----------------------------------------
    # Step 1: Load historical monthly sales
    # ----------------------------------------

    df = load_monthly_sales()

    print("\nMonthly Sales Forecasting Data")
    print("-" * 40)
    print(df)

    print("\nShape:", df.shape)

    print("\nMissing Values:")
    print(df.isnull().sum())

    # ----------------------------------------
    # Step 2: Build model
    # ----------------------------------------

    model, result, r2, mae, rmse = (
        build_sales_forecast_model(df)
    )

    # ----------------------------------------
    # Step 3: Display model evaluation
    # ----------------------------------------

    print("\nModel Evaluation")
    print("-" * 40)

    print("R2 Score:", r2)
    print("MAE:", mae)
    print("RMSE:", rmse)

    # ----------------------------------------
    # Step 4: Generate future forecast
    # ----------------------------------------

    last_month_number = len(df)
    last_date = pd.to_datetime(df["date"].iloc[-1])

    forecast_df = generate_future_forecast(
        model,
        last_month_number,
        last_date,
        periods=3
    )

    # ----------------------------------------
    # Step 5: Display future forecast
    # ----------------------------------------

    print("\nFuture Sales Forecast")
    print("-" * 40)

    print(forecast_df)

    # ----------------------------------------
    # Step 6: Save forecast CSV
    # ----------------------------------------

    output_directory = "data/processed"

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    output_file = os.path.join(
        output_directory,
        "sales_forecast.csv"
    )

    forecast_df.to_csv(
        output_file,
        index=False
    )

    print("\nForecast CSV Saved")
    print("-" * 40)

    print("File:", output_file)

    # ----------------------------------------
    # Step 7: Verify saved CSV
    # ----------------------------------------

    saved_forecast = pd.read_csv(
        output_file
    )

    print("\nSaved Forecast Data")
    print("-" * 40)

    print(saved_forecast)

    print("\nSaved Shape:", saved_forecast.shape)

    print("\nSaved Missing Values:")
    print(saved_forecast.isnull().sum())
