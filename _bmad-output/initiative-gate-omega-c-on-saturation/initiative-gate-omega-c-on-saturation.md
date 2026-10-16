---
tracker_id: ""
key: ""
type: initiative
title: "Gate ωc on saturation"
parent: none
covers: [CAP-1, CAP-2, CAP-3, CAP-4, CAP-5, CAP-6]
after: []
assignee: ""
risk: medium
estimate: ""
estimate_basis: ""
---

# Gate ωc on saturation

## Description

After sustained Critical Zone underheat with Set Water Temperature at clamp, healthy-but-saturated ticks still ratchet online ωc upward until a later ESO reset latches soft-kill. This initiative delivers `_bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/` — directional commit clamp, strict apply, write-on-change, latched ωc decay with adapt skipped, docs under criterion A, and regression tests.

## Outcome

Operators keep a recoverable LADRC loop under winter max-SWT underheat; the signal is the spec's Success signal (no upward ωc ratchet at max, latched decay on real `|u_track|`, redundant SWT writes skipped without freezing the tick).

## Done when

1. At `setpoint_max`, upward ωc is not committed and downward may be; symmetric at `setpoint_min`; guard trip still blocks commit.
2. On a blocked tick, tracking uses current committed ωc only (no one-tick proposed-ωc ratchet).
3. Identical plant entity float skips `number/set_value` while the tick continues; unreadable entity stays fail-closed (abort).
4. With latch already active, adapt is skipped and ωc decays by `max_rate_fraction` while `|u_track| > 0.8 · u_track_max` (or non-finite) until residue is at or below that band.
5. ADR 0003 Guards and house-calibration §5 describe criterion A and these behaviors (not headroom-only full freeze).
6. CAP-6 automated tests pass and fail if the ratchet, equality-skip abort, or missing latched decay return.

## Boundaries

Capability boundary: HVAC AppDaemon LADRC ωc auto-tune and plant write path. Not full freeze on any clamp, not ESO anti-windup, not changing `u_track_max` or 40/55 limits, not online `b0`/`ωo`/MADRC. One epic owns the whole fix. Tracer path: directional+strict → write-on-change → latch decay → docs → sweep.

- Touch point: `LadrcTuner` persist/rate limits — consumed for decay step/floor; owner: epic-gate-omega-c-on-saturation
- Touch point: ADR 0003 + house-calibration — amended in place; owner: epic-gate-omega-c-on-saturation

## References

- spec — _bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation.md, section Capabilities
- constraint — the same spec, section Constraints
- companion — _bmad-output/initiative-gate-omega-c-on-saturation/spec-gate-omega-c-on-saturation/control-tick-behaviors.md
- forge — _bmad-output/initiative-gate-omega-c-on-saturation/forge-gate-omega-c-on-saturation/forge-gate-omega-c-on-saturation.md

## Notes

- Decision: one epic for CAP-1–CAP-6; no platform-baseline epic — brownfield fix on existing app (2026-10-17).
- Decision: repo ticketing store (2026-10-17).
