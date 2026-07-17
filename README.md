# oracle

[![ci](https://github.com/agentic-paybench/oracle/actions/workflows/ci.yml/badge.svg)](https://github.com/agentic-paybench/oracle/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

Capability oracle for agentic payment rails: schema, ingestion, methodology,
and the static read surface. Live at
[oracle.agentic-paybench.dev](https://oracle.agentic-paybench.dev/).

## Quickstart

Prerequisites: Python 3.12+ and Node 22+.

```sh
# run the Python suite (schema, PDP gates, mutation drill, manifest check)
python -m pytest tests -q

# verify the frozen methodology bytes against the anchored manifest
docs/methodology/verify-vendored-freeze.sh

# verify the already-published capability credentials (no keys needed)
cd ingest/signer && npm ci && node verify.mjs && cd ../..

# run the right-of-reply Worker suite
cd worker && npm ci && npx vitest run
```

## Scope

A queryable, methodology-grounded data layer over the capability and pricing
surface of agentic payment rails. The day-one schema is hybrid-tiered:

- **Tier 1**: pre-registered benchmark dimensions (settlement finality first;
  authorisation latency and fee predictability follow). The frozen methodology
  is vendored here and byte-verifiable against its external anchors.
- **Tier 2**: factual lookup (fees, supported assets, custody model,
  auth/dispute/refund/sanctions bundle), served as signed static credentials.
  Tier-2 field values are seeded `pending` at launch and fill in as sourced
  (see `docs/site/roadmap.md`); the credential envelope and its signature
  chain are live from day one.
- **Tier 3**: declared roadmap items, clearly labelled, no measurements.

The live surface carries no rail rankings and accepts no payment-intent
parameters; that is an enforced property, not a promise. See
[ADR-007](docs/adr/ADR-007-intent-free-oracle.md) (the intent-free contract)
and [ADR-009](docs/adr/ADR-009-canemit-pdp.md) (the fail-closed gate that
keeps gated surfaces inert), both enforced by CI property tests including a
mutation drill.

## Structure

- `schema/`: JSON-LD context + JSON Schema for capability records
  (VCDM 2.0-enveloped).
- `ingest/`: Python pipeline building the served capability records, plus the
  offline VC signer.
- `pdp/` + `config/`: the ADR-009 policy decision point and the two posture
  configs (testnet and live; default-deny).
- `docs/methodology/`: the frozen settlement-finality methodology (v1.2
  public subset); `docs/methodology/verify-vendored-freeze.sh` proves the
  bytes against the anchored manifest.
- `docs/site/`: the static oracle read surface as deployed.
- `worker/`: the right-of-reply Worker (reply capture; human-signed
  publication; see `worker/README.md`).
- `tests/`: the Python suite enforcing the ADR-007/ADR-009 properties, the
  mutation drill, and the manifest check.
- `public-manifest.toml`: every tracked file mapped to its reason for being
  public; CI fails default-deny on any unmapped file.

## Operating notes

- No persistent backend. Credentials are pre-signed offline and served as
  static artefacts; there is no runtime signing exposure.
- No Durable Objects on critical paths (portability).
- Production credentials are hardware-signed only; the committed dev key
  material is non-production (see `ingest/signer/README.md`).

## License

Apache-2.0. See [LICENSE](LICENSE).
