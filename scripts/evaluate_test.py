import subprocess
from hashlib import sha256
from pathlib import Path

import mlflow
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "wuhan_pm25_features.csv"
REPORT_DIR = ROOT / "reports"
METRICS_PATH = REPORT_DIR / "test_metrics.csv"
PREDICTIONS_PATH = REPORT_DIR / "test_predictions.csv"
DB_PATH = ROOT / "mlflow.db"

FEATURE_COLUMNS = [
    "pm25_lag_0h",
    "pm25_lag_1h",
    "pm25_lag_2h",
    "pm25_lag_3h",
    "pm25_lag_6h",
    "pm25_lag_12h",
    "pm25_lag_24h",
    "target_hour_sin",
    "target_hour_cos",
    "target_weekday",
]
TARGET_COLUMN = "target_pm25_ug_m3"


def metrics(actual, predicted):
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
    }


def main():
    df = pd.read_csv(DATA_PATH)
    train = df[df["split"] == "train"].copy()
    test = df[df["split"] == "test"].copy()

    X_train = train[FEATURE_COLUMNS]
    y_train = train[TARGET_COLUMN]
    X_test = test[FEATURE_COLUMNS]
    y_test = test[TARGET_COLUMN]

    # 使用验证阶段选定的固定参数；测试集只用于最终评估
    model = RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        max_features=0.8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    baseline_prediction = X_test["pm25_lag_0h"]
    model_prediction = model.predict(X_test)

    baseline_metrics = metrics(y_test, baseline_prediction)
    model_metrics = metrics(y_test, model_prediction)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = pd.DataFrame([
        {"model": "Persistence_Baseline", **baseline_metrics},
        {"model": "RandomForest_300_leaf2", **model_metrics},
    ])
    report.to_csv(METRICS_PATH, index=False)

    predictions = pd.DataFrame({
        "target_timestamp": test["target_timestamp"],
        "actual_pm25_ug_m3": y_test,
        "baseline_prediction": baseline_prediction,
        "random_forest_prediction": model_prediction,
    })
    predictions.to_csv(PREDICTIONS_PATH, index=False)

    code_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    data_sha = sha256(DATA_PATH.read_bytes()).hexdigest()

    mlflow.set_tracking_uri(f"sqlite:///{DB_PATH.as_posix()}")
    mlflow.set_experiment("Wuhan_PM25_Next_Hour")
    with mlflow.start_run(run_name="Final_Test_Evaluation"):
        mlflow.log_params({
            "selected_model": "RandomForestRegressor",
            "n_estimators": 300,
            "min_samples_leaf": 2,
            "max_features": 0.8,
            "random_state": 42,
            "code_sha": code_sha,
            "data_sha256": data_sha,
        })
        mlflow.log_metrics({
            "baseline_test_mae": baseline_metrics["mae"],
            "baseline_test_rmse": baseline_metrics["rmse"],
            "random_forest_test_mae": model_metrics["mae"],
            "random_forest_test_rmse": model_metrics["rmse"],
        })
        mlflow.log_artifact(str(METRICS_PATH), artifact_path="test_evaluation")
        mlflow.log_artifact(str(PREDICTIONS_PATH), artifact_path="test_evaluation")

    print(f"测试样本：{len(test)}")
    print(f"代码提交号：{code_sha}")
    print(f"数据 SHA-256：{data_sha}")
    print(report.to_string(index=False))
    print(f"测试预测明细：{PREDICTIONS_PATH}")


if __name__ == "__main__":
    main()
