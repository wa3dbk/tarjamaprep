from __future__ import annotations

from tarjamaprep.normalize.common import (
    DigitGroupCollation,
    EmojiRemoval,
    ExcessiveRepetition,
    NumeralConversion,
    PunctuationCollation,
    PunctuationNormalization,
    FinalCharFilter,
    SpecialTokenNormalization,
)
from tarjamaprep.pipeline import align_terminal_punct
from tarjamaprep.types import SentencePair, Side


def _pair(src, tgt):
    return SentencePair(source=src, target=tgt, line_number=1)


def test_align_terminal_punct_adds_period_to_source():
    p = align_terminal_punct(_pair("مرحبا", "Hello."))
    assert p.source == "مرحبا."
    assert p.target == "Hello."


def test_align_terminal_punct_adds_arabic_question_mark():
    p = align_terminal_punct(_pair("كيف الحال", "How are you?"))
    assert p.source == "كيف الحال\u061F"


def test_align_terminal_punct_adds_period_to_target():
    p = align_terminal_punct(_pair("مرحبا.", "Hello"))
    assert p.target == "Hello."


def test_align_terminal_punct_question_to_target():
    p = align_terminal_punct(_pair("كيف الحال\u061F", "How are you"))
    assert p.target == "How are you?"


def test_align_terminal_punct_both_present_untouched():
    p = align_terminal_punct(_pair("مرحبا.", "Hello."))
    assert p.source == "مرحبا."
    assert p.target == "Hello."


def test_align_terminal_punct_neither_present_untouched():
    p = align_terminal_punct(_pair("مرحبا", "Hello"))
    assert p.source == "مرحبا"
    assert p.target == "Hello"


_DEFAULT_TOK_CTX = {
    "_config_removal_tokens": ["<unk>", "{noise}", "%breath", "%pwm", "%pw"],
}


def test_special_token_removal():
    rule = SpecialTokenNormalization()
    ctx = dict(_DEFAULT_TOK_CTX)
    assert rule.apply("hello <unk> world", Side.SOURCE, ctx) == "hello   world"
    assert rule.apply("مرحبا %pw كيف الحال", Side.SOURCE, ctx) == "مرحبا   كيف الحال"
    assert rule.apply("ok %pwm done", Side.SOURCE, ctx) == "ok   done"
    assert rule.apply("sound %breath here", Side.TARGET, ctx) == "sound   here"


def test_special_token_percent_word_strip():
    rule = SpecialTokenNormalization()
    ctx = dict(_DEFAULT_TOK_CTX)
    assert rule.apply("%Yeah man", Side.TARGET, ctx) == "Yeah man"
    assert rule.apply("say %yeah now", Side.SOURCE, ctx) == "say yeah now"


def test_special_token_removal_user_extension():
    rule = SpecialTokenNormalization()
    ctx = {"_config_removal_tokens": ["<unk>", "<custom>"]}
    assert rule.apply("hi <custom> there", Side.SOURCE, ctx) == "hi   there"
    # %pw is NOT in this user's list, so prefix-strip applies instead
    assert rule.apply("hi %pw there", Side.SOURCE, ctx) == "hi pw there"


def test_special_token_removal_no_tokens():
    rule = SpecialTokenNormalization()
    assert rule.apply("hi <unk> there", Side.SOURCE, {}) == "hi <unk> there"


def test_punctuation_collation():
    rule = PunctuationCollation()
    ctx = {}
    assert rule.apply("what?!?.", Side.TARGET, ctx) == "what?"
    assert rule.apply("really??", Side.TARGET, ctx) == "really?"
    assert rule.apply("wait!!,", Side.TARGET, ctx) == "wait!"
    assert rule.apply("end...", Side.TARGET, ctx) == "end."
    assert rule.apply("single.", Side.TARGET, ctx) == "single."
    # Arabic punctuation is also collapsed
    assert rule.apply("كيف\u061F\u061F", Side.SOURCE, ctx) == "كيف\u061F"


def test_emoji_removal():
    rule = EmojiRemoval()
    ctx = {}
    assert rule.apply("hello 😀 world 🎉", Side.TARGET, ctx) == "hello  world "


def test_excessive_repetition():
    rule = ExcessiveRepetition()
    ctx = {}
    assert rule.apply("hellooooo", Side.TARGET, ctx) == "helloo"
    assert rule.apply("ااااااا", Side.SOURCE, ctx) == "اا"


def test_excessive_repetition_preserves_digits():
    rule = ExcessiveRepetition()
    ctx = {}
    assert rule.apply("25000", Side.TARGET, ctx) == "25000"
    assert rule.apply("1000000", Side.TARGET, ctx) == "1000000"


def test_digit_group_collation():
    rule = DigitGroupCollation()
    ctx = {}
    assert rule.apply("1 000 000", Side.TARGET, ctx) == "1000000"
    assert rule.apply("I have 5 000 apples", Side.TARGET, ctx) == "I have 5000 apples"
    assert rule.apply("no digits here", Side.TARGET, ctx) == "no digits here"


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
    # Curly quotes map to straight " first, then " is stripped by default.
    assert rule.apply("«hello»", Side.TARGET, ctx) == "hello"
    assert rule.apply("text (with) [brackets]", Side.TARGET, ctx) == "text with brackets"


def test_punctuation_normalization_strips_semicolon_colon_quote_by_default():
    rule = PunctuationNormalization()
    ctx = {}
    assert rule.apply("hello; world: \"ok\"", Side.TARGET, ctx) == "hello world ok"


def test_punctuation_normalization_keeps_opted_in_marks():
    rule = PunctuationNormalization()
    ctx = {"_config_extra_punct_keep": [";", ":", "\""]}
    assert rule.apply("hello; world: \"ok\"", Side.TARGET, ctx) == "hello; world: \"ok\""


def test_punctuation_normalization_keeps_only_selected_marks():
    rule = PunctuationNormalization()
    ctx = {"_config_extra_punct_keep": [";"]}
    assert rule.apply("a; b: \"c\"", Side.TARGET, ctx) == "a; b c"


def test_final_char_filter():
    rule = FinalCharFilter()
    ctx = {}
    # Basic punct kept, ; and : stripped by default (not in base allowed set).
    result = rule.apply("hello مرحبا 123 .,!?", Side.SOURCE, ctx)
    assert result == "hello مرحبا 123 .,!?"
    result = rule.apply("hello ★ world", Side.TARGET, ctx)
    assert result == "hello world"


def test_final_char_filter_strips_semicolon_colon_quote_by_default():
    rule = FinalCharFilter()
    ctx = {}
    assert rule.apply("a; b: \"c\"", Side.TARGET, ctx) == "a b c"


def test_final_char_filter_keeps_opted_in_marks():
    rule = FinalCharFilter()
    ctx = {"_config_extra_punct_keep": [";", ":", "\""]}
    assert rule.apply("a; b: \"c\"", Side.TARGET, ctx) == "a; b: \"c\""
