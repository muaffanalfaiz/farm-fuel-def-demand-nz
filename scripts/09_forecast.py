from __future__ import annotations
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from scripts.common import root_path, write_csv

def main() -> None:
    df = pd.read_parquet(root_path("data/marts/feature_store_region.parquet"))
    numeric = df.select_dtypes(include=["number"]).copy()

    if "diesel_litres" not in numeric.columns:
        raise ValueError("feature_store_region.parquet must contain diesel_litres target")

    X = numeric.drop(columns=["diesel_litres"])
    y = numeric["diesel_litres"]

    if len(df) < 10:
        print("Too few rows for robust forecasting; writing feature importance placeholder only.")
        placeholder = pd.DataFrame({"note": ["Add monthly or multi-year panel data before final forecasting."]})
        write_csv(placeholder, "outputs/predictions/model_notes.csv")
        return

    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)
    model = RandomForestRegressor(n_estimators=300, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    metrics = pd.DataFrame([{
        "mae": mean_absolute_error(y_test, pred),
        "r2": r2_score(y_test, pred)
    }])
    feat = pd.DataFrame({"feature": X.columns, "importance": model.feature_importances_}).sort_values("importance", ascending=False)

    write_csv(metrics, "outputs/predictions/model_metrics.csv")
    write_csv(feat, "outputs/predictions/feature_importance.csv")
    print("Trained starter regional model.")

if __name__ == "__main__":
    main()
