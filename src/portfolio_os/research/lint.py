from __future__ import annotations

import re


FORBIDDEN_RECOMMENDATION_PATTERNS: tuple[str, ...] = (
    r"\bshould\s+buy\b",
    r"\bshould\s+sell\b",
    r"\bbuy\b",
    r"\bsell\b",
    r"\brecommend(?:ation|ed|s)?\b",
    r"\baccumulate\b",
    r"\btrim\b",
    r"\boverweight\b",
    r"\bunderweight\b",
    r"\btarget\s+price\b",
    r"\bfair\s+value\b",
    r"\bposition\s+siz(?:e|ing)\b",
    r"\border\s+ticket\b",
    r"\bapprove\b",
    r"\bexecute\b",
    r"매수",
    r"매도",
    r"추천",
    r"비중\s*확대",
    r"비중\s*축소",
    r"목표가",
    r"적정가",
)


class ResearchLintService:
    def __init__(self, patterns: tuple[str, ...] = FORBIDDEN_RECOMMENDATION_PATTERNS) -> None:
        self.patterns = patterns

    def find_forbidden_language(self, text: str | None) -> tuple[str, ...]:
        if not text:
            return ()
        hits: list[str] = []
        for pattern in self.patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(pattern)
        return tuple(hits)
