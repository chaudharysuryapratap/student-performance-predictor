"""Student self-check UI. Business rules and inference live in core/."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from app.results import LABELS, render_results
from core.conversation import Conversation, State
from core.validation import feature_spec

st.set_page_config(page_title="Student Performance Predictor", page_icon="📘", layout="wide")
st.title("Student Performance Predictor")
st.caption(
    "Enter your academic details, review your answers, and explore your model estimate."
)

if "self_check" not in st.session_state:
    st.session_state.self_check = Conversation()
session = st.session_state.self_check
fields = feature_spec()["features"]
provider = os.getenv("LLM_PROVIDER", "none").lower()


def clear_session():
    for key in list(st.session_state):
        if key.startswith(("self_", "entry_", "review_")):
            del st.session_state[key]


if session.state == State.CONSENT:
    st.write(
        "We ask about study hours, attendance, a past exam score, internet access and extracurricular activities. Please leave out your name, roll number and contact details."
    )
    st.info(
        "This is an estimate from limited, self-reported data, not a prediction of your result. A mentor or faculty member is the right person to talk to."
    )
    st.write(
        "Nothing is saved to a student database or transcript by this app. Your validated answers stay in this browser session until you clear them. Demo risk bands use the dataset's passing mark and an interval calibrated on demonstration data. They have not been validated on your college's students."
    )
    if provider == "openai":
        st.warning(
            "Optional OpenAI extraction is enabled. Only filtered academic tokens from your current answer are sent to OpenAI. Provider processing and retention follow your account settings; no transcript or identity fields are sent."
        )
    else:
        st.caption("Offline mode: no answers are sent to an LLM provider.")
    if os.getenv("ENABLE_LOGGING", "false").lower() == "true":
        st.warning(
            "The operator has enabled logging of validated numeric inputs. Free text and identity fields are excluded."
        )
    agree = st.checkbox("I understand and choose to continue.", key="self_consent")
    st.button("Begin self-check", type="primary", disabled=not agree, on_click=session.consent)
    st.stop()

st.button("Clear answers and start again", on_click=clear_session)

if session.stopped:
    st.info(session.message)
    st.stop()

if session.state == State.DONE:
    render_results(session.result, session.values, session.message)
    st.stop()

mode = st.radio(
    "How would you like to answer?",
    ["Form", "Chat"] if provider == "none" else ["Chat", "Form"],
    horizontal=True,
)


def input_form(prefix, values):
    entries = {}
    for field in fields:
        name = field["name"]
        if field["type"] == "number":
            entries[name] = st.number_input(
                LABELS[name],
                help=field["question"],
                min_value=float(field["min"]),
                max_value=float(field["max"]),
                value=values.get(name),
                placeholder="Enter a known value",
                key=f"{prefix}_{name}",
            )
        else:
            options = ["Not answered"] + field["choices"]
            selected = options.index(values[name]) if name in values else 0
            entries[name] = st.selectbox(
                LABELS[name], options, index=selected, key=f"{prefix}_{name}",
                help=field["question"],
            )
            if entries[name] == "Not answered":
                entries[name] = None
    return entries


if session.state == State.COLLECTING and mode == "Form":
    st.subheader("Your academic profile")
    st.caption(
        "Use known values. If you do not know an answer, pause and check your records; it will not be guessed."
    )
    with st.form("self_form"):
        entries = input_form("entry", session.values)
        if st.form_submit_button("Review answers", type="primary"):
            if session.set_form(entries):
                st.rerun()
            st.error(session.message)

if session.state == State.COLLECTING and mode == "Chat":
    pending = session.pending()
    with st.chat_message("assistant"):
        if session.message:
            st.write(session.message)
        st.write(pending["question"])
    if session.values:
        with st.expander("Collected answers"):
            for field in fields:
                if field["name"] in session.values:
                    st.write(
                        f"{field['name'].replace('_', ' ')}: {session.values[field['name']]} {field['unit']}"
                    )

    def on_answer():
        raw = st.session_state.pop("self_answer", "")
        session.submit(raw)

    st.chat_input(
        "Answer this question without personal details",
        key="self_answer",
        on_submit=on_answer,
        max_chars=1000,
    )

if session.state == State.CONFIRMING:
    st.subheader("Check your answers before scoring")
    st.write(
        "Review each value and correct anything below. No score is produced until you confirm."
    )
    for field in fields:
        st.write(
            f"**{field['name'].replace('_', ' ')}:** {session.values[field['name']]} {field['unit']}"
        )
    with st.form("self_review"):
        corrected = input_form("review", session.values)
        verified = st.checkbox("I have checked these values and want to see the model estimate.")
        if st.form_submit_button("Confirm and see estimate", type="primary"):
            if not verified:
                st.error("Please check the confirmation box after reviewing your answers.")
            elif session.set_form(corrected):
                session.confirm()
                st.rerun()
            else:
                st.error(session.message)
