# Deferred work — initiative-gate-omega-c-on-saturation

CAP-2 (PR #31) and CAP-4 sticky (PR #34) wording synced in the refactor sweep.

Package C Q5 Hass-stub locks (multi-tick latched decay persist; equal-value write-on-change side effects) closed in PR #43.

## Deferred from: code review of plan-package-c-latch-hygiene.md (2026-10-17)

- ADR 0003 Guards still document latched skip-adapt + decay but omit Package C `clear_steady()` on `latch_at_start` and app-level `_blow_up_warned` episode WARN; Q6 scoped companion only.
- Epic retrospective / deferred-work framing still leave AI-3 / WARN open-item narrative without an explicit Package C close-out note for AI-1/AI-2.
