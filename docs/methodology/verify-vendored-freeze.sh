#!/usr/bin/env bash
# Verify the vendored de-ranked frozen v1.2 public subset against the anchored
# manifest. This is the CI-grade byte check (served bytes -> manifest -> anchor);
# it needs no payhelm checkout or keyring. Full tag / GPG / OpenTimestamps / Rekor
# verification is a local build-time or founder step, run against the tag itself:
#   payhelm/paybench/methodology/verify-freeze.sh paybench-prereg-v1.2
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FROZEN="$HERE/frozen"
ANCHOR="a5f6feb46819dc3926012a8a38ac519cd0d5df33c20734516dca4b32d30d3a6f"
WITHHELD="runs/finality-run.json"

cd "$FROZEN"

# 1) manifest self-hash == the anchored value.
got="$(sha256sum prereg-manifest.sha256 | awk '{print $1}')"
[ "$got" = "$ANCHOR" ] || { echo "FAIL: manifest self-hash $got != anchor $ANCHOR"; exit 1; }

# 2) every public-subset file matches the manifest (the ranking artefact is withheld).
grep -vE "^#|$WITHHELD" prereg-manifest.sha256 | sha256sum -c --quiet

# 3) the withheld ranking artefact must be absent (F14 de-rank).
[ ! -e "$WITHHELD" ] || { echo "FAIL: $WITHHELD must not be vendored (F14 de-rank)"; exit 1; }

echo "OK: frozen v1.2 public subset verified against anchor $ANCHOR (ranking withheld)"
