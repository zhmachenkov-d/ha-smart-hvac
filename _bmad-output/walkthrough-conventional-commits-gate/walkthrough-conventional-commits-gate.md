# Walkthrough: Conventional Commits PR gate (PR #14)

Target: [PR #14](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/14) · branch `ci/conventional-commits-gate`

**Current block:** Wrap-up (done — walkthrough committed; PR #14 merge requested)

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Slice: Python checker** — done
- [x] **Slice: PR workflow + required checks** — done
- [x] **Slice: Offline tests** — done
- [x] **Periphery** — done

### Intent

Source: frozen Intent from [plan-conventional-commits-gate.md](../plan-conventional-commits-gate.md) (verbatim).

**Problem:** Conventional Commits are skill guidance only today, so bad PR titles or commit subjects can merge unchecked — and that will break or silently skip a future semantic-release train.

**Approach:** Add a Python/shell PR CI gate that fails when the PR title is not Conventional Commits **or** when any non-merge commit in the PR range is not, and make those checks required on the `branch-protection` ruleset. Scope is the gate only; python-semantic-release release automation is deferred.

**Review notes**

- Gate-only PR; PSR release train is in [deferred-work.md](../deferred-work.md).
- Ruleset already requires `pr-title` and `pr-commits` (added during build; other open PRs without this workflow may stay pending until rebase).

### Broad strokes

Dual CI gate: shared Python validator, two PR jobs, packaging/offline tests, skill note.

1. [`scripts/check_conventional_commits.py`](../../scripts/check_conventional_commits.py) — stdlib Conventional Commits checker (`--title` / `--range`, skips merges).
2. [`.github/workflows/conventional-commits.yaml`](../../.github/workflows/conventional-commits.yaml) — jobs `pr-title` and `pr-commits` on `pull_request`.
3. [`tests/test_conventional_commits.py`](../../tests/test_conventional_commits.py) — offline rules + workflow shape + behind-main two-dot coverage.
4. [`.cursor/skills/git-workflow/SKILL.md`](../../.cursor/skills/git-workflow/SKILL.md) — CI enforcement note.
5. Ruleset `branch-protection` — required checks `pr-title` / `pr-commits` (GitHub Settings, not in-repo).

### Slice: Python checker

Shared stdlib validator for PR titles and commit subjects. Types match the git-workflow skill; merge commits are skipped only in `--range` mode via `git log --no-merges`.

- [`scripts/check_conventional_commits.py`](../../scripts/check_conventional_commits.py) — `TYPES`, `SUBJECT_RE`, `check_title`, `check_range`, CLI `--title` / `--range`
- [`git-workflow/SKILL.md`](../../.cursor/skills/git-workflow/SKILL.md) — type list + CI note (wording guide; CI is source of enforcement)

### Slice: PR workflow + required checks

Two independent jobs on `pull_request` so title vs commits failures show separately. Title uses the event payload; commits use two-dot `base..head` with full history. Required status checks on ruleset `branch-protection` make a red job block merge.

- [`.github/workflows/conventional-commits.yaml`](../../.github/workflows/conventional-commits.yaml) — `pr-title` / `pr-commits`, `permissions: contents: read`, two-dot `CC_RANGE`
- Ruleset `branch-protection` (id `24390720`) — required contexts `pr-title`, `pr-commits` (GitHub Settings)

### Slice: Offline tests

Pytest covers the checker without GitHub Actions: valid/invalid subjects, merge-skip, behind-main three-dot vs two-dot, and workflow shape (job ids + `..` range).

- [`tests/test_conventional_commits.py`](../../tests/test_conventional_commits.py) — unit + temp-repo git cases + YAML shape lock

### Periphery

- [`_bmad-output/plan-conventional-commits-gate.md`](../plan-conventional-commits-gate.md) — build plan (`status: built`)
- [`_bmad-output/deferred-work.md`](../deferred-work.md) — PSR release train + migration note for other open PRs
- [`.cursor/skills/git-workflow/SKILL.md`](../../.cursor/skills/git-workflow/SKILL.md) — CI enforcement note (agents)
- This walkthrough folder — review narrative + log for PR #14

### Wrap-up

All blocks accepted. PR [#14](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/14) is the ship path; walkthrough files are still untracked on the feature branch.
