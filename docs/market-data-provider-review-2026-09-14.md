# Market-data provider rights review — 2026-09-14

Purpose: determine whether any reviewed provider can support the public Economics Research Dashboard under a JPY 0 monthly-cost ceiling while explicitly permitting automated retrieval, storage/caching, transformation, public display and redistribution.

This is a product-rights review, not legal advice. A provider is not approved merely because an API or free tier exists. Exchange/index-owner terms can impose additional requirements.

## Executive decision

No reviewed zero-cost provider currently establishes the complete rights set required for automated public stock/index refresh. All six market stages therefore remain `blocked_by_rights`, and the existing September 10, 2026 reviewed stock/index snapshot remains frozen.

## Provider matrix

| Provider | Programmatic retrieval | Public/customer display | Redistribution | Zero-cost path for this dashboard | Decision |
| --- | --- | --- | --- | --- | --- |
| StockAnalysis.com | No API/MCP/programmatic interface offered | Website display is licensed to StockAnalysis | StockAnalysis states it does not hold rights to redistribute/resell its upstream data programmatically | No | Reject for automation |
| Alpha Vantage | API available | Personal realtime/delayed access is separated from business/commercial use | Business/commercial use requires onboarding; reviewed public policy does not grant this dashboard public redistribution rights | Not established | Keep blocked |
| Twelve Data | API/WebSocket available | External display only as expressly authorized by the relevant tier/add-on/agreement | Redistribution requires a Redistribution Rights Add-On or separate written agreement; exchange rules may also apply | Free tier cannot be used commercially and does not grant redistribution | Keep blocked |
| Tiingo | API available | Internal/personal use under standard accounts | Redistribution requires special permission/license and additional fees | No reviewed zero-cost redistribution license | Keep blocked |
| Massive / Polygon | API available | Individual plans are personal/non-professional; customer-facing display requires Business terms | Public display/redistribution is restricted absent written consent or provider agreement | No reviewed zero-cost public redistribution path | Keep blocked |

## Official evidence reviewed

### StockAnalysis.com
- API access FAQ, updated July 8, 2026: https://stockanalysis.com/help/faq/api-access/
- States there is no API, MCP server or other programmatic interface.
- States its licenses allow display but not programmatic redistribution/resale of upstream data.

### Alpha Vantage
- Market Data Policies: https://www.alphavantage.co/realtime_data_policy/
- API documentation: https://www.alphavantage.co/documentation/
- Realtime and 15-minute delayed US equity data is exchange-regulated.
- Personal/non-commercial access and business/commercial use are treated separately; business/commercial use requires provider onboarding.
- The reviewed public materials do not provide an explicit JPY 0 right for this dashboard to redistribute data publicly.

### Twelve Data
- Terms: https://twelvedata.com/terms
- Commercial/personal usage: https://support.twelvedata.com/en/articles/5332349-commercial-and-personal-usage
- US equities market data: https://support.twelvedata.com/en/articles/9935903-us-equities-market-data
- Attribution guidance: https://support.twelvedata.com/en/articles/12647398-attribution-guidelines-for-using-twelve-data
- External display/redistribution must be expressly authorized by a subscription entitlement, Redistribution Rights Add-On or separate agreement.
- Free Tier data may not be used commercially; individual plans do not permit redistribution or commercial display to third parties.
- ASX external/public usage requires additional licensing.

### Tiingo
- General API documentation: https://www.tiingo.com/documentation/general
- Terms of Use: https://api.tiingo.com/tos/
- Developer program: https://www.tiingo.com/documentation/appendix/developers
- Basic/Power data is internal/personal only; redistribution requires a redistribution license.
- Terms state redistribution is available only by special request/permission and comes with additional fees.

### Massive / Polygon
- Market Data Terms: https://massive.com/legal/market-data-terms-of-service
- Stock market API: https://www.massive.com/stocks
- Individual plans are for personal/non-professional use.
- Brokerage, redistribution and customer-facing display require Business arrangements.
- Market data and derived works may not be redistributed/displayed to third parties absent express written consent or a relevant provider agreement.

## Stage status

1. `us_stocks` — NVDA, MSFT, AAPL, GOOGL, AMZN: BLOCKED
2. `us_etf` — SPY: BLOCKED
3. `us_indices` — S&P 500, Nasdaq Composite, Dow Jones Industrial Average: BLOCKED
4. `japan_indices` — Nikkei 225, TOPIX: BLOCKED
5. `europe_indices` — FTSE 100, DAX, CAC 40, EURO STOXX 50: BLOCKED
6. `asia_indices` — Hang Seng, Shanghai Composite, KOSPI, NIFTY 50, ASX 200: BLOCKED

The index stages also require index-owner/exchange rights. Existing evidence in the private approval issue remains authoritative for S&P DJI, Nasdaq, JPX, Nikkei, STOXX/DAX, Euronext, Hang Seng Indexes, SSE, KRX, NSE/Nifty and ASX.

## Approval gate

A stage may switch to `ready` only after every dataset in that stage has dated evidence showing all of the following:

1. Automated retrieval explicitly permitted.
2. Storage/caching explicitly permitted.
3. Transformation explicitly permitted.
4. Public display explicitly permitted.
5. Redistribution explicitly permitted, including exchange/index-owner rights where applicable.
6. JPY 0 monthly cost confirmed if the project retains the zero-cost constraint.
7. Attribution and retention obligations captured.
8. Product-owner approval, validity window and review date recorded in `data-rights/registry.json`.

Until then, `scripts/market_refresh_guard.py` must remain fail-closed and must not contact a quote provider or mutate `site/data/market.json`.
