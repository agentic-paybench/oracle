import { describe, expect, it, vi } from "vitest";
import { makeSlackNotifier, type ReplyNotice } from "../src/notify.js";
import { handleReply, type PendingStore } from "../src/capture.js";

const NOTICE: ReplyNotice = {
  id: "20260706T101500Z-abcd1234",
  axis: "A3",
  received: "2026-07-06T10:15:00.000Z",
  rail_name: "Rail X Ltd",
};

describe("makeSlackNotifier", () => {
  it("is a no-op when no webhook is configured (never touches the network)", async () => {
    const spy = vi.spyOn(globalThis, "fetch");
    await makeSlackNotifier(undefined)(NOTICE);
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it("POSTs a PII-minimal message to the webhook URL", async () => {
    const spy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response("ok", { status: 200 }));
    await makeSlackNotifier("https://hooks.slack.example/T/B/X")(NOTICE);
    expect(spy).toHaveBeenCalledOnce();
    const [url, init] = spy.mock.calls[0]!;
    expect(url).toBe("https://hooks.slack.example/T/B/X");
    const text = JSON.parse((init as RequestInit).body as string).text as string;
    expect(text).toContain("20260706T101500Z-abcd1234");
    expect(text).toContain("A3");
    expect(text).toContain("Rail X Ltd");
    spy.mockRestore();
  });

  it("throws on a non-2xx webhook response (so the caller's catch swallows it)", async () => {
    const spy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response("no", { status: 500 }));
    await expect(makeSlackNotifier("https://hooks.slack.example/T/B/X")(NOTICE)).rejects.toThrow();
    spy.mockRestore();
  });
});

/** Minimal append-only store + valid form, mirroring capture.test.ts. */
function memStore() {
  const map = new Map<string, string>();
  const store: PendingStore = {
    head: async (k) => map.has(k),
    put: async (k, v) => {
      if (map.has(k)) throw new Error(`overwrite attempt on ${k}`);
      map.set(k, v);
    },
  };
  return { store, map };
}

function validForm(overrides: Record<string, string> = {}): FormData {
  const f = new FormData();
  const base: Record<string, string> = {
    rail_name: "Rail X Ltd",
    submitter: "Jane Roe, Head of Eng, jane@railx.example",
    authorised_signatory: "on",
    publication_url: "https://example.org/benchmark 2026-07-01",
    challenged_passage: "The finality median row for Rail X.",
    axis: "A3",
    grounds: "The chosen metric weighting mischaracterises our tail latency.",
    evidence: "https://example.org/our-metric",
    requested_remedy: "annotated reply",
    public_reply: "We disagree with the weighting; here is an alternative metric.",
    good_faith: "on",
    consent: "on",
    "cf-turnstile-response": "1x-dummy-token",
  };
  for (const [k, v] of Object.entries({ ...base, ...overrides })) f.set(k, v);
  return f;
}

const req = (form: FormData) => new Request("https://x/reply", { method: "POST", body: form });

describe("capture fires best-effort notify", () => {
  function depsWithNotify() {
    const { store, map } = memStore();
    const seen: ReplyNotice[] = [];
    const pending: Promise<unknown>[] = [];
    const deps = {
      store,
      verifyTurnstile: async () => true,
      now: () => new Date("2026-07-06T10:15:00.000Z"),
      notify: async (n: ReplyNotice) => {
        seen.push(n);
      },
      waitUntil: (p: Promise<unknown>) => pending.push(p),
    };
    return { deps, map, seen, drain: () => Promise.all(pending) };
  }

  it("notifies exactly once, with only id/axis/received/rail_name, on a new submission", async () => {
    const { deps, seen, drain } = depsWithNotify();
    const res = await handleReply(req(validForm()), deps);
    await drain();
    expect(res.status).toBe(202);
    expect(seen).toHaveLength(1);
    expect(seen[0]!.axis).toBe("A3");
    expect(seen[0]!.rail_name).toBe("Rail X Ltd");
    expect(seen[0]!.id).toMatch(/^20260706T101500Z-[0-9a-f]{8}$/);
    // PII discipline: the notice carries ONLY these four keys (no submitter/grounds/evidence/reply).
    expect(Object.keys(seen[0]!).sort()).toEqual(["axis", "id", "rail_name", "received"]);
  });

  it("does NOT notify on a duplicate re-POST", async () => {
    const { deps, seen, drain } = depsWithNotify();
    await handleReply(req(validForm()), deps);
    await handleReply(req(validForm()), deps); // identical => duplicate, no new record
    await drain();
    expect(seen).toHaveLength(1);
  });

  it("does NOT notify on a rejected (invalid) submission", async () => {
    const { deps, seen, drain } = depsWithNotify();
    const bad = validForm();
    bad.delete("public_reply");
    const res = await handleReply(req(bad), deps);
    await drain();
    expect(res.status).toBe(400);
    expect(seen).toHaveLength(0);
  });
});
