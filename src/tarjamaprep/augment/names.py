from __future__ import annotations

import random

from tarjamaprep.augment.base import AugmentationStrategy
from tarjamaprep.augment.registry import register
from tarjamaprep.augment.data_loader import load_custom_or_builtin
from tarjamaprep.types import SentencePair, TargetLang


@register
class NameSubstitution(AugmentationStrategy):
    """Substitute person names while preserving gender."""
    name = "names"
    description = "Replace names with other names of the same gender"

    _data: dict | None = None
    _custom_path: str | None = None

    def _load_data(self):
        if self._data is None:
            raw = load_custom_or_builtin(self._custom_path, "names.yaml")
            self._data = {"m": [], "f": []}
            for entry in raw.get("names", []):
                gender = entry.get("gender", "m")
                self._data[gender].append(entry)

    def _find_names_in_pair(self, pair: SentencePair, target_lang: TargetLang):
        """Find which names from our database appear in the sentence pair."""
        self._load_data()
        found = []
        lang_key = target_lang.value
        for gender in ("m", "f"):
            for entry in self._data[gender]:
                ar_name = entry["ar"]
                tgt_name = entry.get(lang_key, "")
                if ar_name in pair.source and tgt_name and tgt_name in pair.target:
                    found.append((entry, gender))
        return found

    def augment(
        self,
        pair: SentencePair,
        target_lang: TargetLang,
        count: int,
        rng: random.Random,
    ) -> list[SentencePair]:
        self._load_data()
        found = self._find_names_in_pair(pair, target_lang)
        if not found:
            return []

        lang_key = target_lang.value
        results = []
        for _ in range(count):
            new_src = pair.source
            new_tgt = pair.target
            for original_entry, gender in found:
                candidates = [
                    e for e in self._data[gender]
                    if e["ar"] != original_entry["ar"]
                    and e.get(lang_key)
                ]
                if not candidates:
                    continue
                replacement = rng.choice(candidates)
                new_src = new_src.replace(original_entry["ar"], replacement["ar"])
                new_tgt = new_tgt.replace(
                    original_entry[lang_key], replacement[lang_key]
                )

            if new_src != pair.source or new_tgt != pair.target:
                results.append(SentencePair(
                    source=new_src,
                    target=new_tgt,
                    line_number=pair.line_number,
                ))
        return results
