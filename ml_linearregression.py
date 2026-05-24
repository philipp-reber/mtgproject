import pandas as pd
from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

input_path = Path("./data/dataframe")

y_train_path = input_path / "card_price_dataframe_train_y.parquet"
y_test_path = input_path /"card_price_dataframe_test_y.parquet"
X_train_path = input_path /"card_price_dataframe_train_x.parquet"
X_test_path = input_path /"card_price_dataframe_test_x.parquet"

X_train_processed = pd.read_parquet(X_train_path)
X_test_processed = pd.read_parquet(X_test_path)
y_train = pd.read_parquet(y_train_path)["target_price_eur"]
y_test = pd.read_parquet(y_test_path)["target_price_eur"]

# LR Model
lr = LinearRegression()
lr.fit(X_train_processed, y_train)

train_pred = lr.predict(X_train_processed)
test_pred = lr.predict(X_test_processed)

print("Linear Regression")
print("Train R2:", r2_score(y_train, train_pred))
print("Test R2:", r2_score(y_test, test_pred))
print("Test MAE:", mean_absolute_error(y_test, test_pred))
print("Test RMSE:", mean_squared_error(y_test, test_pred) ** 0.5)