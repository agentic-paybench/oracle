#!/usr/bin/env bash
# Assemble the Cloudflare Pages deploy directory (docs/site) by copying the served
# source artefacts into it, then render the reader pages (DES-103) from the
# assembled tree with docs/site/build-pages.py. Idempotent. Run before
# `wrangler pages deploy docs/site`.
# The copied trees (schema/, adr/, methodology/) and every rendered page except
# the root index.html and 404.html are gitignored build outputs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SITE="$ROOT/docs/site"

rm -rf "$SITE/schema" "$SITE/adr" "$SITE/methodology" "$SITE/results"
cp -r "$ROOT/schema" "$SITE/schema"
cp -r "$ROOT/docs/adr" "$SITE/adr"
cp -r "$ROOT/docs/methodology/frozen" "$SITE/methodology"

# The named-rail results are G_S21-gated (ADR-009). The gate decides whether the
# artefact is ASSEMBLED into the deploy directory at all, not merely whether the
# site's JSON declares it: a file copied here is served, and a declaration is not
# a gate. posture-guard.mjs is the single shared decision point (it applies
# canEmit('published-rankings') against the same PDP config the worker reads) and
# is fail-closed, so a missing or unreadable config yields OMIT.
RESULTS_DECISION="$(node "$ROOT/worker/scripts/posture-guard.mjs" | cut -d' ' -f1)"
if [ "$RESULTS_DECISION" = "INCLUDE" ]; then
  cp -r "$ROOT/docs/results" "$SITE/results"
  echo "build-site: results INCLUDED (G_S21 open)"
else
  echo "build-site: results OMITTED (G_S21 closed; fail-closed)"
fi

# Render the reader pages from the ASSEMBLED tree only (never from docs/results),
# so a results page exists only when the gate copied the directory. The
# renderer is the vendored family layout (docs/site/family); labels for the
# results listing come from docs/results-labels.tsv. It exits non-zero on any
# failure and set -e stops the deploy.
python3 "$SITE/build-pages.py" --site "$SITE" --labels "$ROOT/docs/results-labels.tsv"

echo "site assembled at $SITE (capabilities + methodology + schema + adr + roadmap + posture + 404 + reader pages; results per the G_S21 decision above)"
