from __future__ import annotations

from tarjamaprep.clean.filters import (
    CurrencyPercentConsistencyFilter,
    EmptyLineFilter,
    WordCountRatioFilter,
    PunctuationMatchFilter,
    NumberConsistencyFilter,
    NonLanguageFilter,
    OOVFilter,
)
from tarjamaprep.types import SentencePair


def _pair(src, tgt, line=1):
    return SentencePair(source=src, target=tgt, line_number=line)


def test_empty_line_filter():
    f = EmptyLineFilter()
    assert f.should_drop(_pair("", "hello")) is not None
    assert f.should_drop(_pair("hello", "")) is not None
    assert f.should_drop(_pair("hello", "world")) is None


def test_word_ratio_filter():
    f = WordCountRatioFilter()
    f.max_ratio = 3.0
    assert f.should_drop(_pair("a b c", "x y z")) is None
    assert f.should_drop(_pair("a", "x y z w v u")) is not None


def test_punct_match_filter():
    f = PunctuationMatchFilter()
    assert f.should_drop(_pair("text.", "text.")) is None
    assert f.should_drop(_pair("text.", "text")) is not None
    assert f.should_drop(_pair("text", "text")) is None


def test_number_consistency():
    f = NumberConsistencyFilter()
    assert f.should_drop(_pair("I have 3 cats", "عندي 3 قطط")) is None
    assert f.should_drop(_pair("I have 3 cats", "عندي 5 قطط")) is not None
    assert f.should_drop(_pair("no numbers", "no numbers")) is None


def test_currency_percent_consistency_percent_word():
    f = CurrencyPercentConsistencyFilter()
    assert f.should_drop(_pair("نسبة 50 بالمائة", "50% of them")) is None
    assert f.should_drop(_pair("نسبة 50%", "50% of them")) is None
    assert f.should_drop(_pair("خمسون من الناس", "50% of them")) is not None


def test_currency_percent_consistency_dollar_euro():
    f = CurrencyPercentConsistencyFilter()
    assert f.should_drop(_pair("يكلف 50 دولار", "costs $50")) is None
    assert f.should_drop(_pair("يكلف 50", "costs $50")) is not None
    assert f.should_drop(_pair("50 يورو", "€50")) is None
    assert f.should_drop(_pair("50 شيء", "€50")) is not None


def test_currency_percent_no_number_no_check():
    f = CurrencyPercentConsistencyFilter()
    # No digit next to %, filter should not trigger
    assert f.should_drop(_pair("مرحبا", "hello %pw world")) is None


def test_non_language_filter():
    f = NonLanguageFilter()
    f.max_non_lang_ratio = 0.5
    assert f.should_drop(_pair("مرحبا بالعالم", "hello world")) is None
    assert f.should_drop(_pair("★★★★★★★★", "hello")) is not None


def test_non_language_filter_accepts_punctuation():
    f = NonLanguageFilter()
    f.max_non_lang_ratio = 0.5
    # Short Arabic word surrounded by punctuation should pass
    assert f.should_drop(_pair("آ . .", "A.")) is None


def test_oov_filter():
    f = OOVFilter()
    f.max_oov_ratio = 0.3
    f.wordlist = frozenset(["hello", "world", "the", "مرحبا"])
    assert f.should_drop(_pair("مرحبا", "hello world")) is None
    assert f.should_drop(_pair("مرحبا", "xyzzy foobar baz quux")) is not None


def test_oov_filter_no_wordlist():
    f = OOVFilter()
    f.wordlist = None
    assert f.should_drop(_pair("anything", "anything")) is None
