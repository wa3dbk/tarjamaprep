from __future__ import annotations

import time
from pathlib import Path

from tarjamaprep.config import AranormConfig
from tarjamaprep.io import read_parallel, write_parallel
from tarjamaprep.normalize.registry import get_rules, apply_rules
from tarjamaprep.clean.registry import get_filters, apply_filters
from tarjamaprep.parallel import process_parallel
from tarjamaprep.types import SentencePair, Side, NormStats, CleanStats, AugStats


def _make_context(config: AranormConfig) -> dict:
    return {
        "_config_protected_words": config.protected_words,
        "_config_char_norm_map": config.char_norm_map,
        "_config_target_lang": config.target_lang,
    }


def _normalize_batch(args: tuple) -> list[SentencePair]:
    """Normalize a batch of pairs. Accepts tuple for pickling."""
    pairs, disabled_rules, protected_words, char_norm_map = args
    from tarjamaprep.normalize import get_rules, apply_rules
    from tarjamaprep.types import Side

    src_rules = get_rules(side=Side.SOURCE, exclude=disabled_rules)
    tgt_rules = get_rules(side=Side.TARGET, exclude=disabled_rules)
    all_rules = get_rules(exclude=disabled_rules)

    results = []
    for pair in pairs:
        context = {
            "_config_protected_words": protected_words,
            "_config_char_norm_map": char_norm_map,
        }
        pair.source = apply_rules(pair.source, Side.SOURCE, all_rules, context)
        pair.target = apply_rules(pair.target, Side.TARGET, all_rules, context)
        results.append(pair)
    return results


def run_normalize(
    source_path: Path,
    target_path: Path,
    output_source: Path,
    output_target: Path,
    config: AranormConfig,
) -> NormStats:
    start = time.time()
    pairs = list(read_parallel(source_path, target_path))
    stats = NormStats(total=len(pairs))

    if config.num_workers > 1 and len(pairs) > 10_000:
        from tarjamaprep.parallel import CHUNK_SIZE
        import multiprocessing as mp

        chunks = []
        for i in range(0, len(pairs), CHUNK_SIZE):
            chunk = pairs[i : i + CHUNK_SIZE]
            chunks.append((
                chunk,
                config.disabled_rules,
                config.protected_words,
                config.char_norm_map,
            ))

        with mp.Pool(config.num_workers) as pool:
            results = pool.map(_normalize_batch, chunks)

        pairs = []
        for chunk_result in results:
            pairs.extend(chunk_result)
    else:
        rules = get_rules(exclude=config.disabled_rules)
        for pair in pairs:
            context = _make_context(config)
            pair.source = apply_rules(pair.source, Side.SOURCE, rules, context)
            pair.target = apply_rules(pair.target, Side.TARGET, rules, context)

    stats.processed = write_parallel(pairs, output_source, output_target)
    stats.elapsed_seconds = time.time() - start
    return stats


