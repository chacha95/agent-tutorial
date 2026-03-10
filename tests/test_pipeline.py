"""
Pipeline tests mock each agent's .run() method to avoid real LLM calls.
Tests verify that agents are called in the right order with the right data shapes.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.deps import AppDeps
from src.models import ContentPackage, ShortsScript, TrendData


@pytest.fixture
def test_deps():
    return AppDeps(openai_api_key="sk-test", tavily_api_key="tvly-test")


@pytest.fixture
def sample_trend_data():
    return TrendData(
        keyword="다이어트",
        competing_titles=["살 빼는 법", "10kg 감량 비법"],
        avg_views=200000,
        best_hook_patterns=["충격적인 사실", "이것만 알면"],
    )


@pytest.fixture
def sample_script():
    return ShortsScript(
        hook="지금 당장 이것을 멈추세요!",
        body="많은 분들이 모르는 다이어트 비법...",
        cta="좋아요와 구독 부탁드립니다!",
        duration_sec=58,
    )


@pytest.fixture
def sample_package(sample_script):
    return ContentPackage(
        title="다이어트 비법 공개!",
        script=sample_script,
        thumbnail_copy="살 -10kg",
        hashtags=["#다이어트", "#건강"],
        upload_time="오후 7시",
        quality_score=8,
    )


def make_mocked_agents(trend_data, script, package):
    """Return three patched agent mocks with pre-set return values."""
    mock_trend_result = MagicMock()
    mock_trend_result.data = trend_data

    mock_script_result = MagicMock()
    mock_script_result.data = script

    mock_package_result = MagicMock()
    mock_package_result.data = package

    return mock_trend_result, mock_script_result, mock_package_result


class TestRunPipeline:
    async def test_returns_content_package(
        self, test_deps, sample_trend_data, sample_script, sample_package
    ):
        """Pipeline should return a ContentPackage when all agents succeed."""
        from src.pipeline import run_pipeline

        t, s, p = make_mocked_agents(sample_trend_data, sample_script, sample_package)

        with (
            patch("src.pipeline.research_agent") as mock_research,
            patch("src.pipeline.writer_agent") as mock_writer,
            patch("src.pipeline.editor_agent") as mock_editor,
        ):
            mock_research.run = AsyncMock(return_value=t)
            mock_writer.run = AsyncMock(return_value=s)
            mock_editor.run = AsyncMock(return_value=p)

            result = await run_pipeline("다이어트", test_deps)

        assert isinstance(result, ContentPackage)
        assert result.quality_score == 8
        assert result.title == "다이어트 비법 공개!"

    async def test_writer_receives_valid_json(
        self, test_deps, sample_trend_data, sample_script, sample_package
    ):
        """Writer agent must receive TrendData serialized as valid JSON, not a Python object."""
        from src.pipeline import run_pipeline

        t, s, p = make_mocked_agents(sample_trend_data, sample_script, sample_package)

        with (
            patch("src.pipeline.research_agent") as mock_research,
            patch("src.pipeline.writer_agent") as mock_writer,
            patch("src.pipeline.editor_agent") as mock_editor,
        ):
            mock_research.run = AsyncMock(return_value=t)
            mock_writer.run = AsyncMock(return_value=s)
            mock_editor.run = AsyncMock(return_value=p)

            await run_pipeline("다이어트", test_deps)

            # The first positional arg to writer_agent.run must be valid JSON
            writer_message = mock_writer.run.call_args[0][0]
            parsed = json.loads(writer_message)  # would raise if not valid JSON
            assert parsed["keyword"] == "다이어트"

    async def test_editor_receives_both_as_valid_json(
        self, test_deps, sample_trend_data, sample_script, sample_package
    ):
        """Editor must receive both TrendData and ShortsScript, each as valid JSON."""
        from src.pipeline import run_pipeline

        t, s, p = make_mocked_agents(sample_trend_data, sample_script, sample_package)

        with (
            patch("src.pipeline.research_agent") as mock_research,
            patch("src.pipeline.writer_agent") as mock_writer,
            patch("src.pipeline.editor_agent") as mock_editor,
        ):
            mock_research.run = AsyncMock(return_value=t)
            mock_writer.run = AsyncMock(return_value=s)
            mock_editor.run = AsyncMock(return_value=p)

            await run_pipeline("다이어트", test_deps)

            editor_message = mock_editor.run.call_args[0][0]

            # Both sections must be present
            assert "트렌드 데이터" in editor_message
            assert "스크립트" in editor_message

            # Extract and validate the embedded JSON blocks
            import re
            json_blocks = re.findall(r'\{.*?\}', editor_message, re.DOTALL)
            assert len(json_blocks) >= 2, "Editor message must contain at least two JSON blocks"
            for block in json_blocks:
                json.loads(block)  # each block must be valid JSON

    async def test_agents_called_in_order(
        self, test_deps, sample_trend_data, sample_script, sample_package
    ):
        """Research must complete before Writer, Writer before Editor."""
        from src.pipeline import run_pipeline

        call_order = []
        t, s, p = make_mocked_agents(sample_trend_data, sample_script, sample_package)

        async def research_side_effect(*args, **kwargs):
            call_order.append("research")
            return t

        async def writer_side_effect(*args, **kwargs):
            call_order.append("writer")
            return s

        async def editor_side_effect(*args, **kwargs):
            call_order.append("editor")
            return p

        with (
            patch("src.pipeline.research_agent") as mock_research,
            patch("src.pipeline.writer_agent") as mock_writer,
            patch("src.pipeline.editor_agent") as mock_editor,
        ):
            mock_research.run = research_side_effect
            mock_writer.run = writer_side_effect
            mock_editor.run = editor_side_effect

            await run_pipeline("다이어트", test_deps)

        assert call_order == ["research", "writer", "editor"]
