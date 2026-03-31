# paper_agent/core/exporter.py
from __future__ import annotations

import os
import shutil
import zipfile
from typing import Optional

from paper_agent.core.context import PaperContext


class Exporter:
    """
    Export a bundle containing:
      - paper.md
      - main.tex (or template entry tex content)
      - refs.bib
      - figures/ (user images)
    If a template project was rendered, out_dir already contains template files.
    We still ensure paper.md and refs.bib exist and finally zip the whole folder.
    """

    def export_bundle(self, ctx: PaperContext, out_dir: str) -> str:
        os.makedirs(out_dir, exist_ok=True)

        # Write paper.md
        md_path = os.path.join(out_dir, "paper.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(ctx.full_paper or "")

        # Write refs.bib
        bib_path = os.path.join(out_dir, "refs.bib")
        with open(bib_path, "w", encoding="utf-8") as f:
            f.write(ctx.bibtex or "")

        # Write main.tex (UI uses ctx.full_latex preview)
        tex_path = os.path.join(out_dir, "main.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(ctx.full_latex or "")

        # Copy user images into figures/
        if ctx.image_paths:
            fig_dir = os.path.join(out_dir, "figures")
            os.makedirs(fig_dir, exist_ok=True)
            for p in ctx.image_paths:
                if not p or not os.path.exists(p):
                    continue
                dst = os.path.join(fig_dir, os.path.basename(p))
                if os.path.abspath(p) != os.path.abspath(dst):
                    shutil.copy2(p, dst)

        # Zip
        zip_path = out_dir.rstrip(os.sep) + ".zip"
        self._make_zip(out_dir, zip_path)
        return zip_path

    def _make_zip(self, folder: str, zip_path: str) -> None:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(folder):
                for fn in files:
                    abs_path = os.path.join(root, fn)
                    rel_path = os.path.relpath(abs_path, folder)
                    z.write(abs_path, rel_path)
