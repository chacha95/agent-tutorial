# YouTube Shorts Content Automation Agent — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a PydanticAI multi-agent pipeline that takes a Korean keyword and outputs a complete YouTube Shorts content package via a Gradio web UI.

**Architecture:** Three sequential PydanticAI agents (Research → Writer → Editor) share a single `AppDeps` dependency object. Agents communicate by serializing Pydantic model outputs to JSON strings. A Gradio web UI calls the pipeline through a single `async def` callback (Gradio 4+ natively supports async).

**Tech Stack:** PydanticAI 1.67+, GPT-5 Nano (`gpt-5-nano-2025-08-07`), Tavily Python SDK, Gradio 4+, python-dotenv, pytest, pytest-asyncio

---

## Build Order Note

The design spec lists the tutorial concept order as `models → tools → deps → agents → pipeline → app`. However, Python import dependencies require a different build order: `tools.py` must import `research_agent` from `agents.py`, and `agents.py` must import `AppDeps` from `deps.py`. The actual build order in this plan is:

**`models → deps → agents → tools → pipeline → app`**

This is the correct dependency order. Each file still teaches exactly one PydanticAI concept.

---

## File Map

| File | Responsibility |
|---|---|
| `src/__init__.py` | Makes `src` a Python package (required for imports) |
| `src/models.py` | **Concept 1:** Structured Output — three typed Pydantic output models |
| `src/deps.py` | **Concept 2:** Dependency Injection — `AppDeps` dataclass + `load_deps()` |
| `src/agents.py` | **Concept 3:** Multi-Agent — three `Agent` instances typed to output models |
| `src/tools.py` | **Concept 4:** Tool Use — `@research_agent.tool` registers Tavily search |
| `src/pipeline.py` | **Concept 5:** Agent Chaining — async sequential orchestration |
| `src/app.py` | Gradio Korean UI with `async def` callback |
| `tests/__init__.py` | Makes `tests` a Python package |
| `tests/conftest.py` | Shared fixtures (fake API keys via monkeypatch) |
| `tests/test_models.py` | Pydantic model validation and field constraints |
| `tests/test_deps.py` | `AppDeps` loading, defaults, and missing key errors |
| `tests/test_tools.py` | Tavily tool with mocked HTTP response |
| `tests/test_pipeline.py` | Full pipeline with mocked agents |

---

## Chunk 1: Project Setup

### Task 1: Add Dependencies and Test Infrastructure

**Files:**
- Modify: `pyproject.toml`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Add missing packages via uv**

```bash
cd /Users/chajinhyeog/workspace/agent-tutorial
uv add gradio tavily-python python-dotenv pytest pytest-asyncio
```

Expected: packages added to `pyproject.toml` and `uv.lock` updated.

- [ ] **Step 2: Verify all imports work**

```bash
uv run python -c "import gradio, tavily, dotenv, pydantic_ai; print('all imports ok')"
```

Expected: `all imports ok`

- [ ] **Step 3: Create `src/__init__.py`**

```bash
touch /Users/chajinhyeog/workspace/agent-tutorial/src/__init__.py
```

This makes `src` a Python package so `from src.models import ...` works.

- [ ] **Step 4: Add API keys to .env.local**

Open `.env.local` and add your actual keys (do not commit this file):
```
OPENAI_API_KEY=sk-your-openai-key-here
TAVILY_API_KEY=tvly-your-tavily-key-here
```

Verify `.env.local` is in `.gitignore`:
```bash
grep "env.local" .gitignore
```

If not present, add it:
```bash
echo ".env.local" >> .gitignore
```

- [ ] **Step 5: Create test infrastructure**

Create `tests/__init__.py` (empty):
```bash
touch /Users/chajinhyeog/workspace/agent-tutorial/tests/__init__.py
```

Create `tests/conftest.py`:
```python
import pytest


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set fake API keys for all tests — no real API calls in unit tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-openai-key")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-fake-tavily-key")
```

- [ ] **Step 6: Add pytest config to pyproject.toml**

