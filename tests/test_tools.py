"""
Tool tests use unittest.mock to avoid real Tavily HTTP calls.
We patch 'src.tools.TavilyClient' before importing the tool.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.deps import AppDeps


@pytest.fixture
def test_deps():
    return AppDeps(openai_api_key="sk-test", tavily_api_key="tvly-test")


class TestSearchYoutubeTrends:
    async def test_tool_returns_formatted_string(self, test_deps):
        """Tool must return a string containing the keyword and search results."""
        import src.tools  # triggers tool registration on research_agent

        fake_results = {
            "results": [
                {
                    "title": "다이어트 성공 비법 TOP5",
                    "content": "전문가가 추천하는 다이어트 방법...",
                    "url": "https://example.com/1",
                },
                {
                    "title": "살 빠지는 운동 루틴",
                    "content": "하루 10분 운동으로 건강하게...",
                    "url": "https://example.com/2",
                },
            ]
        }

        with patch("src.tools.TavilyClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.search.return_value = fake_results
            MockClient.return_value = mock_instance

            from src.tools import search_youtube_trends
            from unittest.mock import MagicMock as MM

            mock_ctx = MM()
            mock_ctx.deps = test_deps

            result = await search_youtube_trends(mock_ctx, "다이어트")

        assert isinstance(result, str)
        assert "다이어트" in result
        assert "다이어트 성공 비법 TOP5" in result

    async def test_tool_uses_tavily_api_key_from_deps(self, test_deps):
        """Tool must read API key from ctx.deps, not from env directly."""
        import src.tools

        with patch("src.tools.TavilyClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.search.return_value = {"results": []}
            MockClient.return_value = mock_instance

            from src.tools import search_youtube_trends
            from unittest.mock import MagicMock as MM

            mock_ctx = MM()
            mock_ctx.deps = test_deps

            await search_youtube_trends(mock_ctx, "테스트")

            # Verify TavilyClient was initialized with the key from deps
            MockClient.assert_called_once_with(api_key="tvly-test")

    async def test_tool_handles_empty_results(self, test_deps):
        """Tool must not crash when Tavily returns zero results."""
        import src.tools

        with patch("src.tools.TavilyClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.search.return_value = {"results": []}
            MockClient.return_value = mock_instance

            from src.tools import search_youtube_trends
            from unittest.mock import MagicMock as MM

            mock_ctx = MM()
            mock_ctx.deps = test_deps

            result = await search_youtube_trends(mock_ctx, "희귀키워드")

        assert isinstance(result, str)
