from __future__ import annotations

import multiprocessing as mp
from collections.abc import Callable
from itertools import islice

from tarjamaprep.types import SentencePair

CHUNK_SIZE = 10_000


def _chunk_iter(pairs: list[SentencePair], chunk_size: int):
    for i in range(0, len(pairs), chunk_size):
        yield pairs[i : i + chunk_size]


def process_parallel(
    pairs: list[SentencePair],
    processor: Callable[[list[SentencePair]], list],
    num_workers: int,
) -> list:
    """Process pairs in parallel using chunked multiprocessing.

    The processor function must be a top-level picklable function.
    Results are returned in original order.
    """
    if num_workers <= 1 or len(pairs) < CHUNK_SIZE:
        return processor(pairs)

    chunks = list(_chunk_iter(pairs, CHUNK_SIZE))

    with mp.Pool(num_workers) as pool:
        results = pool.map(processor, chunks)

    # Flatten results
    flat = []
    for chunk_result in results:
        flat.extend(chunk_result)
    return flat
