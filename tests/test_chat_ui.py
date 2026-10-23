from streamlit.testing.v1 import AppTest

from core.conversation import State


def test_rules_chat_and_clear(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "rules")
    app = AppTest.from_file("app/main.py", default_timeout=30).run()
    app.checkbox[0].check().run()
    next(b for b in app.button if b.label == "Begin self-check").click().run()
    for answer in ["22", "around 78 percent", "64/100", "yes", "no"]:
        app.chat_input[0].set_value(answer).run()
        assert not app.exception
    assert app.session_state["self_check"].state == State.CONFIRMING
    assert app.session_state["self_check"].result is None
    app.checkbox[0].check()
    next(b for b in app.button if b.label == "Confirm and see estimate").click().run()
    assert not app.exception
    assert app.session_state["self_check"].state == State.DONE
    next(b for b in app.button if b.label == "Clear answers and start again").click().run()
    assert not app.exception
    assert app.session_state["self_check"].state == State.CONSENT
    assert not app.session_state["self_check"].values
