# Official economic-calendar rights review

Status: **prepared for product-owner review; no approval has been granted by this document.**

Reviewed sources: Bureau of Labor Statistics (BLS), Bureau of Economic Analysis (BEA), and Board of Governors of the Federal Reserve System (Federal Reserve Board). The proposed scope is limited to the four existing calendar datasets already present in the publication-rights registry: `calendar-cpi`, `calendar-jobs`, `calendar-pce`, and `calendar-fomc`.

## Proposed publication scope

| Dataset | Official schedule source | Published fields | Proposed public targets |
| --- | --- | --- | --- |
| `calendar-cpi` | BLS CPI release schedule | date, family, id, reference period, source, status, local time, JST time | `data/macro-calendar.json`, `index.html` |
| `calendar-jobs` | BLS Employment Situation release schedule | date, family, id, reference period, source, status, local time, JST time | `data/macro-calendar.json`, `index.html` |
| `calendar-pce` | BEA news-release schedule | date, family, id, reference period, source, status, local time, JST time | `data/macro-calendar.json`, `index.html` |
| `calendar-fomc` | Federal Reserve FOMC calendar | date, family, id, source, status; meeting time remains null unless officially published and reviewed | `data/macro-calendar.json`, `index.html` |

No consensus estimates, copyrighted market prices, third-party calendar text, logos, seals, photographs, graphics, or third-party material are included in this proposed scope.

## Primary rights evidence

### Bureau of Labor Statistics

- Terms/evidence URL: <https://www.bls.gov/opub/copyright-information.htm>
- BLS states that, except for previously copyrighted photographs and illustrations, material it publishes is in the public domain and may be used without specific permission.
- BLS asks users to cite the Bureau of Labor Statistics as the source.
- The BLS emblem and variations are federally registered trademarks and are outside this scope.
- CPI schedule source: <https://www.bls.gov/schedule/news_release/cpi.htm>
- Employment Situation schedule source: <https://www.bls.gov/schedule/news_release/empsit.htm>

Candidate decision for owner review: publication rights appear compatible with storage, transformation, display, redistribution, and caching of the schedule facts, with BLS source attribution. Automated retrieval is technically attempted but is currently blocked with HTTP 403 from GitHub-hosted runners; this transport limitation is not a publication-rights limitation.

### Bureau of Economic Analysis

- Terms/evidence URL: <https://www.bea.gov/help/faq/147>
- BEA states that, unless otherwise stated, information posted on its website is in the public domain and may be used or reproduced without specific permission.
- BEA says a citation such as `Source: U.S. Bureau of Economic Analysis` is appreciated.
- PCE schedule source: <https://www.bea.gov/news/schedule>

Candidate decision for owner review: publication rights appear compatible with storage, transformation, display, redistribution, caching, and automated retrieval of the schedule facts, with BEA source attribution.

### Federal Reserve Board

- Terms/evidence URL: <https://www.federalreserve.gov/disclaimer.htm>
- The Board states that, unless otherwise indicated, information on its website is in the public domain and may be copied and distributed without permission, and asks users to cite the Board as the source.
- Non-Board photos, graphics, and other third-party materials require separate permission and are outside this scope.
- Board seals, logos, and official insignia are protected and are outside this scope.
- FOMC schedule source: <https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm>

Candidate decision for owner review: publication rights appear compatible with storage, transformation, display, redistribution, caching, and automated retrieval of the FOMC meeting-date facts, with Federal Reserve Board source attribution.

## Proposed registry decision

The conservative candidate is **CONDITIONAL**, not APPROVED, for all four calendar datasets so that source attribution is enforced by the existing publication-rights gate even where the government source describes attribution as requested/appreciated rather than a condition of reuse.

Proposed purpose values after explicit owner approval:

- `access`: ALLOWED
- `automated_retrieval`: ALLOWED for BEA/Federal Reserve; BLS legal permission appears compatible, but current GitHub-runner transport is blocked. Record ALLOWED only if the owner treats technical reachability separately from rights.
- `storage`: ALLOWED
- `transformation`: ALLOWED
- `display`: ALLOWED
- `redistribution`: ALLOWED
- `commercial_use`: confirm separately before setting ALLOWED; leave UNKNOWN if not needed for this public research site.
- `caching`: ALLOWED
- `ai_processing`: leave UNKNOWN unless separately needed and reviewed.
- `retention.mode`: WHILE_VALID

Proposed literal attribution conditions:

- BLS datasets: `Source: U.S. Bureau of Labor Statistics`
- BEA dataset: `Source: U.S. Bureau of Economic Analysis`
- FOMC dataset: `Source: Board of Governors of the Federal Reserve System`

The registry requires an explicit `valid_until` and `review_due_at` even for public-domain sources. A candidate administrative review cycle is one year, but dates must be selected by the product owner at approval time rather than inferred by engineering.

## Technical state

- The reviewed static calendar remains the only published calendar snapshot under the migration exception.
- Official BEA and Federal Reserve schedule probes run on `main` and currently retrieve successfully.
- BLS ICS, CPI schedule HTML, and Employment Situation schedule HTML all return HTTP 403 from GitHub-hosted runners. The code retains the reviewed BLS snapshot and does not treat the 403 as permission to use a mirror or proxy.
- Probe candidates do not mutate `site/data/macro-calendar.json`.
- The publication-rights gate continues to report the four calendar datasets as UNKNOWN / PENDING_RIGHTS_REVIEW until an explicit owner-approved registry change is merged.

## Approval checklist

Before changing any registry status from UNKNOWN:

1. Product owner confirms the four dataset scopes above.
2. Product owner confirms whether attribution should be enforced as a CONDITIONAL requirement.
3. Product owner selects `valid_from`, `valid_until`, and `review_due_at`.
4. Capture a reproducible public-safe evidence record for each terms page, including the terms URL and SHA-256 required by the registry schema.
5. Add the selected literal attribution to every required final target and verify it is visible and accurate.
6. Update the four registry entries in one reviewed PR; do not modify the migration baseline to manufacture approval.
7. Run rights tests, release tests, browser tests, publication gate, Pages deployment, exact HTTPS verification, and post-deploy health.
8. Only after the rights PR passes may live official calendar candidates be wired to replace the reviewed static calendar.

This document is an engineering review aid. It is not legal advice and does not itself grant or record publication approval.
