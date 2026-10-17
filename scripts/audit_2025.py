from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OBSERVED_PATH = PROJECT_ROOT / "data" / "processed" / "wuhan_pm25_observed.csv"
HOURLY_PATH = PROJECT_ROOT / "data" / "processed" / "wuhan_pm25_hourly.csv"
MISSING_PATH = PROJECT_ROOT / "reports" / "pm25_missing_hours.csv"
MONTHLY_PATH = PROJECT_ROOT / "reports" / "monthly_coverage.csv"
SAMPLES_PATH = PROJECT_ROOT / "reports" / "usable_samples.csv"
VALUE_COLUMN = "pm25_ug_m3"


def main():
    observed = pd.read_csv(OBSERVED_PATH, parse_dates=["timestamp"])
    if observed["timestamp"].duplicated().any():
        raise ValueError("Duplicate timestamps found in the observed data.")

    expected = pd.date_range(
        "2025-01-01 00:00:00",
        "2025-12-31 23:00:00",
        freq="h",
        name="timestamp_local",
    )

    observed = observed.set_index("timestamp").sort_index()
    if not observed.index.isin(expected).all():
        raise ValueError("Observed data contains timestamps outside 2025.")

    source_has_row = pd.Series(expected.isin(observed.index), index=expected)
    hourly = observed.reindex(expected)
    hourly.index.name = "timestamp_local"

    HOURLY_PATH.parent.mkdir(parents=True, exist_ok=True)
    hourly.reset_index().to_csv(
        HOURLY_PATH,
        index=False,
        date_format="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
    )

    missing = hourly[VALUE_COLUMN].isna()
    missing_times = hourly.index[missing]
    reasons = [
        "blank_value" if source_has_row.loc[timestamp] else "no_PM2.5_row"
        for timestamp in missing_times
    ]
    missing_report = pd.DataFrame(
        {"timestamp_local": missing_times, "reason": reasons}
    )
    MISSING_PATH.parent.mkdir(parents=True, exist_ok=True)
    missing_report.to_csv(MISSING_PATH, index=False, encoding="utf-8")

    monthly_rows = []
    for month in range(1, 13):
        values = hourly.loc[hourly.index.month == month, VALUE_COLUMN]
        monthly_rows.append(
            {
                "month": month,
                "expected_hours": len(values),
                "valid_hours": int(values.notna().sum()),
                "missing_hours": int(values.isna().sum()),
                "missing_percent": round(float(values.isna().mean() * 100), 4),
            }
        )
    monthly = pd.DataFrame(monthly_rows)
    monthly.to_csv(MONTHLY_PATH, index=False, encoding="utf-8")

    lag_hours = [0, 1, 2, 3, 6, 12, 24]
    feature_names = []
    samples = pd.DataFrame(index=hourly.index)
    for lag in lag_hours:
        name = f"pm25_lag_{lag}h"
        samples[name] = hourly[VALUE_COLUMN].shift(lag)
        feature_names.append(name)

    samples["target_next_hour"] = hourly[VALUE_COLUMN].shift(-1)
    samples["target_time"] = samples.index + pd.Timedelta(hours=1)
    usable = samples.dropna(subset=feature_names + ["target_next_hour"])

    split_ranges = [
        ("train", "2025-01-01", "2025-10-01"),
        ("validation", "2025-10-01", "2025-11-01"),
        ("test", "2025-11-01", "2026-01-01"),
    ]
    sample_rows = []
    for split, start, end in split_ranges:
        start_time = pd.Timestamp(start)
        end_time = pd.Timestamp(end)
        part = usable[
            (usable["target_time"] >= start_time)
            & (usable["target_time"] < end_time)
        ]
        sample_rows.append({"split": split, "usable_samples": len(part)})

    pd.DataFrame(sample_rows).to_csv(
        SAMPLES_PATH, index=False, encoding="utf-8"
    )

    missing_source_rows = int((missing & ~source_has_row).sum())
    blank_values = int((missing & source_has_row).sum())
    print(f"Expected hours: {len(expected)}")
    print(f"Valid PM2.5 hours: {int(hourly[VALUE_COLUMN].notna().sum())}")
    print(f"Missing hours: {int(missing.sum())}")
    print(f"  No PM2.5 row in source: {missing_source_rows}")
    print(f"  Blank PM2.5 value: {blank_values}")
    print(f"Missing rate: {missing.mean() * 100:.4f}%")
    print(f"Usable lag-feature samples: {len(usable)}")
    print(pd.DataFrame(sample_rows).to_string(index=False))
    print(f"Full hourly table: {HOURLY_PATH}")
    print(f"Monthly coverage: {MONTHLY_PATH}")
    print(f"Missing-hour list: {MISSING_PATH}")


if __name__ == "__main__":
    main()
