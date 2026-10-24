# Open questions

- No validated Low/Medium/High risk mapping or failure-probability calibration exists. V1 can show the regression score and `Not established` band only. Faculty must define and validate any risk interpretation before enabling it; this task does not authorize retraining.
- The supplied task calls the data past college records; inspection shows public demonstration data with unverified provenance. Institution-specific validity is unknown.
- `Past_Exam_Scores` does not identify a subject, aggregation method or period. Ask students to enter a known past exam percentage and confirm it; do not invent a course mapping.
- Attendance should be verified by the student if not known. Unknown values stop scoring. No feature is inherently impossible to self-report, but self-report accuracy is unverified.
- The broad numeric input limits differ from the narrower training distribution. Out-of-range profiles are flagged uncertain; no individual confidence probability is claimed.
- Live OpenAI integration requires the operator to choose a compatible structured-output model and supply a key in the environment. No provider or model is assumed. Rules chat and form work offline.
- The deployment package includes the frozen primary model and minimal explanation metadata. The complete training-workspace audit is local-only; CI still enforces the mandatory model SHA check.
- Support copy is configurable with SUPPORT_MESSAGE. The default is generic support wording and contains no invented phone numbers. The operator should review it for the institution and local context.
- Distress and PII handling are conservative local heuristics, not complete detection. Raw free text is never sent to the provider; only allowlisted academic tokens are sent after local filtering. Do not deploy with real students until the limitations and consent have been reviewed.
