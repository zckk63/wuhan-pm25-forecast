from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "processed" / "wuhan_pm25_features.csv"
OUTPUT = ROOT / "data" / "processed" / "wuhan_pm25_features_v2.csv"


def build_v2_features(data):
    result = data.copy()
    for hours in [1, 3, 24]:
        result[f"pm25_change_{hours}h"] = (
            result["pm25_lag_0h"] - result[f"pm25_lag_{hours}h"]
        )
    return result


def main():
    data = pd.read_csv(INPUT)
    result = build_v2_features(data)
    result.to_csv(OUTPUT, index=False)

    print(f"Feature samples: {len(result)}")
    print(f"Feature columns added: {len(result.columns) - len(data.columns)}")
    print(result["split"].value_counts().to_string())
    print(f"Output: {OUTPUT}")


if __name__ == "__main__":
    main()