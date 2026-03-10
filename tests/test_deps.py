import pytest

from src.deps import AppDeps, load_deps


class TestAppDeps:
    def test_defaults(self):
        deps = AppDeps(openai_api_key="sk-test", tavily_api_key="tvly-test")
        assert deps.target_language == "Korean"
        assert deps.max_duration_sec == 60

    def test_custom_values(self):
        deps = AppDeps(
            openai_api_key="sk-test",
            tavily_api_key="tvly-test",
            target_language="English",
            max_duration_sec=45,
        )
        assert deps.max_duration_sec == 45


class TestLoadDeps:
    def test_reads_env_vars(self):
        """load_deps() reads API keys from environment.
        conftest.py autouse fixture sets these for all tests.
        """
        deps = load_deps()
        assert deps.openai_api_key == "sk-test-fake-openai-key"
        assert deps.tavily_api_key == "tvly-test-fake-tavily-key"

    def test_missing_openai_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            load_deps()

    def test_missing_tavily_key_raises(self, monkeypatch):
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            load_deps()
