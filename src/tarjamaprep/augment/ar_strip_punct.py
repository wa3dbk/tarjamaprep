from __future__ import annotations

import random

import regex as re

from tarjamaprep.augment.base import AugmentationStrategy
from tarjamaprep.augment.registry import register
from tarjamaprep.types import SentencePair, TargetLang


_AR_PUNCT_RE = re.compile(r"[.,!?;:\"'\u060C\u061B\u061F\u06D4\-]+")
_WS_RE = re.compile(r"\s+")


def _strip_arabic_punct(text: str) -> str:
    out = _AR_PUNCT_RE.sub(" ", text)
    out = _WS_RE.sub(" ", out).strip()
    return out


@register
class ArabicStripPunct(AugmentationStrategy):
    """Emit a duplicate pair with Arabic-side punctuation stripped."""
    name = "ar_strip_punct"
    description = "Duplicate pair with Arabic-side punctuation stripped (target intact)"

    sample_rate: float = 0.4

    def augment(
        self,
        pair: SentencePair,
        target_lang: TargetLang,
        count: int,
        rng: random.Random,
    ) -> list[SentencePair]:
        if rng.random() >= self.sample_rate:
            return []
        stripped = _strip_arabic_punct(pair.source)
        if not stripped or stripped == pair.source:
            return []
        return [SentencePair(
            source=stripped,
            target=pair.target,
            line_number=pair.line_number,
        )]
