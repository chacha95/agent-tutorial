import pytest
from pydantic import ValidationError

from src.models import ContentPackage, ShortsScript, TrendData


class TestTrendData:
    def test_valid_creation(self):
        data = TrendData(
            keyword="다이어트",
            competing_titles=["살 빼는 법 TOP5", "운동 없이 10kg 감량"],
            avg_views=150000,
            best_hook_patterns=["충격적인 사실", "이것만 알면"],
        )
        assert data.keyword == "다이어트"
        assert len(data.competing_titles) == 2

    def test_missing_keyword_raises(self):
        with pytest.raises(ValidationError):
            TrendData(
                competing_titles=[],
                avg_views=0,
                best_hook_patterns=[],
            )

    def test_avg_views_wrong_type_raises(self):
        with pytest.raises(ValidationError):
            TrendData(
                keyword="테스트",
                competing_titles=[],
                avg_views="not-a-number",
                best_hook_patterns=[],
            )


class TestShortsScript:
    def test_valid_creation(self):
        script = ShortsScript(
            hook="지금 당장 이것을 멈추세요!",
            body="많은 분들이 모르는 사실인데요...",
            cta="좋아요와 구독 부탁드립니다!",
            duration_sec=58,
        )
        assert script.duration_sec == 58

    def test_missing_cta_raises(self):
        with pytest.raises(ValidationError):
            ShortsScript(hook="훅", body="본문", duration_sec=55)


class TestContentPackage:
    def test_nested_script_model(self):
        """ContentPackage embeds ShortsScript — demonstrates nested Pydantic models."""
        script = ShortsScript(hook="훅", body="본문", cta="구독!", duration_sec=57)
        package = ContentPackage(
            title="다이어트 비법 공개!",
            script=script,
            thumbnail_copy="살 -10kg",
            hashtags=["#다이어트", "#건강"],
            upload_time="오후 7시",
            quality_score=8,
        )
        assert package.script.hook == "훅"
        assert package.quality_score == 8

    def test_quality_score_below_range_raises(self):
        script = ShortsScript(hook="h", body="b", cta="c", duration_sec=55)
        with pytest.raises(ValidationError):
            ContentPackage(
                title="제목",
                script=script,
                thumbnail_copy="썸네일",
                hashtags=[],
                upload_time="오후 7시",
                quality_score=0,  # below ge=1
            )

    def test_quality_score_above_range_raises(self):
        script = ShortsScript(hook="h", body="b", cta="c", duration_sec=55)
        with pytest.raises(ValidationError):
            ContentPackage(
                title="제목",
                script=script,
                thumbnail_copy="썸네일",
                hashtags=[],
                upload_time="오후 7시",
                quality_score=11,  # above le=10
            )

    def test_quality_score_wrong_type_raises(self):
        script = ShortsScript(hook="h", body="b", cta="c", duration_sec=55)
        with pytest.raises(ValidationError):
            ContentPackage(
                title="제목",
                script=script,
                thumbnail_copy="썸네일",
                hashtags=[],
                upload_time="오후 7시",
                quality_score="high",
            )
