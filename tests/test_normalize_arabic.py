from __future__ import annotations

from tarjamaprep.normalize.arabic import (
    ArabicPresentationForms,
    TaMarbutaSeparation,
    WawCollation,
    CharNormalization,
    ArabicPunctuation,
    ProtectedWords,
    RestoreProtectedWords,
)
from tarjamaprep.types import Side


def test_presentation_forms_isolated_kaf():
    rule = ArabicPresentationForms()
    assert rule.apply("ﻙ", Side.SOURCE, {}) == "ك"


def test_presentation_forms_lam_alef_ligature():
    rule = ArabicPresentationForms()
    # LAM WITH ALEF ISOLATED FORM U+FEFB -> لا (U+0644 U+0627)
    assert rule.apply("ﻻ", Side.SOURCE, {}) == "لا"


def test_presentation_forms_lam_alef_hamza_above_ligature():
    rule = ArabicPresentationForms()
    # U+FEF7 LAM WITH ALEF WITH HAMZA ABOVE -> لأ
    assert rule.apply("ﻷ", Side.SOURCE, {}) == "لأ"


def test_presentation_forms_mixed_word():
    rule = ArabicPresentationForms()
    # Mixed presentation-form word → base form word
    assert rule.apply("ﻛﺘﺎﺏ", Side.SOURCE, {}) == "كتاب"


def test_presentation_forms_strips_bidi_controls():
    rule = ArabicPresentationForms()
    text = "\u202bمرحبا\u202c"
    assert rule.apply(text, Side.SOURCE, {}) == "مرحبا"


def test_presentation_forms_zwsp_to_space():
    rule = ArabicPresentationForms()
    assert rule.apply("مرحبا\u200bبك", Side.SOURCE, {}) == "مرحبا بك"


def test_presentation_forms_compose_hamza_sequences():
    rule = ArabicPresentationForms()
    # ا + ٕ → إ
    assert rule.apply("\u0627\u0655", Side.SOURCE, {}) == "\u0625"
    # ا + ٔ → أ
    assert rule.apply("\u0627\u0654", Side.SOURCE, {}) == "\u0623"


def test_presentation_forms_already_base_untouched():
    rule = ArabicPresentationForms()
    assert rule.apply("كتاب", Side.SOURCE, {}) == "كتاب"
    # Extended Arabic chars already in 06xx are left alone
    assert rule.apply("چی ک ھ", Side.SOURCE, {}) == "چی ک ھ"


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


def test_char_normalization_default_tcheh_to_jeem():
    from tarjamaprep.config import AranormConfig
    rule = CharNormalization()
    ctx = {"_config_char_norm_map": AranormConfig().char_norm_map}
    assert rule.apply("چرب", Side.SOURCE, ctx) == "جرب"


def test_char_normalization():
    rule = CharNormalization()
    ctx = {"_config_char_norm_map": {"\u0762": "\u06AF"}}
    assert rule.apply("ݢ", Side.SOURCE, ctx) == "گ"


def test_arabic_punctuation():
    rule = ArabicPunctuation()
    ctx = {}
    result = rule.apply("hello; world? ok,", Side.SOURCE, ctx)
    assert result == "hello\u061B world\u061F ok\u060C"


def test_arabic_punctuation_preserves_thousands_comma():
    rule = ArabicPunctuation()
    ctx = {}
    assert rule.apply("1,000", Side.SOURCE, ctx) == "1,000"
    assert rule.apply("1,000,000", Side.SOURCE, ctx) == "1,000,000"
    # trailing or leading non-digit side still converts
    assert rule.apply("1, hello", Side.SOURCE, ctx) == "1\u060C hello"


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
