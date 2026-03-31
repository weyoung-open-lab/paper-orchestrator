# paper_agent/app/gradio_app.py
from __future__ import annotations

import os
import time
from typing import Any, List, Dict, Optional

import gradio as gr

# Dual-mode import
try:
    from paper_agent.core.agent import ClaudeWriteAgent
    from paper_agent.core.pipeline import PaperPipeline
    from paper_agent.core.latex import LatexService
    from paper_agent.core.exporter import Exporter
    from paper_agent.core.config import PipelineConfig
except ModuleNotFoundError:
    from ..core.agent import ClaudeWriteAgent
    from ..core.pipeline import PaperPipeline
    from ..core.latex import LatexService
    from ..core.exporter import Exporter
    from ..core.config import PipelineConfig


custom_css = """
.container { max-width: 1400px; margin: auto; }
.main-header { text-align: center; padding: 22px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); border-radius: 14px; margin-bottom: 18px; }
.panel { border: 1px solid #eee; border-radius: 12px; padding: 16px; background: rgba(255,255,255,0.65); backdrop-filter: blur(2px); }
.card { border: 1px solid #eee; border-radius: 12px; padding: 14px; background: rgba(255,255,255,0.55); backdrop-filter: blur(2px); }
.hint { color: #666; font-size: 12px; }

/* Key code area: fixed height + inner scroll */
#keycode_box { min-height: 360px !important; }
#keycode_box .cm-editor,
#keycode_box .cm-theme,
#keycode_box .cm-scroller,
#keycode_box .cm-content { max-height: 360px !important; }
#keycode_box .cm-scroller { overflow: auto !important; }
#keycode_box .wrap, #keycode_box > div { height: 360px !important; max-height: 360px !important; }

/* comfy background */
body, .gradio-container { background: #f6f7fb !important; }
"""


def _safe_path(file_obj: Any) -> Optional[str]:
    if not file_obj:
        return None
    if isinstance(file_obj, str):
        return file_obj
    return getattr(file_obj, "name", None) or getattr(file_obj, "path", None)


def update_status(agent: Optional[ClaudeWriteAgent]) -> str:
    if not agent:
        return "Waiting for initialization..."

    ctx = agent.context
    def ok(v: str) -> str:
        return "✅" if (v and v.strip()) else "⛔"

    lines = [
        f"Project description: {ok(ctx.project_description)}",
        f"Key code / method: {ok(ctx.model_method)}",
        f"Experiment data: {ok(ctx.experiment_data)}",
        f"Seed references: {ok(ctx.seed_references)}",
        f"Figures: {'✅' if ctx.figures else '⛔'}",
        f"Images: {'✅' if ctx.image_paths else '⛔'}",
        f"Template zip: {'✅' if ctx.template_zip_path else '⛔'}",
        "",
        f"Draft paper ready: {'✅' if ctx.full_paper else '⛔'}",
        f"LaTeX ready: {'✅' if ctx.full_latex else '⛔'}",
        f"BibTeX ready: {'✅' if ctx.bibtex else '⛔'}",
    ]
    return "\n".join(lines)


def initialize_logic(api_key: str, base_url: str, model: str, lang: str):
    if not api_key.strip():
        # state, status, save_1, save_2, attach_template_btn, run_btn
        return None, "❌ Missing API key.", *(gr.Button(interactive=False) for _ in range(4))

    base_url = base_url.strip() or None
    agent = ClaudeWriteAgent(
        api_key=api_key.strip(),
        model=model,
        language="English" if lang == "English" else "中文",
        base_url=base_url,
    )
    # Return EXACTLY 6 values:
    return agent, update_status(agent), *(gr.Button(interactive=True) for _ in range(4))



def save_material_1(agent: Optional[ClaudeWriteAgent], brief_text: str, code_text: str):
    if not agent:
        return agent, "❌ Please initialize first."
    agent.context.project_description = brief_text or ""
    agent.context.model_method = code_text or ""
    return agent, update_status(agent)


