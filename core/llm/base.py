import os
from typing import Protocol

from core.parsing import parse_fields


class LLMClient(Protocol):
    def extract_fields(self, text, pending): ...
    def phrase_question(self, question): ...
    def soften_reply(self, reply): ...


class MockLLM:
    def extract_fields(self, text, pending):
        return parse_fields(text, pending)[0]

    def phrase_question(self, question):
        return question

    def soften_reply(self, reply):
        return reply


def get_client():
    provider = os.getenv("LLM_PROVIDER", "none").lower()
    if provider in {"none", "rules", "mock"}:
        return MockLLM()
    if provider == "openai":
        from core.llm.provider_openai import OpenAIClient

        return OpenAIClient()
    raise ValueError("LLM_PROVIDER must be none, rules, mock or openai.")
