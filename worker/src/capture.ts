/**
 * POST /reply capture. Validates the 12-field submission, checks the honeypot,
 * verifies Turnstile, then writes ONE write-once record into the append-only
 * pending store. Nothing here publishes; publication is a separate human-gated
 * (L3) step. The endpoint is always live regardless of the G_S21 gate.
 *
 * Runtime-agnostic: the store, the Turnstile verifier, and the clock are injected,
 * so this unit-tests with an in-memory fake and no network (the thin R2 glue is
 * wired in index.ts and exercised by `wrangler dev`).
 */

import { validateSubmission } from "./validate.js";
import { axisById } from "./content.js";
import type { ReplyNotice } from "./notify.js";

/** Append-only store seam. R2 in production; an in-memory fake in tests. */
export interface PendingStore {
  head(key: string): Promise<boolean>;
  put(key: string, value: string): Promise<void>;
}

export interface CaptureDeps {
  store: PendingStore;
  /** Server-side Turnstile verification. Returns true iff the token is valid. */
  verifyTurnstile: (token: string, ip: string | null) => Promise<boolean>;
  /** Injected clock (Date) for a deterministic record id. */
  now: () => Date;
  /** Best-effort operator notification, fired AFTER the write-once record lands. */
  notify?: (n: ReplyNotice) => Promise<void>;
  /** ctx.waitUntil sink so the notification never blocks or fails the response. */
  waitUntil?: (p: Promise<unknown>) => void;
}

const PENDING_PREFIX = "pending/";
const HONEYPOT_FIELD = "website";
const TURNSTILE_FIELD = "cf-turnstile-response";

function json(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

/** Compact UTC stamp YYYYMMDDTHHMMSSZ (no separators), from an injected Date. */
function stamp(d: Date): string {
  return d.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

async function sha256Hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function handleReply(request: Request, deps: CaptureDeps): Promise<Response> {
  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return json({ error: "expected form-encoded body" }, 400);
  }

  // Honeypot: a real submitter leaves this empty. Any content => silently reject.
  const honey = form.get(HONEYPOT_FIELD);
  if (typeof honey === "string" && honey.trim().length > 0) {
    return json({ error: "rejected" }, 400);
  }

  // Turnstile: the token must verify server-side before we do any work.
  const token = form.get(TURNSTILE_FIELD);
  const ip = request.headers.get("cf-connecting-ip");
  const tokenOk =
    typeof token === "string" && token.length > 0 && (await deps.verifyTurnstile(token, ip));
  if (!tokenOk) {
    return json({ error: "turnstile verification failed" }, 400);
  }

  // Validate the 12 fields against the canonical schema.
  const raw: Record<string, string | boolean> = {};
  form.forEach((v, k) => {
    if (typeof v === "string") raw[k] = v;
  });
  const result = validateSubmission(raw);
  if (!result.ok) {
    return json({ error: "validation failed", details: result.errors }, 400);
  }

  const submission = result.value;
  const received = deps.now().toISOString();
  const visibility = axisById(submission.axis)?.visibility ?? "pre-moderated";

  // Content-addressed, write-once id: <stamp>-<8 hex of the submission hash>.
  const canonical = JSON.stringify(submission);
  const hash8 = (await sha256Hex(canonical)).slice(0, 8);
  const id = `${stamp(deps.now())}-${hash8}`;
  const key = `${PENDING_PREFIX}${id}`;

  const record = {
    schema: "right-of-reply/pending/v1",
    id,
    received,
    axis: submission.axis,
    visibility,
    status: "pending-review",
    signed_off_by: null,
    submission,
  };

  // Append-only: never overwrite an existing record. If the same body lands twice
  // in the same second (same key), the first write stands and we ack idempotently.
  if (await deps.store.head(key)) {
    return json({ id, status: "received", duplicate: true }, 202);
  }
  await deps.store.put(key, JSON.stringify(record, null, 2));

  // Best-effort, PII-minimal notification (never blocks or fails capture). The
  // duplicate branch above returns first, so one submission notifies at most once.
  if (deps.notify) {
    const notice: ReplyNotice = {
      id,
      axis: submission.axis,
      received,
      rail_name: submission.rail_name,
    };
    const sink = deps.waitUntil ?? ((p: Promise<unknown>) => void p);
    sink(deps.notify(notice).catch(() => {}));
  }

  return json({ id, status: "received", visibility }, 202);
}

/** Wrap a real R2 bucket as a PendingStore. */
export function r2Store(bucket: R2Bucket): PendingStore {
  return {
    head: async (key) => (await bucket.head(key)) !== null,
    put: async (key, value) => {
      await bucket.put(key, value, {
        httpMetadata: { contentType: "application/json; charset=utf-8" },
      });
    },
  };
}

/** Real Turnstile siteverify. In non-live posture with no secret, accept the test token. */
export function makeTurnstileVerifier(
  secret: string | undefined,
  posture: string | undefined,
): (token: string, ip: string | null) => Promise<boolean> {
  return async (token, ip) => {
    if (!secret) {
      // No secret configured. Live posture NEVER bypasses (fails closed, so a
      // misconfigured live deploy rejects rather than silently drops protection).
      // Off "live" (testnet/demo), Turnstile is simply not enforced: any non-empty
      // token from the test-sitekey widget is accepted so the armed-idle surface is
      // smoke-testable from a browser without a secret.
      if (posture === "live") return false;
      return token.length > 0;
    }
    const body = new FormData();
    body.set("secret", secret);
    body.set("response", token);
    if (ip) body.set("remoteip", ip);
    const resp = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method: "POST",
      body,
    });
    const data = (await resp.json()) as { success?: boolean };
    return data.success === true;
  };
}
