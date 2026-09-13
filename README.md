# Economics Research Dashboard v0.4.0

Nine tabs: world equity indices, individual stocks/ETF and financial charts, plus the existing seven research views. Fourteen world indices are classified by region. Five large technology stocks and SPY are separate from the indices. DAX performance is excluded from price-only relative rankings.

## Data scope

World indices contain only September 8-10, 2026 (three observations). Stocks and SPY contain six trading dates from September 2-10. All prices are secondary reference snapshots, NOT current quotes or independently confirmed official index closes. Provider-derived series may differ from the administrator's final closes. Sources, dates, currencies and time zones are explicit. NVIDIA financials are three selected GAAP comparison periods from its official Q2 FY27 announcement, not a consecutive quarterly time series. No missing dates are fabricated, and RSI14, long-term averages, annualized forecasts and live updates are not supplied.

## Features

Region and index selection, points or base-100 charts, relative comparison, performance cards, candlesticks, closing-price lines, volume, five-observation averages, in-window closing-price drawdown, and financial comparisons. Static source tables are available when JavaScript is disabled. These calculations are not trading recommendations.

## Build and privacy

Public commits are visible before CI. Review all code and data privately BEFORE pushing. Never import personal data, private histories, credentials or account-linked records. The browser makes no background network requests, uses no storage, forms, analytics or external assets. Only explicitly reviewed source links can be followed by the user, with no-referrer.

`templates/base.html` preserves the reviewed research shell. `scripts/build_dashboard.py` combines it with `templates/charts.js`, `templates/charts.css` and local market JSON. It generates `site/index.html` and never updates approval hashes or accesses the network. The generated HTML is not tracked. Tests build it on a fresh checkout, then verify the expected manifest, data schema, security rules and calculations. The scanner also checks embedded data consistency, exact file sets and public noreply commit identities.

Run `python3 scripts/build_dashboard.py`, `python3 -m unittest discover -s tests -v`, and `python3 scripts/check_site.py --check-history --build`. The existing Pages workflow and permissions are unchanged. Only the four reviewed payload files are deployed, never the source repository root. A separate private monthly audit must approve each release hash and run compatible browser tests; detailed results remain private.

## Limits

No market schedule is resumed. No automatic report ingestion, account connection, paid plan, custom domain or ongoing licensed data feed is introduced. Data are limited attributed excerpts for research commentary; this is not a grant of bulk redistribution rights. Primary data reconciliation, long histories, ongoing data rights, actual iPhone/Safari testing and account security remain separate requirements. Hosting still processes connection metadata. Passing automated checks does not prove zero vulnerabilities.
