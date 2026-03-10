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

    try:
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
    except Exception as e:
        error_msg = f"오류가 발생했습니다: {str(e)}"
        return (error_msg,) * 8


# ── Gradio UI 레이아웃 ──────────────────────────────────────────────
with gr.Blocks(title="YouTube Shorts 자동화 에이전트") as demo:
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
    demo.launch(share=False, theme=gr.themes.Soft())
