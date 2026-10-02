"""Dual-layout / public-readiness packaging invariants."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILTERED_APPS_YAML_PATHS = (
    "appdaemon/apps/apps.yaml",
    "apps/apps.yaml",
)


def test_exclusive_session_app_dir_points_at_repo_apps():
    text = (ROOT / "appdaemon" / "appdaemon.yaml").read_text(encoding="utf-8")
    assert "app_dir: ../apps" in text
    assert not (ROOT / "appdaemon" / "apps" / "hvac").exists()
    assert not (ROOT / "appdaemon" / "apps").is_symlink()


def test_fresh_clone_example_has_placeholders_only():
    example = ROOT / "apps" / "apps.yaml.example"
    assert example.is_file()
    text = example.read_text(encoding="utf-8")
    assert "YOUR_" in text
    assert "module: hvac" in text
    tracked = subprocess.check_output(
        ["git", "ls-files", "apps"],
        cwd=ROOT,
        text=True,
    )
    assert "apps/apps.yaml.example" in tracked
    assert "apps/apps.yaml\n" not in tracked and not tracked.endswith("apps/apps.yaml")


def test_history_has_no_live_apps_yaml_entity_ids():
    out = subprocess.check_output(
        [
            "git",
            "log",
            "--all",
            "--",
            *FILTERED_APPS_YAML_PATHS,
        ],
        cwd=ROOT,
        text=True,
    )
    assert out.strip() == "", "filtered apps.yaml paths still present in history"


def test_readme_production_and_stranger_app_dir_examples():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "addon_configs/a0d7b954_appdaemon" in readme
    assert "app_dir: /config/apps" in readme
    assert "app_dir: /config/appdaemon/apps" in readme
    assert "hacs/integration#4442" in readme
    assert "public-readiness" in readme
    assert "hacs.json" in readme
    assert "appdaemon.readthedocs.io" in readme
