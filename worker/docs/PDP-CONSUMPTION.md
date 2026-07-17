# PDP consumption: how the right-of-reply Worker gates on ADR-009

This surface **consumes** the ADR-009 Policy Decision Point; it does not define or
fork one. There is no new ADR here.

## What is owned where

- **Owned by the oracle (Python):** the canonical PDP `can_emit(mechanic, context, config)`
  in `pdp/pdp.py`, the mechanic registry in `pdp/mechanics.py`, the gate keys in
  `pdp/gates.py`, and the shared config loader in `pdp/config.py`.
- **Owned by the oracle (config = the shared contract):** `config/regulatory_posture.live.json`
  and `config/regulatory_posture.testnet.json` at the repo root. These two files are
  the single source of truth for gate state.
- **This Worker (TypeScript):** `worker/src/posture.ts` MIRRORS the PDP contract for
  the one mechanic the right-of-reply surface gates on. It imports the shared config
  files directly (`../../config/regulatory_posture.{live,testnet}.json`); it never
  copies them into the worker tree and never edits `pdp/*.py`.

A Worker has no runtime filesystem, so both configs are bundled at build time and
selected by the `POSTURE_CONFIG` var (default `live`, the most restrictive posture).
A gate flip is a config-value change plus a redeploy, exactly as ADR-009 requires;
it is never a code change.

## The one mechanic this surface gates on

`published-rankings`. Its required gate is **`G_S21`** (the s.21
financial-promotion gate on the named-rail results table). It carries no
emission invariants (contrast ADR-007's intent-free contract on the factual
lookup) and is not posture-governed, so `canEmit(mechanicId, config)`
needs no `EmitContext`; the gate predicate is the whole decision.

Three right-of-reply surfaces derive from one `canEmit('published-rankings', ...)`
call:

1. named-rail results table visibility (`posture-guard.mjs`);
2. the pre-publication notice firing (`send-notice.mjs`);
3. the armed-vs-idle banner on the reply form.

The `POST /reply` capture endpoint is **always live** (armed at Day-0), never gated.

## Fail-closed, and the two flags never share

`canEmit` denies by default. An unknown mechanic, an unknown or missing gate, an
unknown `POSTURE_CONFIG` name, or a malformed config all deny. `G_S21` is the ONLY
gate this surface reads. The scored query's `regulatory_posture`/9Y trigger
(`G_AUTH`/`G_QF`) is deliberately not consulted here: clearing s.21 does not open 9Y
and clearing 9Y does not open s.21 (ADR-009). A CI property test asserts exactly
this decoupling (`test/posture.test.ts`).

## Reconcile step (config is the shared contract)

The oracle Day-0 build owns the config path and gate-key names. This mirror
assumes `config/regulatory_posture.{live,testnet}.json` with gates
`G_AUTH`/`G_QF`/`G_S21`/`G_CUSTODY` and posture enum names
`OFFLINE_TESTNET_ONLY`/`FIRST_PARTY_DEMO`/`LIVE_AUTHORISED`. All of these are already
present on `main` (verified 2026-07-05); if the oracle side ever renames the path or
a gate key, update `worker/src/posture.ts` imports + `GATE_KEYS`/`KNOWN_POSTURES` to
match. The config JSON is the shared contract, not the code.
