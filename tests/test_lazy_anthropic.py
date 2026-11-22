"""Building fictional products does not import anthropic (1.4 s a process)."""

import subprocess
import sys


def test_fictional_does_not_import_anthropic():
    code = "import sys, agentic_usd_gen.fictional, agentic_usd_gen.cli; print('anthropic' in sys.modules)"
    assert subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout.strip() == "False"


def test_api_errors_become_llm_error(monkeypatch):
    import anthropic
    import pytest

    from agentic_usd_gen import llm

    class Down(anthropic.APIError):  # stands for APIConnectionError, RateLimitError, ...
        def __init__(self):
            Exception.__init__(self, "connection refused")

    class Failing:
        def __init__(self, *a, **k):
            raise Down()

    monkeypatch.setattr(anthropic, "Anthropic", lambda: type("C", (), {"beta": type("B", (), {
        "messages": type("M", (), {"stream": Failing})()})()})())
    with pytest.raises(llm.LLMError, match="Claude API"):
        llm.request_json(model="m", system="s", content="c", schema={"type": "object"})
