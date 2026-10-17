import numpy as np
import pandas as pd
import pytest

from scripts.build_features import assign_split, build_features, validate_hourly_table


def make_hourly(periods=72, start="2025-01-01"):
    return pd.DataFrame({
        "timestamp_local": pd.date_range(start, periods=periods, freq="h"),
        "pm25_ug_m3": np.arange(periods, dtype=float),
    })


@pytest.mark.parametrize("missing_column", ["timestamp_local", "pm25_ug_m3"])
def test_hourly_validation_rejects_missing_columns(missing_column):
    data = make_hourly().drop(columns=missing_column)
    with pytest.raises(ValueError):
        validate_hourly_table(data)


@pytest.mark.parametrize(
    "problem",
    ["duplicate", "gap", "missing_timestamp", "invalid_timestamp"],
)
def test_hourly_validation_rejects_invalid_timestamps(problem):
    data = make_hourly()
    if problem == "duplicate":
        data.loc[1, "timestamp_local"] = data.loc[0, "timestamp_local"]
    elif problem == "gap":
        data = data.drop(index=1)
    elif problem == "missing_timestamp":
        data.loc[1, "timestamp_local"] = pd.NaT
    else:
        data["timestamp_local"] = data["timestamp_local"].astype(str)
        data.loc[1, "timestamp_local"] = "invalid"

    with pytest.raises(ValueError):
        validate_hourly_table(data)


@pytest.mark.parametrize("value", [-1.0, np.inf, -np.inf, "invalid"])
def test_hourly_validation_rejects_invalid_concentrations(value):
    data = make_hourly()
    data["pm25_ug_m3"] = data["pm25_ug_m3"].astype(object)
    data.loc[30, "pm25_ug_m3"] = value
    with pytest.raises(ValueError):
        validate_hourly_table(data)


@pytest.mark.parametrize("value", [0.0, np.nan])
def test_hourly_validation_preserves_zero_and_missing_values(value):
    data = make_hourly()
    data.loc[30, "pm25_ug_m3"] = value
    result = validate_hourly_table(data)

    if pd.isna(value):
        assert pd.isna(result.loc[30, "pm25_ug_m3"])
    else:
        assert result.loc[30, "pm25_ug_m3"] == 0.0


def test_hourly_validation_sorts_without_changing_observations():
    data = make_hourly()
    shuffled = data.sample(frac=1, random_state=42)
    pd.testing.assert_frame_equal(validate_hourly_table(shuffled), data)


@pytest.mark.parametrize("periods", [0, 1, 24, 25])
def test_feature_generation_returns_no_samples_when_history_is_insufficient(periods):
    assert build_features(make_hourly(periods)).empty


@pytest.mark.parametrize("periods", [26, 48, 72])
def test_feature_generation_uses_correct_lags_and_next_hour_target(periods):
    result = build_features(make_hourly(periods))
    assert len(result) == periods - 25

    for lag in [0, 1, 2, 3, 6, 12, 24]:
        np.testing.assert_allclose(
            result[f"pm25_lag_{lag}h"],
            result["pm25_lag_0h"] - lag,
        )

    np.testing.assert_allclose(
        result["target_pm25_ug_m3"],
        result["pm25_lag_0h"] + 1,
    )
    assert (
        result["target_timestamp"]
        == result["issue_timestamp"] + pd.Timedelta(hours=1)
    ).all()


@pytest.mark.parametrize("missing_index", [25, 30, 40])
def test_feature_generation_excludes_samples_using_missing_observations(missing_index):
    data = make_hourly()
    missing_time = data.loc[missing_index, "timestamp_local"]
    data.loc[missing_index, "pm25_ug_m3"] = np.nan

    result = build_features(data)

    assert not result["target_timestamp"].eq(missing_time).any()
    for lag in [0, 1, 2, 3, 6, 12, 24]:
        used_times = result["issue_timestamp"] - pd.Timedelta(hours=lag)
        assert not used_times.eq(missing_time).any()

    assert len(result) == 72 - 25 - 8


@pytest.mark.parametrize("offset", [1, 6, 24])
def test_future_concentrations_do_not_change_current_input_features(offset):
    original = make_hourly()
    changed = original.copy()
    issue_time = original.loc[30, "timestamp_local"]
    changed.loc[30 + offset, "pm25_ug_m3"] = 9999.0

    before = build_features(original).set_index("issue_timestamp")
    after = build_features(changed).set_index("issue_timestamp")
    input_columns = [
        column for column in before.columns if column.startswith("pm25_lag_")
    ] + ["target_hour_sin", "target_hour_cos", "target_weekday"]

    pd.testing.assert_series_equal(
        before.loc[issue_time, input_columns],
        after.loc[issue_time, input_columns],
    )


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("2025-01-01 00:00", "train"),
        ("2025-09-30 23:00", "train"),
        ("2025-10-01 00:00", "validation"),
        ("2025-10-31 23:00", "validation"),
        ("2025-11-01 00:00", "test"),
        ("2025-12-31 23:00", "test"),
    ],
)
def test_time_split_uses_target_month(target, expected):
    timestamps = pd.Series(pd.to_datetime([target]))
    assert assign_split(timestamps).iloc[0] == expected


@pytest.mark.parametrize(
    ("start", "expected_split"),
    [
        ("2025-09-29 23:00", "validation"),
        ("2025-10-30 23:00", "test"),
    ],
)
def test_cross_month_prediction_uses_target_split_and_calendar(start, expected_split):
    result = build_features(make_hourly(periods=26, start=start))
    row = result.iloc[0]

    assert row["issue_timestamp"].hour == 23
    assert row["target_timestamp"].hour == 0
    assert row["split"] == expected_split
    assert row["target_hour_sin"] == pytest.approx(0.0)
    assert row["target_hour_cos"] == pytest.approx(1.0)
    assert row["target_weekday"] == row["target_timestamp"].dayofweek