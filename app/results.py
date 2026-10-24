"""Visual explanations of a confirmed, frozen-model result. No new inference."""

import json

import altair as alt
import pandas as pd
import streamlit as st

from core.explanation import DISCLAIMER
from core.validation import ROOT, feature_spec

LABELS = {
    "Study_Hours_per_Week": "Study hours (hours/week)",
    "Attendance_Rate": "Attendance (%)",
    "Past_Exam_Scores": "Past exam score (%)",
    "Internet_Access_at_Home": "Internet at home",
    "Extracurricular_Activities": "Extracurricular activities",
}
ACCENT = "#4f46e5"


@st.cache_data(show_spinner=False)
def source_scores(path=ROOT / "research/dataset/student_performance_dataset.csv"):
    """Read only the public source target; never cache session answers or identities."""
    try:
        frame = pd.read_csv(path, usecols=["Final_Exam_Score"])
        frame["Final_Exam_Score"] = pd.to_numeric(frame["Final_Exam_Score"], errors="raise")
        if frame.empty or not frame["Final_Exam_Score"].between(0, 100).all():
            raise ValueError("Invalid source score range")
        return frame
    except (OSError, ValueError):
        return pd.DataFrame(columns=["Final_Exam_Score"])


def input_comparison(values, metadata):
    rows = []
    for field in feature_spec()["features"]:
        name = field["name"]
        if field["type"] == "number":
            for series, value in (
                ("Your input", values[name]),
                ("Training reference", metadata["reference"][name]),
            ):
                rows.append({"Input": LABELS[name], "Series": series, "Value": float(value)})
    return pd.DataFrame(rows)


def sensitivity_chart(drivers):
    data = pd.DataFrame([
        {"Input": LABELS[item["feature"]], "Score difference": item["difference"]}
        for item in drivers
    ])
    extent = max(1.0, float(data["Score difference"].abs().max()))
    bars = alt.Chart(data).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X("Score difference:Q", scale=alt.Scale(domain=[-extent, extent]),
                title="Difference in model score (points)"),
        y=alt.Y("Input:N", sort=None, title=None, axis=alt.Axis(labelLimit=230)),
        color=alt.condition(alt.datum["Score difference"] >= 0,
                            alt.value(ACCENT), alt.value("#64748b")),
        tooltip=["Input:N", alt.Tooltip("Score difference:Q", format="+.2f")],
    )
    zero = alt.Chart(pd.DataFrame({"zero": [0]})).mark_rule(color="#94a3b8").encode(x="zero:Q")
    return (bars + zero).properties(height=190)


