"""Audit the existing interval and evaluate demo bands. Never fit or save a model."""

import hashlib
import json
import math
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.risk_bands import METHOD, assess_band, validate_policy
from core.validation import ROOT


def evaluate():
    source = ROOT / "research/dataset/student_performance_dataset.csv"
    report_path = ROOT / "artifacts/report.json"
    report = json.loads(report_path.read_text())
    digest = hashlib.sha256((ROOT / "artifacts/model.joblib").read_bytes()).hexdigest()
    if digest != (ROOT / "models/model.lock").read_text().strip():
        raise ValueError("Model lock mismatch")
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_digest != report["sha256"]:
        raise ValueError("Source differs from the original training report")
    frame = pd.read_csv(source).drop_duplicates("Student_ID").set_index("Student_ID")
    if not ((frame.Final_Exam_Score >= 60) == (frame.Pass_Fail == "Pass")).all():
        raise ValueError("Source labels do not follow the approved passing rule")
    splits = {name: set(ids) for name, ids in report["splits"].items()}
    if any(splits[a] & splits[b] for a, b in [("train", "calibration"), ("train", "test"),
                                             ("calibration", "test")]):
        raise ValueError("Overlapping partitions")
    if set.union(*splits.values()) != set(frame.index):
        raise ValueError("Partition membership mismatch")
    model = joblib.load(ROOT / "artifacts/model.joblib")
    calibration = frame.loc[report["splits"]["calibration"]]
    residuals = np.abs(calibration.Final_Exam_Score.to_numpy() -
                       model.predict(calibration[list(model.feature_names_in_)]))
    rank = min(len(residuals), math.ceil((len(residuals) + 1) * report["nominal_coverage"]))
    radius = float(np.sort(residuals)[rank - 1])
    if not math.isclose(radius, report["interval_radius"], abs_tol=1e-10):
        raise ValueError("Existing calibration radius mismatch")
    test = frame.loc[report["splits"]["test"]]
    predictions = model.predict(test[list(model.feature_names_in_)])
    stored = pd.read_csv(ROOT / "artifacts/test_predictions.csv").set_index("Student_ID")
    if not np.allclose(predictions, stored.loc[test.index].Predicted, atol=1e-10, rtol=0):
        raise ValueError("Saved test predictions mismatch")
    policy = {
        "method": METHOD, "passing_score": 60.0, "interval_radius": radius,
        "nominal_coverage": report["nominal_coverage"], "probability_calibrated": False,
        "model_sha256": digest, "source_sha256": source_digest,
        "original_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "calibration_records": len(calibration), "test_records": len(test),
        "test_interval_covered": int((np.abs(test.Final_Exam_Score.to_numpy()-predictions) <= radius).sum()),
        "test_bands": {band: {"records": 0, "below_pass_mark": 0}
                       for band in ["High", "Medium", "Low"]},
        "scope": "Public demonstration dataset only; not validated on college records.",
        "limitations": ["The Low band has very little test support.",
                        "Marginal interval coverage is not an individual passing probability.",
                        "The test set has been inspected; it is not a fresh future validation set."],
    }
    for value, actual in zip(predictions, test.Final_Exam_Score):
        row = policy["test_bands"][assess_band(float(value), policy).band]
        row["records"] += 1
        row["below_pass_mark"] += int(actual < policy["passing_score"])
    validate_policy(policy, digest)
    return policy


if __name__ == "__main__":
    evidence = evaluate()
    (ROOT / "models/band_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
