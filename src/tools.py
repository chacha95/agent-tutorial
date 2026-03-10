"""
tools.py — PydanticAI Concept 4: Tool Use

@research_agent.tool 데코레이터로 Tavily 검색 도구를 등록합니다.

핵심 패턴:
  - 도구는 문자열(str)을 반환합니다
  - LLM이 이 텍스트를 읽고 TrendData 스키마로 구조화합니다
  - 도구가 직접 TrendData를 반환할 필요 없습니다

⚠️ 임포트 순서 주의:
  이 파일은 반드시 agents.py를 임포트한 후에 임포트해야 합니다.
  tools.py가 research_agent에 도구를 등록하기 때문입니다.
  올바른 순서: agents.py → tools.py → pipeline.py
"""
import asyncio

from tavily import TavilyClient

from pydantic_ai import RunContext

from src.agents import research_agent
from src.deps import AppDeps


@research_agent.tool
async def search_youtube_trends(ctx: RunContext[AppDeps], keyword: str) -> str:
    """YouTube Shorts 트렌드를 Tavily로 검색합니다.

    Args:
        ctx: PydanticAI가 자동으로 주입하는 실행 컨텍스트
             ctx.deps로 AppDeps에 접근합니다
        keyword: 검색할 한국어 키워드

    Returns:
        검색 결과를 포맷한 텍스트 문자열
        LLM이 이를 읽고 TrendData로 변환합니다
    """
    # TavilyClient는 동기 SDK이므로 asyncio.to_thread()로 블로킹 방지
    client = TavilyClient(api_key=ctx.deps.tavily_api_key)

    results = await asyncio.to_thread(
        client.search,
        query=f"{keyword} YouTube Shorts 2026 한국 인기",
        max_results=5,
        search_depth="advanced",
    )

    # 검색 결과를 LLM이 읽기 좋은 텍스트로 변환
    formatted = f"키워드 '{keyword}' 검색 결과:\n\n"
    for i, result in enumerate(results.get("results", []), 1):
        formatted += f"{i}. 제목: {result.get('title', '')}\n"
        formatted += f"   내용: {result.get('content', '')[:300]}\n"
        formatted += f"   URL: {result.get('url', '')}\n\n"

    return formatted
