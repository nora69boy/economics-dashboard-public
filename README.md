# Economics Research Dashboard

Initial public-market research framework. No live quotes, personal records, or individualized investment recommendations are included.

## Privacy boundary

This is a public repository: every commit is public before CI starts. Run the scanner in private staging and review all new content BEFORE pushing. Do not rely on a post-commit check to prevent repository disclosure.

- Never copy private workspace history, account data, personal financial records, credentials, or screenshots into this repository.
- There is no private-repository token, cross-repository sync, visitor data entry, analytics, or third-party asset loading in the site.
- `site/manifest.json` fixes the reviewed file names and SHA-256 digests.
- The gate rejects unexpected files, symlinks, sensitive patterns, active external assets, and changed CSP/script hashes.
- Only the three reviewed site files and a generated `.nojekyll` marker enter the deployment artifact. The repository root is never deployed.
- Public commit identities must use GitHub noreply addresses. Private history is not imported.
- Hosting still involves GitHub processing connection metadata. This is not anonymous hosting.

## Checks and publication

Run `python3 -m unittest discover -s tests -v`, then `python3 scripts/check_site.py --check-history --build` in this repository. Content-only pre-publication checks are available with `python3 scripts/check_site.py --build` in a private staging copy.

The workflow uses pinned official actions and standard hosted runners. It deploys only after validation succeeds and verifies the returned HTTPS site. Pull requests are validated, not deployed. The workflow cannot read any private workspace.

The application makes no background network requests. The inline tab program is CSP hash-approved; form submission and background connections are blocked. Source downloads are limited to reviewed local files.

## Limitations

Pattern matching and hashes do not prove anonymity or prevent authorized administrators from changing protections. Review free text, new data categories, file paths, commit identities, and re-identification risk before every release. GitHub usernames remain public. No service upgrade, custom domain purchase, or paid data feed is required for this initial public Pages site.

Market facts must be verified against primary sources before they are added. This initial release describes research questions and hypothetical scenarios, not current market conclusions.
