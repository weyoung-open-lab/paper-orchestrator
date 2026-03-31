# paper_agent/core/utils.py
from __future__ import annotations

import os
from typing import Optional


def ensure_dir(path: str) -> None:
    """Create directory if it does not exist."""
    if not path:
        return
    os.makedirs(path, exist_ok=True)


def safe_write_text(path: str, content: str) -> None:
    """Write UTF-8 text safely."""
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content or "")


def normalize_newlines(text: str) -> str:
    """Normalize newline styles to Unix newlines."""
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def strip_trailing_spaces(text: str) -> str:
    """Remove trailing spaces on each line."""
    return "\n".join([ln.rstrip() for ln in normalize_newlines(text).split("\n")])
