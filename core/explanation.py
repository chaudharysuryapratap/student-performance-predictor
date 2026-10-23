"""Replies are assembled by code. Generated text cannot modify the result."""

import re
from decimal import Decimal

DISCLAIMER = "This is an estimate from limited, self-reported data, not a prediction of your result. A mentor or faculty member is the right person to talk to."


def numbers(text):
    return {Decimal(value) for value in re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?", text)}


def reply(result, confirmed):
    lines = [
        f"Model score: {result.score:.2f}.",
        f"Risk band: {result.band}.",
        "The model produces an exam-score estimate, not a failure probability. Risk calibration is unavailable, so this self-check is marked uncertain.",
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
