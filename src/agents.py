"""
agents.py — PydanticAI Concept 3: Multi-Agent Pipeline

세 개의 Agent 인스턴스를 정의합니다.
result_type 파라미터가 핵심입니다:
  - PydanticAI가 LLM 응답을 해당 모델로 자동 파싱합니다
  - 스키마가 맞지 않으면 PydanticAI가 자동으로 재시도합니다
  - 반환값은 항상 타입이 보장된 Python 객체입니다 (dict 아님)
"""
from pydantic_ai import Agent

from src.deps import AppDeps
from src.models import ContentPackage, ShortsScript, TrendData

# ── Agent 1: Research Agent ──────────────────────────────────────────
# 역할: 키워드를 검색하고 TrendData를 반환
# tools.py에서 @research_agent.tool로 Tavily 검색 도구가 등록됩니다
research_agent: Agent[AppDeps, TrendData] = Agent(
    model="gpt-5-nano-2025-08-07",
    deps_type=AppDeps,
    output_type=TrendData,
    system_prompt=(
        "당신은 YouTube Shorts 트렌드 분석 전문가입니다. "
        "주어진 키워드로 웹을 검색하고, 경쟁 영상 제목, 평균 조회수, "
        "효과적인 훅 패턴을 분석하여 정확한 한국어로 반환하세요. "
        "반드시 제공된 검색 도구를 사용하여 실제 데이터를 기반으로 답변하세요."
    ),
)

# ── Agent 2: Writer Agent ────────────────────────────────────────────
# 역할: TrendData를 받아 60초 Shorts 스크립트를 작성
# 도구 없음 — 순수 LLM 창작
writer_agent: Agent[AppDeps, ShortsScript] = Agent(
    model="gpt-5-nano-2025-08-07",
    deps_type=AppDeps,
    output_type=ShortsScript,
    system_prompt=(
        "당신은 바이럴 YouTube Shorts 스크립트 작가입니다. "
        "트렌드 데이터를 분석하여 시청자를 즉시 사로잡는 훅(hook), "
        "핵심 정보를 담은 본문, 강력한 CTA를 포함한 "
        "60초 이내의 한국어 스크립트를 작성하세요. "
        "훅은 반드시 3초 안에 궁금증을 유발해야 합니다."
    ),
)

# ── Agent 3: Editor Agent ────────────────────────────────────────────
# 역할: 스크립트를 검토하고 최종 ContentPackage를 생성
# 도구 없음 — 분석과 평가
editor_agent: Agent[AppDeps, ContentPackage] = Agent(
    model="gpt-5-nano-2025-08-07",
    deps_type=AppDeps,
    output_type=ContentPackage,
    system_prompt=(
        "당신은 YouTube Shorts 콘텐츠 편집장입니다. "
        "제공된 트렌드 데이터와 스크립트를 바탕으로: "
        "1) 클릭률 높은 제목 작성 "
        "2) 임팩트 있는 썸네일 문구 (10자 이내) "
        "3) 관련 해시태그 10개 (#포함) "
        "4) 최적 업로드 시간 추천 (예: 오후 7시) "
        "5) 스크립트 품질을 1-10점으로 평가 (정수만) "
        "모든 출력은 한국어로 작성하세요."
    ),
)
