"""Read-only scoring. Refuses to load an artifact whose lock no longer matches."""

import hashlib
import json
import logging
import os
from dataclasses import dataclass

import joblib
import pandas as pd

from core.drivers import top_drivers
from core.validation import ROOT, band_config, feature_spec, validate


@dataclass(frozen=True)
class ScoreResult:
    score: float
    band: str
    uncertain: bool
    drivers: tuple
    model_version: str
    calibration_available: bool


def score(features):
    clean, errors = validate(features, complete=True)
    if errors:
        raise ValueError("; ".join(errors.values()))
    spec = feature_spec()
    path = ROOT / spec["artifact"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != (ROOT / "models/model.lock").read_text().strip():
        raise ValueError("The model no longer matches its locked version. Scoring is disabled.")
    model = joblib.load(path)
    names = [f["name"] for f in spec["features"]]
    if names != model.feature_names_in_.tolist():
        raise ValueError("The feature specification does not match the frozen model.")
    frame = pd.DataFrame([[clean[name] for name in names]], columns=names)
    value = float(model.predict(frame)[0])
    metadata = json.loads((ROOT / "artifacts/report.json").read_text())
    config = band_config()
    if config["calibration_available"] or config["thresholds"]:
        raise ValueError(
            "This artifact has no reviewed risk mapping. Risk thresholds cannot be activated by configuration alone."
        )
    drivers = tuple(top_drivers(model, frame, metadata.get("reference", {}), value))
    if os.getenv("ENABLE_LOGGING", "false").lower() == "true":
        numeric = {k: v for k, v in clean.items() if isinstance(v, (int, float))}
        logging.getLogger("student_self_check.numeric").warning(json.dumps(numeric))
    return ScoreResult(value, config["unmapped_band"], True, drivers, digest, False)
