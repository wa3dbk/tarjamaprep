from __future__ import annotations

import unicodedata
import uuid

import regex

from tarjamaprep.normalize.base import NormalizationRule
from tarjamaprep.normalize.registry import register
from tarjamaprep.types import Side

_PLACEHOLDER_PREFIX = "\x00PW"

_BIDI_STRIP_CHARS = (
    "\u200c\u200d\u200e\u200f"  # ZWNJ, ZWJ, LRM, RLM
    "\u202a\u202b\u202c\u202d\u202e"  # LRE, RLE, PDF, LRO, RLO
    "\u2066\u2067\u2068\u2069"  # LRI, RLI, FSI, PDI
)
_BIDI_STRIP_RE = regex.compile(f"[{_BIDI_STRIP_CHARS}]")
_ZWSP = "\u200b"
_PRES_FORMS_RE = regex.compile(r"[\uFB50-\uFDFF\uFE70-\uFEFF]")


@register
class ProtectedWords(NormalizationRule):
    name = "ar_protected"
    sides = (Side.SOURCE, Side.TARGET)
    order = 10

    def apply(self, text: str, side: Side, context: dict) -> str:
        protected = context.get("_config_protected_words", [])
        if not protected:
            return text
        mapping = context.setdefault("_protected_map", {})
        for token in protected:
            if token in text:
                placeholder = f"{_PLACEHOLDER_PREFIX}{uuid.uuid4().hex[:8]}\x00"
                mapping[placeholder] = token
                text = text.replace(token, placeholder)
        return text


@register
class RestoreProtectedWords(NormalizationRule):
    name = "ar_restore"
    sides = (Side.SOURCE, Side.TARGET)
    order = 999

    def apply(self, text: str, side: Side, context: dict) -> str:
        mapping = context.get("_protected_map", {})
        for placeholder, token in mapping.items():
            text = text.replace(placeholder, token)
        return text


@register
class ArabicPresentationForms(NormalizationRule):
    """Fold Arabic Presentation Forms (U+FB50-FDFF, U+FE70-FEFF) to the base
    Arabic block (U+0600-06FF) via NFKC, expanding LAM-ALEF ligatures. Also
    strips bidi/zero-width formatting controls commonly leaked from PDFs."""
    name = "ar_presentation_forms"
    sides = (Side.SOURCE,)
    order = 15

    def apply(self, text: str, side: Side, context: dict) -> str:
        if _BIDI_STRIP_RE.search(text):
            text = _BIDI_STRIP_RE.sub("", text)
        if _ZWSP in text:
            text = text.replace(_ZWSP, " ")
        if _PRES_FORMS_RE.search(text):
            text = _PRES_FORMS_RE.sub(
                lambda m: unicodedata.normalize("NFKC", m.group(0)), text
            )
        # Compose decomposed hamza sequences left by some encoders.
        text = text.replace("\u0627\u0655", "\u0625")  # ا + ٕ → إ
        text = text.replace("\u0627\u0654", "\u0623")  # ا + ٔ → أ
        return text


@register
class TaMarbutaSeparation(NormalizationRule):
    """Split words concatenated via ta marbuta: الحلقةالأولى → الحلقة الأولى"""
    name = "ar_ta_marbuta"
    sides = (Side.SOURCE,)
    order = 20

    _pattern = regex.compile(r"(\p{Arabic}+ة)(\p{Arabic})")

    def apply(self, text: str, side: Side, context: dict) -> str:
        return self._pattern.sub(r"\1 \2", text)


@register
class WawCollation(NormalizationRule):
    """Collate standalone و to next word: و قال → وقال"""
    name = "ar_waw_collate"
    sides = (Side.SOURCE,)
    order = 30

    _pattern = regex.compile(r"(?<=\s)و\s+(?=\p{Arabic})")

    def apply(self, text: str, side: Side, context: dict) -> str:
        result = self._pattern.sub("و", text)
        # Handle و at start of string
        if result.startswith("و "):
            rest = result[2:].lstrip()
            if rest and regex.match(r"\p{Arabic}", rest):
                result = "و" + rest
        return result


@register
class CharNormalization(NormalizationRule):
    """Normalize Arabic characters via configurable mapping."""
    name = "ar_char_norm"
    sides = (Side.SOURCE,)
    order = 40

    def apply(self, text: str, side: Side, context: dict) -> str:
        char_map = context.get("_config_char_norm_map", {})
        for src, dst in char_map.items():
            text = text.replace(src, dst)
        return text


@register
class ArabicPunctuation(NormalizationRule):
    """Normalize punctuation to Arabic equivalents on source side.

    Commas between digits (thousands separators like 1,000) are preserved.
    """
    name = "ar_punctuation"
    sides = (Side.SOURCE,)
    order = 50

    _comma_pattern = regex.compile(r"(?<!\d),|,(?!\d)")

    def apply(self, text: str, side: Side, context: dict) -> str:
        text = text.replace(";", "\u061B")
        text = text.replace("?", "\u061F")
        text = self._comma_pattern.sub("\u060C", text)
        return text
