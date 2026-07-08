"""Minimal YAML frontmatter parser (stdlib only). Handles scalars and simple lists."""

from __future__ import annotations

import re
from typing import Any

LIST_ITEM_RE = re.compile(r"^\s*-\s+(.+)$")


def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",")]
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        return raw[1:-1]
    return raw


def parse_frontmatter_block(text: str) -> dict[str, Any]:
    """Parse simple YAML mapping (no nesting)."""
    result: dict[str, Any] = {}
    current_key: str | None = None
    current_list: list[str] | None = None

    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue

        list_match = LIST_ITEM_RE.match(line)
        if list_match and current_key is not None:
            if current_list is None:
                current_list = []
                result[current_key] = current_list
            current_list.append(list_match.group(1).strip().strip("'\""))
            continue

        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            current_key = key
            current_list = None
            if value:
                result[key] = _parse_value(value)
            else:
                result[key] = []
                current_list = result[key]

    return result
