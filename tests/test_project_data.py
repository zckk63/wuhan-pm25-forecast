from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_hourly_data_has_complete_2025_timeline():
    hourly = pd.read_csv(
        ROOT / "data/processed/wuhan_pm25_hourly.csv",
        parse_dates=["timestamp_local"],
    )

    expected = pd.date_range(
        "2025-01-01 00:00:00",
        "2025-12-31 23:00:00",
        freq="h",
    )

    assert len(hourly) == 8760
    assert hourly["timestamp_local"].is_unique
    assert pd.DatetimeIndex(hourly["timestamp_local"]).equals(expected)
    assert hourly["pm25_ug_m3"].notna().sum() == 8432


def test_features_have_expected_splits_and_complete_values():
    features = pd.read_csv(
        ROOT / "data/processed/wuhan_pm25_features.csv",
        parse_dates=["issue_timestamp", "target_timestamp"],
    )

    assert len(features) == 7078
    assert features["split"].value_counts().to_dict() == {
        "train": 5625,
        "test": 924,
        "validation": 529,
    }

    lag_columns = [
        "pm25_lag_0h",
        "pm25_lag_1h",
        "pm25_lag_2h",
        "pm25_lag_3h",
        "pm25_lag_6h",
        "pm25_lag_12h",
        "pm25_lag_24h",
    ]
    required_columns = lag_columns + [
        "target_pm25_ug_m3",
        "target_hour_sin",
        "target_hour_cos",
        "target_weekday",
    ]

    assert features[required_columns].notna().all().all()


def test_every_feature_row_predicts_exactly_one_hour_ahead():
    features = pd.read_csv(
        ROOT / "data/processed/wuhan_pm25_features.csv",
        parse_dates=["issue_timestamp", "target_timestamp"],
    )

    assert (
        features["target_timestamp"]
        == features["issue_timestamp"] + pd.Timedelta(hours=1)
    ).all()


def test_random_forest_beats_persistence_on_held_out_test():
    metrics = pd.read_csv(ROOT / "reports/test_metrics.csv").set_index("model")

    baseline = metrics.loc["Persistence_Baseline"]
    forest = metrics.loc["RandomForest_300_leaf2"]

    assert forest["mae"] < baseline["mae"]
    assert forest["rmse"] < baseline["rmse"]
