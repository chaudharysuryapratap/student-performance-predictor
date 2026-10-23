import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_model_hash_unchanged():
    expected = (ROOT/'models/model.lock').read_text().strip()
    assert hashlib.sha256((ROOT/'artifacts/model.joblib').read_bytes()).hexdigest() == expected


def test_all_protected_training_files_unchanged():
    files = json.loads((ROOT/'models/protected_files.json').read_text())
    for name, expected in files.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
