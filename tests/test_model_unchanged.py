import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_model_hash_unchanged():
    expected = (ROOT / "models/model.lock").read_text().strip()
    assert hashlib.sha256((ROOT / "artifacts/model.joblib").read_bytes()).hexdigest() == expected


def test_all_protected_training_files_unchanged():
    files = json.loads((ROOT / "models/protected_files.json").read_text())
    # A deployment checkout intentionally excludes the training archive. The
    # mandatory artifact check above still runs there; the full local audit runs
    # only where the original complete training workspace is available.
    if not (ROOT / "train.py").exists():
        pytest.skip("Full training-workspace audit is local-only; datasets are not published.")
    for name, expected in files.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
