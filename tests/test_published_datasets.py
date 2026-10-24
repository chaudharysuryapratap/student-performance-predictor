"""Verify published source bytes without training on or logging student records."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_published_training_inputs_match_manifest():
    manifest = json.loads((ROOT / "research/manifest.json").read_text())
    assert len(manifest["files"]) == 8
    for item in manifest["files"]:
        path = (ROOT / item["path"]).resolve()
        assert path.is_relative_to(ROOT / "research")
        assert path.stat().st_size == item["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
