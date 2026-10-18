from __future__ import annotations

from functools import lru_cache

import regex

from tarjamaprep.normalize.base import NormalizationRule
from tarjamaprep.normalize.registry import register
from tarjamaprep.types import Side


_DEFAULT_EXTRA_PUNCT_STRIP = frozenset(';:"')


@lru_cache(maxsize=16)
def _extra_strip_pattern(chars: str):
    if not chars:
        return None
    return regex.compile(f"[{regex.escape(chars)}]")


@lru_cache(maxsize=16)
def _final_char_pattern(keep_chars: str):
    # Base allowed set: scripts, digits, whitespace, currency, %, °, hyphens,
    # core punctuation (. , ? ! ' ), Arabic punct, placeholder marker.
    # ; : " are intentionally NOT in the base set — they are opt-in via
    # keep_chars (comes from AranormConfig.extra_punct_keep).
    return regex.compile(
        r"[^\p{Arabic}\p{Latin}\p{Cyrillic}\p{Han}\p{Hiragana}\p{Katakana}\d\s"
        r"$€£¥₹₽¢%°"
        r".,?!'\-"
        r"\u060C\u061B\u061F"  # ، ؛ ؟
        r"\x00"
        + (regex.escape(keep_chars) if keep_chars else "")
        + r"]"
    )


@register
class SpecialTokenNormalization(NormalizationRule):
    """Remove or normalize NMT-corpus special tokens.

    Deletes placeholder markers like <unk>, %pw, %pwm, %breath, {noise}.
    Other %<word> tokens (e.g. %Yeah) have the leading % stripped so the
    underlying word is kept rather than discarded by later filters.
    """
    name = "common_special_tokens"
    sides = (Side.SOURCE, Side.TARGET)
    order = 5

    _percent_word = regex.compile(r"%([A-Za-z]\w*)")

    def apply(self, text: str, side: Side, context: dict) -> str:
        tokens = context.get("_config_removal_tokens") or []
        # Sort longest-first so e.g. %pwm matches before %pw.
        for tok in sorted(tokens, key=len, reverse=True):
            text = text.replace(tok, " ")
        text = self._percent_word.sub(r"\1", text)
        return text


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
    """Collapse 3+ consecutive identical non-digit characters to 2.

    Digits are excluded so numbers like 25000 or 1000000 keep their zeros.
    """
    name = "common_repetition"
    sides = (Side.SOURCE, Side.TARGET)
    order = 70

    _pattern = regex.compile(r"(\D)\1{2,}")

    def apply(self, text: str, side: Side, context: dict) -> str:
        return self._pattern.sub(r"\1\1", text)


@register
class DigitGroupCollation(NormalizationRule):
    """Collate digit groups separated by whitespace: 1 000 000 → 1000000."""
    name = "common_digit_collate"
    sides = (Side.SOURCE, Side.TARGET)
    order = 68

    _pattern = regex.compile(r"(\d)\s+(?=\d)")

    def apply(self, text: str, side: Side, context: dict) -> str:
        return self._pattern.sub(r"\1", text)


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
    """Normalize quotes, drop brackets, and strip ; : " by default.

    Curly/typographic quotes are collapsed to straight `"` and `'`. Brackets
    `[](){}` are always removed. The three ASCII marks ; : " are also
    stripped by default — opt out per-mark via `extra_punct_keep` on the
    config (`--keep-punct`/`--broad-punct` on the CLI).
    """
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
    _bracket_pattern = regex.compile(r"[\[\](){}]")
    _dash_pattern = regex.compile(r"[\u2013\u2014\u2015\u2212]")

    def apply(self, text: str, side: Side, context: dict) -> str:
        for src, dst in self._quote_map.items():
            text = text.replace(src, dst)
        text = self._bracket_pattern.sub("", text)
        keep = frozenset(context.get("_config_extra_punct_keep") or ())
        strip = _DEFAULT_EXTRA_PUNCT_STRIP - keep
        pat = _extra_strip_pattern("".join(sorted(strip)))
        if pat is not None:
            text = pat.sub("", text)
        text = self._dash_pattern.sub("-", text)
        return text


@register
class PunctuationCollation(NormalizationRule):
    """Collapse runs of consecutive punctuation to the first non-'.' mark.

    Examples: "?!?." -> "?", "??" -> "?", "!!," -> "!".
    A run that is only dots stays a single ".".
    """
    name = "common_punct_collapse"
    sides = (Side.SOURCE, Side.TARGET)
    order = 85

    _pattern = regex.compile(r"[.!?,\u061F\u060C\u061B]{2,}")

    @staticmethod
    def _pick(match) -> str:
        run = match.group(0)
        for ch in run:
            if ch != ".":
                return ch
        return "."

    def apply(self, text: str, side: Side, context: dict) -> str:
        return self._pattern.sub(self._pick, text)


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

    Allowed by default: Arabic / Latin / Cyrillic / CJK script, digits,
    currency symbols, %, °, hyphens, Arabic punctuation (، ؛ ؟), and the
    core ASCII punctuation set (. , ? ! ' ).

    The marks ; : " are NOT allowed by default. Pass them via
    `extra_punct_keep` (`--keep-punct`/`--broad-punct` on the CLI) to
    retain them.

    Protected word placeholders are preserved (handled by restore rule
    at order=999).
    """
    name = "common_final_filter"
    sides = (Side.SOURCE, Side.TARGET)
    order = 200

    def apply(self, text: str, side: Side, context: dict) -> str:
        keep = context.get("_config_extra_punct_keep") or ()
        keep_key = "".join(sorted(set(keep)))
        pattern = _final_char_pattern(keep_key)
        text = pattern.sub("", text)
        text = regex.sub(r" {2,}", " ", text)
        return text.strip()
