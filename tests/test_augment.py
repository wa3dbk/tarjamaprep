from __future__ import annotations

import random

from tarjamaprep.augment.names import NameSubstitution
from tarjamaprep.augment.codeswitching import CodeSwitching
from tarjamaprep.augment.entities import EntitySubstitution
from tarjamaprep.types import SentencePair, TargetLang


def _pair(src, tgt, line=1):
    return SentencePair(source=src, target=tgt, line_number=line)


def test_name_substitution_male():
    strategy = NameSubstitution()
    pair = _pair("قال أحمد إنه ذاهب", "Ahmed said he is going")
    rng = random.Random(42)
    results = strategy.augment(pair, TargetLang.EN, count=2, rng=rng)
    assert len(results) == 2
    for r in results:
        assert "أحمد" not in r.source
        assert "Ahmed" not in r.target


def test_name_substitution_female():
    strategy = NameSubstitution()
    pair = _pair("فاطمة تعمل هنا", "Fatima works here")
    rng = random.Random(42)
    results = strategy.augment(pair, TargetLang.EN, count=1, rng=rng)
    assert len(results) == 1
    assert "فاطمة" not in results[0].source
    assert "Fatima" not in results[0].target


def test_name_substitution_no_match():
    strategy = NameSubstitution()
    pair = _pair("لا يوجد أسماء هنا", "No names here")
    rng = random.Random(42)
    results = strategy.augment(pair, TargetLang.EN, count=2, rng=rng)
    assert results == []


def test_name_substitution_french():
    strategy = NameSubstitution()
    pair = _pair("قال جون شيئاً", "Jean a dit quelque chose")
    rng = random.Random(42)
    results = strategy.augment(pair, TargetLang.FR, count=1, rng=rng)
    assert len(results) == 1
    assert "جون" not in results[0].source
    assert "Jean" not in results[0].target


def test_codeswitching():
    strategy = CodeSwitching()
    pair = _pair("من فضلك أعطني الكتاب", "Please give me the book")
    rng = random.Random(42)
    results = strategy.augment(pair, TargetLang.EN, count=2, rng=rng)
    assert len(results) == 2
    for r in results:
        assert "من فضلك" not in r.source
        # Should contain either "please" or "بليز"
        assert "please" in r.source or "بليز" in r.source


def test_codeswitching_no_match():
    strategy = CodeSwitching()
    pair = _pair("ذهبت إلى المدرسة أمس", "I went to school yesterday")
    rng = random.Random(42)
    results = strategy.augment(pair, TargetLang.EN, count=2, rng=rng)
    assert results == []


def test_entity_substitution_location():
    strategy = EntitySubstitution()
    pair = _pair("سافر إلى باريس", "He traveled to Paris")
    rng = random.Random(42)
    results = strategy.augment(pair, TargetLang.EN, count=2, rng=rng)
    assert len(results) == 2
    for r in results:
        assert "باريس" not in r.source
        assert "Paris" not in r.target


def test_entity_substitution_org():
    strategy = EntitySubstitution()
    pair = _pair("تعمل في جوجل", "She works at Google")
    rng = random.Random(42)
    results = strategy.augment(pair, TargetLang.EN, count=1, rng=rng)
    assert len(results) == 1
    assert "جوجل" not in results[0].source
    assert "Google" not in results[0].target


def test_entity_substitution_russian():
    strategy = EntitySubstitution()
    pair = _pair("سافر إلى موسكو", "Он поехал в Москва")
    rng = random.Random(42)
    results = strategy.augment(pair, TargetLang.RU, count=1, rng=rng)
    assert len(results) == 1
    assert "موسكو" not in results[0].source
    assert "Москва" not in results[0].target
