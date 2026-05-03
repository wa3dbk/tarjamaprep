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
def normalize(source, target, output_source, output_target, target_lang,
              side, config_path, workers, disable_rule):
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
def clean(source, target, output_source, output_target, target_lang,
          config_path, workers, max_ratio, max_oov_ratio, oov_wordlist,
          reject_log, disable_filter):
    """Clean parallel corpus by filtering sentence pairs."""
    cfg = load_config(
        config_path,
        target_lang=TargetLang(target_lang),
        num_workers=workers,
        max_word_ratio=max_ratio,
        max_oov_ratio=max_oov_ratio,
        oov_wordlist_path=oov_wordlist,
        disabled_filters=set(disable_filter) if disable_filter else None,
    )

    from tarjamaprep.pipeline import run_clean
    stats = run_clean(source, target, output_source, output_target, cfg,
                      reject_log=reject_log)

    click.echo(f"Kept {stats.kept}/{stats.total} pairs, "
               f"dropped {stats.dropped} in {stats.elapsed_seconds:.1f}s")
    if stats.drop_reasons:
        click.echo("Drop reasons:")
        for reason, count in sorted(stats.drop_reasons.items(),
                                     key=lambda x: -x[1]):
            click.echo(f"  {reason}: {count}")
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
def augment(source, target, output_source, output_target, target_lang,
            config_path, workers, strategies, count, seed, include_original,
            arabize_ratio, names_file, entities_file, codeswitching_file):
    """Augment parallel corpus with synthetic sentence pairs."""
    cfg = load_config(
        config_path,
        target_lang=TargetLang(target_lang),
        num_workers=workers,
    )

    from tarjamaprep.pipeline import run_augment
    stats = run_augment(
        source, target, output_source, output_target, cfg,
        strategy_names=list(strategies) if strategies else None,
        count=count,
        seed=seed,
        include_original=include_original,
        arabize_ratio=arabize_ratio,
        names_file=names_file,
        entities_file=entities_file,
        codeswitching_file=codeswitching_file,
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
