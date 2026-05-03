from __future__ import annotations

from abc import ABC, abstractmethod

from tarjamaprep.types import Side


class NormalizationRule(ABC):
    name: str = ""
    sides: tuple[Side, ...] = (Side.SOURCE, Side.TARGET)
    order: int = 100

    @abstractmethod
    def apply(self, text: str, side: Side, context: dict) -> str:
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} order={self.order}>"
