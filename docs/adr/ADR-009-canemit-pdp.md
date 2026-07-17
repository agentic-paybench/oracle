# ADR-009: regulatory_posture as a fail-closed Policy Decision Point (PDP)

**Status:** accepted (2026-07-03).

**Context.** The oracle spans surfaces with different regulatory treatment. Some (the scored query, the named-rail results table, the graduated routing outputs) could emit perimeter-gated output; others (the Tier-2 factual lookup, the methodology form) are OUT. What ships live versus built-but-gated must be enforced in code, not asserted in prose or hidden behind a UI flag.

**Decision.** Build the full capability; gate only live emission. Every surface that could emit a perimeter-gated output routes through one fail-closed canEmit(mechanic, context) PDP driven by a regulatory_posture config keyed by gate (G_AUTH / G_QF / G_S21 / G_CUSTODY). A mechanic emits iff all its required gates are open AND its emission invariants hold (ADR-007's intent-free contract among them). Default deny; an unknown gate is treated as closed. Flipping a gate is one config value plus a redeploy (not a migration, not an unhide); each flip carries an audit record tying it to its trigger (for example external legal advice clearing s.21). Invariants are enforced as CI property tests against the live-posture config, not asserted in prose. One codebase, two posture configs (testnet and live): the gated path is proven to work under testnet posture and proven inert under live posture, so build-to-the-invariant-now and build-for-after-the-flip are one build. The G_S21 gate (named-rail table, s.21) and the regulatory_posture / 9Y trigger (scored query) never share a flag.

**Rationale.** A single fail-closed decision point with a default-deny posture is auditable and testable; hidden-but-present is neither. Keying by gate lets each surface cross to live on its own trigger without coupling to the others.

**Options considered.** (a) Hide gated surfaces behind a feature flag or unpublished route: rejected; hidden is not enforced and not demonstrable. (b) Separate codebases for testnet and live: rejected; divergence risk and double maintenance. (c) One shared flag for all gates: rejected; it conflates independent legal triggers (s.21 versus 9Y).

**Consequences.** All gated emission passes canEmit. The oracle owns the shared regulatory_posture config (config/regulatory_posture.testnet.json and config/regulatory_posture.live.json). Gate flips are config-plus-redeploy with an audit record.

**Related:** ADR-007 (the intent-free invariant this PDP enforces); the day-one tiered-schema decision.
