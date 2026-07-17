/**
 * Best-effort operator notification for a new right-of-reply submission.
 *
 * Fired AFTER the write-once R2 record lands, via ctx.waitUntil, so a delivery
 * failure never blocks or fails capture. PII-minimal by construction: only the
 * record id, axis, received time, and the operator's (public) rail name are sent;
 * submitter contact, grounds, evidence, and reply text stay in R2 only. The
 * webhook URL (which encodes the target channel) is a Worker secret, never
 * committed.
 */

/** The minimal, PII-safe summary sent to the notification channel. */
export interface ReplyNotice {
  id: string;
  axis: string;
  received: string;
  rail_name: string;
}

/**
 * Build a Slack notifier from an incoming-webhook URL. With no webhook
 * configured (e.g. tests, or before the secret is set), returns a no-op that
 * never touches the network. Throws on a non-2xx webhook response so the
 * caller's `.catch` can swallow it (best-effort at the call site).
 */
export function makeSlackNotifier(
  webhookUrl: string | undefined,
): (n: ReplyNotice) => Promise<void> {
  if (!webhookUrl) return async () => {};
  return async (n) => {
    const text =
      `:incoming_envelope: New right-of-reply submission awaiting review\n` +
      `• id: \`${n.id}\`\n` +
      `• axis: ${n.axis}\n` +
      `• rail: ${n.rail_name}\n` +
      `• received: ${n.received}\n` +
      `Review via the R2 dashboard (pending/ prefix). Nothing publishes until a human signs off.`;
    const resp = await fetch(webhookUrl, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!resp.ok) {
      throw new Error(`slack notify failed: ${resp.status}`);
    }
  };
}
