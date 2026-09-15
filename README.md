# Economics Research Dashboard v0.6.0

Independent public-market research dashboard. The public site is generated from versioned source, validated data, explicit publication-rights gates, browser regression checks, and an exact HTTPS artifact check.

## Current production model

The dashboard combines three different data modes and labels them separately:

1. **Provider-hosted market view** — current stock, ETF, index and policy-reaction views use the official TradingView embed. Depending on market/exchange entitlements, TradingView may show real-time, delayed, or end-of-day values. Those widget quote values are not ingested, cached, transformed, or republished by this repository. CI intentionally blocks the third-party quote response during deterministic browser QA, so provider-hosted delivery and successful observation of a current quote are treated as different states.
2. **Self-hosted macro histories** — six government/public histories are refreshed four times per day at 01:17 / 07:17 / 13:17 / 19:17 JST. VIX remains withheld pending republication permission.
3. **Reviewed archive data** — the repository-owned stock/index snapshot remains frozen at 2026-09-10 for audit and regression purposes. It is hidden from normal current-market display and is not used for current-price decisions. Hidden means visually hidden: the reviewed archive remains present in the published HTML payload until a later rights-safe migration removes it from the public artifact.

The runtime navigation contains the market, research, scenario, event, macro and operations views. The macro module includes long histories, period switching, source-health status, year-aware economic-calendar handling, and event-linked chart windows.

## Calendar and event handling

Production runs probe official BLS, BEA and Federal Reserve calendar sources. Calendar publication is fail-closed by family: a complete/reviewed family may update, while blocked or incomplete families retain the previously reviewed schedule instead of publishing a partial calendar as current.

The strategic event panel also contains a separately reviewed FOMC / Bank of Japan watch for September 2026. This short-horizon policy panel is not the authoritative source for the full economic calendar; the macro calendar is the continuously checked release-calendar layer.

## Dashboard Health

The `出典・運用` view exposes current-build health for:

- macro retrieval freshness;
- economic-calendar source status;
- provider-hosted market delivery mode separately from quote-observation status;
- legacy market public presence separately from visual visibility;
- fail-closed browser QA behavior;
- the GitHub Actions run identifier and scheduled execution times.

The v0.7 migration introduces a typed operational-state contract for these distinctions. The visible dashboard still reports release version v0.6.0 until the broader v0.7 information architecture is released.

Historical 7-day / 30-day uptime and first-attempt success rates are not yet persisted in the dashboard. Current health is a build-state view, not an uptime-monitoring service.

## Privacy and external connections

The dashboard does not use personal holdings, account connections, forms, analytics, advertising, browser persistence, local storage, or browser-side API keys.

The provider-hosted TradingView widgets are the intentional exception to the otherwise closed frontend network boundary: opening pages that contain a widget causes the visitor browser to connect to allowlisted TradingView script/frame origins. The dashboard discloses this near the widget. Source links to regulators, issuers and agencies remain user-initiated navigation with no-referrer behavior.

The CSP restricts scripts and frames to the reviewed TradingView embed boundary. The deterministic CI browser blocks TradingView network traffic while validating dashboard behavior, so the release can be tested without depending on live third-party widget responses. This also means CI does not certify the arrival or freshness of a TradingView quote shown to a visitor.

## Market-data rights boundary

`scripts/market_refresh_guard.py` performs no quote-provider retrieval and cannot update `site/data/market.json`. A self-hosted market series may refresh only after its registry entry has explicit permission for automated retrieval, storage/caching, transformation, public display and redistribution and still satisfies the JPY 0 monthly-cost policy.

Until then, the current market view remains provider-hosted and the self-hosted September 10 snapshot remains an audit archive. See `docs/market-data-automation.md`.

## Automatic macro update hardening

The updater rejects responses that drop previously published primary or auxiliary observation dates. A failing or truncated provider response retains the previous validated series and its original successful retrieval timestamp instead of replacing it with incomplete history.

Transient GET failures receive at most one retry. BLS POST requests and HTTP 403/429 responses are not automatically retried. Output writes are atomic and revalidated before replacement. Four production runs per day keep the current BLS query volume below the documented unregistered limit under the existing two-window history configuration.

A post-deployment `refresh-health` job fails visibly when macro retrieval is degraded, while safe retained data can remain published. SEC and calendar probes are separately classified so source access blocks are not silently presented as successful data ingestion.

## Build and release gates

The production workflow currently performs, in order:

1. legacy regression tests;
2. market-data rights gate;
3. SEC and official-calendar probe tests;
4. macro retrieval or PR snapshot fixture;
5. calendar publication and rights checks;
6. release generation;
7. release, v0.7 state-contract, calendar, market, SEC and browser-retry tests;
8. Dashboard Health / provider-hosted market presentation finalization;
9. 390 / 768 / 1440 pixel browser regression checks;
10. allowlisted publication and reproducibility checks;
11. Pages deployment;
12. exact HTTPS SHA-256 verification;
13. post-deployment refresh-health evaluation.

No post-validation quote patch is applied. Builds from the same validated inputs are deterministic. Browser QA covers the specified viewport widths but is not physical Safari/iPhone certification.

## Current limitations and next work

The main remaining product gaps are:

- migrate all legacy version, event and module-state strings to the typed release/state contract rather than keeping multiple source layers;
- a unified event model for strategic policy events and the continuously checked macro calendar;
- evidence-backed research items instead of mostly static topic prompts;
- automated research-report ingestion with FACT / ESTIMATE / INFERENCE / RUMOR classification;
- remove the legacy stock/index archive from the public artifact when the regression/rights design no longer requires public-payload retention;
- lawful long-history self-hosted stock/index data if a JPY 0 source with sufficient rights becomes available;
- consensus forecasts and surprise data with explicit publication rights;
- point-in-time data vintages for historical backtesting;
- persisted 7-day / 30-day operational-health history;
- physical mobile/Safari verification;
- VIX republication approval.

See `docs/release-v060.md`, `docs/data-rights.md`, and `docs/market-data-automation.md` for detailed boundaries.