Add to the bottom of `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 7: Verify pytest collects without errors**

```bash
uv run pytest --collect-only
```

Expected: `no tests ran` with no import errors.

- [ ] **Step 8: Commit (do NOT include .env.local)**

```bash
git add pyproject.toml uv.lock src/__init__.py tests/ .gitignore
git commit -m "chore: add gradio, tavily, pytest deps and test infrastructure"
```

---

## Chunk 2: Pydantic Models

> **PydanticAI Concept 1:** Structured Output — all agent responses are typed Pydantic models, not raw strings. PydanticAI validates the LLM's JSON against the schema automatically.

### Task 2: Write and Test Data Models

**Files:**
- Create: `src/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests first**

Create `tests/test_models.py`:
```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.models'`

- [ ] **Step 3: Implement `src/models.py`**

Create `src/models.py`:
```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_models.py -v
```

Expected: `10 passed`

- [ ] **Step 5: Commit**

```bash
git add src/models.py tests/test_models.py
git commit -m "feat: add structured output models (TrendData, ShortsScript, ContentPackage)"
```

---

## Chunk 3: Dependency Injection

> **PydanticAI Concept 2:** Dependency Injection — config flows through `ctx.deps`, not global variables or scattered `os.getenv()` calls.

### Task 3: Write and Test AppDeps

**Files:**
- Create: `src/deps.py`
- Create: `tests/test_deps.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_deps.py`:
```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_deps.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.deps'`

- [ ] **Step 3: Implement `src/deps.py`**

Create `src/deps.py`:
```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_deps.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/deps.py tests/test_deps.py
git commit -m "feat: add AppDeps dependency injection container"
```

---

## Chunk 4: Agents

> **PydanticAI Concept 3:** Multi-Agent Pipeline — three `Agent` instances, each typed to its output model. The `result_type` parameter tells PydanticAI what schema to validate against.

### Task 4: Define Three Agents

**Files:**
- Create: `src/agents.py`

> Note: Agents are integration-tested via the pipeline in Chunk 6. This task verifies correct instantiation only.

- [ ] **Step 1: Implement `src/agents.py`**

Create `src/agents.py`:
```python
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
    result_type=TrendData,
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
    result_type=ShortsScript,
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
    result_type=ContentPackage,
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
```

- [ ] **Step 2: Verify agents instantiate correctly**

```bash
uv run python -c "from src.agents import research_agent, writer_agent, editor_agent; print('3 agents ok')"
```

Expected: `3 agents ok`

- [ ] **Step 3: Commit**

```bash
git add src/agents.py
git commit -m "feat: define three typed PydanticAI agents"
```

---

## Chunk 5: Tool Use

> **PydanticAI Concept 4:** Tool Use — `@agent.tool` registers a function the LLM can call. Tools return plain strings; the agent handles structuring the output into the typed result model.

### Task 5: Write and Test the Tavily Search Tool

**Files:**
- Create: `src/tools.py`
- Create: `tests/test_tools.py`

- [ ] **Step 1: Write failing tool tests**

Create `tests/test_tools.py`:
```python
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

            # Call the tool function directly (bypassing PydanticAI runtime)
            from src.tools import search_youtube_trends
            from unittest.mock import AsyncMock, MagicMock as MM

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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_tools.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.tools'`

- [ ] **Step 3: Implement `src/tools.py`**

Create `src/tools.py`:
```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_tools.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Run all tests so far**

```bash
uv run pytest -v
```

Expected: all previous tests still pass.

- [ ] **Step 6: Commit**

```bash
git add src/tools.py tests/test_tools.py
git commit -m "feat: add Tavily search tool registered on research_agent"
```

---

## Chunk 6: Pipeline Orchestration

> **PydanticAI Concept 5:** Agent Chaining — agents communicate via JSON-serialized strings, not Python objects. Use `.model_dump_json()` between every agent step.

### Task 6: Write and Test Pipeline

**Files:**
- Create: `src/pipeline.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Write failing pipeline tests**

Create `tests/test_pipeline.py`:
```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
uv run pytest tests/test_pipeline.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.pipeline'`

- [ ] **Step 3: Implement `src/pipeline.py`**