def run_normalize_single(
    input_path: Path,
    output_path: Path,
    side: Side,
    config: AranormConfig,
) -> NormStats:
    """Normalize a single file (not parallel)."""
    start = time.time()
    lines = []
    with open(input_path, encoding="utf-8") as f:
        for line in f:
            lines.append(line.rstrip("\n"))

    stats = NormStats(total=len(lines))
    rules = get_rules(exclude=config.disabled_rules)

    for i, text in enumerate(lines):
        context = _make_context(config)
        lines[i] = apply_rules(text, side, rules, context)

    with open(output_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

    stats.processed = len(lines)
    stats.elapsed_seconds = time.time() - start
    return stats


def _clean_batch(args: tuple) -> tuple[list[SentencePair], list[tuple[int, str]]]:
    """Clean a batch of pairs. Returns (kept, dropped_info)."""
    pairs, disabled_filters, max_word_ratio, max_oov_ratio, max_non_lang_ratio, wordlist = args
    from tarjamaprep.clean.registry import get_filters, apply_filters

    filters = get_filters(exclude=disabled_filters)
    # Configure filter params
    for f in filters:
        if hasattr(f, "max_ratio"):
            f.max_ratio = max_word_ratio
        if hasattr(f, "max_oov_ratio"):
            f.max_oov_ratio = max_oov_ratio
        if hasattr(f, "max_non_lang_ratio"):
            f.max_non_lang_ratio = max_non_lang_ratio
        if hasattr(f, "wordlist") and wordlist is not None:
            f.wordlist = wordlist

    kept = []
    dropped = []
    for pair in pairs:
        reason = apply_filters(pair, filters)
        if reason:
            dropped.append((pair.line_number, reason))
        else:
            kept.append(pair)
    return kept, dropped


def run_clean(
    source_path: Path,
    target_path: Path,
    output_source: Path,
    output_target: Path,
    config: AranormConfig,
    reject_log: Path | None = None,
) -> CleanStats:
    start = time.time()
    pairs = list(read_parallel(source_path, target_path))
    stats = CleanStats(total=len(pairs))

    # Load wordlist if specified
    wordlist = None
    if config.oov_wordlist_path:
        with open(config.oov_wordlist_path, encoding="utf-8") as f:
            wordlist = frozenset(line.strip().lower() for line in f if line.strip())

    filters = get_filters(exclude=config.disabled_filters)
    for f in filters:
        if hasattr(f, "max_ratio"):
            f.max_ratio = config.max_word_ratio
        if hasattr(f, "max_oov_ratio"):
            f.max_oov_ratio = config.max_oov_ratio
        if hasattr(f, "max_non_lang_ratio"):
            f.max_non_lang_ratio = config.max_non_lang_ratio
        if hasattr(f, "wordlist") and wordlist is not None:
            f.wordlist = wordlist

    kept = []
    dropped_info = []

    if config.num_workers > 1 and len(pairs) > 10_000:
        from tarjamaprep.parallel import CHUNK_SIZE
        import multiprocessing as mp

        chunks = []
        for i in range(0, len(pairs), CHUNK_SIZE):
            chunk = pairs[i : i + CHUNK_SIZE]
            chunks.append((
                chunk,
                config.disabled_filters,
                config.max_word_ratio,
                config.max_oov_ratio,
                config.max_non_lang_ratio,
                wordlist,
            ))

        with mp.Pool(config.num_workers) as pool:
            results = pool.map(_clean_batch, chunks)

        for chunk_kept, chunk_dropped in results:
            kept.extend(chunk_kept)
            dropped_info.extend(chunk_dropped)
    else:
        for pair in pairs:
            reason = apply_filters(pair, filters)
            if reason:
                dropped_info.append((pair.line_number, reason))
            else:
                kept.append(pair)

    stats.kept = write_parallel(kept, output_source, output_target)
    stats.dropped = len(dropped_info)

    # Aggregate drop reasons
    for _, reason in dropped_info:
        base_reason = reason.split(":")[0]
        stats.drop_reasons[base_reason] = stats.drop_reasons.get(base_reason, 0) + 1

    # Write reject log
    if reject_log and dropped_info:
        with open(reject_log, "w", encoding="utf-8") as f:
            for line_num, reason in sorted(dropped_info):
                f.write(f"line {line_num}: {reason}\n")

    stats.elapsed_seconds = time.time() - start
    return stats


def run_augment(
    source_path: Path,
    target_path: Path,
    output_source: Path,
    output_target: Path,
    config: AranormConfig,
    strategy_names: list[str] | None = None,
    count: int = 1,
    seed: int | None = None,
    include_original: bool = True,
    arabize_ratio: float = 0.3,
    names_file: str | None = None,
    entities_file: str | None = None,
    codeswitching_file: str | None = None,
) -> AugStats:
    import random as random_mod
    from tarjamaprep.augment import get_strategies

    start = time.time()
    pairs = list(read_parallel(source_path, target_path))
    stats = AugStats(total_input=len(pairs))

    rng = random_mod.Random(seed)
    strategies = get_strategies(strategy_names)

    # Configure strategy-specific paths
    for s in strategies:
        if hasattr(s, "_custom_path") and s.name == "names" and names_file:
            s._custom_path = names_file
        if hasattr(s, "_custom_path") and s.name == "codeswitching" and codeswitching_file:
            s._custom_path = codeswitching_file
        if hasattr(s, "_custom_entities_path") and entities_file:
            s._custom_entities_path = entities_file
        if hasattr(s, "_custom_locations_path") and entities_file:
            s._custom_locations_path = entities_file
        if hasattr(s, "arabize_ratio"):
            s.arabize_ratio = arabize_ratio

    output_pairs = []
    for pair in pairs:
        if include_original:
            output_pairs.append(pair)

        for strategy in strategies:
            augmented = strategy.augment(pair, config.target_lang, count, rng)
            output_pairs.extend(augmented)
            stats.by_strategy[strategy.name] = (
                stats.by_strategy.get(strategy.name, 0) + len(augmented)
            )

    stats.total_output = write_parallel(output_pairs, output_source, output_target)
    stats.elapsed_seconds = time.time() - start
    return stats
