from __future__ import annotations

from tarjamaprep.normalize.arabic import (
    TaMarbutaSeparation,
    WawCollation,
    CharNormalization,
    ArabicPunctuation,
    ProtectedWords,
    RestoreProtectedWords,
)
from tarjamaprep.types import Side


def test_ta_marbuta_separation():
    rule = TaMarbutaSeparation()
    ctx = {}
    assert rule.apply("الحلقةالأولى", Side.SOURCE, ctx) == "الحلقة الأولى"


def test_ta_marbuta_no_change():
    rule = TaMarbutaSeparation()
    ctx = {}
    assert rule.apply("الحلقة الأولى", Side.SOURCE, ctx) == "الحلقة الأولى"


def test_waw_collation():
    rule = WawCollation()
    ctx = {}
    assert rule.apply("و قال الرئيس", Side.SOURCE, ctx) == "وقال الرئيس"


def test_waw_collation_start():
    rule = WawCollation()
    ctx = {}
    assert rule.apply("و قال", Side.SOURCE, ctx) == "وقال"


def test_char_normalization():
    rule = CharNormalization()
    ctx = {"_config_char_norm_map": {"\u0762": "\u06AF"}}
    assert rule.apply("ݢ", Side.SOURCE, ctx) == "گ"


def test_arabic_punctuation():
    rule = ArabicPunctuation()
    ctx = {}
    result = rule.apply("hello; world? ok,", Side.SOURCE, ctx)
    assert result == "hello\u061B world\u061F ok\u060C"


def test_protected_words_roundtrip():
    protect = ProtectedWords()
    restore = RestoreProtectedWords()
    ctx = {"_config_protected_words": ["%pw", "%breath"]}

    text = "hello %pw world %breath"
    text = protect.apply(text, Side.SOURCE, ctx)
    assert "%pw" not in text
    assert "%breath" not in text

    text = restore.apply(text, Side.SOURCE, ctx)
    assert text == "hello %pw world %breath"
