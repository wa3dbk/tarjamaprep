# TarjamaPrep

**TarjamaPrep** (ترجمة = "translation" in Arabic) is a CLI tool for preparing Arabic parallel corpora for Neural Machine Translation. It handles the full NMT data preparation pipeline: normalization, cleaning, and augmentation of parallel text.

**Supported language pairs:** Arabic ↔ English, French, German, Italian, Russian, Spanish, Chinese, Swahili, Turkish

## Features

- **Normalize**: Rule-based text normalization for Arabic and target languages (script fixes, numeral conversion, punctuation, emoji/symbol removal)
- **Single-file mode**: Normalize a single Arabic or target-language file independently
- **Clean**: Filter sentence pairs by quality criteria (word ratio, punctuation match, number consistency, OOV detection)
- **Augment**: Generate synthetic training pairs via name substitution, code-switching, and entity replacement
- **Extensible**: Add custom rules, filters, strategies, and languages via a decorator-based plugin system
- **Parallel processing**: Multiprocessing support for large corpora

## Installation

```bash
# From source
git clone https://github.com/wa3dbk/tarjamaprep.git
cd tarjamaprep
pip install -e .

# Or directly from GitHub
pip install git+https://github.com/wa3dbk/tarjamaprep.git
```

### Requirements

- Python >= 3.9
- Dependencies: `click`, `regex`, `pyyaml` (installed automatically)

## Quick Start

```bash
# Normalize parallel Arabic↔English files
tarjamaprep normalize corpus.ar corpus.en -os norm.ar -ot norm.en -l en

# Normalize a single Arabic file
tarjamaprep normalize corpus.ar -os norm.ar

# Clean normalized parallel files
tarjamaprep clean norm.ar norm.en -os clean.ar -ot clean.en --reject-log rejected.log

# Augment training data with synthetic pairs
tarjamaprep augment clean.ar clean.en -os aug.ar -ot aug.en --count 3 --seed 42
```

### Full Pipeline Example

```bash
# Arabic-Spanish NMT data preparation
tarjamaprep normalize raw.ar raw.es -os norm.ar -ot norm.es -l es -w 8
tarjamaprep clean norm.ar norm.es -os clean.ar -ot clean.es --max-ratio 2.5 -w 8
tarjamaprep augment clean.ar clean.es -os train.ar -ot train.es -l es \
    --strategy names --strategy codeswitching --count 2 --seed 42

# Arabic-Chinese NMT data preparation
tarjamaprep normalize raw.ar raw.zh -os norm.ar -ot norm.zh -l zh -w 4
tarjamaprep clean norm.ar norm.zh -os clean.ar -ot clean.zh --max-ratio 4.0
tarjamaprep augment clean.ar clean.zh -os train.ar -ot train.zh -l zh \
    --strategy entities --count 3

# Arabic-Turkish with custom config
tarjamaprep normalize raw.ar raw.tr -os norm.ar -ot norm.tr -l tr -c my_config.yaml
```

---

## Commands Reference

### `tarjamaprep normalize`

Normalize text files — either a parallel pair (source + target) or a single file.

```bash
# Parallel mode (two files)
tarjamaprep normalize SOURCE TARGET -os OUTPUT_SOURCE -ot OUTPUT_TARGET [OPTIONS]

# Single-file mode (one file)
tarjamaprep normalize SOURCE -os OUTPUT [OPTIONS]
```

**Arguments:**
- `SOURCE` — Path to input file (UTF-8, one sentence per line)
- `TARGET` — (Optional) Path to target language file. If omitted, single-file mode is used.

**Options:**
| Option | Description |
|--------|-------------|
| `-os`, `--output-source` | Output path for normalized source / single file (required) |
| `-ot`, `--output-target` | Output path for normalized target (required in parallel mode) |
| `-l`, `--target-lang` | Target language: `en`, `fr`, `de`, `it`, `ru`, `es`, `zh`, `sw`, `tr` (default: `en`) |
| `-s`, `--side` | Which side the input is in single-file mode: `source` or `target` (default: `source`) |
| `-c`, `--config` | Path to YAML configuration file |
| `-w`, `--workers` | Number of parallel workers (default: 1) |
| `--disable-rule` | Disable a specific rule by name (repeatable) |

