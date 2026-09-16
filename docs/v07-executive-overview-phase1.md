# v0.7 Executive Overview Phase 1

This release adds a conservative Executive Overview inside the existing `overview` panel without changing stable navigation IDs.

## Scope

- Surface the four typed September 2026 FOMC/BOJ policy events from `scripts/policy_events.py`.
- Display schedule facts separately from outcome-verification state.
- Show a small Systemic Market Map using explicitly labelled `INFERENCE` chains only.
- Do not add new self-hosted market quotes, consensus estimates, portfolio allocations, or buy/sell ratings.
- Do not promote an event to completed because a scheduled clock time has passed.

## Public interpretation

`FACT` means the schedule/state is backed by the typed event record and its official source link. `INFERENCE` means the transmission path is an analytical model, not a verified commercial relationship or investment recommendation.

## Next phase

After this Phase 1 layout passes release QA, add the verified entity/index registry and evidence-backed company/theme mappings behind the same overview structure.
