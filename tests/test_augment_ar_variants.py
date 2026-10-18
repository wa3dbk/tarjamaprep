from __future__ import annotations

import random

from tarjamaprep.augment.ar_strip_punct import ArabicStripPunct
from tarjamaprep.augment.ar_dialect_shift import ArabicDialectShift
from tarjamaprep.types import SentencePair, TargetLang


def _pair(src, tgt, line=1):
    return SentencePair(source=src, target=tgt, line_number=line)


def test_strip_punct_full_sample():
    s = ArabicStripPunct()
    s.sample_rate = 1.0
    pair = _pair("القهوة لذيذة ، أليس كذلك ؟", "Coffee is tasty, isn't it?")
    out = s.augment(pair, TargetLang.EN, 1, random.Random(0))
    assert len(out) == 1
    assert out[0].source == "القهوة لذيذة أليس كذلك"
    assert out[0].target == pair.target
    assert out[0].line_number == pair.line_number


def test_strip_punct_zero_sample():
    s = ArabicStripPunct()
    s.sample_rate = 0.0
    pair = _pair("القهوة لذيذة ، أليس كذلك ؟", "Coffee is tasty, isn't it?")
    assert s.augment(pair, TargetLang.EN, 1, random.Random(0)) == []


def test_strip_punct_noop_when_no_punct():
    s = ArabicStripPunct()
    s.sample_rate = 1.0
    pair = _pair("القهوة لذيذة", "Coffee is tasty")
    assert s.augment(pair, TargetLang.EN, 1, random.Random(0)) == []


def test_dialect_shift_full_sample():
    s = ArabicDialectShift()
    s.sample_rate = 1.0
    pair = _pair("أذهب إلى المدرسة الكبيرة", "I go to the big school")
    out = s.augment(pair, TargetLang.EN, 1, random.Random(0))
    assert len(out) == 1
    # hamza drop: أ→ا, إ→ا; ta marbuta ة→ه; ذ→د
    assert out[0].source == "ادهب الى المدرسه الكبيره"
    assert out[0].target == pair.target


def test_dialect_shift_final_ya():
    s = ArabicDialectShift()
    s.sample_rate = 1.0
    pair = _pair("في البيت", "At home")
    out = s.augment(pair, TargetLang.EN, 1, random.Random(0))
    assert len(out) == 1
    assert out[0].source == "فى البيت"


def test_dialect_shift_zero_sample():
    s = ArabicDialectShift()
    s.sample_rate = 0.0
    pair = _pair("أذهب إلى المدرسة", "I go to school")
    assert s.augment(pair, TargetLang.EN, 1, random.Random(0)) == []


def test_dialect_shift_noop_when_no_targets():
    s = ArabicDialectShift()
    s.sample_rate = 1.0
    pair = _pair("من هنا", "From here")
    assert s.augment(pair, TargetLang.EN, 1, random.Random(0)) == []
