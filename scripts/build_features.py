from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "wuhan_pm25_hourly.csv"
OUTPUT = ROOT / "data" / "processed" / "wuhan_pm25_features.csv"
LAGS = [0, 1, 2, 3, 6, 12, 24]


def validate_hourly_table(data):
    """Validate and sort the hourly input without filling missing values."""
    required = {"timestamp_local", "pm25_ug_m3"}
    if not required.issubset(data.columns):
        raise ValueError("Missing required hourly columns.")

    df = data.copy()
    df["timestamp_local"] = pd.to_datetime(
        df["timestamp_local"], errors="raise"
    )
    df["pm25_ug_m3"] = pd.to_numeric(df["pm25_ug_m3"], errors="raise")
    df = df.sort_values("timestamp_local").reset_index(drop=True)

    if df["timestamp_local"].isna().any():
        raise ValueError("Missing timestamps are not allowed.")
    if df["timestamp_local"].duplicated().any():
        raise ValueError("Duplicate timestamps are not allowed.")
    if not df["timestamp_local"].diff().dropna().eq(
        pd.Timedelta(hours=1)
    ).all():
        raise ValueError("Timestamps must be consecutive hourly records.")

    observed = df["pm25_ug_m3"].dropna()
    if not np.isfinite(observed).all() or (observed < 0).any():
        raise ValueError("Observed concentrations must be finite and nonnegative.")

    return df


def assign_split(target_timestamps):
    """Assign splits using the target month, rather than the issue month."""
    months = target_timestamps.dt.month
    result = pd.Series("test", index=target_timestamps.index)
    result.loc[months <= 9] = "train"
    result.loc[months == 10] = "validation"
    return result


def build_features(data):
    """Build next-hour samples using current and past observations."""
    df = validate_hourly_table(data)

    table = pd.DataFrame()
    table["issue_timestamp"] = df["timestamp_local"]

    lag_columns = []
    for lag in LAGS:
        column = f"pm25_lag_{lag}h"
        table[column] = df["pm25_ug_m3"].shift(lag)
        lag_columns.append(column)

    table["target_timestamp"] = df["timestamp_local"].shift(-1)
    table["target_pm25_ug_m3"] = df["pm25_ug_m3"].shift(-1)

    target_hour = table["target_timestamp"].dt.hour
    table["target_hour_sin"] = np.sin(2 * np.pi * target_hour / 24)
    table["target_hour_cos"] = np.cos(2 * np.pi * target_hour / 24)
    table["target_weekday"] = table["target_timestamp"].dt.dayofweek

    table = table.dropna(
        subset=lag_columns + ["target_timestamp", "target_pm25_ug_m3"]
    ).copy()
    table["split"] = assign_split(table["target_timestamp"])
    return table


def main():
    data = pd.read_csv(INPUT, parse_dates=["timestamp_local"])
    table = build_features(data)
    table.to_csv(OUTPUT, index=False)

    print(f"Feature samples: {len(table)}")
    print(
        table["split"].value_counts().reindex(
            ["train", "validation", "test"], fill_value=0
        ).to_string()
    )
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()