from __future__ import annotations

import uuid

import regex

from tarjamaprep.normalize.base import NormalizationRule
from tarjamaprep.normalize.registry import register
from tarjamaprep.types import Side

_PLACEHOLDER_PREFIX = "\x00PW"


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
    """Normalize punctuation to Arabic equivalents on source side."""
    name = "ar_punctuation"
    sides = (Side.SOURCE,)
    order = 50

    _map = {
        ";": "\u061B",  # ؛
        "?": "\u061F",  # ؟
        ",": "\u060C",  # ،
    }

    def apply(self, text: str, side: Side, context: dict) -> str:
        for latin, arabic in self._map.items():
            text = text.replace(latin, arabic)
        return text
