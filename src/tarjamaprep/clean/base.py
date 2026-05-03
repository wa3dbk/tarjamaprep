from __future__ import annotations

from abc import ABC, abstractmethod

from tarjamaprep.types import SentencePair


class CleaningFilter(ABC):
    name: str = ""
    order: int = 100

    @abstractmethod
    def should_drop(self, pair: SentencePair) -> str | None:
        """Return a reason string if the pair should be dropped, else None."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
