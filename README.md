# YouTube Shorts 콘텐츠 자동화 에이전트

PydanticAI를 활용한 멀티 에이전트 파이프라인 튜토리얼.
키워드 하나로 YouTube Shorts 콘텐츠 패키지를 자동 생성합니다.

## PydanticAI 개념 로드맵

| 파일 | 개념 | 설명 |
|---|---|---|
| `src/models.py` | Structured Output | 타입이 보장된 Pydantic 출력 모델 |
| `src/deps.py` | Dependency Injection | ctx.deps로 공유 설정 접근 |
| `src/agents.py` | Multi-Agent Pipeline | output_type으로 출력 스키마 선언 |
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

`.env.local` 파일 (또는 `.env` 파일)에 API 키를 추가하세요:
```
OPENAI_API_KEY=sk-your-openai-key
TAVILY_API_KEY=tvly-your-tavily-key
```
> `.env.local`이 `.env`보다 우선 적용됩니다. 두 파일 모두 git에서 제외됩니다.

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
