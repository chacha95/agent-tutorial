"""
pipeline.py — PydanticAI Concept 5: Agent Chaining

세 에이전트를 순서대로 실행합니다.

⚠️ 핵심 패턴 — 에이전트 간 데이터 전달:

   틀린 방법: writer_agent.run(trend_data)
              → 에러! PydanticAI 에이전트는 Python 객체를 받지 않습니다

   맞는 방법: writer_agent.run(trend_data.model_dump_json())
              → 올바름! JSON 문자열로 직렬화 후 전달

   이유: PydanticAI 에이전트는 LLM과 텍스트로 통신합니다.
         에이전트 간 데이터도 텍스트(JSON)여야 합니다.

⚠️ 임포트 순서:
   src.tools를 임포트해야 research_agent에 도구가 등록됩니다.
"""
import src.tools  # noqa: F401 — tools.py 임포트로 search_youtube_trends 도구 등록

from src.agents import editor_agent, research_agent, writer_agent
from src.deps import AppDeps
from src.models import ContentPackage


async def run_pipeline(keyword: str, deps: AppDeps) -> ContentPackage:
    """YouTube Shorts 콘텐츠 자동화 파이프라인.

    Args:
        keyword: 한국어 검색 키워드 (예: "다이어트", "주식투자")
        deps: API 키와 설정을 담은 의존성 컨테이너

    Returns:
        ContentPackage: 제목, 스크립트, 썸네일, 해시태그, 업로드 시간 포함
    """
    # ── Step 1: Research Agent ──────────────────────────────────────
    print(f"🔍 '{keyword}' 트렌드 분석 중...")
    trend_result = await research_agent.run(keyword, deps=deps)
    trend_data = trend_result.data  # TrendData 인스턴스

    # ── Step 2: Writer Agent ────────────────────────────────────────
    # ⚠️ trend_data.model_dump_json()으로 직렬화 필수
    #    trend_data (Python 객체)를 직접 전달하면 에러 발생
    print("✍️ 스크립트 작성 중...")
    script_result = await writer_agent.run(
        trend_data.model_dump_json(),
        deps=deps,
    )
    shorts_script = script_result.data  # ShortsScript 인스턴스

    # ── Step 3: Editor Agent ────────────────────────────────────────
    # 두 모델 모두 JSON으로 직렬화하여 하나의 메시지에 포함
    print("✏️ 최종 편집 중...")
    editor_message = (
        f"트렌드 데이터:\n{trend_data.model_dump_json()}\n\n"
        f"스크립트:\n{shorts_script.model_dump_json()}"
    )
    package_result = await editor_agent.run(editor_message, deps=deps)

    print("✅ 콘텐츠 패키지 생성 완료!")
    return package_result.data  # ContentPackage 인스턴스
