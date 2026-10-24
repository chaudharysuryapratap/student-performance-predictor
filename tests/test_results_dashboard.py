import json

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from core.conversation import Conversation
from core.validation import ROOT


def test_dashboard_only_after_confirmation(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    app = AppTest.from_file("streamlit_app.py", default_timeout=30).run()
    assert not app.get("arrow_vega_lite_chart")
    session = Conversation()
    session.consent()
    session.set_form({
        "Study_Hours_per_Week": 0.0,
        "Attendance_Rate": 85.0,
        "Past_Exam_Scores": 70.0,
        "Internet_Access_at_Home": "Yes",
        "Extracurricular_Activities": "No",
    })
    app.session_state["self_check"] = session
    app.run()
    assert not app.get("arrow_vega_lite_chart")
    session.confirm()
    app.run()
    assert not app.exception
    assert app.metric[0].value == f"{session.result.score:.2f} / 100"
    assert app.metric[1].value in {"High", "Medium", "Low"}
    assert any("Demo score interval" in item.value for item in app.markdown)
    assert len(app.get("arrow_vega_lite_chart")) == 6
    assert any("outside" in item.value for item in app.warning)
    monkeypatch.setattr("app.results.source_scores", lambda: pd.DataFrame())
    app.run()
    assert not app.exception
    assert app.metric[0].value == f"{session.result.score:.2f} / 100"
    assert len(app.get("arrow_vega_lite_chart")) == 5
    assert any("Source score data is unavailable" in item.value for item in app.warning)


def test_source_scores_exclude_identity_fields_and_missing_file():
    from app.results import source_scores

    scores = source_scores()
    assert list(scores.columns) == ["Final_Exam_Score"]
    assert len(scores) == 708
    assert (scores.min().iloc[0], scores.max().iloc[0]) == (50, 77)
    assert source_scores(ROOT / "research/absent.csv").empty


def test_chart_data_keeps_units_and_signed_sensitivity():
    from app.results import input_comparison, sensitivity_chart

    metadata = json.loads((ROOT / "models/metadata.json").read_text())
    values = dict(metadata["reference"], Study_Hours_per_Week=0.0)
    compared = input_comparison(values, metadata)
    assert len(compared) == 6
    assert set(compared["Series"]) == {"Your input", "Training reference"}
    assert set(compared["Input"]) == {
        "Study hours (hours/week)", "Attendance (%)", "Past exam score (%)"
    }
    assert compared.loc[compared["Series"] == "Your input", "Value"].iloc[0] == 0
    chart = sensitivity_chart((
        {"feature": "Attendance_Rate", "difference": -2.0},
        {"feature": "Past_Exam_Scores", "difference": 0.0},
        {"feature": "Study_Hours_per_Week", "difference": 1.5},
    ))
    spec = chart.to_dict()
    rows = next(iter(spec["datasets"].values()))
    assert [row["Score difference"] for row in rows] == [-2.0, 0.0, 1.5]
    assert spec["layer"][0]["encoding"]["x"]["scale"]["domain"] == pytest.approx([-2, 2])