**Examples:**

```bash
# Parallel mode: normalize both sides
tarjamaprep normalize input.ar input.en -os norm.ar -ot norm.en

# Single-file mode: normalize an Arabic file
tarjamaprep normalize raw_arabic.txt -os normalized_arabic.txt

# Single-file mode: normalize an English target file
tarjamaprep normalize raw_english.txt -os normalized_english.txt --side target

# Single-file mode: normalize a French file
tarjamaprep normalize raw_french.txt -os normalized_french.txt --side target -l fr

# Parallel mode with workers and disabled rule
tarjamaprep normalize input.ar input.fr -os norm.ar -ot norm.fr -l fr -w 4 --disable-rule ar_waw_collate
```

**What normalization does (Arabic source / `--side source`):**
```
Before: الحلقةالأولى من ٣٤٥ 😀 و قال «نعم» ;;; aaaaa
After:  الحلقة الأولى من 345 وقال "نعم" ؛؛ aa
```

**What normalization does (target / `--side target`):**
```
Before: Hello   world 😀 «yes» (really) aaaaa
After:  Hello world "yes" really aa
```

---

### `tarjamaprep clean`

Filter sentence pairs based on quality criteria.

```bash
tarjamaprep clean SOURCE TARGET -os OUTPUT_SOURCE -ot OUTPUT_TARGET [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-os`, `--output-source` | Output path for cleaned source (required) |
| `-ot`, `--output-target` | Output path for cleaned target (required) |
| `-l`, `--target-lang` | Target language (default: `en`) |
| `-c`, `--config` | Path to YAML configuration file |
| `-w`, `--workers` | Number of parallel workers (default: 1) |
| `--max-ratio` | Maximum word count ratio between source/target (default: 3.0) |
| `--max-oov-ratio` | Maximum OOV word ratio (default: 0.3) |
| `--oov-wordlist` | Path to vocabulary file for OOV filtering |
| `--reject-log` | Write rejected pairs info to this file |
| `--disable-filter` | Disable a specific filter by name (repeatable) |

**Examples:**
```bash
# Basic cleaning
tarjamaprep clean norm.ar norm.en -os clean.ar -ot clean.en

# Strict word ratio, log rejected pairs
tarjamaprep clean norm.ar norm.es -os clean.ar -ot clean.es \
    --max-ratio 2.5 --reject-log rejected.log

# With OOV filtering
tarjamaprep clean norm.ar norm.de -os clean.ar -ot clean.de \
    --oov-wordlist vocab.txt --max-oov-ratio 0.2

# Chinese: use higher ratio (fewer words per sentence in Chinese)
tarjamaprep clean norm.ar norm.zh -os clean.ar -ot clean.zh \
    --disable-filter number_check --max-ratio 4.0
```

**Reject log format:**
```
line 15: word_ratio:4.2
line 23: punct_mismatch
line 47: number_mismatch:src={'3'},tgt={'5'}
line 89: non_lang:source:0.67
```

---

### `tarjamaprep augment`

Generate synthetic sentence pairs to enrich training data.

```bash
tarjamaprep augment SOURCE TARGET -os OUTPUT_SOURCE -ot OUTPUT_TARGET [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `-os`, `--output-source` | Output path for augmented source (required) |
| `-ot`, `--output-target` | Output path for augmented target (required) |
| `-l`, `--target-lang` | Target language (default: `en`) |
| `--strategy` | Strategy to apply (repeatable; default: all). Values: `names`, `codeswitching`, `entities` |
| `--count` | Number of augmented variants per pair per strategy (default: 1) |
| `--seed` | Random seed for reproducibility |
| `--include-original/--no-original` | Include original pairs in output (default: yes) |
| `--arabize-ratio` | Probability of arabized vs direct code-switch (0.0-1.0, default: 0.3) |
| `--names-file` | Custom names YAML file |
| `--entities-file` | Custom entities YAML file |
| `--codeswitching-file` | Custom code-switching YAML file |
| `-w`, `--workers` | Number of parallel workers (default: 1) |

**Examples:**
```bash
# All strategies, 2 variants per pair
tarjamaprep augment clean.ar clean.en -os aug.ar -ot aug.en --count 2 --seed 42

