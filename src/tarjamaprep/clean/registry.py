from __future__ import annotations

from tarjamaprep.clean.base import CleaningFilter
from tarjamaprep.types import SentencePair

_FILTERS: dict[str, type[CleaningFilter]] = {}


def register(cls: type[CleaningFilter]) -> type[CleaningFilter]:
    if not cls.name:
        raise ValueError(f"{cls.__name__} must define a non-empty 'name'")
    _FILTERS[cls.name] = cls
    return cls


def get_filters(
    exclude: set[str] | None = None,
    **kwargs,
) -> list[CleaningFilter]:
    exclude = exclude or set()
    filters = []
    for name, cls in _FILTERS.items():
        if name in exclude:
            continue
        inst = cls(**{k: v for k, v in kwargs.items() if hasattr(cls, k)})
        filters.append(inst)
    filters.sort(key=lambda f: f.order)
    return filters


def apply_filters(
    pair: SentencePair,
    filters: list[CleaningFilter],
) -> str | None:
    """Return drop reason or None if pair passes all filters."""
    for f in filters:
        reason = f.should_drop(pair)
        if reason:
            return reason
    return None


def list_all_filters() -> list[CleaningFilter]:
    filters = [cls() for cls in _FILTERS.values()]
    filters.sort(key=lambda f: f.order)
    return filters
