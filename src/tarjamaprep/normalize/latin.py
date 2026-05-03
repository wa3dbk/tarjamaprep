from __future__ import annotations

import regex

from tarjamaprep.normalize.base import NormalizationRule
from tarjamaprep.normalize.registry import register
from tarjamaprep.types import Side


@register
class LatinWhitespaceNorm(NormalizationRule):
    """Normalize whitespace and fix common encoding issues in Latin text."""
    name = "lat_whitespace"
    sides = (Side.TARGET,)
    order = 20

    def apply(self, text: str, side: Side, context: dict) -> str:
        # Normalize various unicode spaces to regular space
        text = regex.sub(r"[\u00A0\u2000-\u200B\u202F\u205F\u3000\uFEFF]", " ", text)
        # Collapse multiple spaces
        text = regex.sub(r" {2,}", " ", text)
        return text.strip()
