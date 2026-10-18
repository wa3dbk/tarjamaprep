from __future__ import annotations

import os
import tempfile
from pathlib import Path

from click.testing import CliRunner

from tarjamaprep.cli import cli


def _write_files(src_lines, tgt_lines, tmpdir):
    src = Path(tmpdir) / "src.ar"
    tgt = Path(tmpdir) / "tgt.en"
    src.write_text("\n".join(src_lines) + "\n", encoding="utf-8")
    tgt.write_text("\n".join(tgt_lines) + "\n", encoding="utf-8")
    return src, tgt


def test_normalize_basic():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        src, tgt = _write_files(
            ["الحلقةالأولى", "و قال"],
            ["The first episode", "He said"],
            tmpdir,
        )
        out_src = Path(tmpdir) / "out_src.ar"
        out_tgt = Path(tmpdir) / "out_tgt.en"

        result = runner.invoke(cli, [
            "normalize", str(src), str(tgt),
            "-os", str(out_src), "-ot", str(out_tgt),
        ])
        assert result.exit_code == 0
        assert "Normalized 2/2" in result.output

        lines = out_src.read_text(encoding="utf-8").strip().split("\n")
        assert lines[0] == "الحلقة الأولى"
        assert lines[1] == "وقال"


def test_clean_basic():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        src, tgt = _write_files(
            ["مرحبا بالعالم", "", "نص عادي"],
            ["Hello world", "", "Normal text"],
            tmpdir,
        )
        out_src = Path(tmpdir) / "out_src.ar"
        out_tgt = Path(tmpdir) / "out_tgt.en"

        result = runner.invoke(cli, [
            "clean", str(src), str(tgt),
            "-os", str(out_src), "-ot", str(out_tgt),
        ])
        assert result.exit_code == 0
        assert "dropped 1" in result.output


def test_list_rules():
    runner = CliRunner()
    result = runner.invoke(cli, ["list-rules"])
    assert result.exit_code == 0
    assert "ar_ta_marbuta" in result.output
    assert "common_numerals" in result.output


def test_list_filters():
    runner = CliRunner()
    result = runner.invoke(cli, ["list-filters"])
    assert result.exit_code == 0
    assert "word_ratio" in result.output
    assert "oov_filter" in result.output


def test_augment_strategy_disable_conflict():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        src, tgt = _write_files(["مرحبا"], ["Hello"], tmpdir)
        out_src = Path(tmpdir) / "out.ar"
        out_tgt = Path(tmpdir) / "out.en"
        result = runner.invoke(cli, [
            "augment", str(src), str(tgt),
            "-os", str(out_src), "-ot", str(out_tgt),
            "--strategy", "names", "--disable-strategy", "names",
        ])
        assert result.exit_code != 0
        assert "both enabled and disabled" in result.output
        assert "names" in result.output


def test_augment_unknown_strategy():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        src, tgt = _write_files(["مرحبا"], ["Hello"], tmpdir)
        out_src = Path(tmpdir) / "out.ar"
        out_tgt = Path(tmpdir) / "out.en"
        result = runner.invoke(cli, [
            "augment", str(src), str(tgt),
            "-os", str(out_src), "-ot", str(out_tgt),
            "--disable-strategy", "nope",
        ])
        assert result.exit_code != 0
        assert "Unknown strategy" in result.output


def test_augment_disable_strategy_runs():
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        src, tgt = _write_files(["مرحبا"], ["Hello"], tmpdir)
        out_src = Path(tmpdir) / "out.ar"
        out_tgt = Path(tmpdir) / "out.en"
        result = runner.invoke(cli, [
            "augment", str(src), str(tgt),
            "-os", str(out_src), "-ot", str(out_tgt),
            "--disable-strategy", "ar_dialect_shift",
            "--disable-strategy", "ar_strip_punct",
            "--seed", "0",
        ])
        assert result.exit_code == 0, result.output
        assert "ar_dialect_shift" not in result.output
        assert "ar_strip_punct" not in result.output
