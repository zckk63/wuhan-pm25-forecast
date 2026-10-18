import json
from pathlib import Path

import pandas as pd
import yaml
from mlflow.tracking import MlflowClient

ROOT = Path(__file__).resolve().parents[1]


def main():
    client = MlflowClient(
        tracking_uri=f"sqlite:///{(ROOT / 'mlflow.db').as_posix()}"
    )
    experiment = client.get_experiment_by_name("Wuhan_PM25_Next_Hour")
    if experiment is None:
        raise ValueError("MLflow experiment not found.")

    logged_models = client.search_logged_models(
        experiment_ids=[experiment.experiment_id],
        max_results=1000,
    )
    records = []
    summary = []

    for version in ["v1", "v2"]:
        filename = (
            "wuhan_pm25_features.csv"
            if version == "v1"
            else "wuhan_pm25_features_v2.csv"
        )
        pointer_path = ROOT / "data/processed" / f"{filename}.dvc"
        pointer = yaml.safe_load(pointer_path.read_text(encoding="utf-8-sig"))
        expected_md5 = pointer["outs"][0]["md5"]

        for model_name in ["Persistence_Baseline", "RandomForest_300_leaf2"]:
            name = f"Data_{version}_{model_name}"
            runs = client.search_runs(
                experiment_ids=[experiment.experiment_id],
                filter_string=f"tags.mlflow.runName = '{name}'",
                order_by=["attributes.start_time DESC"],
                max_results=1,
            )
            if not runs:
                raise ValueError(f"Missing run: {name}")

            run = runs[0]
            params = run.data.params
            if run.info.status != "FINISHED":
                raise ValueError(f"Run is not finished: {name}")
            if params.get("dvc_data_md5") != expected_md5:
                raise ValueError(f"DVC hash mismatch: {name}")
            if params.get("dataset_version") != f"training-data-{version}":
                raise ValueError(f"Dataset label mismatch: {name}")

            model_ids = [
                model.model_id
                for model in logged_models
                if model.source_run_id == run.info.run_id
            ]
            if model_name.startswith("RandomForest") and not model_ids:
                raise ValueError(f"Logged model not found: {name}")

            records.append({
                "name": name,
                "run_id": run.info.run_id,
                "status": run.info.status,
                "params": params,
                "metrics": run.data.metrics,
                "logged_model_ids": model_ids,
            })
            summary.append({
                "dataset_version": params["dataset_version"],
                "model": model_name,
                "run_id": run.info.run_id,
                "code_sha": params["code_sha"],
                "dvc_data_md5": params["dvc_data_md5"],
                "validation_mae": run.data.metrics["validation_mae"],
                "validation_rmse": run.data.metrics["validation_rmse"],
            })

    report_dir = ROOT / "reports"
    report_dir.mkdir(exist_ok=True)
    (report_dir / "mlflow_experiment_records.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    table = pd.DataFrame(summary)
    table.to_csv(report_dir / "mlflow_experiment_summary.csv", index=False)
    print(table[
        ["dataset_version", "model", "validation_mae", "validation_rmse"]
    ].to_string(index=False))
    print(f"Exported {len(records)} verified MLflow runs.")


if __name__ == "__main__":
    main()