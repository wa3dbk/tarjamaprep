from __future__ import annotations

import random

from tarjamaprep.augment.base import AugmentationStrategy
from tarjamaprep.augment.registry import register
from tarjamaprep.augment.data_loader import load_custom_or_builtin
from tarjamaprep.types import SentencePair, TargetLang


@register
class EntitySubstitution(AugmentationStrategy):
    """Substitute named entities (locations, organizations, products) in both sides."""
    name = "entities"
    description = "Replace locations, organizations, and products with alternatives"

    _data: dict | None = None
    _custom_entities_path: str | None = None
    _custom_locations_path: str | None = None

    def _load_data(self):
        if self._data is not None:
            return
        self._data = {"locations": [], "organizations": [], "products": []}

        # Load locations
        loc_raw = load_custom_or_builtin(self._custom_locations_path, "locations.yaml")
        self._data["locations"] = loc_raw.get("locations", [])

        # Load organizations and products
        org_raw = load_custom_or_builtin(self._custom_entities_path, "organizations.yaml")
        self._data["organizations"] = org_raw.get("organizations", [])
        self._data["products"] = org_raw.get("products", [])

    def _find_entities_in_pair(self, pair: SentencePair, target_lang: TargetLang):
        """Find entities present in both source and target."""
        self._load_data()
        lang_key = target_lang.value
        found = []
        for category in ("locations", "organizations", "products"):
            for entry in self._data[category]:
                ar_name = entry["ar"]
                tgt_name = entry.get(lang_key, "")
                if ar_name in pair.source and tgt_name and tgt_name in pair.target:
                    found.append((entry, category))
        return found

    def augment(
        self,
        pair: SentencePair,
        target_lang: TargetLang,
        count: int,
        rng: random.Random,
    ) -> list[SentencePair]:
        self._load_data()
        found = self._find_entities_in_pair(pair, target_lang)
        if not found:
            return []

        lang_key = target_lang.value
        results = []
        for _ in range(count):
            new_src = pair.source
            new_tgt = pair.target
            for original_entry, category in found:
                candidates = [
                    e for e in self._data[category]
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
