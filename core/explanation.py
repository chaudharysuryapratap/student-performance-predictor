"""Replies are assembled by code. Generated text cannot modify the result."""

import re
from decimal import Decimal

from core.risk_bands import MEANINGS

DISCLAIMER = "This is an estimate from limited, self-reported data, not a prediction of your result. A mentor or faculty member is the right person to talk to."


def numbers(text):
    return {Decimal(value) for value in re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?", text)}


def reply(result, confirmed):
    lines = [
        f"Model score: {result.score:.2f}.",
        f"Risk band: {result.band}.",
        f"Demo score interval: {result.interval_low:.2f} to {result.interval_high:.2f}. Passing mark: {result.passing_score:.2f}.",
        MEANINGS[result.band],
        "This interval-based demo band is not a calibrated failure probability. College-level validity is unverified, so the result remains uncertain. Evidence for the Low band is limited.",
    ]
    if result.drivers:
        lines.append("Model sensitivity (not causes or guaranteed improvements):")
        for driver in result.drivers:
            name = driver["feature"].replace("_", " ")
            lines.append(
                f"- {name}: {driver['difference']:+.2f} score difference versus the training reference."
            )
    else:
        lines.append("Individual drivers are unavailable.")
    lines.append(DISCLAIMER)
    return "\n\n".join(lines)


def safe_softening(candidate, result, confirmed):
    """Optional gate: require original reply intact plus no added numbers or guarantees."""
    baseline = reply(result, confirmed)
    allowed = numbers(baseline) | {
        Decimal(str(v)) for v in confirmed.values() if isinstance(v, (int, float))
    }
    if baseline not in candidate or not numbers(candidate) <= allowed:
        return baseline
    if re.search(
        r"will (?:pass|fail)|guarantee|definitely|historical|similar profile|%", candidate, re.I
    ):
        return baseline
    return candidate
