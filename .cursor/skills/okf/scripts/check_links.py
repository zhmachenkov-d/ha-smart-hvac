#!/usr/bin/env python3
"""Report broken bundle-relative links in knowledge/."""

from __future__ import annotations

import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[([^\]]*)\]\((/[^)]+)\)")


def find_bundle_root() -> Path:
    script = Path(__file__).resolve()
    return script.parents[4] / "knowledge"


def resolve_link(bundle: Path, target: str) -> Path | None:
    """Resolve /concepts/foo.md to bundle/concepts/foo.md."""
    if not target.startswith("/"):
        return None  # skip external / relative links
    rel = target.lstrip("/")
    # Strip anchor
    path_part = rel.split("#", 1)[0]
    if not path_part:
        return None
    candidate = bundle / path_part
    if candidate.is_file():
        return candidate
    if candidate.is_dir():
        return candidate
    return None


def collect_md_files(bundle: Path) -> list[Path]:
    files = [bundle / "index.md", bundle / "log.md"]
    for sub in ("concepts", "decisions", "references", "playbooks", "raw"):
        d = bundle / sub
        if d.is_dir():
            files.extend(d.rglob("*.md"))
    return sorted(set(p for p in files if p.is_file()))


def check_links(bundle: Path) -> list[tuple[str, str, str]]:
    broken: list[tuple[str, str, str]] = []
    for md in collect_md_files(bundle):
        text = md.read_text(encoding="utf-8")
        rel_file = md.relative_to(bundle)
        for _label, target in LINK_RE.findall(text):
            if target.startswith("http://") or target.startswith("https://"):
                continue
            if not target.startswith("/"):
                continue
            # Links to repo root outside bundle (e.g. /.cursor/...) — resolve from repo root
            if target.startswith("/.cursor/") or target.startswith("/docs/"):
                repo_root = bundle.parent
                path_part = target.lstrip("/").split("#", 1)[0]
                if not (repo_root / path_part).is_file():
                    broken.append((str(rel_file), target, "file not found"))
                continue
            if resolve_link(bundle, target) is None:
                broken.append((str(rel_file), target, "file not found"))
    return broken


def main() -> int:
    bundle = find_bundle_root()
    if not bundle.is_dir():
        print(f"ERROR: bundle not found at {bundle}", file=sys.stderr)
        return 2

    broken = check_links(bundle)
    if broken:
        print(f"FAIL: {len(broken)} broken link(s)")
        for src, target, reason in broken:
            print(f"  - {src}: {target} ({reason})")
        return 1

    print(f"OK: all bundle-relative links resolve in {bundle}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
