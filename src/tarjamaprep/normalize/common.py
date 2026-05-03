from __future__ import annotations

import regex

from tarjamaprep.normalize.base import NormalizationRule
from tarjamaprep.normalize.registry import register
from tarjamaprep.types import Side


@register
class EmojiRemoval(NormalizationRule):
    """Remove all emoji characters."""
    name = "common_emoji"
    sides = (Side.SOURCE, Side.TARGET)
    order = 60

    # Match emoji and various symbol blocks
    _pattern = regex.compile(
        r"[\U0001F600-\U0001F64F"  # emoticons
        r"\U0001F300-\U0001F5FF"   # misc symbols & pictographs
        r"\U0001F680-\U0001F6FF"   # transport & map
        r"\U0001F1E0-\U0001F1FF"   # flags
        r"\U0001F900-\U0001F9FF"   # supplemental symbols
        r"\U0001FA00-\U0001FA6F"   # chess symbols
        r"\U0001FA70-\U0001FAFF"   # symbols extended-A
        r"\U00002702-\U000027B0"   # dingbats
        r"\U0000FE00-\U0000FE0F"   # variation selectors
        r"\U0000200D"              # ZWJ
        r"\U000023F0-\U000023FA"   # misc technical
        r"\U0000203C\U00002049"    # double exclamation, exclamation question
        r"]+",
    )

    def apply(self, text: str, side: Side, context: dict) -> str:
        return self._pattern.sub("", text)


@register
class UselessSymbolRemoval(NormalizationRule):
    """Remove symbols not in the final allowed set."""
    name = "common_symbols"
    sides = (Side.SOURCE, Side.TARGET)
    order = 65

    def apply(self, text: str, side: Side, context: dict) -> str:
        # Remove common useless symbols: ★ ♦ ● ♥ ■ □ ▪ ♪ ♫ © ® ™ etc.
        text = regex.sub(
            r"[★☆♦♥♠♣●○■□▪▫▲▼►◄♪♫©®™†‡§¶¤¬¦¡¿±×÷µ~`|\\]",
            "",
            text,
        )
        return text


@register
class ExcessiveRepetition(NormalizationRule):
    """Collapse 3+ consecutive identical characters to 2."""
    name = "common_repetition"
    sides = (Side.SOURCE, Side.TARGET)
    order = 70

    _pattern = regex.compile(r"(.)\1{2,}")

    def apply(self, text: str, side: Side, context: dict) -> str:
        return self._pattern.sub(r"\1\1", text)


@register
class NumeralConversion(NormalizationRule):
    """Convert Eastern Arabic and Persian numerals to Western 0-9."""
    name = "common_numerals"
    sides = (Side.SOURCE, Side.TARGET)
    order = 75

    # Eastern Arabic ٠١٢٣٤٥٦٧٨٩
    _eastern = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    # Persian/Urdu ۰۱۲۳۴۵۶۷۸۹
    _persian = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

    def apply(self, text: str, side: Side, context: dict) -> str:
        text = text.translate(self._eastern)
        text = text.translate(self._persian)
        return text


@register
class PunctuationNormalization(NormalizationRule):
    """Normalize quotes and drop brackets/parentheses."""
    name = "common_punctuation"
    sides = (Side.SOURCE, Side.TARGET)
    order = 80

    _quote_map = {
        "\u00AB": '"',  # «
        "\u00BB": '"',  # »
        "\u201E": '"',  # „
        "\u201C": '"',  # "
        "\u201D": '"',  # "
        "\u2018": "'",  # '
        "\u2019": "'",  # '
        "\u2039": "'",  # ‹
        "\u203A": "'",  # ›
        "\u0060": "'",  # `
        "\u00B4": "'",  # ´
    }

    def apply(self, text: str, side: Side, context: dict) -> str:
        for src, dst in self._quote_map.items():
            text = text.replace(src, dst)
        # Drop brackets, parentheses, braces (but not protected words)
        text = regex.sub(r"[\[\](){}]", "", text)
        # Normalize dashes to simple hyphen
        text = regex.sub(r"[\u2013\u2014\u2015\u2212]", "-", text)
        return text


@register
class WhitespaceNormalization(NormalizationRule):
    """Normalize whitespace on both sides."""
    name = "common_whitespace"
    sides = (Side.SOURCE, Side.TARGET)
    order = 90

    def apply(self, text: str, side: Side, context: dict) -> str:
        text = regex.sub(r"[\u00A0\u2000-\u200B\u202F\u205F\u3000\uFEFF]", " ", text)
        text = regex.sub(r" {2,}", " ", text)
        return text.strip()


@register
class FinalCharFilter(NormalizationRule):
    """Strip any character not in the allowed set.

    Allowed: Arabic script, Latin script, digits, currency symbols,
    %, °, and basic punctuation (. , ; : ? ! " ' -).
    Arabic-specific punctuation (، ؛ ؟) is also allowed.
    Protected word placeholders are preserved (handled by restore rule at order=999).
    """
    name = "common_final_filter"
    sides = (Side.SOURCE, Side.TARGET)
    order = 200

    # Keep: Arabic, Latin, Cyrillic, CJK, digits, spaces, currency, %, °,
    # basic punct, Arabic punct, hyphens, protected placeholders
    _pattern = regex.compile(
        r"[^\p{Arabic}\p{Latin}\p{Cyrillic}\p{Han}\p{Hiragana}\p{Katakana}\d\s"
        r"$€£¥₹₽¢%°"
        r".,;:?!\"'\-"
        r"\u060C\u061B\u061F"  # ، ؛ ؟
        r"\x00"  # placeholder delimiter
        r"]"
    )

    def apply(self, text: str, side: Side, context: dict) -> str:
        text = self._pattern.sub("", text)
        # Clean up any resulting multiple spaces
        text = regex.sub(r" {2,}", " ", text)
        return text.strip()
