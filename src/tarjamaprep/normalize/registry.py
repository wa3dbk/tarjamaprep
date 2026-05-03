from __future__ import annotations

from tarjamaprep.normalize.base import NormalizationRule
from tarjamaprep.types import Side

_RULES: dict[str, type[NormalizationRule]] = {}


def register(cls: type[NormalizationRule]) -> type[NormalizationRule]:
    if not cls.name:
        raise ValueError(f"{cls.__name__} must define a non-empty 'name'")
    _RULES[cls.name] = cls
    return cls


def get_rules(
    side: Side | None = None,
    exclude: set[str] | None = None,
) -> list[NormalizationRule]:
    exclude = exclude or set()
    rules = []
    for name, cls in _RULES.items():
        if name in exclude:
            continue
        inst = cls()
        if side is None or side in inst.sides:
            rules.append(inst)
    rules.sort(key=lambda r: r.order)
    return rules


def apply_rules(
    text: str,
    side: Side,
    rules: list[NormalizationRule],
    context: dict,
) -> str:
    for rule in rules:
        if side in rule.sides:
            text = rule.apply(text, side, context)
    return text


def list_all_rules() -> list[NormalizationRule]:
    rules = [cls() for cls in _RULES.values()]
    rules.sort(key=lambda r: r.order)
    return rules
