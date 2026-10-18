\# Current Application Model



\## Selected model



RandomForestRegressor using the v1 lag and calendar features.



\- Model directory: models/random\_forest.

\- DVC pointer: models/random\_forest.dvc.

\- Directory DVC MD5: 59fed1f6f6998ce6a1c5a2b60ba5194a.dir.

\- Source MLflow run: 0ffe9f64766641e58bd86bb5e0915fe9.

\- Source model URI: models:/m-d282d879969647339e26af6db6104fe9.

\- Training code commit: 9e652b723f17269cafb36862e30410f7cd1f4e1d.

\- Training data SHA-256: 3afd9c7c398da91081146c24a73052085448db5562f320d789d481d08fbedf11.

\- Training data DVC MD5: 62c065cecaf6374a0d29b5717a5e62e2.



\## Selection rationale



The v1-feature random forest has the lower validation MAE in the

dataset-version comparison. V2 improves RMSE slightly but worsens MAE,

so the existing application model is retained.



The exported model was compared with the original MLflow model on

924 test inputs. Predictions agreed within rtol=1e-12 and atol=1e-12.

See reports/model\_provenance.json.



The export does not retain MLflow run\_id/model\_id fields internally.

Source attribution is recorded here and in the provenance report,

supported by the project history and prediction consistency check.



\## Application scope



This model supports historical Wuhan 2025 next-hour PM2.5 replay.

It is not connected to a live monitoring feed.



Staging and production use the same selected model. Their environment

configuration differs; the production label does not imply validation

for operational air-quality forecasting.



\## Recovery



Configure authorized local Azure credentials, then run:



&#x20;   dvc pull models/random\_forest.dvc

