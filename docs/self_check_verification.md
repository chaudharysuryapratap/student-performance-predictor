# Self-check verification and deviations

Built around the original `artifacts/model.joblib` without invoking training or writing any protected model/data/training file. The SHA lock and complete protected-file manifest verify byte equality. No supplied pretrained artifact was re-exported, converted or re-saved.

Core: consent-gated state machine, field-spec-driven offline form/chat, required-input validation, review/correction before scoring, deterministic inference, documented sensitivity fallback and exact-template result wording. No transcripts are retained by the application. Optional numeric logging is off by default and disclosed on consent when enabled.

Optional OpenAI extraction uses strict JSON-schema output. Local validation and independent parser evidence prevent provider responses from supplying or changing unreported inputs. Errors fall back locally. Unknown free-form language can require a simpler answer; the provider is not trusted to infer unsupported patterns. Optional question/softening interfaces currently return canonical templates. No generated final reply is used. Live API testing is opt-in and skipped without credentials.

Intentional deviations from the pasted template:
- Artifact inspection found a public-data exam-score regressor, not a college-data risk classifier. No validated calibration or thresholds exist, so Low/Medium/High bands remain disabled and the band is `Not established`. No historical percentages are shown. `uncertain` is true because risk interpretation is unvalidated.
- Config files use JSON syntax, a valid subset of YAML, avoiding an extra dependency. Feature names/order must remain compatible with the frozen pipeline.
- The legacy demonstration app is preserved at app.py; the requested UI is app/main.py on localhost port 8502. Logging and distress handling apply to the self-check; the older demo is not a student chat service.
- No real student records were added. Self-check tests use synthetic inputs; legacy dataset tests still inspect the pre-existing public files. These original assets remain untracked and unmodified, and are not published.
- Local commits contain only the self-check implementation and documentation. The repository was initially uncommitted; pre-existing training code/data/artifacts are left out of these stage commits. A fresh clone therefore needs the exact original locked artifact/report and protected files provisioned separately. CI does not retrain to replace them.

Verification includes hash checks, all-field validation, fraction errors, unknown fields, parser golden examples, PII minimization, prompt injection/guarantee refusals, distress stop, numeric-only opt-in logging, mocked provider requests, network-failure fallback, score determinism, number matching, locked-model refusal, invalid-correction re-ask and offline form/chat UI flows. Live browser synthetic flow also reached the final result. No public deployment, clinical efficacy or real-student accuracy is claimed.

Open questions and limits are documented in OPEN_QUESTIONS.md. Distress and PII detection remain heuristic; a real deployment needs review in its actual language, population and hosting environment.

Final local result: 77 tests passed, 1 live-provider test skipped without explicit credentials/opt-in. Ruff passed. One existing Streamlit/Altair deprecation warning remains in the legacy app test. SHA checks passed for the model and all protected files. The localhost chat flow was verified in a browser with synthetic inputs; screenshot is docs/screenshots/self-check.png.
