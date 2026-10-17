import os
from pathlib import Path

import mlflow.sklearn
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
FEATURES_PATH = ROOT / "data" / "processed" / "wuhan_pm25_features.csv"
PREDICTIONS_PATH = ROOT / "reports" / "test_predictions.csv"
METRICS_PATH = ROOT / "reports" / "test_metrics.csv"
COVERAGE_PATH = ROOT / "reports" / "monthly_coverage.csv"
MODEL_PATH = ROOT / "models" / "random_forest"

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


APP_ENV = os.getenv("APP_ENV", "local")
APP_TITLE = os.getenv("APP_TITLE", "武汉 PM2.5 下一小时预测")

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption("2025 年历史数据回放，不是实时监测或实时预报。")
st.caption(f"运行环境：{APP_ENV}")

@st.cache_data
def load_tables():
    features = pd.read_csv(FEATURES_PATH)
    predictions = pd.read_csv(PREDICTIONS_PATH)
    coverage = pd.read_csv(COVERAGE_PATH)
    metrics = pd.read_csv(METRICS_PATH)

    features["target_timestamp"] = pd.to_datetime(features["target_timestamp"])
    predictions["target_timestamp"] = pd.to_datetime(
        predictions["target_timestamp"]
    )
    test = features[features["split"] == "test"].copy()
    test = test.merge(
        predictions,
        on="target_timestamp",
        how="inner",
        validate="one_to_one",
    )
    return test, coverage, metrics


@st.cache_resource
def load_model():
    return mlflow.sklearn.load_model(str(MODEL_PATH))


test, coverage, metrics = load_tables()
model = load_model()

expected = int(coverage["expected_hours"].sum())
valid = int(coverage["valid_hours"].sum())
missing = int(coverage["missing_hours"].sum())
missing_percent = 100 * missing / expected

baseline = metrics.loc[metrics["model"] == "Persistence_Baseline"].iloc[0]
candidate = metrics.loc[metrics["model"] == "RandomForest_300_leaf2"].iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("2025 应有小时数", f"{expected:,}")
col2.metric("有效 PM2.5 小时", f"{valid:,}")
col3.metric("缺失小时", f"{missing:,}", f"{missing_percent:.2f}%")
col4.metric(
    "测试集随机森林 MAE",
    f"{candidate['mae']:.3f} µg/m³",
    f"{baseline['mae'] - candidate['mae']:.3f} 优于基线",
)

st.subheader("数据覆盖情况")
coverage_chart = coverage.set_index("month")["missing_hours"]
st.bar_chart(coverage_chart, y_label="缺失小时数")
st.caption("逐月缺失小时数；全年缺失率约 3.74%。")

st.subheader("测试集模型表现")
metric_view = metrics.set_index("model")[["mae", "rmse"]]
st.dataframe(
    metric_view.rename(columns={"mae": "MAE (µg/m³)", "rmse": "RMSE (µg/m³)"}),
    use_container_width=True,
)

st.subheader("历史预测回放")
days = sorted(test["target_timestamp"].dt.date.unique())
selected_day = st.selectbox(
    "选择测试集日期",
    days,
    format_func=lambda value: value.strftime("%Y-%m-%d"),
)
daily = test[test["target_timestamp"].dt.date == selected_day].copy()

selected_time = st.selectbox(
    "选择要回放的目标小时",
    daily["target_timestamp"].tolist(),
    format_func=lambda value: value.strftime("%Y-%m-%d %H:%M"),
)
selected = daily.loc[daily["target_timestamp"] == selected_time].iloc[0]
model_prediction = float(
    model.predict(selected[FEATURE_COLUMNS].astype(float).to_frame().T)[0]
)

forecast_col, actual_col, baseline_col = st.columns(3)
forecast_col.metric("随机森林预测", f"{model_prediction:.1f} µg/m³")
actual_col.metric("该小时实际值", f"{selected['actual_pm25_ug_m3']:.1f} µg/m³")
baseline_col.metric(
    "持续性基线预测",
    f"{selected['baseline_prediction']:.1f} µg/m³",
)
st.write(
    f"预测发起时间：**{selected['issue_timestamp']}**　→　"
    f"目标时间：**{selected_time}**"
)

st.markdown("**当天实际值与预测值**")
chart = daily.set_index("target_timestamp")[
    ["actual_pm25_ug_m3", "random_forest_prediction", "baseline_prediction"]
]
chart = chart.rename(columns={
    "actual_pm25_ug_m3": "实际值",
    "random_forest_prediction": "随机森林",
    "baseline_prediction": "持续性基线",
})
st.line_chart(chart, height=360)

with st.expander("数据与方法说明"):
    st.write(
        "数据来源为武汉 2025 年逐小时历史空气质量记录。"
        "模型使用当前及过去 24 小时内的 PM2.5 滞后值和目标小时的日历特征，"
        "预测下一小时。缺失特征或目标值的样本未用于训练与评估。"
    )
