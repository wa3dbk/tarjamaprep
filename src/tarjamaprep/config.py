from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from tarjamaprep.types import TargetLang

_DEFAULT_PROTECTED = ["%pw", "%breath", "{noise}"]
_DEFAULT_CHAR_MAP = {
    "\u0762": "\u06AF",  # ݢ -> گ
}


@dataclass
class AranormConfig:
    target_lang: TargetLang = TargetLang.EN
    num_workers: int = 1
    # normalize
    disabled_rules: set[str] = field(default_factory=set)
    char_norm_map: dict[str, str] = field(default_factory=lambda: dict(_DEFAULT_CHAR_MAP))
    protected_words: list[str] = field(default_factory=lambda: list(_DEFAULT_PROTECTED))
    # clean
    max_word_ratio: float = 3.0
    max_oov_ratio: float = 0.3
    oov_wordlist_path: str | None = None
    max_non_lang_ratio: float = 0.5
    disabled_filters: set[str] = field(default_factory=set)


def load_config(config_path: str | None = None, **overrides) -> AranormConfig:
    data: dict = {}
    if config_path:
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

    cfg = AranormConfig()

    if "target_lang" in data:
        cfg.target_lang = TargetLang(data["target_lang"])
    if "num_workers" in data:
        cfg.num_workers = data["num_workers"]
    if "disabled_rules" in data:
        cfg.disabled_rules = set(data["disabled_rules"])
    if "char_norm_map" in data:
        cfg.char_norm_map.update(data["char_norm_map"])
    if "protected_words" in data:
        cfg.protected_words = data["protected_words"]
    if "max_word_ratio" in data:
        cfg.max_word_ratio = data["max_word_ratio"]
    if "max_oov_ratio" in data:
        cfg.max_oov_ratio = data["max_oov_ratio"]
    if "oov_wordlist_path" in data:
        cfg.oov_wordlist_path = data["oov_wordlist_path"]
    if "max_non_lang_ratio" in data:
        cfg.max_non_lang_ratio = data["max_non_lang_ratio"]
    if "disabled_filters" in data:
        cfg.disabled_filters = set(data["disabled_filters"])

    # CLI overrides win
    for key, val in overrides.items():
        if val is not None and hasattr(cfg, key):
            setattr(cfg, key, val)

    return cfg
