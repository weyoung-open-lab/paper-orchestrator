# paper_agent/core/pipeline.py
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from typing import Optional

from paper_agent.core.config import PipelineConfig
from paper_agent.core.agent import ClaudeWriteAgent
from paper_agent.core.latex import LatexService
from paper_agent.core.exporter import Exporter

from paper_agent.core.biblio import build_bibtex_via_llm
from paper_agent.core.templates.loader import load_template
from paper_agent.core.templates.renderer import render_into_template


@dataclass
class PipelineResult:
    paper_md: str = ""
    latex: str = ""
    bibtex: str = ""
    log: str = ""
    errors: str = ""


class PaperPipeline:
    """
    Orchestrates generation:
      outline -> sections -> full paper -> polish -> latex -> bibtex -> render into template
    """

    def __init__(self, agent: ClaudeWriteAgent, latex_service: LatexService, exporter: Exporter):
        self.agent = agent
        self.latex_service = latex_service
        self.exporter = exporter

    def run(self, cfg: PipelineConfig) -> PipelineResult:
        res = PipelineResult()
        logs = []

        try:
            logs.append("1) Generating outline/framework...")
            self.agent.generate_framework()

            logs.append("2) Generating sections...")
            self.agent.generate_abstract()
            self.agent.generate_introduction()
            self.agent.generate_related_work()
            self.agent.generate_method()
            self.agent.generate_experiment()
            self.agent.generate_discussion()
            self.agent.generate_conclusion()

            logs.append("3) Integrating full paper...")
            self.agent.generate_full_paper()

            if cfg.do_polish:
                logs.append("4) Polishing full paper...")
                self.agent.polish_full_paper()

            # --- BibTeX (NEW) ---
            logs.append("5) Generating BibTeX (draft, please verify)...")
            bibtex = build_bibtex_via_llm(self.agent.llm.generate, self.agent.context, target_n=35)
            self.agent.context.bibtex = bibtex
            res.bibtex = bibtex

            # --- LaTeX ---
            if cfg.gen_latex:
                logs.append("6) Generating LaTeX body...")
                body = self.agent.generate_body_only_latex_robust()
                body = self.agent.inject_user_images_into_latex(body)

                # --- Template render (NEW) ---
                if self.agent.context.template_zip_path:
                    logs.append("7) Rendering into journal template...")
                    with tempfile.TemporaryDirectory(prefix="tmpl_") as tmp:
                        spec = load_template(self.agent.context.template_zip_path, work_dir=tmp)

                        # choose bib style: best-effort, if template has many bst, user can add UI later
                        # For now keep None; template itself may already specify bst, or we insert without style.
                        out_dir = cfg.export_dir or os.path.join(os.getcwd(), "output_project")
                        entry_tex_path = render_into_template(
                            spec=spec,
                            latex_body=body,
                            bibtex=bibtex,
                            out_dir=out_dir,
                            bib_style=None,
                            bib_filename="refs.bib",
                        )
                        logs.append(f"   Template entry tex: {entry_tex_path}")
                        # Store final latex as the rendered entry file content (for UI preview)
                        try:
                            with open(entry_tex_path, "r", encoding="utf-8", errors="ignore") as f:
                                self.agent.context.full_latex = f.read()
                        except Exception:
                            self.agent.context.full_latex = body
                else:
                    logs.append("7) No template zip provided, building generic full LaTeX...")
                    # fallback: wrap into generic preamble
                    tex = self.agent._default_latex_preamble() + "\n" + body + "\n\\end{document}\n"
                    self.agent.context.full_latex = tex

                res.latex = self.agent.context.full_latex

            res.paper_md = self.agent.context.full_paper
            res.log = "\n".join(logs)
            return res

        except Exception as e:
            res.errors = str(e)
            res.log = "\n".join(logs)
            return res
