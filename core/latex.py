# paper_agent/core/latex.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, List

from .utils import strip_trailing_spaces


@dataclass
class LatexService:
    """
    All LaTeX-related logic lives here (moved out of UI):

      - choose best LaTeX generator (robust/body/full)
      - inject user images (if supported by agent)
      - enforce formatting rules (no subsections in Discussion/Conclusion)
      - completeness check + one robust retry
    """

    def check_latex_completeness(self, tex: str) -> List[str]:
        """
        Return missing groups. Empty list means "complete enough".

        NOTE: This preserves the original UI behavior (string containment).
        """
        content = tex or ""
        required_groups = {
            "intro": [r"\section{Introduction}"],
            "related": [r"\section{Related Work}"],
            "method": [r"\section{Methodology}", r"\section{Method}"],
            "exp": [
                r"\section{Experimental Setup and Results}",
                r"\section{Experiments and Results}",
                r"\section{Experiments}",
                r"\section{Results}",
            ],
            "discussion": [r"\section{Discussion}"],
            "conclusion": [r"\section{Conclusion}"],
            "enddoc": [r"\end{document}"],
        }

        missing: List[str] = []
        for k, candidates in required_groups.items():
            if not any(c in content for c in candidates):
                missing.append(k)
        return missing

    def strip_subsections_in_discussion_conclusion(self, tex: str) -> str:
        """Remove \\subsection and \\subsubsection inside Discussion/Conclusion sections."""
        if not tex:
            return tex

        def _process_one(section_name: str, src: str) -> str:
            pattern = (
                rf"(\\section\{{{section_name}\}})"
                rf"(.*?)"
                rf"(?=(\\section\{{)|\\end\{{document\}})"
            )
            m = re.search(pattern, src, flags=re.DOTALL)
            if not m:
                return src

            head = m.group(1)
            body = m.group(2)

            body = re.sub(r"\\subsection\{.*?\}\s*", "\n", body, flags=re.DOTALL)
            body = re.sub(r"\\subsubsection\{.*?\}\s*", "\n", body, flags=re.DOTALL)
            body = re.sub(r"\n{3,}", "\n\n", body)

            replacement = f"{head}\n\n{body.strip()}\n\n"
            start, end = m.span()
            return src[:start] + replacement + src[end:]

        tex = _process_one("Discussion", tex)
        tex = _process_one("Conclusion", tex)
        return tex

    def make_best_latex(self, agent: Any) -> str:
        """
        Replicates the UI's _make_best_latex logic.

        Priority:
          1) generate_body_only_latex_robust()
          2) generate_body_only_latex()
          3) generate_full_latex()

        Then:
          - inject images if possible
          - strip subsections in Discussion/Conclusion
          - completeness check; retry robust once
        """
        # 1) Generate base tex
        if hasattr(agent, "generate_body_only_latex_robust"):
            tex = agent.generate_body_only_latex_robust()
        elif hasattr(agent, "generate_body_only_latex"):
            tex = agent.generate_body_only_latex()
        else:
            tex = agent.generate_full_latex()

        # 2) Inject images if supported
        if hasattr(agent, "inject_user_images_into_latex") and isinstance(tex, str) and tex.strip():
            try:
                tex = agent.inject_user_images_into_latex(tex)
            except Exception:
                pass

        # 3) Enforce formatting policy
        tex = strip_trailing_spaces(tex)
        tex = self.strip_subsections_in_discussion_conclusion(tex)

        # 4) Completeness check; retry robust once
        missing = self.check_latex_completeness(tex)
        if missing and hasattr(agent, "generate_body_only_latex_robust"):
            retry_tex = agent.generate_body_only_latex_robust()

            if hasattr(agent, "inject_user_images_into_latex"):
                try:
                    retry_tex = agent.inject_user_images_into_latex(retry_tex)
                except Exception:
                    pass

            retry_tex = strip_trailing_spaces(retry_tex)
            retry_tex = self.strip_subsections_in_discussion_conclusion(retry_tex)

            if not self.check_latex_completeness(retry_tex):
                tex = retry_tex

        if isinstance(tex, str):
            agent.context.full_latex = tex
        return tex
