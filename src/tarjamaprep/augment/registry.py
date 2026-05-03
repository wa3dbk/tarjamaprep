from __future__ import annotations

from tarjamaprep.augment.base import AugmentationStrategy

_STRATEGIES: dict[str, type[AugmentationStrategy]] = {}


def register(cls: type[AugmentationStrategy]) -> type[AugmentationStrategy]:
    if not cls.name:
        raise ValueError(f"{cls.__name__} must define a non-empty 'name'")
    _STRATEGIES[cls.name] = cls
    return cls


def get_strategies(
    names: list[str] | None = None,
) -> list[AugmentationStrategy]:
    if names:
        return [_STRATEGIES[n]() for n in names if n in _STRATEGIES]
    return [cls() for cls in _STRATEGIES.values()]


def list_all_strategies() -> list[AugmentationStrategy]:
    return [cls() for cls in _STRATEGIES.values()]
