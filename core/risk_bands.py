"""Interval-based demonstration bands, distinct from calibrated failure probabilities."""

import hashlib
import json
import math
from dataclasses import dataclass

from core.validation import ROOT, band_config

METHOD = "split_conformal_interval_demo_v1"
MEANINGS = {
    "High": "The entire score interval is below the passing mark. Review your progress with a mentor.",
    "Medium": "The score interval crosses the passing mark. The result remains uncertain.",
    "Low": "The entire score interval is at or above the passing mark. This does not guarantee a pass.",
}


@dataclass(frozen=True)
class BandAssessment:
    band: str
    lower: float
    upper: float


def validate_policy(policy, model_hash):
    if policy.get("method") != METHOD or policy.get("model_sha256") != model_hash:
        raise ValueError("Risk policy does not match the locked model and method.")
    for key, low, high in [("passing_score", 0, 100), ("interval_radius", 0, 100),
                           ("nominal_coverage", 0, 1)]:
        value = policy.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Invalid risk policy: {key}")
        if not math.isfinite(value) or not low < value < high:
            raise ValueError(f"Invalid risk policy: {key}")
    if policy["passing_score"] != 60 or policy.get("probability_calibrated") is not False:
        raise ValueError("Only the approved dataset demo rule is supported.")
    counts = policy.get("test_bands", {})
    if set(counts) != set(MEANINGS):
        raise ValueError("Risk policy evaluation is incomplete.")
    for row in counts.values():
        n, below = row.get("records"), row.get("below_pass_mark")
        if type(n) is not int or type(below) is not int or not 0 <= below <= n:
            raise ValueError("Invalid band evaluation counts.")
    if sum(row["records"] for row in counts.values()) != policy.get("test_records"):
        raise ValueError("Band evaluation does not match the test count.")


def load_policy(model_hash):
    raw = (ROOT / "models/band_evidence.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != band_config().get("evidence_sha256"):
        raise ValueError("Risk evidence does not match its reviewed checksum.")
    policy = json.loads(raw)
    validate_policy(policy, model_hash)
    return policy


def assess_band(value, policy):
    if not math.isfinite(value) or not 0 <= value <= 100:
        raise ValueError("Model score must be finite and between zero and one hundred.")
    lower = max(0.0, value - policy["interval_radius"])
    upper = min(100.0, value + policy["interval_radius"])
    passing = policy["passing_score"]
    band = "High" if upper < passing else "Low" if lower >= passing else "Medium"
    return BandAssessment(band, lower, upper)
