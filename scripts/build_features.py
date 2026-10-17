from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "wuhan_pm25_hourly.csv"
OUTPUT = ROOT / "data" / "processed" / "wuhan_pm25_features.csv"

df = pd.read_csv(INPUT, parse_dates=["timestamp_local"])
df = df.sort_values("timestamp_local").reset_index(drop=True)

if df["timestamp_local"].duplicated().any():
    raise ValueError("发现重复时间戳，请先检查小时数据。")
if not df["timestamp_local"].diff().dropna().eq(pd.Timedelta(hours=1)).all():
    raise ValueError("时间戳并非连续逐小时，请先检查小时数据。")

table = pd.DataFrame()
table["issue_timestamp"] = df["timestamp_local"]

lag_columns = []
for lag in [0, 1, 2, 3, 6, 12, 24]:
    column = f"pm25_lag_{lag}h"
    table[column] = df["pm25_ug_m3"].shift(lag)
    lag_columns.append(column)

table["target_timestamp"] = df["timestamp_local"].shift(-1)
table["target_pm25_ug_m3"] = df["pm25_ug_m3"].shift(-1)

target_hour = table["target_timestamp"].dt.hour
target_weekday = table["target_timestamp"].dt.dayofweek
table["target_hour_sin"] = np.sin(2 * np.pi * target_hour / 24)
table["target_hour_cos"] = np.cos(2 * np.pi * target_hour / 24)
table["target_weekday"] = target_weekday

table = table.dropna(
    subset=lag_columns + ["target_timestamp", "target_pm25_ug_m3"]
).copy()

target_month = table["target_timestamp"].dt.month
table["split"] = "test"
table.loc[target_month <= 9, "split"] = "train"
table.loc[target_month == 10, "split"] = "validation"

table.to_csv(OUTPUT, index=False)

print(f"特征样本总数：{len(table)}")
print("各数据集样本数：")
print(table["split"].value_counts().reindex(
    ["train", "validation", "test"], fill_value=0
).to_string())
print(f"输出文件：{OUTPUT}")
print("前两行：")
print(table.head(2).to_string(index=False))
