from __future__ import annotations

from pathlib import Path

import yaml

_DATA_DIR = Path(__file__).parent / "data"


def load_builtin(filename: str) -> dict:
    path = _DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_custom_or_builtin(custom_path: str | None, builtin_filename: str) -> dict:
    if custom_path:
        with open(custom_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return load_builtin(builtin_filename)
