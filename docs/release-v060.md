# v0.6.0 implementation, audit findings and remaining work

## Current implemented scope

Implemented: seven macro slots with six government/public histories; VIX withheld pending republication permission; 1/5/10-year and full-range charts; CPI/PCE index and calculated YoY switching; individual/all-series filters; per-chart numeric table and keyboard readout; reviewed economic-calendar publication with family completeness gates; JST/DST conversion and unknown-time handling; event selection focused on a -100/+60 calendar-day chart window.

The current market view is provider-hosted: TradingView widgets are the primary visible surface for stocks, ETFs, world indices and the FOMC/BOJ reaction board. Depending on exchange/provider entitlement, values may be real-time, delayed or EOD. Widget values are not stored or republished by this repository. The self-hosted stock/index snapshot remains frozen at 2026-09-10 for audit only and is hidden from normal current-market display.

Production runs refresh the six macro histories four times per day and probe official BLS, BEA and Federal Reserve calendar sources. A blocked or incomplete calendar family retains the prior reviewed schedule rather than publishing a partial family as current. Dashboard Health reports the current build's macro/calendar/market/browser state and the GitHub Actions run identifier.

Former release weaknesses addressed: misleading connected labels removed from macro; BLS missing-period markers and Treasury mixed-case headers handled; same-input deterministic generation; actual-release tests before publication; exact deployed HTML hash verification; source-failure retention; bounded numeric revision differences; no private source/data access by the public updater; bounded Chrome startup retry; stale self-hosted market values removed from normal display.

## 2026-09-15 audit findings

### P0 — consistency and trust

1. **Release/state metadata had multiple sources of truth.** The generated header still exposed v0.4.0, README described v0.6.0, and `data/current-state.json` remained v0.3.0. The visible header and freshness labels are now normalized by the reviewed presentation finalizer, but the underlying state model still needs consolidation.
2. **Static event copy could be mistaken for current calendar status.** The fixed eight-event research list is a 2026-09-13 reviewed fixture, while the macro calendar is continuously probed. The UI now labels that distinction explicitly.
3. **Frontend network wording was outdated.** TradingView is an intentional allowlisted external connection. The user-facing security wording now states that this exception exists while arbitrary connections/forms remain blocked by CSP.
4. **Private monthly audit pin must track every reviewed public source release.** A stale pin is intentionally blocking, not a warning. It must be advanced only after the public release passes its own gates.

### P1 — research-product quality

1. **The Overview and Reports layers are still mostly taxonomy, not an executive research brief.** The dashboard needs a current conclusion-first layer showing what changed, why it matters, evidence quality, market transmission, catalysts and invalidation.
2. **`topics` are research prompts rather than evidence-backed theses.** P1/P2 priority exists, but there is no systematic Market Impact / Evidence Strength / Portfolio Relevance / Urgency score on the public artifact.
3. **Strategic event watch and macro calendar use separate models.** The FOMC/BOJ tactical panel is hard-coded for September 2026 while the official calendar engine is rolling. These should share a typed event object with status transitions.
4. **Company research coverage is shallow.** The common checklist exists, but company-level growth, profitability, moat, management, capital allocation, balance-sheet health, dilution, accounting quality, governance, catalysts, valuation and sell conditions are not populated as comparable records.

### P2 — data depth

- lawful long-history self-hosted stock/index data and corporate-action adjustment under the JPY 0 rights constraint;
- consensus forecast / surprise data with explicit publication permission;
- point-in-time vintages for historical event/backtest work;
- automated research-report/news ingestion with source classification and editorial review;
- SEC filing publication once source-access and rights constraints are cleared;
- VIX republication approval.

### P3 — operating quality

- persisted 7-day / 30-day health history, first-attempt success rate, retry frequency and source-block frequency;
- physical Safari/iPhone verification;
- account-level notification-delivery confirmation;
- optional branded hostname only if it materially improves usability.

## Redesign boundary

A full visual rewrite is **not** required now. Navigation, security gates, deterministic release generation, responsive behavior and the provider-hosted market boundary are working and should be preserved.

A **data/model redesign is required before the dashboard becomes a mature investment-research terminal**. The recommended v0.7 architecture is:

`source evidence -> typed claim/event/company records -> verification/classification -> relevance scoring -> scenario/catalyst layer -> presentation renderer -> publication-rights gate -> browser/release QA`

The source of truth should move away from strings patched across `base.html`, `build_dashboard.py`, `build_release.py`, `macro.js` and `dashboard_finalize.py`. A single typed release-state object should own version, verified timestamp, freshness, active event phase, data availability and module status. Presentation finalization should become formatting only, not a second state-management layer.

The public information architecture should converge toward:

1. Executive Overview
2. Macro / Rates / FX
3. Global Markets / Positioning
4. AI / Semiconductors / Cloud / Data Centers
5. Japan / TOPIX / Policy
6. Company Watchlist
7. Event Calendar / Catalyst Map
8. Portfolio Sensitivity (public generic mode only)
9. Geopolitical / Tail Risks
10. Evidence / Sources / Update Log

Existing stable IDs and working tabs should be migrated incrementally rather than replaced in one release.

## Release and operating constraints

The zero-cost market-data policy remains unchanged. Do not weaken rights gates or scrape provider-hosted widgets to obtain fresher quotes. The TradingView embed is the intentional frontend-network exception; other data paths remain server-side and allowlisted.

Test evidence must be taken from the final release workflow and private audit, not inferred from this document. Scheduled runs can be delayed. A PASS verifies the defined gates; it is not proof of zero vulnerabilities or economic-data correctness.
