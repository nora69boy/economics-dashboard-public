# Economics Research Dashboard v0.6.0

Independent public-market research. No affiliation with the reference website; its complete research report has not been reconciled, and exact reproduction is not claimed.

## What is available

Eleven panels, same-date stock/index screening, up-to-four compatible series comparison, six government macro histories from 2015, 1/5/10-year and full-range charts, and 37 reviewed economic release dates linked to macro charts. A seventh VIX slot is explicitly withheld pending republication permission. CPI/PCE year-on-year rates use matching calendar months, not an array offset. Government missing values are not zero-filled. Monthly observation months and economic announcement dates are distinct. Current revised values must not be treated as point-in-time backtest inputs.

Stock and world-index data remain the prior September 10, 2026 secondary snapshot: 14 indices with three observations and five stocks plus SPY with six observations. No new stock quotes, real-time stock feed, consensus dataset or news ingestion was added. DAX total-return and provider-derived series remain excluded from compatible screening.

Market-data automation is explicitly fail-closed. `scripts/market_refresh_guard.py` performs no quote-provider network access and cannot mutate `site/data/market.json`; it reports whether every published stock/index series has explicit rights for automated retrieval, storage, transformation, display, redistribution and caching. The current 20 published market series remain blocked from automated refresh until their rights records are approved. See `docs/market-data-automation.md`.

## Updates and calendar

The public workflow fetches only the six fixed government histories every six hours, at 04:17/10:17/16:17/22:17 UTC every day (01:17/07:17/13:17/19:17 JST), and also on approved releases and manual workflow dispatch. Pull requests reuse the previously published validated macro snapshot without polling upstream providers. Source failure retains the previous validated public observations and their original retrieval timestamp with a retained/error label. Initial publication fails if six valid histories are unavailable. Calendar dates are manually reviewed as of September 13, 2026, not automatically refreshed. The calendar includes 12 CPI dates, 12 employment dates, 8 FOMC final days and 5 PCE dates (August-December). Unknown meeting announcement times are left unknown. API/data delays and scheduler delays remain possible.

## Privacy and publication

No personal holdings, account connection, browser persistence, form submission, analytics, advertising, external frontend scripts or background frontend requests. The sole instrument search is bounded to 40 characters and stays in page memory. Data-provider requests run on GitHub-hosted infrastructure without private repository credentials or API keys. Hosting providers still process ordinary access metadata; no anonymity or zero-leakage guarantee is made. A shorter hostname does not erase public GitHub ownership history.

The existing CSP, no-referrer links, strict field/path/URL allowlists, finite-number checks, source fingerprints and SHA-256 artifact checks remain. Only six validated payloads plus an empty .nojekyll marker are deployed; templates, tests and private records are not. Public commits are public before CI: review all contents before writing.

## Build and test

1. python3 scripts/run_legacy_tests.py
2. python3 scripts/market_refresh_guard.py
3. python3 scripts/macro_fetch.py
4. python3 scripts/build_release.py
5. python3 -m unittest discover -s tests -p test_release.py -v
6. python3 -m unittest discover -s tests -p test_rights.py -v
7. python3 -m unittest discover -s tests -p test_market_refresh_guard.py -v
8. node scripts/browser_release.mjs site/index.html
9. python3 scripts/check_release.py --check-history --build

No post-test data patch is applied. Builds from the same validated snapshots are deterministic. The production HTTPS file must equal the generated SHA-256. Browser tests cover 390/768/1440 pixel widths, not physical iPhone/Safari certification. PASS is scoped verification, not proof of zero vulnerabilities or economic-data correctness. The separate private monthly audit must approve each source-code release; daily data refreshes do not mutate source commits.

See docs/data-rights.md and docs/release-v060.md for boundaries and remaining work. No paid service, domain purchase, stopped market-watch task restart or live trading has been added.

## Automatic-update hardening

The updater rejects responses that drop any previously published primary or auxiliary observation date. In that case it retains the prior series and its original retrieval timestamp, rather than replacing a long history with an incomplete response. Revision values for dates still present remain allowed. Removed observations that are intentional agency corrections need a separate review; they are not silently accepted.

Transient GET failures receive at most one retry; BLS POST requests and HTTP 429/403 responses are not retried. Four scheduled runs use eight BLS POST queries per day under the current two-window history configuration, excluding manually triggered runs. The unregistered BLS limit is 25 queries per day: https://www.bls.gov/developers/api_faqs.htm . Do not repeatedly dispatch production runs. Output writes are atomic and revalidated before replacement.

Each production run writes a per-series GitHub Actions summary with retrieval status, successful retrieval time and observation date. A separate refresh-health job runs AFTER a successful deployment and fails if any of the six sources was retained. This preserves the visible error labels and last good data while making the workflow red. Email or other notification delivery still depends on the account's notification settings and has not been verified. An unchanged valid monthly observation is not an error or a newly released statistic.

The existing HTML, CSP, payload allowlist, source endpoints, rights registry and migration baseline remain unchanged. This change does not approve existing UNKNOWN rights records. The existing page displays source retrieval timestamps and retained/error labels in the macro panel; no automatic browser reload or external frontend requests are added. Reopen or reload the page to see the newest successfully deployed artifact. Stocks, indices, news, calendar reviews and VIX remain outside automatic updates.

Scheduler delays, missed jobs and inactivity remain possible. Public GitHub schedules can be disabled after 60 days without repository activity: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule . A monthly manual workflow/status review is required; no keepalive commits, external monitor or extra recurring ChatGPT task is installed by this change.
