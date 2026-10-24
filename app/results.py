"""Visual explanations of a confirmed, frozen-model result. No new inference."""

import json

import altair as alt
import pandas as pd
import streamlit as st

from core.explanation import DISCLAIMER
from core.risk_bands import MEANINGS, load_policy
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


def score_interval_chart(result):
    data = pd.DataFrame({"Score": [result.score], "Lower": [result.interval_low],
                         "Upper": [result.interval_high], "Passing mark": [result.passing_score],
                         "Profile": ["Confirmed estimate"]})
    base = alt.Chart(data).encode(y=alt.Y("Profile:N", axis=None, title=None))
    scale = alt.Scale(domain=[0, 100])
    interval = base.mark_rule(color="#475569", strokeWidth=5).encode(
        x=alt.X("Lower:Q", scale=scale, title="Exam score / 100"), x2="Upper:Q",
        tooltip=[alt.Tooltip("Lower:Q", format=".2f"), alt.Tooltip("Upper:Q", format=".2f")])
    dot = base.mark_point(size=160, filled=True, opacity=1,
                          color={"High": "#dc2626", "Medium": "#d97706", "Low": "#0f766e"}[result.band]).encode(
        x=alt.X("Score:Q", scale=scale, title="Exam score / 100"),
        tooltip=[alt.Tooltip("Score:Q", format=".2f")])
    passing = base.mark_tick(orient="vertical", size=65, thickness=2, color="#334155").encode(
        x=alt.X("Passing mark:Q", scale=scale, title="Exam score / 100"), tooltip=["Passing mark:Q"])
    return (interval + dot + passing).properties(height=110)


def render_results(result, values, message):
    metadata = json.loads((ROOT / "models/metadata.json").read_text())
    scores = source_scores()
    st.subheader("Your performance dashboard")
    score_col, calibration_col = st.columns(2)
    score_col.metric("Estimated exam score", f"{result.score:.2f} / 100")
    calibration_col.metric("Risk band", result.band)
    st.caption("Interval-based demo band · Passing mark: 60 / 100")
    st.write(MEANINGS[result.band])
    st.warning("Demonstration only. The Low band has just two test records; no band guarantees an outcome.")
    st.info(DISCLAIMER)
    overview, sensitivity, inputs = st.tabs([
        "Score overview", "Model sensitivity", "Your inputs"
    ])
    with overview:
        st.markdown("#### Your estimate on the score scale")
        point = pd.DataFrame({"Score": [result.score]})
        policy = load_policy(result.model_version)
        interval_spec = score_interval_chart(result).to_dict()
        interval_rows = next(iter(interval_spec.pop("datasets").values()))
        interval_spec.pop("data", None)
        # Inline each tiny layer to avoid Streamlit 1.45's named-dataset update failure.
        for layer in interval_spec["layer"]:
            layer["data"] = {"values": interval_rows}
        st.vega_lite_chart(spec=interval_spec, use_container_width=True, key="demo_interval_chart")
        st.write(f"**Demo score interval: {result.interval_low:.2f}–{result.interval_high:.2f} / 100**")
        st.caption(
            "Coloured dot: estimate (red High, amber Medium, teal Low). Dark segment: score interval. Vertical line: passing mark. "
            "High: interval entirely below the mark; Medium: crosses the mark; Low: entirely at or above it. "
            "Band boundaries use unrounded values; displayed values are rounded."
        )
        with st.expander("How these demo bands were evaluated"):
            st.write(
                f"The existing interval used {policy['calibration_records']} separate calibration records "
                f"with nominal coverage {policy['nominal_coverage']:.0%}. It covered "
                f"{policy['test_interval_covered']} of {policy['test_records']} held-out recorded scores. "
                "This is population-level interval evidence, not your individual chance of passing."
            )
            st.dataframe(pd.DataFrame([
                {"Demo band": band, "Test records": row["records"],
                 "Recorded scores below pass mark": row["below_pass_mark"]}
                for band, row in policy["test_bands"].items()
            ]), hide_index=True, use_container_width=True)
            st.caption("These test records have already been inspected. A fresh college dataset is needed for external validation.")
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
