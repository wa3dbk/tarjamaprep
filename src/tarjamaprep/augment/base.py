from __future__ import annotations

from abc import ABC, abstractmethod

from tarjamaprep.types import SentencePair, TargetLang


class AugmentationStrategy(ABC):
    name: str = ""
    description: str = ""

    @abstractmethod
    def augment(
        self,
        pair: SentencePair,
        target_lang: TargetLang,
        count: int,
        rng,
    ) -> list[SentencePair]:
        """Generate augmented variants of a sentence pair.

        Args:
            pair: The original sentence pair.
            target_lang: The target language.
            count: Number of variants to generate.
            rng: A random.Random instance for reproducibility.

        Returns:
            List of new SentencePair instances (may be fewer than count
            if not enough substitutions are possible).
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
