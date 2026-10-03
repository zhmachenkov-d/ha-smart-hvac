"""Offline tests for Conventional Commits checker and workflow shape."""

from __future__ import annotations

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_checker():
    path = ROOT / "scripts" / "check_conventional_commits.py"
    spec = importlib.util.spec_from_file_location("check_conventional_commits", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cc = _load_checker()


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(repo: Path) -> None:
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")


def _commit_file(repo: Path, name: str, content: str, message: str) -> None:
    (repo / name).write_text(content, encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-m", message)


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.mark.parametrize(
    "message",
    [
        "feat: add something",
        "fix(opentherm): retry on timeout",
        "docs: add wiring diagram",
        "style: reformat imports",
        "refactor(hvac): extract zone helper",
        "perf: cache sensor reads",
        "test: cover idle heating demand",
        "build: bump appdaemon pin",
        "ci: add conventional commits gate",
        "chore: ignore local secrets",
        "feat(opentherm)!: replace status enum",
        "feat!: breaking without scope",
        "feat: subject\n\nBREAKING CHANGE: callers must update",
    ],
)
def test_valid_messages(message: str):
    assert cc.is_conventional(message)
    assert cc.validate_message("msg", message) is None


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
        "Feat: wrong case",
        "feature: not a type",
        "feat add missing colon",
        "feat:missing space",
        "feat:",
        "feat: ",
        "update readme",
        "Merge branch 'main' into feature",
    ],
)
def test_invalid_messages(message: str):
    assert not cc.is_conventional(message)
    assert cc.validate_message("msg", message) is not None


def test_check_title_exit_codes():
    assert cc.check_title("feat: ok") == 0
    assert cc.check_title("not conventional") == 1


def test_check_range_skips_merge_commits(tmp_path: Path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "a.txt", "a\n", "chore: base")
    base = _head(repo)

    _git(repo, "checkout", "-b", "feature")
    _commit_file(repo, "b.txt", "b\n", "feat: feature work")

    _git(repo, "checkout", "main")
    _commit_file(repo, "c.txt", "c\n", "chore: main progresses")

    _git(repo, "checkout", "feature")
    # Merge main into feature — non-CC merge subject must be ignored.
    merge = subprocess.run(
        ["git", "merge", "main", "-m", "Merge branch 'main' into feature"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert merge.returncode == 0, merge.stderr

    head = _head(repo)
    rev_range = f"{base}..{head}"
    old = os.getcwd()
    try:
        os.chdir(repo)
        assert cc.check_range(rev_range) == 0
    finally:
        os.chdir(old)


def test_check_range_fails_on_bad_non_merge(tmp_path: Path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "a.txt", "a\n", "chore: base")
    base = _head(repo)
    _commit_file(repo, "b.txt", "b\n", "not a conventional commit")
    head = _head(repo)

    old = os.getcwd()
    try:
        os.chdir(repo)
        assert cc.check_range(f"{base}..{head}") == 1
    finally:
        os.chdir(old)


def test_check_range_behind_main_uses_two_dot_not_three(tmp_path: Path):
    """When feature is behind main, three-dot includes main-only non-CC commits."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    _commit_file(repo, "a.txt", "a\n", "chore: base")
    _git(repo, "checkout", "-b", "feature")
    _commit_file(repo, "b.txt", "b\n", "feat: feature work")
    feature_head = _head(repo)

    _git(repo, "checkout", "main")
    _commit_file(repo, "c.txt", "c\n", "Move HVAC package without CC")
    main_tip = _head(repo)

    old = os.getcwd()
    try:
        os.chdir(repo)
        assert cc.check_range(f"{main_tip}...{feature_head}") == 1
        assert cc.check_range(f"{main_tip}..{feature_head}") == 0
    finally:
        os.chdir(old)


def test_main_cli_title():
    assert cc.main(["--title", "feat: ok"]) == 0
    assert cc.main(["--title", "bad"]) == 1


def test_conventional_commits_workflow_shape():
    path = ROOT / ".github" / "workflows" / "conventional-commits.yaml"
    text = path.read_text(encoding="utf-8")
    assert "on:" in text
    assert "pull_request" in text
    assert "pr-title:" in text
    assert "pr-commits:" in text
    assert "scripts/check_conventional_commits.py" in text
    assert "opened" in text
    assert "edited" in text
    assert "synchronize" in text
    assert "reopened" in text
    assert "base.sha }}..${{ github.event.pull_request.head.sha" in text
    assert "base.sha }}...${{ github.event.pull_request.head.sha" not in text
