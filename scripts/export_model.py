from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL_URI = "models:/m-d282d879969647339e26af6db6104fe9"
MODEL_PATH = ROOT / "models" / "random_forest"
DB_PATH = ROOT / "mlflow.db"
FEATURES_PATH = ROOT / "data" / "processed" / "wuhan_pm25_features.csv"
PREDICTIONS_PATH = ROOT / "reports" / "test_predictions.csv"

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


def main():
    mlflow.set_tracking_uri(f"sqlite:///{DB_PATH.as_posix()}")

    if MODEL_PATH.exists():
        raise FileExistsError(f"模型目录已存在，请勿覆盖：{MODEL_PATH}")

    model = mlflow.sklearn.load_model(MODEL_URI)
    mlflow.sklearn.save_model(
        model,
        path=str(MODEL_PATH),
        skops_trusted_types=["sklearn.tree._tree.Tree"],
    )

    exported_model = mlflow.sklearn.load_model(str(MODEL_PATH))
    features = pd.read_csv(FEATURES_PATH)
    test = features[features["split"] == "test"]
    predictions = pd.read_csv(PREDICTIONS_PATH)

    actual = exported_model.predict(test[FEATURE_COLUMNS])
    expected = predictions["random_forest_prediction"].to_numpy()
    np.testing.assert_allclose(actual, expected, rtol=1e-6, atol=1e-6)

    print("模型已导出并重新加载验证通过。")
    print(f"模型目录：{MODEL_PATH}")
    print(f"预测核对：{len(actual)} 条测试记录全部一致。")


if __name__ == "__main__":
    main()
