# Economics Research Dashboard

Public market-research site generated from a separately maintained Private workspace.

## Privacy design

- This repository contains only sanitized public-market research.
- Private workspace history is never imported.
- Site files live under `site/` and must be explicitly allowlisted in `site/manifest.json`.
- `scripts/check_site.py` blocks sensitive patterns and unexpected files.
- The Pages workflow runs the privacy gate before every deployment.
- The site contains no analytics, ads, external scripts, external images, iframes or forms.
- The public HTML uses a restrictive Content Security Policy and no-referrer policy.

## Publishing

GitHub Pages publishes the `site/` directory through GitHub Actions. The `github.io` site is served over HTTPS.

## Research policy

Material market facts should be verified against primary sources. Unsourced figures must not be presented as confirmed facts.
