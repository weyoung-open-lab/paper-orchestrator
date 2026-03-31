# paper_agent/core/checker.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class LatexCompletenessChecker:
    """
    A lightweight checker wrapper.
    If you use LatexService.check_latex_completeness already, this is optional.
    """
    required_groups: List[str]

    def check(self, missing_groups: List[str]) -> Tuple[bool, List[str]]:
        """
        Input is a list of missing group names produced by LatexService.check_latex_completeness().
        """
        missing = [g for g in missing_groups if g in set(self.required_groups)]
        return (len(missing) == 0, missing)
