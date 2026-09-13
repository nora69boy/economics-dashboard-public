# Economics Research Dashboard v0.3.0

Public-market research only: seven tabs, five research classifications, thirteen topics and eight official calendar events. This release does not resume scheduled tasks or ingest full scheduled reports. No live market data or individual records are included.

## Publication boundary

Public commits are visible BEFORE CI runs. Review and scan in private staging before pushing. Never import private history, individual financial information or credentials.

- The existing deployment workflow and its permissions are unchanged.
- Only the three hash-allowlisted site files and a generated .nojekyll are deployed.
- The inline tab and filter program is CSP hash-approved; background connections and form submission remain disabled.
- Source navigation permits only three exact official calendar URLs with no-referrer and noreferrer attributes. No external assets, analytics, input forms or storage are used.
- The gate preserves file, history, credential and active-content checks. It adds duplicate-attribute and duplicate-ID rejection, strict JSON fields and named-time-zone checks.
- All public commit identities must use GitHub noreply addresses.

## Verification

Run `python3 -m unittest discover -s tests -v` and `python3 scripts/check_site.py --check-history --build`.
Content-only validation in private staging omits --check-history. Browser verification and the separately maintained private monthly audit must use seven panels and the event-card/topic-card selectors for this release.

The gate is a secondary check, not proof of anonymity or absence of vulnerabilities. Review freely written text before publication. Hosting connection metadata and public account identifiers remain visible to the hosting provider.

## Data status

Calendar dates were checked against FRB, Bank of Japan and BLS official pages on 2026-09-13. Publication times not verified remain null. Forecasts and results are not invented. The old 2026-09-11 report is retained as a dated archive, not relabeled as a fresh report.

No paid service, subscription upgrade, private-to-public sync or new schedule is introduced by this release.
