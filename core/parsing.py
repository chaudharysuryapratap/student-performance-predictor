"""Rule parser for only the existing model's fields. Unknown features stay unknown."""

import re

from core.safety import guard, strip_pii
from core.validation import feature_spec

NUMBER = r"-?\d+(?:\.\d+)?"


def numeric_value(text, percentage):
    ratio = re.search(rf"({NUMBER})\s*(?:/|by|out of)\s*({NUMBER})", text, re.I)
    if ratio:
        obtained, maximum = map(float, ratio.groups())
        if maximum <= 0 or obtained < 0 or obtained > maximum:
            raise ValueError(
                "Marks or attendance obtained must be between zero and the maximum, and the maximum must be positive."
            )
        if not percentage:
            raise ValueError("Please enter study hours per week as a number, not a fraction.")
        return obtained / maximum * 100
    matches = re.findall(NUMBER, text)
    if len(matches) != 1:
        return None
    return float(matches[0])


def parse_fields(text, pending=None):
    if guard(text)[0]:
        return {}, {}
    text = strip_pii(text).lower()
    output, errors = {}, {}
    # A labelled field consumes only the segment up to the next labelled field.
    hits = []
    for field in feature_spec()["features"]:
        aliases = [field["name"].lower()] + field["aliases"]
        matches = [
            m for alias in aliases for m in re.finditer(r"\b" + re.escape(alias) + r"\b", text)
        ]
        if matches:
            m = min(matches, key=lambda m: m.start())
            hits.append((m.start(), field))
    hits.sort(key=lambda item: item[0])
    segments = [
        (field, text[0 if i == 0 else start : hits[i + 1][0] if i + 1 < len(hits) else len(text)])
        for i, (start, field) in enumerate(hits)
    ]
    if not hits and pending and not re.search(r"\b(backlogs?|name|roll|id)\b", text):
        field = next((f for f in feature_spec()["features"] if f["name"] == pending), None)
        if field:
            segments = [(field, text)]
    for field, segment in segments:
        try:
            if field["type"] == "number":
                value = numeric_value(segment, field["unit"] == "percent")
            else:
                if re.search(r"\b(idk|unknown|not sure|don.t know|do not know)\b", segment):
                    continue
                negative = bool(re.search(r"\b(no|not|none|without|don.t|doesn.t)\b", segment))
                if any(
                    re.search(
                        r"\b(?:no|without|not|don't have|do not have)\s+(?:any\s+)?"
                        + re.escape(alias)
                        + r"\b",
                        text,
                    )
                    for alias in field["aliases"]
                ):
                    negative = True
                positive = bool(re.search(r"\b(yes|have|has)\b", segment))
                value = "No" if negative else "Yes" if positive else None
            if value is not None:
                output[field["name"]] = value
        except ValueError as error:
            errors[field["name"]] = str(error)
    return output, errors
