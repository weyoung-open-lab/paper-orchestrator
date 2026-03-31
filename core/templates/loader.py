# paper_agent/core/templates/loader.py
from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class TemplateSpec:
    """
    Represents an extracted LaTeX template project.
    """
    template_dir: str
    entry_tex: str            # absolute path to entry .tex
    insert_marker: Optional[str] = None  # if marker exists, we replace it; else we insert after \begin{document}


def _find_tex_candidates(root: str) -> List[str]:
    cands = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".tex"):
                cands.append(os.path.join(dirpath, fn))
    return cands


def _looks_like_entry_tex(tex_path: str) -> bool:
    try:
        with open(tex_path, "r", encoding="utf-8", errors="ignore") as f:
            s = f.read(20000)
        return ("\\documentclass" in s) and ("\\begin{document}" in s)
    except Exception:
        return False


def extract_template_zip(zip_path: str, out_dir: str) -> str:
    """
    Extract template zip to out_dir (created if needed). Return extracted folder.
    """
    os.makedirs(out_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(out_dir)
    return out_dir


def load_template(zip_path: str, work_dir: str, insert_marker: Optional[str] = "% === PAPER_AGENT_CONTENT ===") -> TemplateSpec:
    """
    1) Extract zip
    2) Identify entry tex: first tex that contains \\documentclass and \\begin{document}
    3) Set marker (optional). If marker isn't present, we will insert after \\begin{document}.
    """
    extracted = extract_template_zip(zip_path, work_dir)

    tex_files = _find_tex_candidates(extracted)
    entry = None
    for p in tex_files:
        if _looks_like_entry_tex(p):
            entry = p
            break

    # Fallback: if none looks like entry, try common names
    if entry is None:
        for name in ("main.tex", "sn-article.tex", "template.tex"):
            p = os.path.join(extracted, name)
            if os.path.exists(p):
                entry = p
                break

    if entry is None:
        raise FileNotFoundError("Could not find an entry .tex file (with \\documentclass and \\begin{document}).")

    # Check marker presence
    marker = insert_marker
    try:
        with open(entry, "r", encoding="utf-8", errors="ignore") as f:
            s = f.read()
        if marker and (marker not in s):
            marker = None
    except Exception:
        marker = None

    return TemplateSpec(template_dir=extracted, entry_tex=entry, insert_marker=marker)
