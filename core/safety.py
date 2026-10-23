"""Local, conservative guards; no raw text is persisted or sent off-device."""

import os
import re

from core.validation import band_config, feature_spec

DISTRESS = re.compile(
    r"\b(suicid\w*|self[- ]?harm|kill myself|hurt myself|end my life|want to die|hopeless|overwhelmed|panic\w*|distressed|can't cope|cannot cope)\b",
    re.I,
)
INJECTION = re.compile(
    r"ignore (?:your|all|previous|the)|system prompt|override|set (?:my |the )?(?:score|risk)|say i (?:will |shall )?pass|pretend|jailbreak|\b(output|respond|print|developer message|act as)\b",
    re.I,
)
GUARANTEE = re.compile(r"will i (?:pass|fail)|guarantee|promise.*pass|definitely.*pass", re.I)


def support_message():
    return os.getenv("SUPPORT_MESSAGE") or band_config()["support_message"]


def strip_pii(text):
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", " ", text)
    text = re.sub(r"(?<!\w)(?:\+?\d[\d ()-]{8,}\d)(?!\w)", " ", text)
    text = re.sub(
        r"\b(?:my name is|name\s*[:=]|i am called|call me)\s+[a-z]+(?:\s+[a-z]+){0,2}",
        " ",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\b(?:roll(?: number| no)?|student ?id|student number|id)(?:\s+is)?\s*[:=#-]?\s*[a-z0-9-]+",
        " ",
        text,
        flags=re.I,
    )
    return text[:2000]


def minimal_text(text):
    """Allowlist, not claimed general-purpose PII recognition. Unknown words never leave."""
    words = {
        "yes",
        "no",
        "not",
        "have",
        "has",
        "none",
        "percent",
        "percentage",
        "out",
        "of",
        "by",
        "per",
        "week",
        "weekly",
        "hours",
        "hour",
        "around",
        "about",
        "previous",
        "exam",
        "score",
        "marks",
        "attendance",
        "attended",
        "study",
        "internet",
        "wifi",
        "wi-fi",
        "extracurricular",
        "activities",
        "sports",
        "clubs",
    }
    for field in feature_spec()["features"]:
        for alias in field["aliases"]:
            words.update(alias.lower().split())
    return " ".join(
        token
        for token in re.findall(r"[a-zA-Z0-9-]+(?:\.\d+)?|[%/]", strip_pii(text).lower())
        if token in words or re.fullmatch(r"-?\d+(?:\.\d+)?|[%/]", token)
    )


def guard(text):
    if DISTRESS.search(text):
        return "distress", support_message()
    if INJECTION.search(text):
        return (
            "refusal",
            "I can use only your confirmed model inputs. Instructions to change a score cannot affect it.",
        )
    if GUARANTEE.search(text):
        return (
            "refusal",
            "I cannot guarantee an academic outcome. A mentor or faculty member can help you interpret your situation.",
        )
    return None, None
