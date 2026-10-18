\# Data and Model Provenance



\## Traceability chain



Source archive -> audited hourly table -> versioned features ->

MLflow training run -> exported model -> Docker application.



Raw data, processed datasets and the exported model are managed by DVC

with Azure remote storage. Git stores code, pointers and small reports.



\## Dataset-version experiments



| Version | Training commit | DVC MD5 |

|---|---|---|

| training-data-v1 | 2e7b7dc6a914c4262bfe03e5862d633523e29cd0 | 62c065cecaf6374a0d29b5717a5e62e2 |

| training-data-v2 | 1588751a8b1082a34c6c34423aa93b2cd351e281 | b9f7601cbc4af9fd0842f3067d70443e |



The training-data tags identify snapshots containing the respective

dataset pointers and reports. The training commits above identify

the code actually executed, which can precede the report commits.



Both version-comparison scripts log code SHA, DVC MD5, file SHA-256,

dataset label, parameters and validation metrics.



\## Application model



The application model predates the version-comparison reruns.



\- Original training run: 0ffe9f64766641e58bd86bb5e0915fe9.

\- Original training commit: 9e652b723f17269cafb36862e30410f7cd1f4e1d.

\- Model URI: models:/m-d282d879969647339e26af6db6104fe9.

\- Exported directory DVC MD5: 59fed1f6f6998ce6a1c5a2b60ba5194a.dir.



The original run recorded the feature-file SHA-256. That SHA-256 matches

the dataset subsequently identified as training-data-v1.



Prediction agreement on 924 test inputs is a consistency check, not

by itself proof of identical model files. Source attribution also

uses the recorded model URI and project export history.



Machine-readable export verification:

reports/model\_provenance.json



Model selection and metrics:

ml/README\_experiments.md



\## CI and environment delivery



Pull-request CI checks code, runs the full test suite and builds Docker.



After CI succeeds on staging/main pushes, the delivery job reads the

corresponding environment Secrets, builds an image tagged with the branch

and full Git SHA, and verifies the application inside the container.



The delivery-summary.json workflow artifact records environment, code SHA,

image tag, image ID and verification result.



Local MLflow databases and Azure credentials are not committed.

