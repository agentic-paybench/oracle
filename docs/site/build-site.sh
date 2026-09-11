#!/usr/bin/env bash
# Assemble the Cloudflare Pages deploy directory (docs/site) by copying the served
# source artefacts into it, then generate directory index pages so /adr/ and
# /methodology/ resolve (Cloudflare Pages serves index.html for a directory
# request). Idempotent. Run before `wrangler pages deploy docs/site`.
# The copied trees (schema/, adr/, methodology/) are gitignored build outputs.
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

# Generate a simple directory index so the landing-page links resolve.
gen_index () {  # $1 = dir under site, $2 = page title
  local dir="$SITE/$1" title="$2"
  {
    echo "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
    echo "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
    echo "<title>${title}</title><style>body{font:16px/1.6 system-ui,sans-serif;max-width:46rem;margin:3rem auto;padding:0 1rem}code{font-family:ui-monospace,monospace}</style></head><body>"
    echo "<h1>${title}</h1><p><a href=\"../\">&larr; oracle index</a></p><ul>"
    ( cd "$dir" && find . -type f ! -name index.html | sort | while read -r f; do
        f="${f#./}"; echo "<li><a href=\"${f}\"><code>${f}</code></a></li>"
      done )
    echo "</ul></body></html>"
  } > "$dir/index.html"
}
gen_index adr "Decision records (ADR)"
gen_index methodology "Settlement-finality methodology (frozen v1.2)"
if [ -d "$SITE/results" ]; then
  gen_index results "Named-rail measurements"
fi

echo "site assembled at $SITE (capabilities + methodology + schema + adr + roadmap + posture + 404 + dir indexes; results per the G_S21 decision above)"
