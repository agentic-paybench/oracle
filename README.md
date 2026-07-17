# oracle

Capability oracle for agentic payment rails: schema, ingestion, methodology,
and the static read surface.

## Scope

A queryable, methodology-grounded data layer over the capability and pricing
surface of agentic payment rails. The day-one schema is hybrid-tiered:

- **Tier 1**: pre-registered benchmark dimensions (settlement finality first;
  authorisation latency and fee predictability follow). The frozen methodology
  is vendored here and byte-verifiable against its external anchors.
- **Tier 2**: factual lookup (fees, supported assets, custody model,
  auth/dispute/refund/sanctions bundle), served as signed static credentials.
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
