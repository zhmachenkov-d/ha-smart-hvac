# Tick flow (gate ωc on saturation)

```mermaid
flowchart TD
  S{Latch already active?}
  S -->|yes| C[compute_tracking with current ωc]
  S -->|no| A[maybe_adapt propose ωc]
  A --> B{Directional blocks apply?}
  B -->|yes| C
  B -->|no| D[compute_tracking with proposed ωc]
  C --> E[guard_u_track]
  D --> E
  E --> F{_write_setpoint}
  F -->|entity unreadable| X[fail-closed: abort tick]
  F -->|same float: skip set_value| G[ESO reset if needed / advance]
  F -->|different: set_value| G
  G --> H{Latch active and |u_track| > 0.8·u_track_max or non-finite?}
  H -->|yes| I[Step ωc down max_rate_fraction; persist]
  H -->|no| J{should_commit_omega_c?}
  J -->|yes| K[commit_omega_c]
  J -->|no| L[skip commit]
  I --> M[end tick]
  K --> M
  L --> M
```

While latch is already active, adapt is skipped for the whole tick. Decay persist is a separate branch and is not blocked by the guard-trip skip of normal `commit_omega_c`.
