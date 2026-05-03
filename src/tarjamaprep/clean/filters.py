from __future__ import annotations

import re

import regex

from tarjamaprep.clean.base import CleaningFilter
from tarjamaprep.clean.registry import register
from tarjamaprep.types import SentencePair


@register
class EmptyLineFilter(CleaningFilter):
    """Drop pairs where either side is empty or whitespace-only."""
    name = "empty_line"
    order = 5

    def should_drop(self, pair: SentencePair) -> str | None:
        if not pair.source.strip() or not pair.target.strip():
            return "empty_line"
        return None


@register
class WordCountRatioFilter(CleaningFilter):
    """Drop pairs with excessive word count ratio."""
    name = "word_ratio"
    order = 10
    max_ratio: float = 3.0

    def should_drop(self, pair: SentencePair) -> str | None:
        src_words = len(pair.source.split())
        tgt_words = len(pair.target.split())
        if src_words == 0 or tgt_words == 0:
            return "zero_words"
        ratio = max(src_words, tgt_words) / min(src_words, tgt_words)
        if ratio > self.max_ratio:
            return f"word_ratio:{ratio:.1f}"
        return None


@register
class PunctuationMatchFilter(CleaningFilter):
    """Drop pairs where final punctuation doesn't match."""
    name = "punct_match"
    order = 20

    _final_punct_src = set(".!?\u061F\u06D4")  # . ! ? ؟ ۔
    _final_punct_tgt = set(".!?")

    def should_drop(self, pair: SentencePair) -> str | None:
        src = pair.source.rstrip()
        tgt = pair.target.rstrip()
        if not src or not tgt:
            return None
        src_has_punct = src[-1] in self._final_punct_src
        tgt_has_punct = tgt[-1] in self._final_punct_tgt
        if src_has_punct != tgt_has_punct:
            return "punct_mismatch"
        return None


@register
class NumberConsistencyFilter(CleaningFilter):
    """Drop pairs where numbers don't match between source and target."""
    name = "number_check"
    order = 30

    _digit_pattern = re.compile(r"\d+")

    def should_drop(self, pair: SentencePair) -> str | None:
        src_nums = set(self._digit_pattern.findall(pair.source))
        tgt_nums = set(self._digit_pattern.findall(pair.target))
        # Only check if there are numbers on at least one side
        if not src_nums and not tgt_nums:
            return None
        if src_nums != tgt_nums:
            return f"number_mismatch:src={src_nums},tgt={tgt_nums}"
        return None


@register
class NonLanguageFilter(CleaningFilter):
    """Drop pairs where majority of characters are not from expected scripts."""
    name = "non_lang"
    order = 40
    max_non_lang_ratio: float = 0.5

    _lang_pattern = regex.compile(r"[\p{Arabic}\p{Latin}\p{Cyrillic}\p{Han}\p{Hiragana}\p{Katakana}\d\s]")

    def should_drop(self, pair: SentencePair) -> str | None:
        for text, label in [(pair.source, "source"), (pair.target, "target")]:
            if not text.strip():
                continue
            total = len(text.replace(" ", ""))
            if total == 0:
                continue
            lang_chars = len(self._lang_pattern.findall(text.replace(" ", "")))
            non_lang_ratio = 1.0 - (lang_chars / total)
            if non_lang_ratio > self.max_non_lang_ratio:
                return f"non_lang:{label}:{non_lang_ratio:.2f}"
        return None


@register
class OOVFilter(CleaningFilter):
    """Drop pairs with too many out-of-vocabulary words."""
    name = "oov_filter"
    order = 50
    max_oov_ratio: float = 0.3
    wordlist: frozenset[str] | None = None

    def should_drop(self, pair: SentencePair) -> str | None:
        if self.wordlist is None:
            return None
        for text, label in [(pair.source, "source"), (pair.target, "target")]:
            words = text.lower().split()
            if not words:
                continue
            oov_count = sum(1 for w in words if w not in self.wordlist)
            oov_ratio = oov_count / len(words)
            if oov_ratio > self.max_oov_ratio:
                return f"oov:{label}:{oov_ratio:.2f}"
        return None
