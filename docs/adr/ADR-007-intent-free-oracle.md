# ADR-007: Intent-Free Oracle

**Status:** proposed (DRAFT; 2026-07-03). The input/output contract is enforceable now; the legal claim that it sits outside RAO 9Y is subject to external legal confirmation. This is the Day-0 oracle's live-legality condition.

**Context.** The Day-0 oracle ships a live Tier-2 factual lookup. Draft PERG 19.8 reads venue and price-finding as likely arranging, so an oracle that scores or ranks, or that ingests a specific payment's parameters, risks being IN on 9Y. The factual-lookup surface must be demonstrably not doing that.

**Decision.** The live oracle query surface must satisfy the Intent-Free invariant: (1) the query excludes intent parameters {amount, payee, asset-to-pay}; (2) the response excludes {score, rank, recommendation}. It answers "what is true about rail X" (fees, supported assets, custody model, and the auth/dispute/refund/sanctions bundle), never "what should I do for this payment". If both hold, the factual lookup is treated as OUT. Enforced via the ADR-009 PDP plus a CI property test run against the live-posture config. Note: the Day-0 implementation makes this vacuously true by serving Tier-2 as static, path-addressed VCs with no query object that could accept intent params; any future Worker read path must be a dumb path-addressed GET and must re-pass the property test.

**Rationale.** A scored query and an inform-only ranked list are the SAME arranging act, seen from the lookup side versus the routing side. The factual lookup is OUT precisely because it carries no intent and emits no scored output. Making that a testable input/output contract gives a bright line rather than a judgment call.

**Options considered.** (a) Ship a "lightly scored" oracle at Day-0: rejected; any score or rank makes it a scored query (IN). (b) Withhold the oracle entirely until authorisation: rejected; the factual lookup is genuinely OUT and is real B1 value. (c) Hide the scored path behind a UI flag only: rejected per ADR-009; hidden is not enforced.

**Consequences.** The Day-0 oracle carries no rankings and refuses intent params. Reverse tripwire: if the oracle accepts an intent param or emits a score, rank, or recommendation, the factual lookup becomes a scored query (IN) and must be gated behind regulatory_posture / 9Y. The scored query is built but testnet-only. The property test is a build milestone.

**Related:** ADR-009 (the enforcement spine); the day-one tiered-schema decision.
