"""Explicit state machine. Only confirmed validated features reach the scorer."""

from dataclasses import dataclass, field
from enum import StrEnum

from core.explanation import reply
from core.llm.base import get_client
from core.parsing import parse_fields
from core.safety import guard, minimal_text
from core.scoring_service import score
from core.validation import feature_spec, validate


class State(StrEnum):
    CONSENT = "CONSENT"
    COLLECTING = "COLLECTING"
    CONFIRMING = "CONFIRMING"
    SCORING = "SCORING"
    EXPLAINING = "EXPLAINING"
    DONE = "DONE"


@dataclass
class Conversation:
    state: State = State.CONSENT
    values: dict = field(default_factory=dict)
    result: object = None
    message: str = ""
    stopped: bool = False
    history: list = field(default_factory=lambda: [State.CONSENT])

    def transition(self, state):
        self.state = state
        self.history.append(state)

    def consent(self):
        if self.state == State.CONSENT:
            self.transition(State.COLLECTING)

    def pending(self):
        return next((f for f in feature_spec()["features"] if f["name"] not in self.values), None)

    def submit(self, text, client=None):
        if self.state not in {State.COLLECTING, State.CONFIRMING} or self.stopped:
            return
        kind, message = guard(text)
        if kind:
            self.message = message
            if kind == "distress":
                self.values.clear()
                self.result = None
                self.stopped = True
                self.transition(State.DONE)
            return
        pending = self.pending()
        name = pending["name"] if pending else None
        parsed, errors = parse_fields(text, name)
        # Only minimal academic tokens ever reach an optional provider. Provider
        # suggestions need independent local evidence and cannot overwrite a score.
        try:
            proposed = (client or get_client()).extract_fields(minimal_text(text), name)
            if isinstance(proposed, dict):
                for key, value in proposed.items():
                    if key in parsed and value == parsed[key]:
                        parsed[key] = value
        except Exception:
            pass  # No exception body is logged: it may contain provider input.
        clean, invalid = validate(parsed)
        errors.update(invalid)
        for key in errors:
            self.values.pop(key, None)
        self.values.update(clean)
        self.message = (
            " ".join(errors.values())
            if errors
            else (
                "Values received. Please check them below."
                if clean
                else "I could not identify a value. Please answer the current question, or use the form."
            )
        )
        self.transition(State.CONFIRMING if self.pending() is None else State.COLLECTING)

    def set_form(self, fields):
        if self.state == State.CONSENT or self.stopped:
            raise ValueError("Consent is required before entering values.")
        clean, errors = validate(fields, complete=True)
        if errors:
            self.message = " ".join(errors.values())
            return False
        self.values = clean
        self.result = None
        self.transition(State.CONFIRMING)
        return True

    def confirm(self):
        if self.state != State.CONFIRMING or self.stopped:
            raise ValueError("Review and confirm every required input before scoring.")
        self.transition(State.SCORING)
        try:
            result = score(self.values)
        except Exception:
            self.transition(State.CONFIRMING)
            self.message = (
                "Scoring is unavailable. Check the locked model and feature configuration."
            )
            return
        self.result = result
        self.transition(State.EXPLAINING)
        self.message = reply(result, self.values)
        self.transition(State.DONE)
