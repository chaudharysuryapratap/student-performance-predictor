import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from core.validation import ROOT


def test_interval_band_boundaries():
    from core.risk_bands import assess_band

    policy = {"passing_score": 60.0, "interval_radius": 6.0}
    for value, expected in [(53.99, "High"), (54, "Medium"), (65.99, "Medium"), (66, "Low")]:
        result = assess_band(value, policy)
        assert result.band == expected
        assert result.lower <= value <= result.upper
    assert assess_band(0, policy).lower == 0
    assert assess_band(100, policy).upper == 100
    with pytest.raises(ValueError):
        assess_band(float("nan"), policy)


def test_policy_is_bound_to_frozen_model_and_evaluation():
    from core.risk_bands import validate_policy

    digest = (ROOT / "models/model.lock").read_text().strip()
    policy = json.loads((ROOT / "models/band_evidence.json").read_text())
    validate_policy(policy, digest)
    assert policy["passing_score"] == 60
    assert sum(row["records"] for row in policy["test_bands"].values()) == 100
    assert policy["test_bands"]["Low"]["records"] == 2
    invalid = deepcopy(policy)
    invalid["model_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="model"):
        validate_policy(invalid, digest)
    for field, value in [("passing_score", True), ("interval_radius", -1),
                         ("nominal_coverage", 1.5)]:
        invalid = deepcopy(policy)
        invalid[field] = value
        with pytest.raises(ValueError):
            validate_policy(invalid, digest)


def test_tampered_evidence_disables_bands(monkeypatch, tmp_path):
    import core.risk_bands as bands

    (tmp_path / "models").mkdir()
    raw = (ROOT / "models/band_evidence.json").read_bytes()
    (tmp_path / "models/band_evidence.json").write_bytes(raw + b" ")
    monkeypatch.setattr(bands, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="checksum"):
        bands.load_policy((ROOT / "models/model.lock").read_text().strip())


def test_interval_chart_preserves_full_precision_data():
    from app.results import score_interval_chart

    result = SimpleNamespace(score=66.26076080693664, interval_low=60.0,
                             interval_high=72.52152161387328, passing_score=60.0, band="Low")
    spec = score_interval_chart(result).to_dict()
    rows = next(iter(spec["datasets"].values()))
    assert rows == [{"Score": result.score, "Lower": result.interval_low,
                     "Upper": result.interval_high, "Passing mark": 60.0,
                     "Profile": "Confirmed estimate"}]
    assert len(spec["layer"]) == 3
