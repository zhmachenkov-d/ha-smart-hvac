---
tracker_id: ""
key: ""
type: epic
title: "Fix LADRC u_track blow-up"
parent: initiative-fix-ladrc-blow-up
covers: [CAP-1, CAP-2, CAP-3, CAP-4]
after: []
assignee: ""
risk: high
estimate: ""
estimate_basis: ""
---

# Fix LADRC u_track blow-up

## Description

Retune plant-channel LADRC defaults for absolute Set Water Temperature at `dt=60`, add an `hvac_app`-only finite/magnitude blow-up guard with a config threshold (default 100 °C), lock behavior with regression tests, and amend ADR 0002. Spec: `spec-fix-ladrc-blow-up/` beside this file.

## Outcome

Under heating demand the plant no longer bang-bangs 40↔55 from exploded `u_track`; the spec Success signal is the check.

## Requirements

- CAP-1: Plant-channel defaults (`b0`, `omega_o`) keep ESO/`u_track` numerically stable under absolute SWT at 60 s. (spec Capabilities)
- CAP-2: `hvac_app` detects non-finite or over-threshold `|u_track|`, resets ESO, issues `clamp(u_ff)`, logs WARNING once per episode. (spec Capabilities)
- CAP-3: Tests reproduce old divergence, assert new-default boundedness, and cover the guard path. (spec Capabilities)
- CAP-4: ADR 0002 amended; ADR 0003 remains ωc-only. (spec Capabilities)

## Done when

1. Multi-tick advance with new example defaults, `y≈21`, `u∈[40,55]` keeps `u_track`/`z` finite and `|u_track|` in tens of °C.
2. Poisoned or exploded `u_track` yields feedforward-only command + ESO reset + WARNING; loop recovers without waiting for zone change / idle / plant-off.
3. Regression suite fails on old/large gains or missing guard and passes on the fixed path (`uv run pytest`).
4. ADR 0002 carries the Huang/`dt=60`/absolute-SWT warning and house-calibration note.

## Boundaries

HVAC AppDaemon LADRC + example/config wiring + ADR 0002 prose. Not feedforward structure, Critical Zone selection, online `b0`/`omega_o` adaptation, setpoint min/max changes, or a guard API inside `LadrcState` (spec Non-goals).

## References

- parent — _bmad-output/initiative-fix-ladrc-blow-up/initiative-fix-ladrc-blow-up.md
- spec — _bmad-output/initiative-fix-ladrc-blow-up/epic-fix-ladrc-blow-up/spec-fix-ladrc-blow-up/spec-fix-ladrc-blow-up.md
- constraint — the same spec, section Constraints
- adr — docs/adr/0002-ladrc-critical-zone-control.md
- adr — docs/adr/0003-online-ladrc-omega-c-auto-tune.md (ωc-only; unchanged)

## Notes

- Decision: blow-up guard in `hvac_app` only; magnitude threshold is config default 100 °C (spec Q&A, 2026-10-16).
- Decision: no platform-baseline epic; brownfield (2026-10-16).
- Decision: inception 2026-10-16 — tracer bullet is entry 1 (retune + threshold config + ADR + diverge/boundedness tests); entry 2 is the guard (after 1). CAP-3 split across both. No refactor sweep (2 entries). Build-auto/loop: `plan_checkpoint` and `done_checkpoint` on both entries.
- Decision: optional refuse-to-advance after guard trip is in scope for entry 2 (2026-10-16).
