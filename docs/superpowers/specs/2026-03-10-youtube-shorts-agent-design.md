# YouTube Shorts Content Automation Agent — Design Spec
**Date:** 2026-03-10
**Status:** Approved
**Framework:** PydanticAI · GPT-5 Nano · Tavily · Gradio
**Target audience:** Non-technical Korean entrepreneurs

---

## Goal

A fully automated multi-agent pipeline that accepts a single Korean keyword and outputs a complete YouTube Shorts content package — with zero human intervention after the initial trigger. Delivered as a Gradio web UI.

---

## Architecture

```
keyword (Korean)
     │
     ▼
┌─────────────────┐
│  Research Agent  │  ← Tool Use: Tavily web search
│  tools.py        │  → returns TrendData
└────────┬────────┘
         │ TrendData (serialized via .model_dump_json())
         ▼
┌─────────────────┐
│  Writer Agent    │  ← Structured Output: ShortsScript
│  (no tools)      │  → returns ShortsScript
└────────┬────────┘
         │ ShortsScript (serialized via .model_dump_json())
         ▼
┌─────────────────┐
│  Editor Agent    │  ← Quality scoring + Korean polish
│  (no tools)      │  → returns ContentPackage
└────────┬────────┘
         │ ContentPackage
         ▼
┌─────────────────┐
│   Gradio UI      │  ← app.py (Korean interface)
└─────────────────┘
```

### Key architectural decisions
- All three agents share one `AppDeps` dependency object (holds API keys + config)
- Agents communicate by serializing Pydantic model instances to JSON strings — no direct object passing
- Gradio UI calls a single `run_pipeline()` async function in `pipeline.py`
- `.env` holds `OPENAI_API_KEY` and `TAVILY_API_KEY` — loaded once in `deps.py`
- All generated content (scripts, titles, hashtags) is in Korean

---

## File Structure

```
agent-tutorial/
├── src/
│   ├── models.py      # Concept 1: Structured Output (Pydantic models)
│   ├── tools.py       # Concept 2: Tool Use (Tavily search)
│   ├── deps.py        # Concept 3: Dependency Injection (config object)
│   ├── agents.py      # Concept 4: Multi-Agent Pipeline (3 agents)
│   ├── pipeline.py    # Concept 5: Orchestration (async sequential flow)
│   └── app.py         # Gradio UI (wires everything together)
├── docs/
│   └── superpowers/specs/
│       └── 2026-03-10-youtube-shorts-agent-design.md
├── .env               # OPENAI_API_KEY, TAVILY_API_KEY
├── pyproject.toml
└── README.md
```

**Tutorial build order:** models → tools → deps → agents → pipeline → app
Each file introduces exactly one new PydanticAI concept.

---

## Data Models (`models.py`)

Three Pydantic models. Each represents one agent's output. Strict typing enables automatic validation.

```python
class TrendData(BaseModel):
    keyword: str                    # 입력 키워드
    competing_titles: list[str]     # 경쟁 영상 제목 (최대 5개)
    avg_views: int                  # 평균 조회수 추정치
    best_hook_patterns: list[str]   # 효과적인 훅 패턴

class ShortsScript(BaseModel):
    hook: str                       # 첫 3초 훅 문장
    body: str                       # 본문 (40-50초)
    cta: str                        # 마지막 행동 유도
    duration_sec: int               # 예상 길이 (55-60초)

class ContentPackage(BaseModel):
    title: str                      # 영상 제목
    script: ShortsScript            # 완성된 스크립트 (중첩 모델)
    thumbnail_copy: str             # 썸네일 문구
    hashtags: list[str]             # 해시태그 (최대 10개)
    upload_time: str                # 권장 업로드 시간 (e.g. "오후 7시")
    quality_score: int              # 품질 점수 1-10
```

`ContentPackage` embeds `ShortsScript` — demonstrates nested Pydantic model composition.

---

## Tool Use (`tools.py`)

One tool decorated with `@research_agent.tool`. Returns raw text; PydanticAI extracts `TrendData`.

```python
@research_agent.tool
async def search_youtube_trends(ctx: RunContext[AppDeps], keyword: str) -> str:
    client = TavilyClient(api_key=ctx.deps.tavily_api_key)
    results = await client.search(
        query=f"{keyword} YouTube Shorts 2026 한국",
        max_results=5
    )
    return format_results(results)
```

**Teaching point:** Tools return plain strings. The agent handles structuring the response into the typed output model.

---

## Dependency Injection (`deps.py`)

A single dataclass passed to every agent at runtime. No global variables or scattered `os.getenv()` calls.

