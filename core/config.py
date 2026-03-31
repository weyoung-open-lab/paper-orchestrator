# paper_agent/core/config.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """
    Configuration for the writing agent.
    Keep anything related to LLM calling policy here.
    """
    model: str = "claude-3-5-sonnet-latest"  # adjust to your actual deployed model
    max_tokens: int = 6000
    temperature: float = 0.4

    # Continuation policy (if output is cut off)
    max_continue_rounds: int = 3

    # Safety / quality rules
    forbid_fabrication: bool = True


@dataclass
class PipelineConfig:
    """Runtime switches for the end-to-end writing pipeline."""
    gen_latex: bool = True
    do_polish: bool = True
    strict_check: bool = False
    export_dir: Optional[str] = None
