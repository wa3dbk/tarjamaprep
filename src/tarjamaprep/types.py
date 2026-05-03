from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Side(Enum):
    SOURCE = "source"
    TARGET = "target"


class TargetLang(Enum):
    EN = "en"
    FR = "fr"
    DE = "de"
    IT = "it"
    RU = "ru"
    ES = "es"
    ZH = "zh"
    SW = "sw"
    TR = "tr"


@dataclass
class SentencePair:
    source: str
    target: str
    line_number: int


@dataclass
class NormStats:
    total: int = 0
    processed: int = 0
    elapsed_seconds: float = 0.0


@dataclass
class CleanStats:
    total: int = 0
    kept: int = 0
    dropped: int = 0
    drop_reasons: dict[str, int] = field(default_factory=dict)
    elapsed_seconds: float = 0.0


@dataclass
class AugStats:
    total_input: int = 0
    total_output: int = 0
    by_strategy: dict[str, int] = field(default_factory=dict)
    elapsed_seconds: float = 0.0
