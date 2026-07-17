/**
 * Right-of-reply channel Worker: entry point.
 *
 * Two jobs, one origin:
 *   - GET  /            server-rendered reply form (banner reflects the live gate)
 *   - GET  /policy      server-rendered response cap + visibility policy
 *   - POST /reply       capture a named subject's reply into append-only R2
 *   - <other GET>       static assets (CSS) via the ASSETS binding
 *
 * Nothing here auto-publishes. The named-rail surfaces (table visibility, notice,
 * the armed-vs-idle banner) consult canEmit('published-rankings', ...); the
 * capture endpoint is always live.
 */

import { canEmitFromEnv } from "./posture.js";
import { renderFormPage, renderPolicyPage } from "./render.js";
import { handleReply, makeTurnstileVerifier, r2Store } from "./capture.js";
import { makeSlackNotifier } from "./notify.js";

export interface Env {
  /** Static assets binding (CSS) served from ./public. */
  ASSETS: Fetcher;
  /** Append-only, non-public pending store. Operator-provisioned at go-live. */
  REPLY_PENDING: R2Bucket;
  /** ADR-009 deployment discriminator: "live" (default, most restrictive) | "testnet". */
  POSTURE_CONFIG?: string;
  /** Public Turnstile sitekey (safe to embed). Defaults to the always-pass test key. */
  TURNSTILE_SITEKEY?: string;
  /** Cloudflare Turnstile secret. Operator-supplied at go-live; never committed. */
  TURNSTILE_SECRET?: string;
  /** Slack incoming-webhook URL for the L3-review notification. Secret; never committed. */
  SLACK_WEBHOOK_URL?: string;
}

/** Cloudflare's documented always-passes Turnstile test sitekey (public, safe). */
const TURNSTILE_TEST_SITEKEY = "1x00000000000000000000AA";

function html(body: string, status = 200): Response {
  return new Response(body, {
    status,
    headers: { "content-type": "text/html; charset=utf-8" },
  });
}

export default {
  async fetch(request: Request, env: Env, ctx?: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/healthz") {
      return new Response("ok\n", {
        status: 200,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }

    if (request.method === "GET" && url.pathname === "/") {
      const rankingsGate = canEmitFromEnv("published-rankings", env.POSTURE_CONFIG);
      return html(
        renderFormPage({
          rankingsGate,
          turnstileSitekey: env.TURNSTILE_SITEKEY || TURNSTILE_TEST_SITEKEY,
        }),
      );
    }

    if (request.method === "GET" && url.pathname === "/policy") {
      return html(renderPolicyPage());
    }

    // POST /reply: always-live capture into the append-only pending store.
    // Never gated (arming is not the same as publishing); nothing auto-publishes.
    if (request.method === "POST" && url.pathname === "/reply") {
      return handleReply(request, {
        store: r2Store(env.REPLY_PENDING),
        verifyTurnstile: makeTurnstileVerifier(env.TURNSTILE_SECRET, env.POSTURE_CONFIG),
        now: () => new Date(),
        notify: makeSlackNotifier(env.SLACK_WEBHOOK_URL),
        waitUntil: ctx ? (p) => ctx.waitUntil(p) : undefined,
      });
    }

    // Everything else falls through to the static assets (CSS).
    return env.ASSETS.fetch(request);
  },
};