Create `src/pipeline.py`:
```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run pytest tests/test_pipeline.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Run all tests**

```bash
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/pipeline.py tests/test_pipeline.py
git commit -m "feat: add async pipeline with agent chaining via model_dump_json"
```

---

## Chunk 7: Gradio UI + Final Verification

### Task 7: Build Korean Gradio Interface

**Files:**
- Create: `src/app.py`
- Modify: `README.md`

> Gradio UIs are tested manually. No automated tests for this file.

- [ ] **Step 1: Create `src/app.py`**

```python
"""
app.py — Gradio 한국어 웹 인터페이스

Gradio 4+는 async def 콜백을 네이티브로 지원합니다.
asyncio.run()을 사용하지 마세요 — Gradio가 이미 이벤트 루프를 실행 중이므로
RuntimeError: asyncio.run() cannot be called from a running event loop 오류가 발생합니다.

올바른 방법: async def generate_content(...)
틀린 방법: def generate_content(...) + asyncio.run(...)
"""
import gradio as gr

from src.deps import load_deps
from src.pipeline import run_pipeline

# 의존성 한 번만 로드 (앱 시작 시)
deps = load_deps()


async def generate_content(keyword: str) -> tuple[str, str, str, str, str, str, str, str]:
    """Gradio 비동기 콜백. Gradio 4+가 자동으로 await합니다.

    Returns:
        8개의 문자열 튜플 — 각 Gradio 출력 컴포넌트에 매핑됩니다
    """
    if not keyword.strip():
        empty = "키워드를 입력해주세요."
        return (empty,) * 8

    package = await run_pipeline(keyword.strip(), deps)
    hashtags_text = " ".join(package.hashtags)

    return (
        package.title,
        package.script.hook,
        package.script.body,
        package.script.cta,
        package.thumbnail_copy,
        hashtags_text,
        package.upload_time,
        f"{package.quality_score}/10",
    )


