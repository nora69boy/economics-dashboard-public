# Market-data automation gate

Public stock and world-index values remain a frozen reviewed snapshot until redistribution rights are explicitly approved in `data-rights/registry.json`.

## Current decision

- Do not automate StockAnalysis.com: its published terms do not permit full republication, and its July 2026 help page states that it provides no programmatic access and does not hold rights to redistribute its upstream data programmatically.
- Do not replace that source with a free/self-service market-data API merely because an API exists. Retail plans can impose personal/internal-use or redistribution restrictions, and exchange-level rights can still apply.
- Existing market datasets therefore remain `FROZEN_SNAPSHOT`. The new `scripts/market_refresh_guard.py` performs no network access and cannot mutate `site/data/market.json`; it reports whether every published market series has explicit rights for automated retrieval, storage, transformation, display, redistribution and caching.

## Unlock conditions

Before a provider can be wired into production, the product owner must review the provider and exchange terms, record dated evidence in the rights registry, approve all required public uses, set a bounded validity/review window, and define retention/attribution conditions. Only then should a provider-specific fetcher be added.

## Preferred architecture after approval

`provider -> bounded server-side fetch -> schema validation -> continuity checks -> rights gate -> build -> GitHub Pages -> exact HTTPS hash verification`

No browser-side API keys, scraping workarounds, credential commits, or silent fallback to a different quote provider.
