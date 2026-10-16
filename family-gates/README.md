# family-gates

The family page gates of oracle.agentic-paybench.dev, vendored from the design
system (re-vendor, never edit the vendored files here; this README is this
repository's own).

What runs when:

- **On every pull request and push to main (`ci`, job `pages`)**: the site is
  assembled exactly as the deploy ships it and served on its own origin;
  `check.mjs` runs the network-log, script, layout and axe-core checks on the
  reader pages; Lighthouse CI runs the score and size budgets; `lh-check.mjs`
  then fails on any third-party or script resource beyond the decided-assets
  list. A failure fails `ci`, and `deploy-pages` runs only when `ci` succeeds.
- **After every deploy (`deploy-pages`, job `live-gate`)**: the job waits,
  for at most ten minutes, until the live root page is the build just
  deployed, then runs the same checks against the LIVE URL, because the host
  can add at the edge what the repository never ships. It runs after the
  deploy, so a failure is an alarm on the live site, not a block on it.

The decided-assets list (`decided-assets.json`): a third-party asset is
permitted only by a decision taken before it is incorporated, recorded with
the asset, its origin and its purpose. The gates pass exactly the listed
entries and report each one they saw. Today the list has one entry, the
Cloudflare Web Analytics beacon (cookieless, added by the host at the edge).
Anything else fails.