# Only name substitution for Spanish
tarjamaprep augment clean.ar clean.es -os aug.ar -ot aug.es -l es \
    --strategy names --count 3

# Code-switching with high arabization rate
tarjamaprep augment clean.ar clean.en -os aug.ar -ot aug.en \
    --strategy codeswitching --arabize-ratio 0.7

# Only synthetic pairs (no originals)
tarjamaprep augment clean.ar clean.en -os synthetic.ar -ot synthetic.en \
    --no-original --count 5 --seed 123
```

---

### Listing Commands

```bash
tarjamaprep list-rules        # Show all normalization rules
tarjamaprep list-filters      # Show all cleaning filters
tarjamaprep list-strategies   # Show all augmentation strategies
tarjamaprep --version         # Show version
tarjamaprep --help            # Show all commands
```

---

## Normalization Rules

Rules are applied in order (lower = runs first):

| Rule | Order | Side | Description |
|------|-------|------|-------------|
| `ar_protected` | 10 | both | Protect tagged tokens (`%pw`, `%breath`, `{noise}`) from modification |
| `ar_ta_marbuta` | 20 | source | Split concatenated words at ta marbuta: `الحلقةالأولى` → `الحلقة الأولى` |
| `lat_whitespace` | 20 | target | Normalize unicode whitespace |
| `ar_waw_collate` | 30 | source | Collate standalone و to next word: `و قال` → `وقال` |
| `ar_char_norm` | 40 | source | Normalize characters via configurable mapping (e.g., `ݢ` → `گ`) |
| `ar_punctuation` | 50 | source | Convert to Arabic punctuation: `;` → `؛`, `?` → `؟`, `,` → `،` |
| `common_emoji` | 60 | both | Remove all emoji characters |
| `common_symbols` | 65 | both | Remove decorative symbols (★, ♦, ©, ™, etc.) |
| `common_repetition` | 70 | both | Collapse 3+ repeated identical characters to 2 |
| `common_numerals` | 75 | both | Convert Eastern Arabic (`٠-٩`) and Persian (`۰-۹`) numerals to `0-9` |
| `common_punctuation` | 80 | both | Normalize quotes (`« » „ "` → `"`), drop brackets/parentheses |
| `common_whitespace` | 90 | both | Normalize whitespace and trim |
| `common_final_filter` | 200 | both | Strip any character not in allowed set |
| `ar_restore` | 999 | both | Restore protected word placeholders |

**Allowed characters after normalization:** Arabic, Latin, Cyrillic, CJK, digits, currency symbols ($, €, £, ¥, ₹, ₽, ¢), %, °, and basic punctuation (`. , ; : ? ! " ' -`). Arabic punctuation (`، ؛ ؟`) is preserved on the source side.

---

## Cleaning Filters

| Filter | Description | Config |
|--------|-------------|--------|
| `empty_line` | Drop pairs where either side is empty | — |
| `word_ratio` | Drop if word count ratio exceeds threshold | `--max-ratio` (default: 3.0) |
| `punct_match` | Drop if final punctuation doesn't match | — |
| `number_check` | Drop if digit sequences differ between source/target | — |
| `non_lang` | Drop if majority of characters are non-language script | threshold: 0.5 |
| `oov_filter` | Drop if too many out-of-vocabulary words | `--oov-wordlist`, `--max-oov-ratio` |

---

## Augmentation Strategies

### `names` — Name Substitution

Finds person names in both source and target, replaces with another name of the **same gender**.

```
Input:  AR: قال أحمد إنه ذاهب     EN: Ahmed said he is going
Output: AR: قال يوسف إنه ذاهب    EN: Youssef said he is going
        AR: قال جون إنه ذاهب     EN: John said he is going
```

### `codeswitching` — Code-Switching Injection

Replaces Arabic phrases in the source with their foreign equivalent or an arabized form, simulating code-switching patterns common in Arabic speech.

```
Input:  AR: من فضلك أعطني الكتاب   EN: Please give me the book
Output: AR: please أعطني الكتاب     (direct foreign substitution)
        AR: بليز أعطني الكتاب       (arabized/phoneticized form)
```

### `entities` — Entity Substitution

Replaces named entities (locations, organizations, products) in **both** source and target.

