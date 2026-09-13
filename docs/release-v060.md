# v0.6.0 implementation and remaining work

Implemented: seven macro slots with six real government histories; VIX rights-pending explanation instead of fake data; 1/5/10-year and full-range charts; CPI/PCE index and calculated YoY switching; individual/all-series filters; per-chart numeric table and keyboard readout; 37 manually reviewed 2026 dates, JST/DST conversion and unknown-time handling; event selection focuses a -100/+60 calendar-day chart window. The event panel compares preceding and next available daily observations within seven days, not intraday impact or causation. Forecast and surprise values remain unavailable.

Former release weaknesses addressed: misleading connected labels removed from macro; CPI August 2026 obtained from the official API; fixed presentation values replaced by typed histories; BLS missing-period markers and Treasury mixed-case headers handled; same-input deterministic generation; actual-release tests precede publication; exact deployed HTML hash verification; source-failure retention; bounded numeric revision differences; no private source/data access by the public updater.

Preserved: public research only, private audit isolation, free service scope, existing historical stock/index snapshots, CSP, no frontend network/storage/analytics, explicit no-referrer source links. No repository visibility or user account identity has been changed.

Still required: Cboe republication approval for VIX; lawful long-history stock/index source and corporate-action adjustment; consensus forecast source/rights; complete research-report ingestion with editorial approval; point-in-time vintages; physical Safari testing; periodic official-calendar review; account-level protections and confirmation of notification delivery. These are not represented as complete.

A URL such as https://economics-dashboard-public/ is not a normal registered public HTTPS domain. A free branded pages.dev subdomain or a registered custom domain is a separate hosting/DNS decision. No new hostname has been registered or activated by this release. Hiding a username in the address does not erase the public repository's ownership/history.

Test evidence must be taken from the final release workflow and private audit, not inferred from this document. Scheduled runs can be delayed. No vulnerability scan or source fingerprint proves absence of every vulnerability or factual error.