# ── Gradio UI 레이아웃 ──────────────────────────────────────────────
with gr.Blocks(title="YouTube Shorts 자동화 에이전트", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎬 YouTube Shorts 콘텐츠 자동화 에이전트")
    gr.Markdown("키워드 하나만 입력하면 완성된 콘텐츠 패키지를 생성합니다.")

    with gr.Row():
        keyword_input = gr.Textbox(
            label="키워드 입력",
            placeholder="예: 다이어트, 주식투자, 영어회화",
            scale=4,
        )
        generate_btn = gr.Button("🚀 생성하기", variant="primary", scale=1)

    gr.Markdown("---")
    gr.Markdown("### 📦 생성된 콘텐츠 패키지")

    with gr.Row():
        title_output = gr.Textbox(label="📋 영상 제목", interactive=False)
        quality_output = gr.Textbox(label="⭐ 품질 점수", interactive=False)

    hook_output = gr.Textbox(label="🎯 훅 (첫 3초)", interactive=False)
    body_output = gr.Textbox(label="📝 본문", interactive=False, lines=4)
    cta_output = gr.Textbox(label="📢 CTA (행동 유도)", interactive=False)

    with gr.Row():
        thumbnail_output = gr.Textbox(label="🖼️ 썸네일 문구", interactive=False)
        upload_time_output = gr.Textbox(label="⏰ 권장 업로드 시간", interactive=False)

    hashtags_output = gr.Textbox(label="#️⃣ 해시태그", interactive=False)

    generate_btn.click(
        fn=generate_content,
        inputs=[keyword_input],
        outputs=[
            title_output,
            hook_output,
            body_output,
            cta_output,
            thumbnail_output,
            hashtags_output,
            upload_time_output,
            quality_output,
        ],
    )

    gr.Markdown("---")
    gr.Markdown(
        "💡 **팁:** 구체적인 키워드일수록 더 정확한 결과가 나옵니다. "
        "예: '다이어트' 보다 '직장인 점심 다이어트'가 더 좋습니다."
    )


if __name__ == "__main__":
    demo.launch(share=False)
```

- [ ] **Step 2: Launch the app and verify the UI loads**

```bash
uv run python src/app.py
```

Expected: Gradio prints `Running on local URL: http://127.0.0.1:7860`. Open in browser — confirm Korean UI with all output fields renders correctly. Do NOT run a keyword test yet (requires real API keys and quota).

- [ ] **Step 3: Stop the server (Ctrl+C) and commit**

```bash
git add src/app.py
git commit -m "feat: add Korean Gradio UI with async callback"
```

- [ ] **Step 4: Run full test suite**

```bash
uv run pytest -v --tb=short
```

Expected: all tests pass.

- [ ] **Step 5: Verify API keys are set**

```bash
grep -c "API_KEY" .env.local
```

Expected: `2`

- [ ] **Step 6: End-to-end live test**

```bash
uv run python src/app.py
```

Open `http://127.0.0.1:7860`, enter `다이어트`, click `생성하기`.

Expected within 60 seconds:
- `📋 영상 제목` — Korean title filled
- `🎯 훅` — compelling opening line in Korean
- `📝 본문` — paragraph of Korean script content
- `📢 CTA` — short Korean call to action
- `#️⃣ 해시태그` — 10 hashtags starting with `#`
- `⭐ 품질 점수` — shows `N/10` where N is 1–10

- [ ] **Step 7: Write README.md**

Replace the contents of `README.md`:
```markdown
# YouTube Shorts 콘텐츠 자동화 에이전트

PydanticAI를 활용한 멀티 에이전트 파이프라인 튜토리얼.
키워드 하나로 YouTube Shorts 콘텐츠 패키지를 자동 생성합니다.

## PydanticAI 개념 로드맵

| 파일 | 개념 | 설명 |
|---|---|---|
| `src/models.py` | Structured Output | 타입이 보장된 Pydantic 출력 모델 |
| `src/deps.py` | Dependency Injection | ctx.deps로 공유 설정 접근 |
| `src/agents.py` | Multi-Agent Pipeline | result_type으로 출력 스키마 선언 |
| `src/tools.py` | Tool Use | @agent.tool로 LLM 도구 등록 |
| `src/pipeline.py` | Agent Chaining | model_dump_json()으로 에이전트 연결 |
| `src/app.py` | Gradio UI | async def 콜백으로 파이프라인 호출 |

## 파이프라인 흐름

```
키워드 입력
    ↓
Research Agent (Tavily 검색) → TrendData
    ↓ [model_dump_json()]
Writer Agent → ShortsScript
    ↓ [model_dump_json()]
Editor Agent → ContentPackage
    ↓
Gradio UI 출력 (한국어)
```

## 시작하기

### 1. 환경 설정

`.env.local` 파일을 생성하고 API 키를 추가하세요:
```
OPENAI_API_KEY=sk-your-openai-key
TAVILY_API_KEY=tvly-your-tavily-key
```

### 2. 의존성 설치

```bash
uv sync
```

### 3. 실행

```bash
uv run python src/app.py
```

`http://127.0.0.1:7860` 접속 후 키워드를 입력하세요.

## 테스트

```bash
uv run pytest -v
```
```

- [ ] **Step 8: Final commit**

```bash
git add README.md
git commit -m "docs: add complete setup and usage README"
```

---

## Common Pitfalls Reference

| 상황 | 증상 | 해결 |
|---|---|---|
| Python 객체를 에이전트에 직접 전달 | `TypeError` 또는 에이전트가 이상한 입력을 받음 | `.model_dump_json()` 후 전달 |
| `asyncio.run()` in Gradio | `RuntimeError: cannot be called from a running event loop` | `async def` 콜백 사용 (Gradio 4+ 네이티브 지원) |
| `.env.local`에 키 없음 | `ValueError: TAVILY_API_KEY가 설정되지 않았습니다` | `.env.local`에 두 키 모두 추가 |
| Tavily 무료 한도 초과 | `429 Too Many Requests` | 테스트에서 도구 mock 처리; 실제 API는 아껴서 사용 |
| `tools.py`를 `agents.py` 전에 임포트 | `AttributeError: Agent has no tool` | `pipeline.py`에서 `import src.tools` 순서 유지 |
| `src/__init__.py` 없음 | `ModuleNotFoundError: No module named 'src'` | `touch src/__init__.py` 실행 |
