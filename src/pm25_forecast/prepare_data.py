from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "wuhan_pm25_observed.csv"


def main():
    files = sorted(RAW_DIR.glob("china_cities_*.csv"))
    if not files:
        raise FileNotFoundError(f"No source CSV files found in {RAW_DIR}")

    frames = []
    for file_path in files:
        raw = pd.read_csv(file_path, encoding="utf-8-sig")
        required = {"date", "hour", "type", "武汉"}
        missing_columns = required - set(raw.columns)
        if missing_columns:
            raise ValueError(f"{file_path.name} is missing columns: {sorted(missing_columns)}")

        rows = raw.loc[
            raw["type"].eq("PM2.5"),
            ["date", "hour", "武汉"],
        ].copy()

        if rows.empty:
            continue

        hour_text = rows["hour"].astype(int).astype(str).str.zfill(2)
        date_hour = rows["date"].astype(str).str.strip() + hour_text
        timestamp = pd.to_datetime(
            date_hour,
            format="%Y%m%d%H",
            errors="coerce",
        )
        if timestamp.isna().any():
            raise ValueError(f"Invalid date or hour found in {file_path.name}")

        concentration = pd.to_numeric(rows["武汉"], errors="coerce")
        frames.append(
            pd.DataFrame(
                {
                    "timestamp": timestamp,
                    "pm25_ug_m3": concentration,
                }
            )
        )

    if not frames:
        raise ValueError("No rows with type == 'PM2.5' were found.")

    data = pd.concat(frames, ignore_index=True)
    if data["timestamp"].duplicated().any():
        raise ValueError("Duplicate hourly timestamps were found.")

    data = data.sort_values("timestamp").reset_index(drop=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(
        OUTPUT_PATH,
        index=False,
        date_format="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
    )

    print(f"Input files: {len(files)}")
    print(f"PM2.5 hourly rows: {len(data)}")
    print(f"Valid concentrations: {data['pm25_ug_m3'].notna().sum()}")
    print(f"Blank concentrations preserved: {data['pm25_ug_m3'].isna().sum()}")
    print(f"Time range: {data['timestamp'].min()} to {data['timestamp'].max()}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
