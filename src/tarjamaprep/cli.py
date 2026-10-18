from __future__ import annotations

from pathlib import Path

import click

from tarjamaprep import __version__
from tarjamaprep.config import load_config
from tarjamaprep.types import TargetLang


@click.group()
@click.version_option(version=__version__, prog_name="tarjamaprep")
def cli():
    """tarjamaprep: Arabic parallel corpus normalization, cleaning, and augmentation."""


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("target", type=click.Path(exists=True, path_type=Path), required=False, default=None)
@click.option("-os", "--output-source", required=True, type=click.Path(path_type=Path))
@click.option("-ot", "--output-target", type=click.Path(path_type=Path), default=None,
              help="Output target file (required for parallel mode).")
@click.option(
    "-l", "--target-lang",
    type=click.Choice(["en", "fr", "de", "it", "ru", "es", "zh", "sw", "tr"]),
    default="en",
    help="Target language.",
)
@click.option("-s", "--side", type=click.Choice(["source", "target"]),
              default=None, help="Which side the input is (single-file mode). Default: auto-detect.")
@click.option("-c", "--config", "config_path", type=click.Path(exists=True), default=None)
@click.option("-w", "--workers", type=int, default=1, help="Number of parallel workers.")
@click.option("--disable-rule", multiple=True, help="Disable rule(s) by name.")
@click.option("--removal-token", "removal_tokens", multiple=True,
              help="Extra special token to strip during normalization. "
                   "Repeat to add multiple. Added on top of the defaults.")
@click.option("--keep-punct", "keep_puncts", multiple=True,
              type=click.Choice([";", ":", "\""]),
              help="Keep this punctuation mark in the output (default: "
                   "stripped like {}[]). Repeat for multiple.")
@click.option("--broad-punct", is_flag=True,
              help="Shortcut: keep all of ; : \" in the output.")
def normalize(source, target, output_source, output_target, target_lang,
              side, config_path, workers, disable_rule, removal_tokens,
              keep_puncts, broad_punct):
    """Normalize parallel source/target files, or a single file.

    In parallel mode (two input files): normalizes both source and target.
    In single-file mode (one input file): normalizes a single text file.
    Use --side to specify whether the file is Arabic (source) or target language.
    """
    cfg = load_config(
        config_path,
        target_lang=TargetLang(target_lang),
        num_workers=workers,
        disabled_rules=set(disable_rule) if disable_rule else None,
    )
    if removal_tokens:
        cfg.removal_tokens = list(cfg.removal_tokens) + list(removal_tokens)

    keep = set(keep_puncts)
    if broad_punct:
        keep |= {";", ":", "\""}
    if keep:
        cfg.extra_punct_keep = sorted(keep)

    if target is None:
        # Single-file mode
        from tarjamaprep.pipeline import run_normalize_single
        from tarjamaprep.types import Side
        if side == "target":
            file_side = Side.TARGET
        else:
            file_side = Side.SOURCE
        stats = run_normalize_single(source, output_source, file_side, cfg)
        click.echo(f"Normalized {stats.processed}/{stats.total} lines "
                   f"in {stats.elapsed_seconds:.1f}s")
        click.echo(f"Output: {output_source}")
    else:
        # Parallel mode
        if output_target is None:
            raise click.UsageError("--output-target (-ot) is required in parallel mode.")
        from tarjamaprep.pipeline import run_normalize
        stats = run_normalize(source, target, output_source, output_target, cfg)
        click.echo(f"Normalized {stats.processed}/{stats.total} pairs "
                   f"in {stats.elapsed_seconds:.1f}s")
        click.echo(f"Output: {output_source}, {output_target}")


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("target", type=click.Path(exists=True, path_type=Path))
@click.option("-os", "--output-source", required=True, type=click.Path(path_type=Path))
@click.option("-ot", "--output-target", required=True, type=click.Path(path_type=Path))
@click.option(
    "-l", "--target-lang",
    type=click.Choice(["en", "fr", "de", "it", "ru", "es", "zh", "sw", "tr"]),
    default="en",
    help="Target language.",
)
@click.option("-c", "--config", "config_path", type=click.Path(exists=True), default=None)
@click.option("-w", "--workers", type=int, default=1, help="Number of parallel workers.")
@click.option("--max-ratio", type=float, default=None, help="Max word count ratio (default: 3.0).")
@click.option("--max-oov-ratio", type=float, default=None, help="Max OOV ratio (default: 0.3).")
@click.option("--oov-wordlist", type=click.Path(exists=True), default=None)
@click.option("--reject-log", type=click.Path(path_type=Path), default=None,
              help="Write rejected pairs info to this file.")
