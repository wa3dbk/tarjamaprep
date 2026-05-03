from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

from tarjamaprep.types import SentencePair


def read_parallel(source_path: Path, target_path: Path) -> Iterator[SentencePair]:
    with open(source_path, encoding="utf-8") as sf, \
         open(target_path, encoding="utf-8") as tf:
        for i, (src_line, tgt_line) in enumerate(zip(sf, tf), start=1):
            yield SentencePair(
                source=src_line.rstrip("\n"),
                target=tgt_line.rstrip("\n"),
                line_number=i,
            )
        # Check for length mismatch: try reading one more line from each
        src_extra = sf.readline()
        tgt_extra = tf.readline()
        if src_extra or tgt_extra:
            longer = "source" if src_extra else "target"
            raise ValueError(
                f"Line count mismatch: {longer} file has more lines "
                f"(diverged after line {i})"
            )


def write_parallel(
    pairs: Iterable[SentencePair],
    source_path: Path,
    target_path: Path,
) -> int:
    count = 0
    with open(source_path, "w", encoding="utf-8") as sf, \
         open(target_path, "w", encoding="utf-8") as tf:
        for pair in pairs:
            sf.write(pair.source + "\n")
            tf.write(pair.target + "\n")
            count += 1
    return count
