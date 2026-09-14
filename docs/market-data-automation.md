# Market-data automation gate

Self-hosted stock and world-index values remain a frozen reviewed snapshot until redistribution rights are explicitly approved in `data-rights/registry.json`. The primary on-screen market view now uses the official TradingView embed widget, served directly by TradingView, without ingesting or persisting those live quote values in this repository.

## Zero-cost operating policy

The dashboard is operated under a **JPY 0 monthly-cost ceiling** for market-data acquisition.

- Do not compare, trial, purchase, or integrate paid market-data APIs or paid redistribution licenses for this project.
- Continue automated refresh only for official/public macro sources already covered by the publication controls.
- Keep the repository-owned stock, ETF, and world-index datasets as the reviewed frozen snapshot while no zero-cost source has the complete rights set for automated retrieval, storage/caching, transformation, public display, and redistribution.
- Use the TradingView official embed only as a provider-hosted display surface; do not scrape, capture, cache, transform, or republish values shown by that widget.
- Do not weaken the rights gate merely to obtain fresher quotes.
- Re-open self-hosted provider evaluation only if a genuinely zero-cost source publishes explicit rights covering the full required use, or if the project owner later changes the JPY 0 constraint.

## Current decision

### User-visible current-state handling

- The 2026-09-10 repository-owned market snapshot is an **audit archive**, not the current-price display. It is intentionally not refreshed while redistribution/storage rights remain unresolved.
- Current market state is shown through provider-hosted TradingView widgets. The repository does not ingest, store, cache, transform, or republish those widget quote values.
- The Policy Reaction Board uses the same provider-hosted boundary for US 10Y, USD/JPY, S&P 500, Nasdaq Composite, Nikkei 225 and TOPIX. Event-window quote deltas are not persisted by this repository.

- Primary market display: TradingView official Market Overview widget. It is loaded by the visitor's browser and may show real-time, delayed, or end-of-day data depending on market/exchange entitlements and TradingView availability.
- Audit/history layer: the existing reviewed stock/index snapshot remains unchanged with `as_of = 2026-09-10`.
- The repository does not write TradingView quote values to `site/data/market.json`, the release artifact, caches, logs, or analytics.
- Page load now initiates an external connection to the allowlisted TradingView widget origin. The dashboard discloses this in the UI; other external source links remain user-initiated navigation.
- If the external widget is unavailable or blocked, the page retains the labeled historical snapshot rather than fabricating or silently substituting quote data.
- Do not automate StockAnalysis.com: its published terms do not permit full republication, and its July 2026 help page states that it provides no programmatic access and does not hold rights to redistribute its upstream data programmatically.
- Existing self-hosted market datasets therefore remain `FROZEN_SNAPSHOT`. `scripts/market_refresh_guard.py` performs no network access and cannot mutate `site/data/market.json`.

## Security and publication boundary

The release gate allows only the exact reviewed TradingView embed script URL and a bounded set of TradingView frame origins. No arbitrary third-party script, browser-side API key, form submission, local storage, analytics tag, quote fetcher, or self-hosted market transport is permitted.

CI validates the widget configuration statically and blocks the TradingView network during deterministic browser regression tests. Production browsers can load the allowlisted widget; the dashboard itself still does not receive or persist the quote payload.

## Staged rights gate retained for future zero-cost self-hosted eligibility

The rights gate continues to evaluate six independent stages so any future zero-cost source can be enabled without weakening the rest:

1. `us_stocks`: NVDA, MSFT, AAPL, GOOGL, AMZN
2. `us_etf`: SPY
3. `us_indices`: S&P 500, Nasdaq Composite, Dow Jones Industrial Average
4. `japan_indices`: Nikkei 225, TOPIX
5. `europe_indices`: FTSE 100, DAX, CAC 40, EURO STOXX 50
6. `asia_indices`: Hang Seng, Shanghai Composite, KOSPI, NIFTY 50, ASX 200

A stage becomes `ready` only when every self-hosted dataset in that stage has explicit APPROVED/CONDITIONAL rights for automated retrieval, storage, transformation, display, redistribution and caching, valid evidence and review dates, and a confirmed monthly cost of JPY 0.

## Unlock conditions

Before a provider can be wired into the self-hosted production data path, the product owner must review the provider and exchange terms, record dated evidence in the rights registry, approve all required public uses, confirm JPY 0 monthly cost, set a bounded validity/review window, and define retention/attribution conditions. Only then should a provider-specific fetcher be added.

## Architecture

Provider-hosted live display:

`visitor browser -> allowlisted TradingView embed -> TradingView-hosted market display`

Reviewed self-hosted data path:

`official/approved source -> bounded server-side fetch -> schema validation -> continuity checks -> rights gate -> build -> GitHub Pages -> exact HTTPS hash verification`

No browser-side API keys, scraping workarounds, credential commits, paid-provider fallback, widget-value capture, or silent fallback to a different quote provider.