```
Input:  AR: سافر خالد إلى نيويورك    EN: Khaled traveled to New York
Output: AR: سافر خالد إلى باريس     EN: Khaled traveled to Paris
```

---

## Configuration

### YAML Config File

```yaml
target_lang: en
num_workers: 4

# Normalization
disabled_rules: []
char_norm_map:
  "ݢ": "گ"
  "ٱ": "ا"
protected_words:
  - "%pw"
  - "%breath"
  - "{noise}"
  - "<laughter>"

# Cleaning
max_word_ratio: 3.0
max_oov_ratio: 0.3
max_non_lang_ratio: 0.5
disabled_filters: []
```

Use with: `tarjamaprep normalize input.ar input.en -os o.ar -ot o.en -c config.yaml`

### Custom Augmentation Data Files

**Names** (`--names-file`):
```yaml
names:
  - {ar: "أحمد", en: "Ahmed", fr: "Ahmed", de: "Ahmed", it: "Ahmed",
     ru: "Ахмед", es: "Ahmed", zh: "艾哈迈德", sw: "Ahmed", tr: "Ahmet", gender: "m"}
  - {ar: "فاطمة", en: "Fatima", fr: "Fatima", de: "Fatima", it: "Fatima",
     ru: "Фатима", es: "Fátima", zh: "法蒂玛", sw: "Fatima", tr: "Fatma", gender: "f"}
```

**Code-switching** (`--codeswitching-file`):
```yaml
phrases:
  - {ar: "من فضلك", en: "please", fr: "s'il vous plaît", de: "bitte",
     it: "per favore", ru: "пожалуйста", es: "por favor", zh: "请",
     sw: "tafadhali", tr: "lütfen", arabized: "بليز"}
```

**Entities** (`--entities-file`):
```yaml
organizations:
  - {ar: "جوجل", en: "Google", fr: "Google", de: "Google", it: "Google",
     ru: "Гугл", es: "Google", zh: "谷歌", sw: "Google", tr: "Google"}
products:
  - {ar: "آيفون", en: "iPhone", fr: "iPhone", de: "iPhone", it: "iPhone",
     ru: "Айфон", es: "iPhone", zh: "苹果手机", sw: "iPhone", tr: "iPhone"}
```

---

## Tutorial: Extending TarjamaPrep

### Adding a New Normalization Rule

Create a decorated class in `src/tarjamaprep/normalize/` — it's automatically registered.

```python
# In src/tarjamaprep/normalize/arabic.py (or a new file)

import regex
from tarjamaprep.normalize.base import NormalizationRule
from tarjamaprep.normalize.registry import register
from tarjamaprep.types import Side


@register
class AlefNormalization(NormalizationRule):
    """Normalize all alef variants to bare alef."""
    name = "ar_alef_norm"           # unique name (used with --disable-rule)
    sides = (Side.SOURCE,)          # only apply to Arabic side
    order = 42                      # execution order (lower = earlier)

    _pattern = regex.compile(r"[إأآٱ]")

    def apply(self, text: str, side: Side, context: dict) -> str:
        return self._pattern.sub("ا", text)
```

The rule is now automatically:
- Listed by `tarjamaprep list-rules`
- Applied during `tarjamaprep normalize`
- Disableable with `--disable-rule ar_alef_norm`

**Key points:**
- `name` — unique identifier
- `sides` — `(Side.SOURCE,)` for Arabic, `(Side.TARGET,)` for target language, or both
- `order` — lower numbers run first
- `context` — dict containing `_config_protected_words`, `_config_char_norm_map`, `_config_target_lang`

### Adding a New Cleaning Filter

```python
from tarjamaprep.clean.base import CleaningFilter
from tarjamaprep.clean.registry import register
from tarjamaprep.types import SentencePair


@register
class MinLengthFilter(CleaningFilter):
    """Drop pairs where either sentence is too short."""
    name = "min_length"
    order = 8
    min_words: int = 3

    def should_drop(self, pair: SentencePair) -> str | None:
        if len(pair.source.split()) < self.min_words:
            return f"min_length:source"
        if len(pair.target.split()) < self.min_words:
            return f"min_length:target"
        return None
```

Return `None` to keep the pair, or a reason string to drop it.

