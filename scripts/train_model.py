import subprocess
from hashlib import sha256
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "wuhan_pm25_features.csv"
REPORT_PATH = ROOT / "reports" / "validation_metrics.csv"
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


def calculate_metrics(actual, predicted):
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
    }


def main():
    df = pd.read_csv(DATA_PATH)
    train = df[df["split"] == "train"].copy()
    valid = df[df["split"] == "validation"].copy()

    X_train = train[FEATURE_COLUMNS]
    y_train = train[TARGET_COLUMN]
    X_valid = valid[FEATURE_COLUMNS]
    y_valid = valid[TARGET_COLUMN]

    code_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    data_sha = sha256(DATA_PATH.read_bytes()).hexdigest()

    mlflow.set_tracking_uri(f"sqlite:///{DB_PATH.as_posix()}")
    mlflow.set_experiment("Wuhan_PM25_Next_Hour")

    results = []

    # 基线：假设下一小时浓度等于当前小时浓度
    baseline_prediction = X_valid["pm25_lag_0h"]
    baseline_metrics = calculate_metrics(y_valid, baseline_prediction)
    with mlflow.start_run(run_name="Persistence_Baseline"):
        mlflow.log_params({
            "model_type": "persistence",
            "feature_count": len(FEATURE_COLUMNS),
            "code_sha": code_sha,
            "data_sha256": data_sha,
        })
        mlflow.log_metrics({
            "validation_mae": baseline_metrics["mae"],
            "validation_rmse": baseline_metrics["rmse"],
        })
    results.append({"model": "Persistence_Baseline", **baseline_metrics})

    # 候选模型：只用训练集拟合，在验证集评估
    model = RandomForestRegressor(
        n_estimators=300,
        min_samples_leaf=2,
        max_features=0.8,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    model_prediction = model.predict(X_valid)
    model_metrics = calculate_metrics(y_valid, model_prediction)

    with mlflow.start_run(run_name="RandomForest_300_leaf2"):
        mlflow.log_params({
            "model_type": "RandomForestRegressor",
            "n_estimators": 300,
            "min_samples_leaf": 2,
            "max_features": 0.8,
            "random_state": 42,
            "feature_count": len(FEATURE_COLUMNS),
            "code_sha": code_sha,
            "data_sha256": data_sha,
        })
        mlflow.log_metrics({
            "validation_mae": model_metrics["mae"],
            "validation_rmse": model_metrics["rmse"],
        })
        mlflow.sklearn.log_model(
            model,
    name="model",
    input_example=X_train.head(2),
    skops_trusted_types=["sklearn.tree._tree.Tree"],
        )
    results.append({"model": "RandomForest_300_leaf2", **model_metrics})

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = pd.DataFrame(results)
    report.to_csv(REPORT_PATH, index=False)

    print(f"训练样本：{len(train)}；验证样本：{len(valid)}")
    print(f"代码提交号：{code_sha}")
    print(f"数据 SHA-256：{data_sha}")
    print(report.to_string(index=False))
    print(f"MLflow 数据库：{DB_PATH}")
    print(f"指标报告：{REPORT_PATH}")


if __name__ == "__main__":
    main()
