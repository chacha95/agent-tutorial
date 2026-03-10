"""
models.py — PydanticAI Concept 1: Structured Output

PydanticAI requires all agent outputs to be typed Pydantic models.
The LLM returns JSON; PydanticAI validates it against these schemas.
If the LLM returns invalid output, PydanticAI retries automatically.
"""
from pydantic import BaseModel, Field


class TrendData(BaseModel):
    """Research Agent의 출력 모델.

    YouTube Shorts 트렌드 분석 결과를 담습니다.
    """
    keyword: str                    # 입력 키워드
    competing_titles: list[str]     # 경쟁 영상 제목 (최대 5개)
    avg_views: int                  # 평균 조회수 추정치
    best_hook_patterns: list[str]   # 효과적인 훅 패턴


class ShortsScript(BaseModel):
    """Writer Agent의 출력 모델.

    60초 YouTube Shorts 스크립트 구성 요소.
    """
    hook: str                       # 첫 3초 훅 문장
    body: str                       # 본문 (40-50초)
    cta: str                        # 마지막 행동 유도 (Call To Action)
    duration_sec: int               # 예상 길이 (목표: 55-60초)


class ContentPackage(BaseModel):
    """Editor Agent의 최종 출력 모델.

    업로드 준비가 완료된 전체 콘텐츠 패키지.
    ShortsScript를 중첩 모델로 포함합니다.
    """
    title: str                      # 영상 제목
    script: ShortsScript            # 완성된 스크립트 (중첩 Pydantic 모델)
    thumbnail_copy: str             # 썸네일 문구 (짧고 임팩트 있게)
    hashtags: list[str]             # 해시태그 (최대 10개, #포함)
    upload_time: str                # 권장 업로드 시간 (예: "오후 7시")
    quality_score: int = Field(ge=1, le=10)  # 품질 점수 1-10 (범위 강제)
