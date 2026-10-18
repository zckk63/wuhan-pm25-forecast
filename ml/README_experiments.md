\# MLflow Experiments and Model Selection



\## Tracking



Experiment: Wuhan\_PM25\_Next\_Hour.



The local MLflow backend is mlflow.db. The database is ignored by Git.

Training scripts recreate experiment records; run IDs below identify

the original local runs and will differ when training is repeated.



Each dataset-version run records the code SHA, dataset label, DVC MD5,

file SHA-256, model parameters and validation metrics.

Random-forest runs also log the trained model.



\## Models and controlled comparison



Persistence predicts the next-hour concentration as the current value.



RandomForestRegressor uses:



\- n\_estimators: 300.

\- min\_samples\_leaf: 2.

\- max\_features: 0.8.

\- random\_state: 42.



V1 and v2 use identical training/validation rows and model settings.

The changed factor is the addition of three historical change features.



\## Validation results



Metric units: micrograms per cubic metre. Lower is better.



| Dataset | Model | MAE | RMSE |

|---|---|---:|---:|

| v1 | Persistence | 2.155009 | 3.100704 |

| v1 | Random forest | 2.071407 | 3.061594 |

| v2 | Persistence | 2.155009 | 3.100704 |

| v2 | Random forest | 2.091484 | 3.042828 |



\## Recorded runs



| Dataset | Model | Run ID |

|---|---|---|

| v1 | Persistence | 39bc9ed0e89645fdb3a6ce1ab2ccef9b |

| v1 | Random forest | f8ab43b28e7f4b2e826f0e88baf25204 |

| v2 | Persistence | b292d971a9f848c38a79da8585cbc7e5 |

| v2 | Random forest | ee01f5228ec947378b480c62afd225f7 |



V1 code commit:

2e7b7dc6a914c4262bfe03e5862d633523e29cd0



V2 code commit:

1588751a8b1082a34c6c34423aa93b2cd351e281



See README\_data.md for the corresponding DVC and SHA-256 hashes.



\## Model choice



The application retains the v1-feature random forest.



MAE is the primary selection metric because it expresses the typical

absolute concentration error in the same units displayed by the app.

RMSE is a secondary metric that gives larger errors greater weight.



V2 slightly improves validation RMSE but worsens validation MAE.

It is therefore retained as a documented feature experiment rather

than replacing the application model.



The selected model is suitable for this historical-replay course app.

These results do not establish readiness for operational forecasting.



\## Original application model and test evaluation



The application uses the previously exported v1-feature model,

rather than either newly logged version-comparison model.



\- Original source run: 0ffe9f64766641e58bd86bb5e0915fe9.

\- Original model URI: models:/m-d282d879969647339e26af6db6104fe9.

\- Original training commit: 9e652b723f17269cafb36862e30410f7cd1f4e1d.

\- Exported model directory: models/random\_forest.

\- Exported directory DVC MD5: 59fed1f6f6998ce6a1c5a2b60ba5194a.dir.



The exported model and original MLflow model were checked on all

924 test inputs; predictions agreed within the verification tolerance.

See reports/model\_provenance.json.



The original held-out test results were:



| Model | MAE | RMSE |

|---|---:|---:|

| Persistence | 3.309524 | 5.501869 |

| v1-feature random forest | 3.127650 | 5.129012 |



The evaluation script was recorded at commit:

8a7ac195b328a467d44d79b8915f8773bcd1eca1



\## Evaluation limitation



The v2 experiment was added after the original test results had already

been viewed. V2 was compared on validation data only; it was not selected

using an additional test comparison.



The reported test results are the original evaluation, not a new blind

test of the expanded development process. Further model development

should use a new untouched time period for an independent final check.

