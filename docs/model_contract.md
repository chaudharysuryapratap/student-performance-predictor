# Frozen model contract

Inspected the existing artifact at `artifacts/model.joblib` on 2026-10-23. The model is read-only. SHA-256 is stored in `models/model.lock`; `models/protected_files.json` additionally records all existing artifacts, training scripts and research data. Neither training script is invoked by the self-check.

Format: joblib-serialized scikit-learn 1.6.1 `Pipeline`: `ColumnTransformer` -> `RandomForestRegressor` (180 trees, min_samples_leaf=5). Python runtime inspected: 3.13. Numeric columns pass through StandardScaler; categories through OneHotEncoder(handle_unknown='ignore', sparse_output=False). No imputation exists. Required missing values are re-asked; no defaults are supplied for unknown student inputs. The service rejects unknown categories even though the encoder could ignore them.

Expected ordered pandas DataFrame columns:

| Feature | Type | Accepted range | Training range | Self-report |
|---|---|---|---|---|
| Study_Hours_per_Week | float | 0–168 hours/week | From frozen report | Yes; typical week estimate |
| Attendance_Rate | float | 0–100 percent | From frozen report | Yes if known from attendance record |
| Past_Exam_Scores | float | 0–100 percent | From frozen report | Yes; student confirms which past exam is relevant |
| Internet_Access_at_Home | string | Yes / No | Yes / No | Yes |
| Extracurricular_Activities | string | Yes / No | Yes / No | Yes |

Output: one continuous final-exam score; no classes or `predict_proba`. It is not a probability, risk score, percentile or official grade. The artifact was trained on the public demonstration dataset described in README, not verified college records. Observed source target range is 50–77. Exact training feature ranges remain in the existing `artifacts/report.json` and are used for uncertainty checks, without modifying that file.

The existing report has a split-conformal absolute-residual interval radius and nominal coverage, not a validated failure-probability calibration or risk-band mapping. This self-check therefore reports `band='Not established'` and `calibration_available=False`. No historical pass/fail percentages are displayed. Risk thresholds remain disabled in `core/bands.yaml`. A valid threshold mapping would require evidence and a different reviewed score contract; a YAML edit alone does not validate a mapping.

The deterministic service returns the model's exact score, model SHA, uncertainty flag, band, calibration flag and optional model-sensitivity drivers. Sensitivity drivers replace one feature at a time with the frozen training reference from the existing report. They are not SHAP, additive explanations, causes or study prescriptions.

Every result states: it is an estimate from limited self-reported data, not a prediction of the student's result, and a mentor or faculty member is the right person to talk to.

Deployment packaging: the original model is included byte-for-byte. Runtime explanation reference values are copied into `models/metadata.json` without training records, partition IDs or predictions. The original report, datasets, training scripts and other dataset artifacts remain untouched locally and are not published. The model hash check runs everywhere; the complete protected-workspace audit runs only in the original workspace where `train.py` and all protected assets exist.
