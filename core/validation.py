"""Configuration and validation shared by chat, extraction, form and inference."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def feature_spec():
    # JSON is a YAML subset; these files use that subset to avoid another parser.
    return json.loads((ROOT / "core/feature_spec.yaml").read_text(encoding="utf-8"))


def band_config():
    return json.loads((ROOT / "core/bands.yaml").read_text(encoding="utf-8"))


def validate(fields, complete=False):
    spec = feature_spec()["features"]
    allowed = {s["name"] for s in spec}
    errors, clean = {}, {}
    for name in set(fields) - allowed:
        errors[name] = "This is not a model input."
    for field in spec:
        name = field["name"]
        value = fields.get(name)
        if value is None or value == "":
            if complete and field["required"]:
                errors[name] = "Please provide this value; it will not be guessed."
            continue
        if field["type"] == "number":
            try:
                if isinstance(value, bool):
                    raise ValueError
                value = float(value)
                if not math.isfinite(value) or not field["min"] <= value <= field["max"]:
                    raise ValueError
            except (TypeError, ValueError):
                errors[name] = (
                    f"Use a number from {field['min']} to {field['max']} {field['unit']}."
                )
                continue
        elif not isinstance(value, str) or value.strip().title() not in field["choices"]:
            errors[name] = "Choose Yes or No."
            continue
        else:
            value = value.strip().title()
        clean[name] = value
    return clean, errors


def extraction_schema():
    properties = {}
    for field in feature_spec()["features"]:
        item = (
            {"type": ["number", "null"]}
            if field["type"] == "number"
            else {"type": ["string", "null"], "enum": field["choices"] + [None]}
        )
        properties[field["name"]] = item
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }
