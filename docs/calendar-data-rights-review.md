# Official economic-calendar rights review

Status: **product-owner approved on 2026-09-14 JST (2026-09-13 UTC) for the four calendar datasets in this document.** The approval is implemented as a narrow fail-closed overlay in `data-rights/calendar-approvals.json`; it does not approve any market, index, VIX, research, or financial dataset.

Reviewed sources: Bureau of Labor Statistics (BLS), Bureau of Economic Analysis (BEA), and Board of Governors of the Federal Reserve System (Federal Reserve Board). The approved scope is limited to `calendar-cpi`, `calendar-jobs`, `calendar-pce`, and `calendar-fomc`.

## Approved publication scope

| Dataset | Official schedule source | Published fields | Public targets |
| --- | --- | --- | --- |
| `calendar-cpi` | BLS CPI release schedule | date, family, id, reference period, source, status, local time, JST time | `data/macro-calendar.json`, `index.html` |
| `calendar-jobs` | BLS Employment Situation release schedule | date, family, id, reference period, source, status, local time, JST time | `data/macro-calendar.json`, `index.html` |
| `calendar-pce` | BEA news-release schedule | date, family, id, reference period, source, status, local time, JST time | `data/macro-calendar.json`, `index.html` |
| `calendar-fomc` | Federal Reserve FOMC calendar | date, family, id, source, status; meeting time remains null unless officially published and reviewed | `data/macro-calendar.json`, `index.html` |

No consensus estimates, copyrighted market prices, third-party calendar text, logos, seals, photographs, graphics, or third-party material are included.

## Primary rights evidence

### Bureau of Labor Statistics

- Terms/evidence URL: <https://www.bls.gov/opub/copyright-information.htm>
- BLS states that, except for previously copyrighted photographs and illustrations, material it publishes is in the public domain and may be used without specific permission.
- BLS asks users to cite the Bureau of Labor Statistics as the source.
- The BLS emblem and variations are federally registered trademarks and are outside this scope.
- CPI schedule source: <https://www.bls.gov/schedule/news_release/cpi.htm>
- Employment Situation schedule source: <https://www.bls.gov/schedule/news_release/empsit.htm>

Rights decision: storage, transformation, display, redistribution, caching and automated retrieval of the schedule facts are approved. The current HTTP 403 from GitHub-hosted runners is a transport limitation, not a rights denial.

### Bureau of Economic Analysis

- Terms/evidence URL: <https://www.bea.gov/help/faq/147>
- BEA states that, unless otherwise stated, information posted on its website is in the public domain and may be used or reproduced without specific permission.
- BEA says a citation such as `Source: U.S. Bureau of Economic Analysis` is appreciated.
- PCE schedule source: <https://www.bea.gov/news/schedule>

Rights decision: storage, transformation, display, redistribution, caching and automated retrieval of the schedule facts are approved.

### Federal Reserve Board

- Terms/evidence URL: <https://www.federalreserve.gov/disclaimer.htm>
- The Board states that, unless otherwise indicated, information on its website is in the public domain and may be copied and distributed without permission, and asks users to cite the Board as the source.
- Non-Board photos, graphics, and other third-party materials require separate permission and are outside this scope.
- Board seals, logos, and official insignia are protected and are outside this scope.
- FOMC schedule source: <https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm>

Rights decision: storage, transformation, display, redistribution, caching and automated retrieval of the FOMC meeting-date facts are approved.

## Approved rights decision

The four datasets use **CONDITIONAL** status in the effective publication registry. This intentionally keeps an executable source-attribution condition even where citation is requested or appreciated rather than a legal precondition.

Approved purpose values:

- `access`: ALLOWED
- `automated_retrieval`: ALLOWED as a rights decision; BLS transport remains blocked from GitHub-hosted runners
- `storage`: ALLOWED
- `transformation`: ALLOWED
- `display`: ALLOWED
- `redistribution`: ALLOWED
- `commercial_use`: UNKNOWN
- `caching`: ALLOWED
- `ai_processing`: UNKNOWN
- `retention.mode`: WHILE_VALID
- `retention.max_age_days`: null

Administrative dates are stored in UTC because the publication-rights gate evaluates the runner calendar date in UTC. The product-owner instruction occurred on 2026-09-14 JST, which was 2026-09-13 UTC at execution time.

- `reviewed_at`: 2026-09-13 UTC
- `valid_from`: 2026-09-13 UTC
- `review_due_at`: 2027-08-13 UTC
- `valid_until`: 2027-09-13 UTC

The machine-enforced attribution token is the exact official schedule URL already carried by every reviewed event and rendered as the `公式日程` source link. The condition is checked in both `data/macro-calendar.json` and `index.html`. This avoids modifying the reviewed calendar schema solely to duplicate a source-name string while retaining explicit source attribution in the user interface.

Each approved entry receives a reproducible SHA-256 of the canonical reviewed public-domain evidence excerpt stored in `data-rights/calendar-approvals.json`, with `approved_by_role: product_owner` in the effective registry.

## Technical state

- The reviewed static calendar remains the published calendar snapshot.
- Official BEA and Federal Reserve schedule probes run on `main` and retrieve successfully.
- BLS ICS, CPI schedule HTML, and Employment Situation schedule HTML return HTTP 403 from GitHub-hosted runners. The code retains the reviewed BLS snapshot and does not use mirrors, proxies, or aggressive retrying.
- Probe candidates still do not mutate `site/data/macro-calendar.json`.
- Rights approval and live-publication wiring remain separate controls. Approval of the four datasets does not permit a partial BEA/Fed candidate to overwrite the complete reviewed calendar.
- The migration baseline is unchanged; approval is not manufactured by modifying the baseline.
- The original base registry gate still executes first. The calendar overlay can reduce only the four reviewed UNKNOWN warnings and cannot bypass a block produced by the base gate.

## Verification requirements

1. Exactly the four approved calendar datasets become CONDITIONAL in the effective registry; the other 36 registry entries remain unchanged.
2. Required public uses are ALLOWED; commercial use and AI processing remain UNKNOWN.
3. Evidence hashes are reproducible from the canonical reviewed excerpts.
4. Official source URLs exist in both required public targets.
5. Removing an attribution condition blocks publication.
6. The original base rights gate remains wired before the four-dataset overlay.
7. Rights tests, release tests, browser tests, publication gate, Pages deployment, exact HTTPS verification, and post-deploy health must pass before merge.
8. Live calendar publication is a separate follow-on change with completeness protection.

This document records the engineering rights decision and implementation boundary. It is not legal advice.
