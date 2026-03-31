# paper_agent/core/agent.py
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from paper_agent.core.context import PaperContext
from paper_agent.llm.anthropic_client import AnthropicClient, LLMConfig
from paper_agent.llm.prompts import DEFAULT_PROMPTS


class ClaudeWriteAgent:
    """
    Paper-writing agent that:
      - Generates sections (outline/abstract/intro/...)
      - Integrates them into a full paper draft
      - Produces LaTeX (body-only robust, or full latex)
      - Injects user images into LaTeX

    Prompts live in: paper_agent/llm/prompts.py
    LLM calling lives in: paper_agent/llm/anthropic_client.py
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        language: str = "English",
        temperature: float = 0.4,
        max_tokens: int = 4000,
        max_continue_rounds: int = 3,
        base_url: Optional[str] = None,
    ):
        self.context = PaperContext()
        self.language = language  # "English" or "中文"
        self.prompts = DEFAULT_PROMPTS

        llm_cfg = LLMConfig(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_continue_rounds=max_continue_rounds,
        )
        self.llm = AnthropicClient(api_key=api_key, base_url=base_url, cfg=llm_cfg)

        # Keep your original length policies (same spirit; easy to tweak)
        self.min_lengths = {
            "framework": {"en": 400, "zh": 600},
            "abstract": {"en": 150, "zh": 260},
            "introduction": {"en": 900, "zh": 1400},
            "related_work": {"en": 1000, "zh": 1600},
            "method": {"en": 1200, "zh": 1800},
            "experiment": {"en": 1200, "zh": 1800},
            "discussion": {"en": 800, "zh": 1200},
            "conclusion": {"en": 350, "zh": 500},
        }
        self.max_lengths = {
            "abstract": {"en": 280, "zh": 420},
            "introduction": {"en": 2200, "zh": 3200},
            "related_work": {"en": 2400, "zh": 3600},
            "method": {"en": 3000, "zh": 4500},
            "experiment": {"en": 3000, "zh": 4500},
            "discussion": {"en": 2000, "zh": 3000},
            "conclusion": {"en": 900, "zh": 1300},
        }

    # ----------------------------
    # Basic setters / helpers
    # ----------------------------

    def set_language(self, language: str) -> None:
        if language in ("English", "中文"):
            self.language = language

    def add_project_info(
        self,
        project_description: str,
        model_method: str,
        experiment_data: str,
        seed_references: str = "",
        figures: Optional[List[Dict]] = None,
        image_paths: Optional[List[str]] = None,
        reference_papers: Optional[List[str]] = None,
    ) -> None:
        self.context.project_description = project_description or ""
        self.context.model_method = model_method or ""
        self.context.experiment_data = experiment_data or ""
        self.context.seed_references = seed_references or ""
        self.context.figures = figures or []
        self.context.image_paths = image_paths or []
        self.context.reference_papers = reference_papers or []

    def _lang_key(self) -> str:
        return "zh" if self.language == "中文" else "en"

    def _system(self) -> str:
        return self.prompts.system_zh if self.language == "中文" else self.prompts.system_en

    def _tmpl(self, key: str) -> str:
        t = self.prompts.templates_zh if self.language == "中文" else self.prompts.templates_en
        if key not in t:
            raise KeyError(f"Prompt template '{key}' not found in prompts.py")
        return t[key]

    def _format(self, key: str, **kwargs) -> str:
        # Ensure all placeholders exist (safe defaults)
        defaults = dict(
            project_description=self.context.project_description,
            model_method=self.context.model_method,
            experiment_data=self.context.experiment_data,
            seed_references=self.context.seed_references,
            full_paper=self.context.full_paper,
        )
        defaults.update(kwargs)
        return self._tmpl(key).format(**defaults)

    def _length_guard(self, section: str, text: str) -> str:
        """
        Best-effort length control:
          - If too short => ask to expand
          - If too long  => ask to compress
        """
        if not text:
            return text

        key = self._lang_key()
        min_len = self.min_lengths.get(section, {}).get(key)
        max_len = self.max_lengths.get(section, {}).get(key)

        n = len(text)
        # Expand if too short
        if min_len and n < min_len:
            expand_prompt = (
                f"Expand the following {section} section to meet academic standards. "
                f"Keep consistent with provided content. Do not fabricate.\n\n{text}"
                if self.language != "中文"
                else f"请扩写以下{section}部分，使其达到学术论文标准，保持内容一致，不要编造：\n\n{text}"
            )
            text = self.llm.generate(
                system=self._system(),
                user=expand_prompt,
                image_paths=self.context.image_paths,
            )

        # Compress if too long
        if max_len and len(text) > max_len:
            compress_prompt = (
                f"Compress the following {section} section to be concise while retaining key points. "
                f"Do not fabricate.\n\n{text}"
                if self.language != "中文"
                else f"请精炼以下{section}部分，保留关键点，不要编造：\n\n{text}"
            )
            text = self.llm.generate(
                system=self._system(),
                user=compress_prompt,
                image_paths=self.context.image_paths,
            )

        return text

    # ----------------------------
    # Section generation (names kept)
    # ----------------------------

    def generate_framework(self) -> str:
        out = self.llm.generate(self._system(), self._format("outline"), image_paths=self.context.image_paths)
        out = self._length_guard("framework", out)
        self.context.framework = out
        return out

    def generate_abstract(self) -> str:
        out = self.llm.generate(self._system(), self._format("abstract"), image_paths=self.context.image_paths)
        out = self._length_guard("abstract", out)
        self.context.abstract = out
        return out

    def generate_introduction(self) -> str:
        out = self.llm.generate(self._system(), self._format("introduction"), image_paths=self.context.image_paths)
        out = self._length_guard("introduction", out)
        self.context.introduction = out
        return out

    def generate_related_work(self) -> str:
        out = self.llm.generate(self._system(), self._format("related_work"), image_paths=self.context.image_paths)
        out = self._length_guard("related_work", out)
        self.context.related_work = out
        return out

    def generate_method(self) -> str:
        out = self.llm.generate(self._system(), self._format("method"), image_paths=self.context.image_paths)
        out = self._length_guard("method", out)
        self.context.method = out
        return out

    def generate_experiment(self) -> str:
        out = self.llm.generate(self._system(), self._format("experiments"), image_paths=self.context.image_paths)
        out = self._length_guard("experiment", out)
        self.context.experiment = out
        return out

    def generate_discussion(self) -> str:
        out = self.llm.generate(self._system(), self._format("discussion"), image_paths=self.context.image_paths)
        out = self._length_guard("discussion", out)
        self.context.discussion = out
        return out

    def generate_conclusion(self) -> str:
        out = self.llm.generate(self._system(), self._format("conclusion"), image_paths=self.context.image_paths)
        out = self._length_guard("conclusion", out)
        self.context.conclusion = out
        return out

    def generate_references(self) -> str:
        out = self.llm.generate(self._system(), self._format("references"), image_paths=self.context.image_paths)
        self.context.references_list = out
        return out

    # ----------------------------
    # Integration / polish
    # ----------------------------

    def generate_full_paper(self) -> str:
        """
        Keep the same integrated structure you used before.
        """
        if self.language == "中文":
            paper = (
                f"{self.context.framework}\n\n"
                f"\\section*{{摘要}}\n{self.context.abstract}\n\n"
                f"\\section{{Introduction}}\n{self.context.introduction}\n\n"
                f"\\section{{Related Work}}\n{self.context.related_work}\n\n"
                f"\\section{{Methodology}}\n{self.context.method}\n\n"
                f"\\section{{Experiments}}\n{self.context.experiment}\n\n"
                f"\\section{{Discussion}}\n{self.context.discussion}\n\n"
                f"\\section{{Conclusion}}\n{self.context.conclusion}\n\n"
                f"\\section*{{References}}\n{self.context.references_list}\n"
            )
        else:
            paper = (
                f"{self.context.framework}\n\n"
                f"\\section*{{Abstract}}\n{self.context.abstract}\n\n"
                f"\\section{{Introduction}}\n{self.context.introduction}\n\n"
                f"\\section{{Related Work}}\n{self.context.related_work}\n\n"
                f"\\section{{Methodology}}\n{self.context.method}\n\n"
                f"\\section{{Experiments}}\n{self.context.experiment}\n\n"
                f"\\section{{Discussion}}\n{self.context.discussion}\n\n"
                f"\\section{{Conclusion}}\n{self.context.conclusion}\n\n"
                f"\\section*{{References}}\n{self.context.references_list}\n"
            )

        self.context.full_paper = paper
        return paper

    def polish_full_paper(self) -> str:
        if not self.context.full_paper:
            self.generate_full_paper()

        user = self._format("polish_full", full_paper=self.context.full_paper)
        out = self.llm.generate(self._system(), user, image_paths=self.context.image_paths)
        if out.strip():
            self.context.full_paper = out
        return self.context.full_paper

    # ----------------------------
    # LaTeX generation (kept)
    # ----------------------------

    def _default_latex_preamble(self) -> str:
        return r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=1in]{geometry}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{url}
\usepackage{hyperref}
\usepackage{caption}
\usepackage{subcaption}
\begin{document}
"""

    def generate_full_latex(self) -> str:
        """
        Convert full paper (already has \\section etc.) to a compilable LaTeX file.
        """
        if not self.context.full_paper:
            self.generate_full_paper()

        tex = self._default_latex_preamble() + "\n" + (self.context.full_paper or "") + "\n\\end{document}\n"
        self.context.full_latex = tex
        return tex

    def generate_body_only_latex(self) -> str:
        """
        Use LLM to convert the full paper into LaTeX body only.
        """
        if not self.context.full_paper:
            self.generate_full_paper()

        user = self._format("latex_body", full_paper=self.context.full_paper)
        out = self.llm.generate(self._system(), user, image_paths=self.context.image_paths)
        self.context.full_latex = out
        return out

    def generate_body_only_latex_robust(self) -> str:
        """
        Robust strategy: convert each section separately to LaTeX and then merge.
        This keeps the same spirit as your original robust function.
        """
        # Ensure sections exist
        if not self.context.abstract:
            self.generate_abstract()
        if not self.context.introduction:
            self.generate_introduction()
        if not self.context.related_work:
            self.generate_related_work()
        if not self.context.method:
            self.generate_method()
        if not self.context.experiment:
            self.generate_experiment()
        if not self.context.discussion:
            self.generate_discussion()
        if not self.context.conclusion:
            self.generate_conclusion()
        if not self.context.references_list:
            self.generate_references()

        blocks = [
            ("Abstract", self.context.abstract, True),
            ("Introduction", self.context.introduction, False),
            ("Related Work", self.context.related_work, False),
            ("Methodology", self.context.method, False),
            ("Experiments", self.context.experiment, False),
            ("Discussion", self.context.discussion, False),
            ("Conclusion", self.context.conclusion, False),
            ("References", self.context.references_list, True),
        ]

        parts: List[str] = []
        for title, txt, starred in blocks:
            if not (txt or "").strip():
                continue

            if self.language == "中文":
                user = (
                    f"请把以下内容转换成 LaTeX 段落（仅正文，不包含documentclass/begin/end）。\n\n"
                    f"章节标题：{title}\n\n内容：\n{txt}\n"
                )
            else:
                user = (
                    f"Convert the following content to LaTeX for section '{title}'. "
                    f"Output LaTeX ONLY (no documentclass/begin/end).\n\nContent:\n{txt}\n"
                )

            sec_tex = self.llm.generate(self._system(), user, image_paths=self.context.image_paths)

            if starred:
                parts.append(f"\\section*{{{title}}}\n{sec_tex}\n")
            else:
                parts.append(f"\\section{{{title}}}\n{sec_tex}\n")

        merged = "\n".join(parts).strip()
        self.context.full_latex = merged
        return merged

    def inject_user_images_into_latex(self, tex: str) -> str:
        """
        Inject user images as a dedicated Figures section.
        The exporter will copy images into figures/ folder.
        """
        if not tex or not (self.context.image_paths or []):
            return tex

        figure_blocks: List[str] = []
        for i, p in enumerate(self.context.image_paths):
            if not p:
                continue
            name = os.path.basename(p)

            cap = ""
            if i < len(self.context.figures) and isinstance(self.context.figures[i], dict):
                cap = self.context.figures[i].get("description", "") or ""
            if not cap:
                cap = f"Figure {i+1}."

            block = (
                "\\begin{figure}[t]\n"
                "\\centering\n"
                f"\\includegraphics[width=0.85\\linewidth]{{figures/{name}}}\n"
                f"\\caption{{{cap}}}\n"
                f"\\label{{fig:{i+1}}}\n"
                "\\end{figure}\n"
            )
            figure_blocks.append(block)

        if not figure_blocks:
            return tex

        fig_section = "\\section*{Figures}\n" + "\n".join(figure_blocks) + "\n"

        # Insert figures before References if possible
        if "\\section*{References}" in tex:
            return tex.replace("\\section*{References}", fig_section + "\n\\section*{References}")
        if "\\section{References}" in tex:
            return tex.replace("\\section{References}", fig_section + "\n\\section{References}")

        return tex + "\n\n" + fig_section

    def print_length_report(self) -> str:
        key = self._lang_key()
        parts = {
            "framework": self.context.framework,
            "abstract": self.context.abstract,
            "introduction": self.context.introduction,
            "related_work": self.context.related_work,
            "method": self.context.method,
            "experiment": self.context.experiment,
            "discussion": self.context.discussion,
            "conclusion": self.context.conclusion,
        }
        lines = []
        for k, v in parts.items():
            n = len(v or "")
            mn = self.min_lengths.get(k, {}).get(key)
            mx = self.max_lengths.get(k, {}).get(key)
            lines.append(f"{k}: len={n} (min={mn}, max={mx})")
        return "\n".join(lines)
