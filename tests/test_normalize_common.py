from __future__ import annotations

from tarjamaprep.normalize.common import (
    EmojiRemoval,
    ExcessiveRepetition,
    NumeralConversion,
    PunctuationNormalization,
    FinalCharFilter,
)
from tarjamaprep.types import Side


def test_emoji_removal():
    rule = EmojiRemoval()
    ctx = {}
    assert rule.apply("hello 😀 world 🎉", Side.TARGET, ctx) == "hello  world "


def test_excessive_repetition():
    rule = ExcessiveRepetition()
    ctx = {}
    assert rule.apply("hellooooo", Side.TARGET, ctx) == "helloo"
    assert rule.apply("ااااااا", Side.SOURCE, ctx) == "اا"


def test_numeral_conversion_eastern():
    rule = NumeralConversion()
    ctx = {}
    assert rule.apply("٠١٢٣٤٥٦٧٨٩", Side.SOURCE, ctx) == "0123456789"


def test_numeral_conversion_persian():
    rule = NumeralConversion()
    ctx = {}
    assert rule.apply("۰۱۲۳۴۵۶۷۸۹", Side.SOURCE, ctx) == "0123456789"


def test_punctuation_normalization():
    rule = PunctuationNormalization()
    ctx = {}
    assert rule.apply("«hello»", Side.TARGET, ctx) == '"hello"'
    assert rule.apply("text (with) [brackets]", Side.TARGET, ctx) == "text with brackets"


def test_final_char_filter():
    rule = FinalCharFilter()
    ctx = {}
    # Should keep Arabic, Latin, digits, basic punct
    result = rule.apply("hello مرحبا 123 .,!?", Side.SOURCE, ctx)
    assert result == "hello مرحبا 123 .,!?"
    # Should strip weird symbols
    result = rule.apply("hello ★ world", Side.TARGET, ctx)
    assert result == "hello world"
