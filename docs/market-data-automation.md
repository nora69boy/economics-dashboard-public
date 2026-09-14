# Market-data automation gate

Public stock and world-index values remain a frozen reviewed snapshot until redistribution rights are explicitly approved in `data-rights/registry.json`.

## Zero-cost operating policy

The dashboard is now operated under a **JPY 0 monthly-cost ceiling** for market-data acquisition.

- Do not compare, trial, purchase, or integrate paid market-data APIs or paid redistribution licenses for this project.
- Continue automated refresh only for official/public macro sources already covered by the publication controls.
- Keep stock, ETF, and world-index values as the reviewed frozen snapshot while no zero-cost source has the complete rights set for automated retrieval, storage/caching, transformation, public display, and redistribution.
- Do not weaken the rights gate merely to obtain fresher quotes.
- Re-open provider evaluation only if a genuinely zero-cost source publishes explicit rights covering the full required use, or if the project owner later changes the JPY 0 constraint.

## Current decision

- Do not automate StockAnalysis.com: its published terms do not permit full republication, and its July 2026 help page states that it provides no programmatic access and does not hold rights to redistribute its upstream data programmatically.
- Do not replace that source with a free/self-service market-data API merely because an API exists. Retail plans can impose personal/internal-use or redistribution restrictions, and exchange-level rights can still apply.
- Provider review on September 14, 2026 found no zero-cost reviewed provider with explicit rights covering automated retrieval, storage, transformation, public display and redistribution for the requested market set.
- Existing market datasets therefore remain `FROZEN_SNAPSHOT`. `scripts/market_refresh_guard.py` performs no network access and cannot mutate `site/data/market.json`.

## Staged rights gate retained for future zero-cost eligibility

The rights gate continues to evaluate six independent stages so any future zero-cost source can be enabled without weakening the rest:

1. `us_stocks`: NVDA, MSFT, AAPL, GOOGL, AMZN
2. `us_etf`: SPY
3. `us_indices`: S&P 500, Nasdaq Composite, Dow Jones Industrial Average
4. `japan_indices`: Nikkei 225, TOPIX
5. `europe_indices`: FTSE 100, DAX, CAC 40, EURO STOXX 50
6. `asia_indices`: Hang Seng, Shanghai Composite, KOSPI, NIFTY 50, ASX 200

A stage becomes `ready` only when every dataset in that stage has explicit APPROVED/CONDITIONAL rights for automated retrieval, storage, transformation, display, redistribution and caching, valid evidence and review dates, and a confirmed monthly cost of JPY 0.

## Unlock conditions

Before a provider can be wired into production, the product owner must review the provider and exchange terms, record dated evidence in the rights registry, approve all required public uses, confirm JPY 0 monthly cost, set a bounded validity/review window, and define retention/attribution conditions. Only then should a provider-specific fetcher be added.

## Architecture after a future zero-cost approval

`provider -> bounded server-side fetch -> schema validation -> continuity checks -> stage rights gate -> build -> GitHub Pages -> exact HTTPS hash verification`

No browser-side API keys, scraping workarounds, credential commits, paid-provider fallback, or silent fallback to a different quote provider.
