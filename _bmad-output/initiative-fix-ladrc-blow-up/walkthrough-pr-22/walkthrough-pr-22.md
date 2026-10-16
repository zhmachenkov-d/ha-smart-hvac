# Walkthrough — PR #22: continuous-form ESO in LadrcState

Target: [PR #22](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/22) (`fix/1-1-continuous-form-eso` → `main`)
Focus: risks, boundaries, merge-readiness
Current block: all blocks done — **Wrap-up** suggested

## Blocks

- [x] **Intent** — done (changed during review: tighter AC + Euler comment in 8c09bc2)
- [x] **Broad strokes** — done
- [x] **Continuous-form advance** — done
- [x] **CAP-5 lock tests** — done
- [x] **Periphery** — done

## Intent

Source: [story-continuous-form-eso-in-ladrcstate-plan.md](../epic-fix-ladrc-blow-up/story-continuous-form-eso-in-ladrcstate-plan.md) (frozen Intent, pasted verbatim).

**Problem:** Production `LadrcState.advance` uses exp_map (`α = 1 − exp(−ωo·dt)`, `g1=2α`, `g2=α²`). At `dt=60` that discrete map is wrong: Huang-scale `omega_o` saturates (`α→1`); thermal-band gains need not saturate `α`, yet multi-tick runs still diverge. CAP-5 requires continuous-form ESO.

**Approach:** Replace production exp_map with continuous-form integration (`β1=2ωo`, `β2=ωo²` over the sample; RK/substeps — reject single-step Euler over full `dt` if AC fails). Lock CAP-5 with a **mandatory frozen exp_map helper**: same thermal+C scenario diverges under the helper and stays bounded under production `advance`. Tracer may merge before story 1.2; does not close epic Success. Huang+absolute CAP-3a case deferred (see [deferred-work.md](../deferred-work.md)).

Review focus (user): risks, boundaries, merge-readiness.

Review notes: risk1 → tighter AC; risk2 → comment fix; risk4 → accepted.

## Broad strokes

What the change is: production `LadrcState.advance` switches from α-map ESO to continuous-form β1/β2 Euler with 2 substeps; CAP-5 locked by frozen exp_map helper + multi-tick thermal+C tests. Review focus remains risks/boundaries/merge-readiness.

Entry points (open in this order):

1. [ladrc.py advance](../../../apps/hvac/ladrc.py) — continuous-form ESO integration (β1=2ωo, β2=ωo², 2 Euler substeps); replaced production exp_map.
2. [_ESO_EULER_SUBSTEPS](../../../apps/hvac/ladrc.py) — documents why 2 substeps for thermal CAP-5 ωo/dt (exact |1−2hωo| numbers after review fix).
3. [_advance_exp_map + _run_thermal_c_ticks](../../../tests/test_ladrc.py) — frozen pre-change α-map on the same `LadrcState`; shared thermal+C harness for CAP-5 contrast.
4. [test_cap5_exp_map_thermal_c_diverges / test_cap5_continuous_thermal_c_bounded](../../../tests/test_ladrc.py) — CAP-5 lock: helper diverges; production stays |u_track|<100 for N=80.
5. [story plan Boundaries](../epic-fix-ladrc-blow-up/story-continuous-form-eso-in-ladrcstate-plan.md) — Always/Never + tracer merge rules (not epic Success).

## Continuous-form advance

Production ESO no longer uses the α-map. Each sample integrates the continuous-form ODEs with forward Euler over `_ESO_EULER_SUBSTEPS` equal pieces of `dt`. Gains come from `config.omega_o` / `config.beta2` (β1=2ωo, β2=ωo²). `compute_tracking` / `reset` / `clear` stay untouched — boundary for merge risk.

- [advance](../../../apps/hvac/ladrc.py) — ż1/ż2 Euler loop; sets `_last_u_applied`
- [_ESO_EULER_SUBSTEPS](../../../apps/hvac/ladrc.py) — fixed 2; thermal CAP-5 numbers in comment
- [LadrcConfig.beta2 / omega_o](../../../apps/hvac/models.py) — reused, not changed in this PR

Residual (accepted): 2 substeps sized for locked ωo=0.03; not a stability guarantee across the full nudge band.

## CAP-5 lock tests

CAP-5 is locked by a paired contrast on the same thermal+C scenario: frozen exp_map must diverge; production continuous-form must keep every-tick |u_track|<100 for N=80. The harness clamps plant write and feeds ESO known input `command−u_ff` (path C) — deliberately not the live absolute-command path in hvac_app.

- [_thermal_config / locked constants](../../../tests/test_ladrc.py) — b0=5e-4, omega_o=0.03, omega_c=0.01, dt=60, N=80, clamp [40,55]
- [_advance_exp_map](../../../tests/test_ladrc.py) — frozen α-map body mutating the same LadrcState
- [_run_thermal_c_ticks](../../../tests/test_ladrc.py) — shared loop; use_exp_map selects contrast vs pass
- [test_cap5_exp_map_thermal_c_diverges](../../../tests/test_ladrc.py) — non-finite or |u_track|≥1e6
- [test_cap5_continuous_thermal_c_bounded](../../../tests/test_ladrc.py) — finite; |u_track|<100 each tick
- [test_eso_bounded_with_60s_dt](../../../tests/test_ladrc.py) — one-step smoke; tightened in review to 1<|Δz1|<3

Merge note: proves discretization CAP-5, not live bang-bang / epic Success.

## Periphery

- [story-continuous-form-eso-in-ladrcstate-plan.md](../epic-fix-ladrc-blow-up/story-continuous-form-eso-in-ladrcstate-plan.md) — story plan + frozen Boundaries + review triage
- [deferred-work.md](../deferred-work.md) — Huang+absolute CAP-3a divergence deferred from this tracer
- [PR #22](https://github.com/zhmachenkov-d/ha-smart-hvac/pull/22) title/body — Conventional Commits; messaging = CAP-5 tracer not blow-up fixed
- CI on PR — lint/test/pr-title/pr-commits/validate-hacs (includes review commit 8c09bc2)
- Not in PR: hvac_app, apps.yaml.example, ADRs, test_ladrc_tuner — intentionally untouched
