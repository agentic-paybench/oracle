# Frozen settlement-finality methodology (v1.2, de-ranked public subset)

This is the byte-identical public subset of the PayBench settlement-finality
pre-registration, methodology v1.2, vendored from the signed tag
`paybench-prereg-v1.2` (commit `aeab0640`) in the public
[payhelm repository](https://github.com/agentic-paybench/payhelm). Extracted
from the tagged tree, not a working checkout.

- **What is here (the "how"):** the frozen `methodology.md`, the calibration plan,
  the 5 finality provenance files (log-space mu/sigma calibration params), the 5
  content-addressed fixtures, the MockBench harness, and the manifest.
- **What is withheld (the "who-beat-whom", F14 de-rank):** `runs/finality-run.json`
  (the Bradley-Terry league table) and any named-rail results table. Those publish
  only if the `G_S21` gate flips (UK s.21 financial-promotion clearance).

## Verify

CI-grade byte check (no payhelm checkout or keyring needed):

    docs/methodology/verify-vendored-freeze.sh

Full anchor verification (tag signature + OpenTimestamps + cosign/Rekor) is a
local maintainer step against the tag itself:

    payhelm/paybench/methodology/verify-freeze.sh paybench-prereg-v1.2

The manifest's own sha256 is the anchored value
`a5f6feb46819dc3926012a8a38ac519cd0d5df33c20734516dca4b32d30d3a6f` (OSF DOI plus
Bitcoin block 952636 plus Rekor logIndex 1740328355).

The frozen files are vendored byte-exact, so working references inside them
(file paths, planning labels) refer to the pre-registration's source
repository and its working context, not to this repo.
