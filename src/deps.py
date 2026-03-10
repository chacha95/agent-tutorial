"""
deps.py — PydanticAI Concept 2: Dependency Injection

AppDeps는 모든 에이전트가 공유하는 설정 컨테이너입니다.
에이전트 내부에서 ctx.deps로 접근합니다.

이렇게 하면:
  - 전역 변수가 없습니다
  - os.getenv()가 에이전트 코드에 흩어지지 않습니다
  - 테스트 시 deps를 쉽게 교체할 수 있습니다
"""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# .env.local을 먼저 로드하고, 없으면 .env를 사용
load_dotenv(".env.local")
load_dotenv(".env")


@dataclass
class AppDeps:
    """모든 에이전트에 주입되는 의존성 컨테이너.

    에이전트 도구(tool) 안에서 ctx.deps.tavily_api_key처럼 접근합니다.
    """
    openai_api_key: str
    tavily_api_key: str
    target_language: str = field(default="Korean")
    max_duration_sec: int = field(default=60)


def load_deps() -> AppDeps:
    """환경 변수에서 AppDeps를 생성합니다."""
    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    if not openai_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env.local을 확인하세요.")
    if not tavily_key:
        raise ValueError("TAVILY_API_KEY가 설정되지 않았습니다. .env.local을 확인하세요.")

    return AppDeps(
        openai_api_key=openai_key,
        tavily_api_key=tavily_key,
    )