def save_material_2(agent: Optional[ClaudeWriteAgent], result_text: str, figs_val: str, imgs: Any):
    if not agent:
        return agent, "❌ Please initialize first."

    agent.context.experiment_data = result_text or ""
    agent.context.figures = []
    agent.context.image_paths = []

    if figs_val:
        for line in figs_val.splitlines():
            line = line.strip()
            if line:
                agent.context.figures.append({"description": line})

    # Gradio Files -> list
    if imgs:
        if not isinstance(imgs, (list, tuple)):
            imgs = [imgs]
        for f in imgs:
            p = _safe_path(f)
            if p:
                agent.context.image_paths.append(p)

    return agent, update_status(agent)


def attach_template(agent: Optional[ClaudeWriteAgent], template_zip: Any):
    """
    Replace the old 'reference papers' block:
    user uploads a template zip, we store its path in context.
    """
    if not agent:
        return agent, "❌ Please initialize first."
    p = _safe_path(template_zip)
    agent.context.template_zip_path = p
    return agent, update_status(agent)


def run_pipeline(agent: Optional[ClaudeWriteAgent], do_polish: bool, gen_latex: bool, export_folder: str):
    if not agent:
        return agent, "", "", "", "❌ Please initialize first.", update_status(agent)

    export_folder = (export_folder or "").strip() or "final_project"
    out_dir = os.path.join(os.getcwd(), export_folder)

    pipeline = PaperPipeline(agent=agent, latex_service=LatexService(), exporter=Exporter())
    cfg = PipelineConfig(
        gen_latex=gen_latex,
        do_polish=do_polish,
        strict_check=False,
        export_dir=out_dir,   # IMPORTANT: template render + export share this folder
    )
    res = pipeline.run(cfg)

    return agent, (res.paper_md or ""), (res.latex or ""), (res.bibtex or ""), (res.log + ("\n\n" + res.errors if res.errors else "")), update_status(agent)


def export_zip(agent: Optional[ClaudeWriteAgent], export_folder: str):
    if not agent:
        return agent, None, "❌ Please initialize first."

    export_folder = (export_folder or "").strip() or "final_project"
    out_dir = os.path.join(os.getcwd(), export_folder)

    exporter = Exporter()
    zip_path = exporter.export_bundle(agent.context, out_dir)
    return agent, zip_path, f"✅ Exported: {zip_path}"


