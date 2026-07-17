# worker

The right-of-reply Worker: serves the reply form and policy pages and accepts
one `POST /reply` into an append-only, non-public R2 pending store. Nothing
auto-publishes; a published reply is a human-signed static artefact under
`content/published/`. Gated surfaces (the named-rail table, the pre-publication
notice) consult the shared ADR-009 posture config via `src/posture.ts`
(fail-closed; see `docs/PDP-CONSUMPTION.md`).

Cloudflare Workers (TypeScript); no Durable Objects on critical paths.
Dev: `npm ci && npx vitest run`; local serve via `wrangler dev` (defaults to
the most-restrictive `live` posture; pass `--var POSTURE_CONFIG:testnet` to
exercise the open path locally).
