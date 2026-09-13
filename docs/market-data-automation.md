# Market-data automation gate

Public stock and world-index values remain a frozen reviewed snapshot until redistribution rights are explicitly approved in `data-rights/registry.json`.

## Current decision

- Do not automate StockAnalysis.com: its published terms do not permit full republication, and its July 2026 help page states that it provides no programmatic access and does not hold rights to redistribute its upstream data programmatically.
- Do not replace that source with a free/self-service market-data API merely because an API exists. Retail plans can impose personal/internal-use or redistribution restrictions, and exchange-level rights can still apply.
- Provider review on September 14, 2026 found no zero-cost reviewed provider with explicit rights covering automated retrieval, storage, transformation, public display and redistribution for the requested market set. Alpha Vantage requires business/commercial onboarding for business market-data use; Twelve Data requires an authorized external-display/redistribution entitlement or separate agreement. Tiingo and Massive/Polygon likewise do not establish zero-cost public redistribution rights for this dashboard from the reviewed public terms.
- Existing market datasets therefore remain `FROZEN_SNAPSHOT`. `scripts/market_refresh_guard.py` performs no network access and cannot mutate `site/data/market.json`.

## Staged rollout

The rights gate now evaluates six independent stages so one approved segment can be enabled without weakening the rest:

1. `us_stocks`: NVDA, MSFT, AAPL, GOOGL, AMZN
2. `us_etf`: SPY
3. `us_indices`: S&P 500, Nasdaq Composite, Dow Jones Industrial Average
4. `japan_indices`: Nikkei 225, TOPIX
5. `europe_indices`: FTSE 100, DAX, CAC 40, EURO STOXX 50
6. `asia_indices`: Hang Seng, Shanghai Composite, KOSPI, NIFTY 50, ASX 200

A stage becomes `ready` only when every dataset in that stage has explicit APPROVED/CONDITIONAL rights for automated retrieval, storage, transformation, display, redistribution and caching, plus valid evidence and review dates. Other stages remain blocked.

## Unlock conditions

Before a provider can be wired into production, the product owner must review the provider and exchange terms, record dated evidence in the rights registry, approve all required public uses, set a bounded validity/review window, and define retention/attribution conditions. Only then should a provider-specific fetcher be added.

## Preferred architecture after approval

`provider -> bounded server-side fetch -> schema validation -> continuity checks -> stage rights gate -> build -> GitHub Pages -> exact HTTPS hash verification`

No browser-side API keys, scraping workarounds, credential commits, or silent fallback to a different quote provider.
