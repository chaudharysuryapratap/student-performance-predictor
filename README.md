# Student self-check around a frozen model

A consent-first Streamlit form and chat around the existing student-performance model. The model, training code and data are read-only. No training, artifact conversion or model export is part of this application.

## Run

Use Python 3.13 and the existing frozen artifact at `artifacts/model.joblib`, its original `artifacts/report.json`, and `models/model.lock`. Install pinned dependencies in a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
$env:LLM_PROVIDER="none"
.venv\Scripts\python -m streamlit run app/main.py --server.address 127.0.0.1 --server.port 8502
```

The default is form-first and entirely offline. Choose Chat in the app or set `LLM_PROVIDER=rules` for chat-first offline mode. `LLM_PROVIDER=mock` uses the same deterministic local extraction for tests. The previous demonstration remains available through `app.py` on its existing port.

Do not rerun `train.py` or `train_datasets.py`: that would invalidate the frozen contract. If artifacts are missing, obtain the exact original files. The self-check refuses a changed model hash. Protected files are checked by the test suite. The legacy CI training step has been removed; the original protected assets need private provisioning before hosted CI can run. No real student datasets or transcripts are added by the self-check work.

## What it collects and returns

Only the existing five inputs: study hours per week, attendance percentage, past exam percentage, internet access and extracurricular activities. All answers are required; unknown answers remain missing. Fractions such as `18/30` or `18 by 30` are converted to percentages, with obtained <= maximum checks. No names, roll numbers or contacts are requested.

Consent -> collecting -> confirming -> scoring -> explaining -> done. The state machine chooses the missing field and requires review before inference. Students can correct answers in the confirmation form. Scoring is deterministic and the LLM cannot supply a score or band.

**This artifact predicts a continuous exam score, not a failure probability. No validated risk-band or historical probability mapping exists.** V1 shows the model score, `Risk band: Not established`, and an uncertainty flag. It does not invent Low/Medium/High thresholds. See `docs/model_contract.md` and `docs/OPEN_QUESTIONS.md`.

Every result includes the limited self-report disclaimer and points students to a mentor or faculty member. Model-sensitivity drivers use changes relative to the existing training reference, not SHAP or causal explanations.

## Configuration

`.env.example` documents process environment variables; the app does not automatically load `.env` files.

| Variable | Default | Purpose |
|---|---|---|
| LLM_PROVIDER | none | none, rules, mock or openai |
| OPENAI_MODEL | unset | Operator-selected model supporting strict JSON-schema output |
| OPENAI_API_KEY | unset | Needed only for optional OpenAI extraction |
| ENABLE_LOGGING | false | If true, log validated numeric inputs only; consent discloses this |
| SUPPORT_MESSAGE | generic local support wording | Institution-reviewed distress response; no fabricated phone numbers |
| RUN_LLM_INTEGRATION | false | Explicit opt-in for the live integration test |

For optional OpenAI extraction, set provider/model/key in the environment before starting Streamlit. The consent screen discloses external processing. The adapter uses strict structured output generated from feature_spec; errors fall back to the rule parser. Only allowlisted academic tokens from the current answer are sent, never raw free text or a transcript. Provider values also need independent local parsing evidence. This deliberately limits extraction to supported patterns; ambiguous language triggers a re-ask. No live API request was required for local tests.

Question phrasing and final replies use templates. The adapter exposes phrasing/softening interfaces but V1 does not use generated result wording. An optional softening guard rejects changed templates, unapproved numbers or guarantees. This keeps result interpretation under code control.

`core/feature_spec.yaml` and `core/bands.yaml` use the JSON subset of YAML, parsed with Python's standard library. Edit questions, aliases and bounds while preserving model feature names, order and types. No unsupported feature may be added. `bands.yaml` has no thresholds: enabling thresholds is rejected until a reviewed calibration contract exists. The YAML file cannot itself establish validity.

## Privacy and safety

No database, transcript file or automatic persistence. Only validated values and safe assistant text stay in Streamlit session state. Clear answers removes the self-check and widgets. The client temporarily holds the currently typed answer as part of normal browser interaction; the app removes submitted raw text from its state and stores no transcript. Application-level logs contain no free text; reverse-proxy or hosting infrastructure must be reviewed separately before deployment.

Local distress detection stops scoring, clears collected answers and shows SUPPORT_MESSAGE. Instruction/guarantee requests cannot set scores. PII stripping plus an outbound academic-token allowlist prevent arbitrary names or identifiers from reaching the extraction provider. These are conservative heuristics, not complete distress or PII recognition. No helpline numbers are invented.

## Verify

```powershell
python -m pytest -q
python -m ruff check .
```

Ruff is a development tool; install the pinned `requirements-dev.txt`. Tests use synthetic self-check examples, mocked provider requests, real read-only inference, UI form/chat flows and SHA checks. Legacy dataset tests still exercise the existing public demonstration files. They do not authorize retraining or copying new student data into the repository.

The optional live test is marked `llm_integration` and skipped without explicit opt-in and credentials. No public deployment, institution validation or live LLM quality claim is made.
