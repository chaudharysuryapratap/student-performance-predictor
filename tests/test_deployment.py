import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_minimal_metadata_and_model_hash():
    metadata = json.loads((ROOT / "models/metadata.json").read_text())
    assert metadata["model_sha256"] == (ROOT / "models/model.lock").read_text().strip()
    assert set(metadata) == {"model_sha256", "reference", "ranges", "source"}
    assert "Student_ID" not in json.dumps(metadata)


def test_cloud_entrypoint(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    app = AppTest.from_file("streamlit_app.py", default_timeout=30).run()
    assert not app.exception
    assert any("Student self-check" in title.value for title in app.title)
    assert app.button[0].disabled
