from __future__ import annotations

import random

import regex as re

from tarjamaprep.augment.base import AugmentationStrategy
from tarjamaprep.augment.registry import register
from tarjamaprep.types import SentencePair, TargetLang


_HAMZA_MAP = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا"})
_CONSONANT_MAP = str.maketrans({"ة": "ه", "ظ": "ض", "ذ": "د", "ث": "ت"})
_FINAL_YA_RE = re.compile(r"ي(?=\s|$)")


def _dialect_shift(text: str) -> str:
    out = text.translate(_HAMZA_MAP)
    out = out.translate(_CONSONANT_MAP)
    out = _FINAL_YA_RE.sub("ى", out)
    return out


@register
class ArabicDialectShift(AugmentationStrategy):
    """Emit a duplicate pair with ASR/dialect-flattened Arabic side."""
    name = "ar_dialect_shift"
    description = "Duplicate pair with hamza/ta-marbuta/final-ya/emphatic flattening on Arabic side"

    sample_rate: float = 0.3

    def augment(
        self,
        pair: SentencePair,
        target_lang: TargetLang,
        count: int,
        rng: random.Random,
    ) -> list[SentencePair]:
        if rng.random() >= self.sample_rate:
            return []
        shifted = _dialect_shift(pair.source)
        if not shifted or shifted == pair.source:
            return []
        return [SentencePair(
            source=shifted,
            target=pair.target,
            line_number=pair.line_number,
        )]
