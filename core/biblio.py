# paper_agent/core/biblio.py
from __future__ import annotations

from typing import Optional, List

from paper_agent.core.context import PaperContext


def build_bibtex_prompt(ctx: PaperContext, target_n: int = 35) -> str:
    """
    Build a prompt asking LLM to output BibTeX entries ONLY.
    IMPORTANT: This is a draft generator and may hallucinate. For production,
    replace with Crossref/OpenAlex retrieval.
    """
    seed = (ctx.seed_references or "").strip()

    return f"""
You are a bibliographic assistant.

Task:
- Generate a BibTeX file with about {target_n} entries relevant to the described paper.
- Output BibTeX ONLY. No markdown fences. No commentary.
- Use consistent citekeys (e.g., AuthorYearKeyword).
- Prefer peer-reviewed papers, surveys, and widely cited works.
- If seed references are provided, include them (as best as possible).

Paper description:
{ctx.project_description}

Method / key code summary:
{ctx.model_method}

Experiment / data setup:
{ctx.experiment_data}

Seed references (optional):
{seed}

Output requirements:
- Output ONLY valid BibTeX entries (e.g., @article, @inproceedings, @book).
- Each entry must include at least: title, author, year.
- Include DOI when known.
""".strip()


def build_bibtex_via_llm(llm_generate_fn, ctx: PaperContext, target_n: int = 35) -> str:
    """
    llm_generate_fn(system: str, user: str, image_paths: list[str]) -> str
    """
    user = build_bibtex_prompt(ctx, target_n=target_n)
    # system prompt can be the same as writing system prompt, but it's better to keep it strict
    system = "You output strictly BibTeX entries only."
    out = llm_generate_fn(system, user, [])
    return (out or "").strip()
