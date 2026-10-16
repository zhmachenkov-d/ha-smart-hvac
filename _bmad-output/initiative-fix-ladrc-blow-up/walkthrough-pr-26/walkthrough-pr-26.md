# Walkthrough — PR #26: retune defaults, u_track_max, ADR 0002 amend

Target: [PR #26](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/26) (`fix/1-3-retune-defaults-u-track-max` → `main`)
Focus: risks, boundaries, merge-readiness
Current block: closed — walkthrough complete; story 1.3 marked `done`; PR #26 merge + branch delete in wrap-up

## Blocks

- [x] **Intent** — done
- [x] **Broad strokes** — done
- [x] **Config handoff** — done
- [x] **CAP-3(b) boundedness** — done
- [x] **ADR 0002 must-language** — done
- [x] **Periphery** — done

## Intent

Source: [story-retune-defaults-u-track-max-config-adr-amend-plan.md](../epic-fix-ladrc-blow-up/story-retune-defaults-u-track-max-config-adr-amend-plan.md) (frozen Intent, pasted verbatim).

**Problem:** Example LADRC gains are still Huang (`b0=2.8`, `omega_o=19.49`); there is no `u_track_max` config handoff for the guard story; ADR 0002 lacks the CAP-4 amendment bullets.

**Approach:** Retune `apps.yaml.example` `b0`/`omega_o` to the CAP-5 thermal band; add `u_track_max` (default 100) on `LadrcConfig` / parse / example (field only — guard wires it in entry 4); lock CAP-3(b) boundedness on those example defaults under continuous-form + C known-input; amend ADR 0002; leave ADR 0003 untouched (ωc-only).

Review focus (user): risks, boundaries, merge-readiness.

**Review notes (Intent):**
1. Guard not in scope — no `hvac_app` `u_track_max` refs; field-only handoff until entry 4.
2. ADR 0003 untouched (absent from diff).
3. Example `omega_c` stays `0.053`; Approach retunes `b0`/`omega_o` only.


## Broad strokes

What the change is: product example leaves Huang gains for the thermal band; `u_track_max` lands on config only (no guard yet); CAP-3(b) locks multi-tick boundedness on example-aligned gains; ADR 0002 gets CAP-4 must-language; ADR 0003 stays untouched.

Entry points (open in this order):

1. [apps.yaml.example ladrc block](../../../apps/apps.yaml.example) — thermal `b0`/`omega_o`, `omega_c=0.053` comment, `u_track_max` + guard-not-yet comment
2. [LadrcConfig.u_track_max + with_omega_c](../../../apps/hvac/models.py) — field default 100; tuner path preserves it
3. [parse_config u_track_max](../../../apps/hvac/config.py) — optional YAML key, default 100.0
4. [test_cap3b_example_aligned_continuous_c_bounded](../../../tests/test_ladrc.py) — CAP-3(b) multi-tick `|u_track|<100`
5. [ADR 0002 CAP-4 must bullets](../../../docs/adr/0002-ladrc-critical-zone-control.md) — exp_map fails; continuous ESO; known input C; Huang forbidden; house calibration

**Review notes (Broad strokes):**
1. Live [`with_omega_c`](../../../apps/hvac/hvac_app.py) at ~L87 is why preserve matters — covered in Config handoff slice, not as a Broad strokes entry.
2. CAP-3(b) ≠ CAP-5 on `omega_c`: example-aligned `0.053` vs thermal unit-test `0.01`.
3. Test matrix green: 27 pytest passed; ruff clean; ADR 0003 diff empty.
4. Example comments + ADR must-language match story Always/Never (spot-checked).

## Config handoff

`u_track_max` is config-only in this story: dataclass + parse + example. The blow-up guard (entry 4) does not read it yet. Live YAML without the key still parses to 100. `with_omega_c` must copy the field so the online tuner does not drop it each tick.

- [models.py LadrcConfig](../../../apps/hvac/models.py) — `u_track_max: float = 100.0`; preserved in `with_omega_c`
- [config.py parse](../../../apps/hvac/config.py) — `raw.get("u_track_max", 100.0)`
- [test_parse_u_track_max_explicit](../../../tests/test_ladrc_tuner.py) / [test_with_omega_c_preserves_u_track_max](../../../tests/test_ladrc_tuner.py) / [test_parse_apps_yaml_example](../../../tests/test_ladrc_tuner.py)

**Review notes (Config handoff):**
1. `with_omega_c` hand-lists fields — preserve is present; future fields have the same footgun.
2. No sign/range validation on `u_track_max` — OK while unused; defer to entry 4.
3. omit→100 + preserve + example tests green (4 focused tests).
4. Story 1.4 should read `u_track_max` from `effective_ladrc` (post-`with_omega_c`), not raw `config.ladrc`.

## CAP-3(b) boundedness

Locks that example-aligned gains under continuous-form advance and known input `(command − u_ff)` stay finite with `|u_track|<100` for N=80 on the locked scenario (`y=21`, `Tr=21.2`, `uff=40`, clamp `[40,55]`, `dt=60`). Product example `omega_c=0.053` (not CAP-5 unit-test `0.01`). Does not assert the future guard; only the thermal-band boundedness bar.

- [test_cap3b_example_aligned_continuous_c_bounded](../../../tests/test_ladrc.py)

**Review notes (CAP-3(b)):**
1. Product `omega_c=0.053` is stricter than CAP-5 `0.01` (measured max `|u_track|` ≈36).
2. Bar `|u_track|<100` with comfortable margin.
3. Shares `_run_thermal_c_ticks` C-path helper with CAP-5.
4. Helper numbers vs YAML dual source bridged by `test_parse_apps_yaml_example`.
5. Tests green with CAP-5 continuous/exp_map neighbors.

## ADR 0002 must-language

CAP-4 amendment: normative must / must-not (not soft discourage). No integrator recipe (no Euler substep count). ADR 0003 must remain byte-identical.

- [ADR 0002](../../../docs/adr/0002-ladrc-critical-zone-control.md) — exp_map fails/must not return; continuous-form ESO; known input post-clamp `(command − u_ff)`; Huang must not; house calibration needed
- ADR 0003: verify empty `git diff` (out of narrative scope for edits — periphery check)

**Review notes (ADR 0002):**
1. Soft "not copy-paste" replaced by must/must-not.
2. All five CAP-4 bullets present.
3. No integrator recipe (no Euler/substep count).
4. ADR 0003 diff empty (byte-identical).
5. Guard / `u_track_max` out of CAP-4 scope (entry 4 / CAP-2).

## Periphery

- [story plan](../epic-fix-ladrc-blow-up/story-retune-defaults-u-track-max-config-adr-amend-plan.md) — status `done`; planning artifact
- [party-mode memlog](../party-mode/memories/installed/.memlog.md) — incidental party session log (not load-bearing)
- PR test plan: pytest ladrc + tuner; ruff; empty ADR 0003 diff; spot-check ADR/example comments

**Review notes (Periphery):**
1. Story plan status set `done` (Wrap-up).
2. Memlog incidental — A/Stay/Hard (optional clutter, not blocking).
3. CI green on PR #26.
4. `walkthrough-pr-26/` still local untracked (commit after Wrap-up).
