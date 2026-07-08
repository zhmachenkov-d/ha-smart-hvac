#!/usr/bin/env python3
"""OKF v0.1 conformance checker for knowledge/ bundle."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from frontmatter import parse_frontmatter_block

try:
    import yaml  # type: ignore

    def _parse_yaml(text: str) -> dict:
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else {}

except ImportError:
    _parse_yaml = parse_frontmatter_block

VALID_TYPES = {"Concept", "Decision", "Reference", "Playbook"}
REQUIRED_FIELDS = {"type", "title", "description", "timestamp"}
TYPE_DIRS = {
    "Concept": "concepts",
    "Decision": "decisions",
    "Reference": "references",
    "Playbook": "playbooks",
}
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def find_bundle_root() -> Path:
    script = Path(__file__).resolve()
    # .cursor/skills/okf/scripts -> repo root is parents[4]
    return script.parents[4] / "knowledge"


def parse_frontmatter(path: Path) -> tuple[dict | None, str | None]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None, "missing YAML frontmatter"
    try:
        data = _parse_yaml(match.group(1))
    except Exception as exc:
        return None, f"invalid YAML: {exc}"
    if not isinstance(data, dict):
        return None, "frontmatter must be a mapping"
    return data, None


def collect_md_files(bundle: Path) -> list[Path]:
    files: list[Path] = []
    for sub in ("concepts", "decisions", "references", "playbooks"):
        d = bundle / sub
        if d.is_dir():
            files.extend(sorted(p for p in d.glob("*.md") if p.name != "index.md"))
    return files


def validate(bundle: Path) -> list[str]:
    errors: list[str] = []

    root_index = bundle / "index.md"
    if not root_index.is_file():
        errors.append("missing knowledge/index.md")
    else:
        fm, err = parse_frontmatter(root_index)
        if err:
            errors.append(f"index.md: {err}")
        elif fm and fm.get("okf_version") != "0.1":
            errors.append("index.md: okf_version must be '0.1'")

    if not (bundle / "log.md").is_file():
        errors.append("missing knowledge/log.md")

    for md in collect_md_files(bundle):
        fm, err = parse_frontmatter(md)
        rel = md.relative_to(bundle)
        if err:
            errors.append(f"{rel}: {err}")
            continue

        missing = REQUIRED_FIELDS - set(fm.keys())
        if missing:
            errors.append(f"{rel}: missing required fields: {sorted(missing)}")

        doc_type = fm.get("type")
        if doc_type not in VALID_TYPES:
            errors.append(f"{rel}: invalid type '{doc_type}' (expected one of {sorted(VALID_TYPES)})")
        else:
            expected_dir = TYPE_DIRS[doc_type]
            if md.parent.name != expected_dir:
                errors.append(f"{rel}: type {doc_type} must live in {expected_dir}/")

        if doc_type == "Reference" and "resource" not in fm:
            errors.append(f"{rel}: Reference type requires 'resource' field")

    return errors


def main() -> int:
    bundle = find_bundle_root()
    if not bundle.is_dir():
        print(f"ERROR: bundle not found at {bundle}", file=sys.stderr)
        return 2

    errors = validate(bundle)
    if errors:
        print(f"FAIL: {len(errors)} issue(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {bundle} passes OKF v0.1 validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
