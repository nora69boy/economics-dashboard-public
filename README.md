# Economics Research Dashboard v0.5.0

An independent, public-market research portal. This release adds a market overview,
a regional reference heatmap, local instrument search, same-date screening,
comparison of up to four compatible series, and a macro/data coverage catalogue.
It is not affiliated with a reference site, and is not a pixel-perfect reproduction.
The completed research document and reference website were unavailable for exact
comparison during this release. No original-site text, images or source were copied.

## Scope and data honesty

There are 11 panels with JavaScript enabled. Without JavaScript the nine previous
static panels and their source tables remain available; the new interactive
portal controls require JavaScript. No real-time data or new price observations
were added. The existing secondary snapshot still ends on September 10, 2026:
14 indices with three observations, five stocks and SPY with six observations.
The old research JSON version describes its data schema, not the new UI version.

All screening calculations use the common September 8-10 window. DAX total-return
and provider-derived reference series are excluded from comparable rankings and
multi-series selection. They remain accessible in the existing index explorer.
Different local closing times and currencies are explicitly not reconciled.
Historical data, financial results and their dates are inherited, not newly verified.

The macro catalogue has no numeric observations: unavailable values are shown as
unconnected, not zero, and official navigation links do not imply an active feed.
Long histories, quote updates, news ingestion and consensus data are not implemented.
No stopped schedule was restarted. Market-data publication rights for ongoing use
remain a separate decision before any continuous or bulk distribution is enabled.

## Privacy and publication

There is one bounded search box for instrument names and symbols. Filtering happens
only in page memory, with no form submission, persistence, network request, analytics
or account connection. Never enter individual financial or identifying records.
Search text is never interpolated as HTML. All render operations use text nodes.
All source links are explicit HTTPS URLs with no-referrer and noreferrer/noopener.
Source navigation is user initiated; it leaves the application when clicked.

A public commit is public BEFORE CI. Review and scan privately before writing.
The content gate, SHA-256 manifest, restricted CSP, no-referrer, fixed file allowlist,
and official pinned deployment workflow remain in place. No deployment permission
or paid service was added. A separate private monthly audit must approve this
release and validate all eleven runtime panels and the new controls.

## Build and verification

The existing deterministic builder combines reviewed base HTML, local market data,
and the chart/portal program and stylesheet. It recalculates the program CSP hash
but never changes the approval manifest. index.html is generated, not tracked.
Only four reviewed payload files are deployed; templates and test code are not.

Run python3 scripts/build_dashboard.py, then python3 -m unittest discover -s tests -v,
and python3 scripts/check_site.py --check-history --build. Search, comparison,
keyboard, no-JavaScript fallback and zero-background-request checks also run in the
private browser audit. PASS is scoped verification, not proof of zero vulnerabilities.

## Next dependencies

1. Review the completed research report and the reference site's available pages.
2. Approve a lawful data source and update policy before adding automatic history.
3. Add tested ingestion with observation timestamps, revisions and corporate actions.
4. Verify physical Safari, account protections and device notification delivery.

These are dependencies, not scheduled background implementation promises.