def render_results(result, values, message):
    metadata = json.loads((ROOT / "models/metadata.json").read_text())
    scores = source_scores()
    st.subheader("Your performance dashboard")
    score_col, calibration_col = st.columns(2)
    score_col.metric("Estimated exam score", f"{result.score:.2f} / 100")
    calibration_col.metric("Risk band", result.band)
    st.info(DISCLAIMER)
    overview, sensitivity, inputs = st.tabs([
        "Score overview", "Model sensitivity", "Your inputs"
    ])
    with overview:
        st.markdown("#### Your estimate on the score scale")
        point = pd.DataFrame({"Score": [result.score], "Row": ["Model estimate"]})
        base = alt.Chart(point).encode(
            x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 100]), title="Exam score / 100"),
            y=alt.Y("Row:N", title=None, axis=None),
            tooltip=[alt.Tooltip("Score:Q", format=".2f")],
        )
        st.altair_chart(
            (base.mark_bar(size=16, color="#e0e7ff") +
             base.mark_point(size=170, filled=True, color=ACCENT)).properties(height=85),
            use_container_width=True,
        )
        st.caption("This score is not a pass probability. No validated risk thresholds are applied.")
        st.markdown("#### Where scores appear in the source dataset")
        if scores.empty:
            st.warning("Source score data is unavailable. The confirmed model estimate is still shown above.")
        else:
            histogram = alt.Chart(scores).mark_bar(color="#c7d2fe", binSpacing=2).encode(
                x=alt.X("Final_Exam_Score:Q", bin=alt.Bin(step=2),
                        scale=alt.Scale(domain=[0, 100]), title="Recorded final exam score / 100"),
                y=alt.Y("count():Q", title="Source records"),
                tooltip=[alt.Tooltip("Final_Exam_Score:Q", bin=alt.Bin(step=2), title="Score bin"),
                         alt.Tooltip("count():Q", title="Records")],
            )
            marker = alt.Chart(point).mark_rule(color=ACCENT, strokeWidth=3).encode(
                x="Score:Q", tooltip=[alt.Tooltip("Score:Q", title="Your estimate", format=".2f")]
            )
            st.altair_chart((histogram + marker).properties(height=260), use_container_width=True)
            low, high = scores["Final_Exam_Score"].agg(["min", "max"])
            st.caption(
                f"{len(scores):,} public demonstration records; recorded scores {low:g}–{high:g}. "
                "The vertical line is your model estimate. This is the full source dataset, "
                "not an independent test set, a confidence interval, or a comparison with your college."
            )
    with sensitivity:
        st.markdown("#### Which inputs changed this estimate most?")
        st.write(
            "For each input below, the model replaces only that input with its training reference "
            "and keeps your other answers fixed. The bar shows your estimate minus that replacement score."
        )
        if result.drivers:
            st.altair_chart(sensitivity_chart(result.drivers), use_container_width=True)
            st.caption(
                "The three largest absolute differences are shown. Right = higher estimate than the "
                "replacement; left = lower. Zero means no change for that replacement. These are "
                "model sensitivities, not causes, global feature importance, or guaranteed gains. "
                "The bars do not add up to your score."
            )
            references = pd.DataFrame([
                {"Input": LABELS[d["feature"]],
                 "Training reference used": str(metadata["reference"][d["feature"]]),
                 "Score difference": round(d["difference"], 2)}
                for d in result.drivers
            ])
            st.dataframe(references, hide_index=True, use_container_width=True)
        else:
            st.caption("Individual sensitivities are unavailable for this result.")
    with inputs:
        st.markdown("#### Your answers and the training reference")
        comparison = input_comparison(values, metadata)
        for label, rows in comparison.groupby("Input", sort=False):
            st.markdown(f"**{label}**")
            chart = alt.Chart(rows).mark_bar(cornerRadiusEnd=3).encode(
                x=alt.X("Value:Q", title=None),
                y=alt.Y("Series:N", title=None, sort=["Your input", "Training reference"]),
                color=alt.Color("Series:N", scale=alt.Scale(
                    domain=["Your input", "Training reference"], range=[ACCENT, "#cbd5e1"]),
                    legend=None),
                tooltip=["Input:N", "Series:N", alt.Tooltip("Value:Q", format=".2f")],
            ).properties(height=75)
            st.altair_chart(chart, use_container_width=True)
        st.caption(
            "Each panel uses its own units and scale. The training reference is a model comparison "
            "value, not a target, a recommended study schedule, or an average for your college."
        )
        for name, (low, high) in metadata["ranges"].items():
            if not low <= values[name] <= high:
                st.warning(
                    f"Your {LABELS[name].lower()} ({values[name]:g}) is outside the recorded "
                    f"training range ({low:.2f}–{high:.2f}). Treat this estimate with extra caution."
                )
        st.dataframe(pd.DataFrame([
            {"Input": LABELS[name], "Confirmed answer": str(value)}
            for name, value in values.items()
        ]), hide_index=True, use_container_width=True)
    with st.expander("Text explanation and model details"):
        st.markdown(message)
        st.caption(metadata["source"])
        st.write("Model: frozen Random Forest regressor. No retraining occurs in this dashboard.")
        st.code(result.model_version, language=None)
