\# Dataset Versions



\## Source and scope



The data comes from the Quotsoft China air-quality archive:

https://quotsoft.net/air/



The archive attributes its source to the China National Environmental

Monitoring Centre. This project extracts Wuhan city-level hourly PM2.5

records for 2025, using local China time (UTC+8).



City-level records must not be interpreted as measurements from one

individual monitoring station.



\## Quality audit



\- Daily source files: 365.

\- Expected hourly timestamps: 8,760.

\- Valid PM2.5 values: 8,432.

\- Missing hours: 328 (3.7443%).

\- Missing PM2.5 rows: 138.

\- Present rows with blank concentrations: 190.



The complete hourly table preserves missing values. Missing concentrations

are not interpolated. Samples with missing required predictors or targets

are excluded during feature generation.



\## Training dataset v1



\- Tag: training-data-v1.

\- File: data/processed/wuhan\_pm25\_features.csv.

\- DVC MD5: 62c065cecaf6374a0d29b5717a5e62e2.

\- SHA-256: 3afd9c7c398da91081146c24a73052085448db5562f320d789d481d08fbedf11.

\- Training code commit: 2e7b7dc6a914c4262bfe03e5862d633523e29cd0.

\- Generator: scripts/build\_features.py.

\- Training entry point: scripts/train\_model.py.



Features: PM2.5 at offsets 0, 1, 2, 3, 6, 12 and 24 hours,

plus target-hour sine/cosine and target weekday.



\## Training dataset v2



\- Tag: training-data-v2.

\- File: data/processed/wuhan\_pm25\_features\_v2.csv.

\- DVC MD5: b9f7601cbc4af9fd0842f3067d70443e.

\- SHA-256: 04d65cb8bc849bae26d1b814f28d5a1786239b8dc08009ca009eb5e69dd8a915.

\- Training code commit: 1588751a8b1082a34c6c34423aa93b2cd351e281.

\- Generator: scripts/build\_features\_v2.py.

\- Training entry point: scripts/train\_model\_v2.py.



V2 retains all v1 columns and adds three concentration-change features:

current concentration minus the concentration 1, 3 and 24 hours earlier.



These features use only information available at the issue time.

They do not introduce additional missing samples.



\## Common temporal split



Both versions contain the same 7,078 samples:



| Split | Target period | Samples |

|---|---|---:|

| Training | January-September 2025 | 5,625 |

| Validation | October 2025 | 529 |

| Test | November-December 2025 | 924 |



Splits are determined by target time, including predictions that cross

a month boundary. Data is not randomly shuffled.



The older tags data-v1-source-audit and data-v2-lag-features describe

data-preparation milestones. The training-data-v1 and training-data-v2

tags identify the two datasets actually used in the version comparison.



\## Storage and reproduction



Git stores DVC pointer files. Data and the exported application model

are stored in Azure through the DVC remote:



azure://dvc/wuhan-pm25



After configuring authorized local Azure credentials:



&#x20;   dvc pull



Reproduce the two feature datasets:



&#x20;   python scripts/build\_features.py

&#x20;   python scripts/build\_features\_v2.py



Reproduce their validation experiments:



&#x20;   python scripts/train\_model.py

&#x20;   python scripts/train\_model\_v2.py



Each training script records the checked-out Git commit, dataset label,

DVC MD5, file SHA-256, parameters and validation metrics in MLflow.



For exact historical reproduction, use the recorded training commit

or inspect the corresponding training-data tag. Run each version in

a separate clone when comparing historical checkouts.



Local credentials belong in ignored .dvc/config.local, never in Git.

