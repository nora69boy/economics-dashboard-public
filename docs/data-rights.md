# Public data scope and reuse boundary

Government-only history expansion: US Treasury 10-year par yield (2-year auxiliary), BLS CPI-U all items NSA CUUR0000SA0 (SA/core auxiliaries), BEA PCE price index DPCERG (core DPCCRG), BLS unemployment LNS14000000 (CES payroll auxiliary), Fed H.10 JPY per USD, EIA Cushing WTI spot dollars per barrel. WTI is spot, not a continuous front-month futures price. No proprietary forecast aggregation is redistributed.

Sources are fixed in scripts/macro_core.py and scripts/macro_fetch.py. Each group retains the retrieval time and SHA-256 of its retrieved source input. Missing periods are omitted, never zero-filled. The displayed index bases are CPI 1982-84=100 and PCE 2017=100. Derived inflation rates and inter-observation differences are research calculations, not separately published official releases. Latest revised observations do not reproduce information available at an earlier announcement date. Revision differences after initial collection are capped at 50 primary-series changes; auxiliary revision history and full vintage backtests are not implemented.

VIX remains rights_pending. Cboe Terms section 2 distinguishes personal non-commercial viewing from redistribution and generally requires prior written consent for other publication: https://www.cboe.com/terms . No VIX history is fetched or published by this release. A free webpage is not itself a licence to republish its database. A future VIX change requires an explicit rights review and schema/test update, not just changing a status flag.

Do not use keyless FRED scraping as a workaround. FRED terms also distinguish copyrighted third-party series and restrict automated access: https://fred.stlouisfed.org/legal/ . Use approved official interfaces rather than assuming all FRED-hosted series are public domain.

The pre-existing small secondary stock/index snapshot is unchanged, explicitly marked historical and not primary-verified. Rights for expanding those prices into a continuous public history remain unresolved. No assumption of blanket commercial redistribution permission is made.

Calendar sources: https://www.bls.gov/schedule/news_release/cpi.htm , https://www.bls.gov/schedule/news_release/empsit.htm , https://www.bea.gov/news/schedule , https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm . Calendar review date stays fixed until actual review. Original agency disclaimers continue to apply.
