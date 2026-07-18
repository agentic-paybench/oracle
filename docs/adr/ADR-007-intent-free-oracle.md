# ADR-007: Intent-Free Oracle

**Status:** accepted (2026-07-03; wording revised 2026-07-18). This record decides an engineering control; it does not decide, and takes no position on, any question of regulatory classification.

**Context.** The oracle ships a live Tier-2 factual lookup. Draft PERG 19.8 (the UK FCA's draft perimeter guidance for cryptoasset activities) reads venue and price-finding expansively, so a lookup surface should be demonstrably factual: no scoring, no ranking, no ingestion of a specific payment's parameters. The invariant below makes that a tested property of the surface rather than a description of it.

**Decision.** The live oracle query surface must satisfy the Intent-Free invariant: (1) the query excludes intent parameters {amount, payee, asset-to-pay}; (2) the response excludes {score, rank, recommendation}. It answers "what is true about rail X" (fees, supported assets, custody model, and the auth/dispute/refund/sanctions bundle), never "what should I do for this payment". The invariant is enforced via the ADR-009 PDP plus a CI property test run against the live-posture config. Note: the current implementation makes this vacuously true by serving Tier-2 as static, path-addressed VCs with no query object that could accept intent params; any future Worker read path must be a dumb path-addressed GET and must re-pass the property test.

**Rationale.** A factual lookup and a scored recommendation are different acts: the first states what is true, the second advises what to do. The invariant keeps the live surface unambiguously on the factual side of that line, as a testable input/output contract rather than a judgment call, and regardless of how any regulator ultimately classifies either act.

**Options considered.** (a) Ship a "lightly scored" lookup: rejected; any score or rank crosses the line the invariant exists to hold. (b) Withhold the lookup entirely: rejected; the factual lookup is real developer value, and the invariant makes its factual character provable. (c) Hide a scored path behind a UI flag only: rejected per ADR-009; hidden is not enforced.

**Consequences.** The live oracle carries no rankings and refuses intent params. Reverse tripwire: if the surface ever accepts an intent param or emits a score, rank, or recommendation, it has left the factual-lookup contract and must instead pass the posture gate as a scored query, which the live config holds inert. The property test runs in CI on every change.

**Related:** ADR-009 (the enforcement spine); the tiered-schema design.