def create_app() -> gr.Blocks:
    with gr.Blocks(title="One-Click Academic Paper Writing System") as demo:
        agent_state = gr.State(None)

        with gr.Group(elem_classes="main-header"):
            gr.Markdown("# 🧪 One-Click Academic Paper Writing System")
            gr.Markdown(
                "Provide two kinds of inputs: **(1) experiment brief + key code** and **(2) figures/tables + results**. "
                "Optional: upload a **journal LaTeX template zip** to render output into that template."
            )

        with gr.Row():
            # Left
            with gr.Column(scale=1):
                with gr.Group(elem_classes="panel"):
                    gr.Markdown("### ⚙️ Configuration")
                    api_key = gr.Textbox(label="Anthropic API Key", type="password", value=os.environ.get("ANTHROPIC_API_KEY", ""))
                    base_url = gr.Textbox(label="Base URL (optional)", value=os.environ.get("ANTHROPIC_BASE_URL", ""))
                    model = gr.Dropdown(
                        choices=["claude-3-5-sonnet-20241022", "claude-sonnet-4-20250514"],
                        value="claude-3-5-sonnet-20241022",
                        label="Model",
                    )
                    lang = gr.Radio(choices=["English", "中文"], value="English", label="Output Language")
                    init_btn = gr.Button("Initialize", variant="primary")
                    status = gr.Textbox(label="Current input status / progress", lines=11, interactive=False)

                with gr.Accordion("Advanced (optional)", open=False):
                    seed_refs = gr.Textbox(
                        label="Seed References (optional; helps BibTeX draft)",
                        lines=7,
                        placeholder="One per line: Authors / Title / Venue / Year / DOI (optional)",
                    )

            # Right
            with gr.Column(scale=2):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Group(elem_classes="card"):
                            gr.Markdown("## (1) Experiment Brief + Key Code")
                            brief = gr.Textbox(label="Experiment brief", lines=10)
                            code = gr.Code(label="Key code", language="python", lines=16, max_lines=16, wrap_lines=True, elem_id="keycode_box")
                            save_1 = gr.Button("Save Input (1)", interactive=False)

                    with gr.Column(scale=1):
                        with gr.Group(elem_classes="card"):
                            gr.Markdown("## (2) Figures/Tables + Results")
                            results = gr.Textbox(label="Results text", lines=10)
                            figs = gr.Textbox(label="Figure/table descriptions (one per line)", lines=5)
                            images = gr.Files(label="Upload images (optional)", file_types=["image"])
                            save_2 = gr.Button("Save Input (2)", interactive=False)

                # ---- Replace "reference papers" with TEMPLATE ZIP uploader (NEW) ----
                with gr.Row():
                    with gr.Group(elem_classes="panel"):
                        gr.Markdown("### 🧩 Journal Template (optional)")
                        template_zip = gr.File(label="Upload journal LaTeX template (.zip)", file_types=[".zip"])
                        attach_template_btn = gr.Button("Attach template zip", interactive=False)

                with gr.Row():
                    with gr.Group(elem_classes="panel"):
                        gr.Markdown("### ▶️ Run")
                        do_polish = gr.Checkbox(label="Consistency polishing", value=True)
                        gen_latex = gr.Checkbox(label="Generate LaTeX", value=True)
                        export_folder = gr.Textbox(label="Output folder name", value="final_project")
                        run_btn = gr.Button("Run pipeline (outline → sections → paper → LaTeX + Bib)", interactive=False)

                with gr.Row():
                    with gr.Group(elem_classes="panel"):
                        gr.Markdown("### 📄 Outputs")
                        paper_out = gr.Markdown()
                        latex_out = gr.Code(language="latex", label="LaTeX (main.tex)")
                        bib_out = gr.Textbox(label="BibTeX (refs.bib)", lines=16)

                        log_out = gr.Textbox(label="Runtime log / status", lines=10)

                with gr.Row():
                    with gr.Group(elem_classes="panel"):
                        gr.Markdown("### 📦 Export")
                        export_btn = gr.Button("Export & Download ZIP", interactive=False)
                        zip_file = gr.File(label="Download ZIP")
                        export_msg = gr.Textbox(label="Export status", lines=2)

        # Wiring
        init_btn.click(
            fn=initialize_logic,
            inputs=[api_key, base_url, model, lang],
            outputs=[agent_state, status, save_1, save_2, attach_template_btn, run_btn],
        )

        save_1.click(fn=save_material_1, inputs=[agent_state, brief, code], outputs=[agent_state, status])
        save_2.click(fn=save_material_2, inputs=[agent_state, results, figs, images], outputs=[agent_state, status])

        attach_template_btn.click(fn=attach_template, inputs=[agent_state, template_zip], outputs=[agent_state, status])

        # Seed refs stored before run (simple: set ctx field via textbox value)
        def _set_seed(agent: Optional[ClaudeWriteAgent], txt: str):
            if agent:
                agent.context.seed_references = txt or ""
            return agent, update_status(agent)

        seed_refs.change(fn=_set_seed, inputs=[agent_state, seed_refs], outputs=[agent_state, status])

        run_btn.click(
            fn=run_pipeline,
            inputs=[agent_state, do_polish, gen_latex, export_folder],
            outputs=[agent_state, paper_out, latex_out, bib_out, log_out, status],
        )

        export_btn.click(
            fn=export_zip,
            inputs=[agent_state, export_folder],
            outputs=[agent_state, zip_file, export_msg],
        )

        # Enable export only after a run (optional: keep simple, allow after init)
        def _enable_export(agent: Optional[ClaudeWriteAgent]):
            return gr.Button(interactive=bool(agent))

        init_btn.click(fn=_enable_export, inputs=[agent_state], outputs=[export_btn])

    return demo


if __name__ == "__main__":
    demo = create_app()
    # Gradio 6+: pass css/theme into launch if your version warns; harmless otherwise.
    demo.launch(css=custom_css, theme=gr.themes.Soft())
