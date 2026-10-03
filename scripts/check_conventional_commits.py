#!/usr/bin/env python3
"""Validate Conventional Commits subjects / PR titles (stdlib only)."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
)

# Matches skill types; optional scope; optional breaking `!`; requires subject text.
SUBJECT_RE = re.compile(
    rf"^({'|'.join(TYPES)})"  # type
    r"(\([^)]+\))?"  # optional scope
    r"!?"  # optional breaking marker
    r": .+"  # colon, space, non-empty subject
)


def subject_line(message: str) -> str:
    """Return the first line of a commit message or PR title."""
    return message.splitlines()[0].strip() if message else ""


def is_conventional(message: str) -> bool:
    """True if the first line matches Conventional Commits type/shape."""
    return bool(SUBJECT_RE.match(subject_line(message)))


def validate_message(label: str, message: str) -> str | None:
    """Return an error string if invalid, else None."""
    subject = subject_line(message)
    if not subject:
        return f"{label}: empty subject"
    if not is_conventional(message):
        return (
            f"{label}: not Conventional Commits "
            f"(expected type in {{{', '.join(TYPES)}}}, optional scope, "
            f"optional !, then ': <subject>'): {subject!r}"
        )
    return None


def check_title(title: str) -> int:
    err = validate_message("PR title", title)
    if err:
        print(err, file=sys.stderr)
        return 1
    return 0


def _git_commit_subjects(rev_range: str) -> list[tuple[str, str]]:
    """Return (shortsha, subject) for non-merge commits in rev_range."""
    result = subprocess.run(
        [
            "git",
            "log",
            "--no-merges",
            "--pretty=format:%h\t%s",
            rev_range,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip() or "git log failed"
        raise RuntimeError(stderr)
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    out: list[tuple[str, str]] = []
    for line in lines:
        sha, _, subject = line.partition("\t")
        out.append((sha, subject))
    return out


def check_range(rev_range: str) -> int:
    try:
        commits = _git_commit_subjects(rev_range)
    except RuntimeError as exc:
        print(f"git range {rev_range!r}: {exc}", file=sys.stderr)
        return 1

    failures: list[str] = []
    for sha, subject in commits:
        err = validate_message(f"commit {sha}", subject)
        if err:
            failures.append(err)

    if failures:
        for err in failures:
            print(err, file=sys.stderr)
        print(
            f"{len(failures)} non-merge commit(s) failed Conventional Commits "
            f"check in range {rev_range!r}",
            file=sys.stderr,
        )
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint a PR title or git commit subjects for Conventional Commits.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--title",
        metavar="TEXT",
        help="Validate a single PR title (or subject line).",
    )
    group.add_argument(
        "--range",
        dest="rev_range",
        metavar="REV_RANGE",
        help="Validate non-merge commit subjects in a git revision range "
        "(e.g. base..head). Merge commits are skipped.",
    )
    args = parser.parse_args(argv)

    if args.title is not None:
        return check_title(args.title)
    return check_range(args.rev_range)


if __name__ == "__main__":
    sys.exit(main())
