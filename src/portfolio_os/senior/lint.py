from __future__ import annotations

import re


FORBIDDEN_EXECUTION_LANGUAGE: tuple[str, ...] = (
    r"\bexecute\s+this\s+order\b",
    r"\bplace\s+order\s+now\b",
    r"\bapproved\s+order\b",
    r"\brisk\s+validated\b",
    r"\bguaranteed\b",
    r"\bmust\s+buy\b",
    r"\bmust\s+sell\b",
    r"\bautomatic\s+execution\b",
    r"\bskip\s+risk\s+validation\b",
    r"\bbypass\s+risk\b",
    r"\bignore\s+ledger\s+status\b",
)


class SeniorMemoLintService:
    def __init__(self, patterns: tuple[str, ...] = FORBIDDEN_EXECUTION_LANGUAGE) -> None:
        self.patterns = patterns

    def find_forbidden_execution_language(self, text: str | None) -> tuple[str, ...]:
        if not text:
            return ()
        hits: list[str] = []
        for pattern in self.patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(pattern)
        return tuple(hits)
