# Economics Research Dashboard — Frozen Public Reference (v0.6.0)

> **Frozen reference as of 2026-09-18.** Active Production has moved to the private repository `nora69boy/economics-dashboard`. New product development and scheduled public refresh/deployment have stopped here. This repository is retained only as historical design, audit, rollback-reference and public-rights evidence. Private raw market data, private research data, portfolio data and Private repository history must not be copied into this repository.

The sections below document the last Public production design. They are retained for engineering/audit reference and should not be read as a statement that scheduled Public production remains active.

## Frozen production model (historical)

The dashboard combined three different data modes and labeled them separately:

1. **Provider-hosted market view** — current stock, ETF, index and policy-reaction views used the official TradingView embed. Depending on market/exchange entitlements, TradingView could show real-time, delayed, or end-of-day values. Those widget quote values were not ingested, cached, transformed, or republished by this repository. CI intentionally blocked the third-party quote response during deterministic browser QA, so provider-hosted delivery and successful observation of a current quote were treated as different states.
2. **Self-hosted macro histories** — six government/public histories were refreshed four times per day at 01:17 / 07:17 / 13:17 / 19:17 JST while this repository was active Production. VIX remained withheld pending republication permission.
3. **Reviewed archive data** — the repository-owned stock/index snapshot remained frozen at 2026-09-10 for audit and regression purposes. It was hidden from normal current-market display and was not used for current-price decisions.

The runtime navigation contained the market, research, scenario, event, macro and operations views. The macro module included long histories, period switching, source-health status, year-aware economic-calendar handling, and event-linked chart windows.

## Calendar and event handling

Active Production used official BLS, BEA and Federal Reserve calendar sources. Calendar publication was fail-closed by family: a complete/reviewed family could update, while blocked or incomplete families retained the previously reviewed schedule instead of publishing a partial calendar as current.

The strategic event panel also contained a separately reviewed FOMC / Bank of Japan watch for September 2026. This short-horizon policy panel was not the authoritative source for the full economic calendar; the macro calendar was the continuously checked release-calendar layer.

## Dashboard Health

The `出典・運用` view exposed build health for:

- macro retrieval freshness;
- economic-calendar source status;
- provider-hosted market delivery mode separately from quote-observation status;
- legacy market public presence separately from visual visibility;
- fail-closed browser QA behavior;
- the GitHub Actions run identifier and scheduled execution times.

The v0.7 migration introduced a typed operational-state contract for these distinctions. The visible Public dashboard remained release version v0.6.0 before Production moved to Private.

Historical 7-day / 30-day uptime and first-attempt success rates were not persisted in the dashboard. Dashboard Health represented build state, not an uptime-monitoring service.

## Privacy and external connections

The Public dashboard did not use personal holdings, account connections, forms, analytics, advertising, browser persistence, local storage, or browser-side API keys.

The provider-hosted TradingView widgets were the intentional exception to the otherwise closed frontend network boundary: opening pages that contained a widget caused the visitor browser to connect to allowlisted TradingView script/frame origins. Source links to regulators, issuers and agencies remained user-initiated navigation with no-referrer behavior.

The CSP restricted scripts and frames to the reviewed TradingView embed boundary. The deterministic CI browser blocked TradingView network traffic while validating dashboard behavior, so the release could be tested without depending on live third-party widget responses.

## Market-data rights boundary

`scripts/market_refresh_guard.py` performed no quote-provider retrieval and could not update `site/data/market.json`. A self-hosted market series could refresh only after its registry entry had explicit permission for automated retrieval, storage/caching, transformation, public display and redistribution and still satisfied the JPY 0 monthly-cost policy.

The Public market view therefore used provider-hosted TradingView widgets while the self-hosted September 10 snapshot remained an audit archive. See `docs/market-data-automation.md`.

## Automatic macro update hardening

The former updater rejected responses that dropped previously published primary or auxiliary observation dates. A failing or truncated provider response retained the previous validated series and its original successful retrieval timestamp instead of replacing it with incomplete history.

Transient GET failures received at most one retry. BLS POST requests and HTTP 403/429 responses were not automatically retried. Output writes were atomic and revalidated before replacement.

## Historical build and release gates

The last Public production workflow performed, in order:

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

That scheduled workflow has been removed from this frozen repository. Its implementation remains available in Git history.

## Ongoing policy for this repository

- No new product capabilities are developed here.
- No scheduled market/macro refresh is run here.
- No automated Pages deployment is run here.
- Do not add Bigdata.com / Massive raw data.
- Do not add personal holdings, account information, cost basis, credentials or Private-repository history.
- Critical security or legal maintenance may still be applied if required.
- Any future Public revival requires a fresh privacy, licensing, rights and deployment review.

Active development continues only in the Private Production repository.