### Adding a New Augmentation Strategy

```python
import random
from tarjamaprep.augment.base import AugmentationStrategy
from tarjamaprep.augment.registry import register
from tarjamaprep.types import SentencePair, TargetLang


@register
class DialectVariant(AugmentationStrategy):
    """Generate Egyptian Arabic variants (final ي → ى)."""
    name = "dialect"
    description = "Generate Egyptian Arabic dialect variants"

    def augment(self, pair: SentencePair, target_lang: TargetLang,
                count: int, rng: random.Random) -> list[SentencePair]:
        import regex
        new_src = regex.sub(r"ي(?=\s|$)", "ى", pair.source)
        if new_src != pair.source:
            return [SentencePair(source=new_src, target=pair.target,
                                line_number=pair.line_number)]
        return []
```

Then import it in `src/tarjamaprep/augment/__init__.py`:
```python
import tarjamaprep.augment.my_module  # noqa: F401
```

### Adding a New Target Language

1. **Add to enum** in `src/tarjamaprep/types.py`:
   ```python
   class TargetLang(Enum):
       ...
       PT = "pt"   # Portuguese
   ```

2. **Add to CLI choices** in `src/tarjamaprep/cli.py`:
   ```python
   type=click.Choice(["en", "fr", ..., "pt"])
   ```

3. **Add translations** to YAML data files (`names.yaml`, `locations.yaml`, etc.):
   ```yaml
   - {ar: "أحمد", ..., pt: "Ahmed", gender: "m"}
   ```

4. **For non-Latin/Arabic/Cyrillic/CJK scripts** (e.g., Thai), update regex patterns in:
   - `src/tarjamaprep/normalize/common.py` → `FinalCharFilter._pattern` (add `\p{Thai}`)
   - `src/tarjamaprep/clean/filters.py` → `NonLanguageFilter._lang_pattern`

5. **Run tests**: `pytest tests/ -v`

### Adding Language-Specific Rules

Rules can check the target language from context to apply conditionally:

```python
@register
class TurkishCaseNorm(NormalizationRule):
    """Handle Turkish-specific İ/I casing."""
    name = "tr_case_norm"
    sides = (Side.TARGET,)
    order = 25

    def apply(self, text: str, side: Side, context: dict) -> str:
        from tarjamaprep.types import TargetLang
        if context.get("_config_target_lang") != TargetLang.TR:
            return text
        # Turkish-specific logic
        return text
```

---

## Architecture

```
src/tarjamaprep/
├── cli.py                  # Click CLI entry point
├── config.py               # YAML + CLI config loading
├── types.py                # Data types (SentencePair, enums, stats)
├── io.py                   # Parallel file read/write
├── pipeline.py             # Orchestration (normalize, clean, augment)
├── parallel.py             # Multiprocessing support
├── normalize/
│   ├── base.py             # Abstract NormalizationRule
│   ├── registry.py         # @register decorator + rule chain
│   ├── arabic.py           # Arabic-specific rules
│   ├── latin.py            # Latin script rules
│   └── common.py           # Shared rules (both sides)
├── clean/
│   ├── base.py             # Abstract CleaningFilter
│   ├── registry.py         # Filter registry
│   └── filters.py          # All filter implementations
└── augment/
    ├── base.py             # Abstract AugmentationStrategy
    ├── registry.py         # Strategy registry
    ├── names.py            # Name substitution
    ├── codeswitching.py    # Code-switching injection
    ├── entities.py         # Entity replacement
    ├── data_loader.py      # YAML data loading
    └── data/               # Built-in YAML data
        ├── names.yaml
        ├── locations.yaml
        ├── codeswitching.yaml
        └── organizations.yaml
```

---

## Input Format

- Plain text files in UTF-8 encoding
- One sentence per line
- For parallel mode: source and target files must have the same number of lines

---

## Tips

- **Always normalize before cleaning** — filters like `number_check` work best on normalized text
- **Use `--reject-log`** to understand why pairs are dropped
- **For Chinese**, use `--max-ratio 4.0` or higher (fewer words per sentence)
- **Set `--seed`** for reproducible augmentation
- **Single-file mode** is useful for normalizing monolingual data or pre-processing before alignment

---

## License

MIT
