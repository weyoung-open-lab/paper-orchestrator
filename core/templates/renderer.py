# paper_agent/core/templates/renderer.py
from __future__ import annotations

import os
import shutil
from typing import Optional

from .loader import TemplateSpec


def _ensure_bib_hook(entry_tex_text: str, bib_filename_no_ext: str = "refs", bib_style: Optional[str] = None) -> str:
    """
    Ensure bibliography commands exist.
    This is a best-effort BibTeX hook:
      \\bibliographystyle{...}
      \\bibliography{refs}
    We insert them before \\end{document} if not present.
    """
    s = entry_tex_text

    has_bibliography = "\\bibliography{" in s
    if has_bibliography:
        return s

    bib_block = []
    if bib_style:
        bib_block.append(f"\\bibliographystyle{{{bib_style}}}")
    bib_block.append(f"\\bibliography{{{bib_filename_no_ext}}}")
    block = "\n" + "\n".join(bib_block) + "\n"

    if "\\end{document}" in s:
        s = s.replace("\\end{document}", block + "\\end{document}")
    else:
        s = s + block
    return s


def render_into_template(
    spec: TemplateSpec,
    latex_body: str,
    bibtex: str,
    out_dir: str,
    bib_style: Optional[str] = None,
    bib_filename: str = "refs.bib",
) -> str:
    """
    Copy template project to out_dir, then inject latex_body and write refs.bib.
    Returns the path to the new entry tex in out_dir.
    """
    os.makedirs(out_dir, exist_ok=True)

    # Copy entire template directory
    # (If you want to avoid copying large PDFs, you can filter later.)
    if os.path.abspath(out_dir) != os.path.abspath(spec.template_dir):
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        shutil.copytree(spec.template_dir, out_dir)

    # Locate entry tex in copied dir (same relative path)
    rel_entry = os.path.relpath(spec.entry_tex, spec.template_dir)
    out_entry = os.path.join(out_dir, rel_entry)

    with open(out_entry, "r", encoding="utf-8", errors="ignore") as f:
        tex = f.read()

    # Inject body
    if spec.insert_marker:
        tex = tex.replace(spec.insert_marker, latex_body)
    else:
        # Insert after \begin{document}
        token = "\\begin{document}"
        if token in tex:
            tex = tex.replace(token, token + "\n\n" + latex_body + "\n\n", 1)
        else:
            # Worst-case: append
            tex = tex + "\n\n" + latex_body + "\n\n"

    # Ensure bibliography hook (BibTeX)
    tex = _ensure_bib_hook(tex, bib_filename_no_ext=os.path.splitext(bib_filename)[0], bib_style=bib_style)

    with open(out_entry, "w", encoding="utf-8") as f:
        f.write(tex)

    # Write bib
    out_bib = os.path.join(out_dir, bib_filename)
    with open(out_bib, "w", encoding="utf-8") as f:
        f.write(bibtex or "")

    return out_entry