```python
@dataclass
class AppDeps:
    openai_api_key: str
    tavily_api_key: str
    target_language: str = "Korean"
    max_duration_sec: int = 60

def load_deps() -> AppDeps:
    return AppDeps(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
    )
```

**Teaching point:** All config flows through `ctx.deps` inside tools and agents — no hidden state.

---

## Agents (`agents.py`)

Three agents, each typed to its output model. Writer and Editor receive prior outputs as JSON strings in their user messages.

```python
research_agent = Agent(
    model="gpt-5-nano-2025-08-07",
    deps_type=AppDeps,
    result_type=TrendData,
    system_prompt="당신은 YouTube Shorts 트렌드 분석가입니다..."
)

writer_agent = Agent(
    model="gpt-5-nano-2025-08-07",
    deps_type=AppDeps,
    result_type=ShortsScript,
    system_prompt="당신은 바이럴 숏폼 스크립트 작가입니다..."
)

editor_agent = Agent(
    model="gpt-5-nano-2025-08-07",
    deps_type=AppDeps,
    result_type=ContentPackage,
    system_prompt="당신은 콘텐츠 편집자입니다. 품질을 1-10점으로 평가하세요..."
)
```

**Critical pitfall:** Agents cannot receive Python objects from other agents — must serialize with `.model_dump_json()`.

---

## Pipeline Orchestration (`pipeline.py`)

One async function chains all three agents sequentially.

```python
async def run_pipeline(keyword: str, deps: AppDeps) -> ContentPackage:
    # Step 1: Research
    trend_result = await research_agent.run(keyword, deps=deps)
    trend_data: TrendData = trend_result.data

    # Step 2: Write
    script_result = await writer_agent.run(
        trend_data.model_dump_json(), deps=deps
    )
    shorts_script: ShortsScript = script_result.data

    # Step 3: Edit
    package_result = await editor_agent.run(
        f"트렌드: {trend_data.model_dump_json()}\n"
        f"스크립트: {shorts_script.model_dump_json()}",
        deps=deps
    )
    return package_result.data
```

---

## Gradio UI (`app.py`)

Korean-language interface. One keyword input, one button, results in labeled text boxes.

```
┌─────────────────────────────────────┐
│  🎬 YouTube Shorts 자동화 에이전트   │
├─────────────────────────────────────┤
│  키워드 입력: [____________] [생성]  │
├─────────────────────────────────────┤
│  📋 영상 제목:    [result]           │
│  🎯 훅:          [result]           │
│  📝 본문:        [result]           │
│  📢 CTA:         [result]           │
│  🖼️ 썸네일 문구: [result]           │
│  #️⃣ 해시태그:    [result]           │
│  ⏰ 업로드 시간: [result]           │
│  ⭐ 품질 점수:   [result]/10        │
└─────────────────────────────────────┘
```

**Implementation note:** Use `asyncio.run()` inside the Gradio callback to bridge sync Gradio with async pipeline.

---

## Common Pitfalls

1. **Agent-to-agent serialization** — Must use `.model_dump_json()` between agents, not raw Python object passing. PydanticAI agents communicate through text.
2. **Async in Gradio** — Gradio's default `Interface` is synchronous. Wrap `run_pipeline()` with `asyncio.run()` in the callback, or define the callback as `async def` with `gr.Interface`.
3. **Tavily rate limits** — Free tier is 1,000 searches/month. Mock the tool in development to avoid burning quota during iteration.

---

## Extension Path: Remotion Video Pipeline

Add a 4th agent `VideoAgent` that takes `ContentPackage` and outputs a `RemotionConfig` model:

```python
class RemotionConfig(BaseModel):
    scenes: list[Scene]           # Timed scene breakdowns
    subtitle_positions: list[str] # Per-scene subtitle placement
    broll_queries: list[str]      # Stock footage search terms
    background_music: str         # Music mood descriptor
```

Feed `RemotionConfig` as JSON to a Remotion CLI call via `subprocess.run()`. This turns the content automation agent into a full video production pipeline.

---

## Dependencies to Add

```toml
# pyproject.toml additions
gradio = ">=4.0"
tavily-python = ">=0.3"
python-dotenv = ">=1.0"
```

---

## Success Criteria

- Single keyword input → complete `ContentPackage` in Korean in under 60 seconds
- Each of the 6 source files demonstrates exactly one PydanticAI concept
- Gradio UI runs with `python src/app.py` — no configuration beyond `.env`
- All agent outputs are validated Pydantic models (no untyped dict responses)