@click.option("--disable-filter", multiple=True, help="Disable filter(s) by name.")
@click.option("--ignore-word-ratio", is_flag=True, help="Disable word_ratio filter.")
@click.option("--ignore-number-check", is_flag=True, help="Disable number_check filter.")
@click.option("--ignore-punct-match", is_flag=True, help="Disable punct_match filter.")
@click.option("--ignore-currency-percent", is_flag=True,
              help="Disable currency_percent_check filter.")
@click.option("--ignore-non-lang", is_flag=True, help="Disable non_lang filter.")
@click.option("--ignore-foreign-arabic", is_flag=True,
              help="Disable foreign_arabic filter (keep pairs with Persian/Urdu letters).")
@click.option("--permissive", is_flag=True,
              help="Shortcut: enable all --ignore-* flags for internal/verified data.")
@click.option("--report/--no-report", default=True,
              help="Print a final report table (totals + drop reasons). Default: on.")
def clean(source, target, output_source, output_target, target_lang,
          config_path, workers, max_ratio, max_oov_ratio, oov_wordlist,
          reject_log, disable_filter, ignore_word_ratio, ignore_number_check,
          ignore_punct_match, ignore_currency_percent, ignore_non_lang,
          ignore_foreign_arabic, permissive, report):
    """Clean parallel corpus by filtering sentence pairs."""
    disabled = set(disable_filter)
    if permissive:
        ignore_word_ratio = ignore_number_check = True
        ignore_punct_match = ignore_currency_percent = ignore_non_lang = True
        ignore_foreign_arabic = True
    if ignore_word_ratio:
        disabled.add("word_ratio")
    if ignore_number_check:
        disabled.add("number_check")
    if ignore_punct_match:
        disabled.add("punct_match")
    if ignore_currency_percent:
        disabled.add("currency_percent_check")
    if ignore_non_lang:
        disabled.add("non_lang")
    if ignore_foreign_arabic:
        disabled.add("foreign_arabic")

    cfg = load_config(
        config_path,
        target_lang=TargetLang(target_lang),
        num_workers=workers,
        max_word_ratio=max_ratio,
        max_oov_ratio=max_oov_ratio,
        oov_wordlist_path=oov_wordlist,
        disabled_filters=disabled if disabled else None,
    )

    from tarjamaprep.pipeline import run_clean
    stats = run_clean(source, target, output_source, output_target, cfg,
                      reject_log=reject_log)

    click.echo(f"Kept {stats.kept}/{stats.total} pairs, "
               f"dropped {stats.dropped} in {stats.elapsed_seconds:.1f}s")
    if report:
        from tarjamaprep.report import print_clean_report, section_from_stats
        print_clean_report([section_from_stats(stats, label=source.name)])
    click.echo(f"Output: {output_source}, {output_target}")


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.argument("target", type=click.Path(exists=True, path_type=Path))
@click.option("-os", "--output-source", required=True, type=click.Path(path_type=Path))
@click.option("-ot", "--output-target", required=True, type=click.Path(path_type=Path))
@click.option(
    "-l", "--target-lang",
    type=click.Choice(["en", "fr", "de", "it", "ru", "es", "zh", "sw", "tr"]),
    default="en",
    help="Target language.",
)
@click.option("-c", "--config", "config_path", type=click.Path(exists=True), default=None)
@click.option("-w", "--workers", type=int, default=1, help="Number of parallel workers.")
@click.option("--strategy", "strategies", multiple=True,
              help="Strategy to apply (can repeat). Default: all.")
@click.option("--disable-strategy", "disabled_strategies", multiple=True,
              help="Strategy to disable (can repeat). Cannot overlap with --strategy.")
@click.option("--count", type=int, default=1,
              help="Number of augmented variants per pair per strategy.")
@click.option("--seed", type=int, default=None, help="Random seed for reproducibility.")
@click.option("--include-original/--no-original", default=True,
              help="Include original pairs in output.")
