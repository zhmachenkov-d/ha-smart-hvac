#!/usr/bin/env python3
"""Rebuild type index.md files from frontmatter."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from frontmatter import parse_frontmatter_block

try:
    import yaml  # type: ignore

    def _parse_yaml(text: str) -> dict | None:
        data = yaml.safe_load(text)
        return data if isinstance(data, dict) else None

except ImportError:
    def _parse_yaml(text: str) -> dict | None:
        return parse_frontmatter_block(text)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

TYPE_CONFIG = {
    "concepts": "Concept",
    "decisions": "Decision",
    "references": "Reference",
    "playbooks": "Playbook",
}


def find_bundle_root() -> Path:
    script = Path(__file__).resolve()
    return script.parents[4] / "knowledge"


def parse_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    return _parse_yaml(match.group(1))


def build_index(section: str, expected_type: str, entries: list[tuple[str, dict]]) -> str:
    lines = [
        "---",
        f'okf_version: "0.1"',
        f"title: {section.title()}",
        f"description: Index of {section} in the knowledge bundle.",
        "---",
        "",
        f"# {section.title()}",
        "",
        f"| Title | Description |",
        f"|-------|-------------|",
    ]
    for filename, fm in sorted(entries, key=lambda x: x[1].get("title", x[0]).lower()):
        title = fm.get("title", filename)
        desc = fm.get("description", "")
        link = f"/{section}/{filename}"
        lines.append(f"| [{title}]({link}) | {desc} |")
    lines.append("")
    return "\n".join(lines)


def regen(bundle: Path, check_only: bool) -> list[str]:
    issues: list[str] = []

    for section, expected_type in TYPE_CONFIG.items():
        dir_path = bundle / section
        if not dir_path.is_dir():
            issues.append(f"missing directory {section}/")
            continue

        entries: list[tuple[str, dict]] = []
        for md in sorted(dir_path.glob("*.md")):
            if md.name == "index.md":
                continue
            fm = parse_frontmatter(md)
            if fm is None:
                issues.append(f"{section}/{md.name}: cannot parse frontmatter")
                continue
            if fm.get("type") != expected_type:
                issues.append(
                    f"{section}/{md.name}: expected type {expected_type}, got {fm.get('type')}"
                )
            entries.append((md.name, fm))

        content = build_index(section, expected_type, entries)
        index_path = dir_path / "index.md"
        if check_only:
            if index_path.is_file():
                existing = index_path.read_text(encoding="utf-8")
                if existing != content:
                    issues.append(f"{section}/index.md is stale (run without --check to regenerate)")
            else:
                issues.append(f"missing {section}/index.md")
        else:
            index_path.write_text(content, encoding="utf-8")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate OKF type index files")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if indexes are stale instead of rewriting",
    )
    args = parser.parse_args()

    bundle = find_bundle_root()
    if not bundle.is_dir():
        print(f"ERROR: bundle not found at {bundle}", file=sys.stderr)
        return 2

    issues = regen(bundle, check_only=args.check)
    if issues:
        print(f"FAIL: {len(issues)} issue(s)")
        for i in issues:
            print(f"  - {i}")
        return 1

    action = "up to date" if args.check else "regenerated"
    print(f"OK: type indexes {action} for {bundle}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
