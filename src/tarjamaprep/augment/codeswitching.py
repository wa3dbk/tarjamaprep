from __future__ import annotations

import random

from tarjamaprep.augment.base import AugmentationStrategy
from tarjamaprep.augment.registry import register
from tarjamaprep.augment.data_loader import load_custom_or_builtin
from tarjamaprep.types import SentencePair, TargetLang


@register
class CodeSwitching(AugmentationStrategy):
    """Inject code-switching by replacing Arabic phrases with foreign or arabized forms."""
    name = "codeswitching"
    description = "Replace Arabic phrases with foreign/arabized equivalents"

    _data: list | None = None
    _custom_path: str | None = None
    arabize_ratio: float = 0.3

    def _load_data(self):
        if self._data is None:
            raw = load_custom_or_builtin(self._custom_path, "codeswitching.yaml")
            self._data = raw.get("phrases", [])

    def _find_phrases_in_source(self, source: str):
        """Find which code-switching phrases appear in the source."""
        self._load_data()
        found = []
        for entry in self._data:
            if entry["ar"] in source:
                found.append(entry)
        return found

    def augment(
        self,
        pair: SentencePair,
        target_lang: TargetLang,
        count: int,
        rng: random.Random,
    ) -> list[SentencePair]:
        self._load_data()
        found = self._find_phrases_in_source(pair.source)
        if not found:
            return []

        lang_key = target_lang.value
        results = []
        for _ in range(count):
            new_src = pair.source
            new_tgt = pair.target
            for entry in found:
                # Decide: use arabized form or direct foreign word
                use_arabized = rng.random() < self.arabize_ratio
                if use_arabized and entry.get("arabized"):
                    replacement = entry["arabized"]
                else:
                    replacement = entry.get(lang_key, entry.get("en", ""))

                if not replacement:
                    continue

                new_src = new_src.replace(entry["ar"], replacement, 1)
                # Target stays the same (the foreign word is now in the source,
                # mimicking code-switching in Arabic speech)

            if new_src != pair.source:
                results.append(SentencePair(
                    source=new_src,
                    target=new_tgt,
                    line_number=pair.line_number,
                ))
        return results