@click.option("--arabize-ratio", type=float, default=0.3,
              help="Probability of arabized vs direct substitution (0.0-1.0).")
@click.option("--names-file", type=click.Path(exists=True), default=None,
              help="Custom names YAML file.")
@click.option("--entities-file", type=click.Path(exists=True), default=None,
              help="Custom entities YAML file (orgs + products).")
@click.option("--codeswitching-file", type=click.Path(exists=True), default=None,
              help="Custom code-switching phrases YAML file.")
@click.option("--strip-punct-ratio", type=float, default=None,
              help="Sampling ratio for ar_strip_punct strategy (default: 0.4).")
@click.option("--dialect-shift-ratio", type=float, default=None,
              help="Sampling ratio for ar_dialect_shift strategy (default: 0.3).")
def augment(source, target, output_source, output_target, target_lang,
            config_path, workers, strategies, disabled_strategies, count,
            seed, include_original, arabize_ratio, names_file, entities_file,
            codeswitching_file, strip_punct_ratio, dialect_shift_ratio):
    """Augment parallel corpus with synthetic sentence pairs."""
    from tarjamaprep.augment import list_all_strategies

    selected = set(strategies)
    disabled = set(disabled_strategies)
    conflict = selected & disabled
    if conflict:
        raise click.UsageError(
            f"Strategies cannot be both enabled and disabled: "
            f"{', '.join(sorted(conflict))}"
        )

    known = {s.name for s in list_all_strategies()}
    unknown = (selected | disabled) - known
    if unknown:
        raise click.UsageError(
            f"Unknown strategy name(s): {', '.join(sorted(unknown))}. "
            f"Run `tarjamaprep list-strategies` to see available names."
        )

    if selected:
        resolved_names = sorted(selected)
    elif disabled:
        resolved_names = [n for n in known if n not in disabled]
    else:
        resolved_names = None

    cfg = load_config(
        config_path,
        target_lang=TargetLang(target_lang),
        num_workers=workers,
    )

    from tarjamaprep.pipeline import run_augment
    stats = run_augment(
        source, target, output_source, output_target, cfg,
        strategy_names=resolved_names,
        count=count,
        seed=seed,
        include_original=include_original,
        arabize_ratio=arabize_ratio,
        names_file=names_file,
        entities_file=entities_file,
        codeswitching_file=codeswitching_file,
        strip_punct_ratio=strip_punct_ratio,
        dialect_shift_ratio=dialect_shift_ratio,
    )

    click.echo(f"Augmented {stats.total_input} → {stats.total_output} pairs "
               f"in {stats.elapsed_seconds:.1f}s")
    if stats.by_strategy:
        click.echo("Generated per strategy:")
        for name, n in sorted(stats.by_strategy.items()):
            click.echo(f"  {name}: {n}")
    click.echo(f"Output: {output_source}, {output_target}")


@cli.command("list-rules")
def list_rules():
    """List available normalization rules."""
    from tarjamaprep.normalize.registry import list_all_rules
    rules = list_all_rules()
    click.echo(f"{'Name':<25} {'Order':<8} {'Sides':<20} Description")
    click.echo("-" * 80)
    for r in rules:
        sides = ", ".join(s.value for s in r.sides)
        doc = (r.__class__.__doc__ or "").strip().split("\n")[0]
        click.echo(f"{r.name:<25} {r.order:<8} {sides:<20} {doc}")


@cli.command("list-filters")
def list_filters():
    """List available cleaning filters."""
    from tarjamaprep.clean.registry import list_all_filters
    filters = list_all_filters()
    click.echo(f"{'Name':<20} {'Order':<8} Description")
    click.echo("-" * 60)
    for f in filters:
        doc = (f.__class__.__doc__ or "").strip().split("\n")[0]
        click.echo(f"{f.name:<20} {f.order:<8} {doc}")


@cli.command("list-strategies")
def list_strategies():
    """List available augmentation strategies."""
    from tarjamaprep.augment import list_all_strategies
    strategies = list_all_strategies()
    click.echo(f"{'Name':<20} Description")
    click.echo("-" * 60)
    for s in strategies:
        click.echo(f"{s.name:<20} {s.description}")


if __name__ == "__main__":
    cli()
