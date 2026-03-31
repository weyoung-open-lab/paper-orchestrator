# paper_agent/core/context.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class PaperContext:
    """
    Shared state container used across UI / pipeline / agent / exporter.

    Keep fields explicit and easy to inspect.
    """
    # User inputs
    project_description: str = ""
    model_method: str = ""
    experiment_data: str = ""
    seed_references: str = ""

    # Optional figures metadata: [{"description": "..."}]
    figures: List[Dict] = field(default_factory=list)

    # Local paths of uploaded images
    image_paths: List[str] = field(default_factory=list)

    # ---- Journal template (NEW) ----
    # Path to uploaded template zip (from Gradio)
    template_zip_path: Optional[str] = None
    # Where the template zip is extracted
    template_dir: Optional[str] = None

    # Generated sections
    framework: str = ""
    abstract: str = ""
    introduction: str = ""
    related_work: str = ""
    method: str = ""
    experiment: str = ""
    discussion: str = ""
    conclusion: str = ""
    references_list: str = ""  # human-readable refs list (optional)

    # BibTeX output (NEW)
    bibtex: str = ""

    # Final outputs
    full_paper: str = ""   # integrated text/latex-ish
    full_latex: str = ""   # final compilable latex (either template-rendered or generic)
