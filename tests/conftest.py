import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set fake API keys for all tests — no real API calls in unit tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-openai-key")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-fake-tavily-key")
