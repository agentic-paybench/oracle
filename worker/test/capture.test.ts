import { describe, expect, it } from "vitest";
import { handleReply, type PendingStore } from "../src/capture.js";

/** In-memory append-only store. put() refuses to overwrite an existing key. */
function memStore() {
  const map = new Map<string, string>();
  let putCalls = 0;
  const store: PendingStore = {
    head: async (k) => map.has(k),
    put: async (k, v) => {
      putCalls++;
      if (map.has(k)) throw new Error(`overwrite attempt on ${k}`);
      map.set(k, v);
    },
  };
  return { store, map, putCalls: () => putCalls };
}

const FIXED = new Date("2026-07-05T09:00:00.000Z");

function deps(store: PendingStore, verify = async () => true) {
  return { store, verifyTurnstile: verify, now: () => FIXED };
}

/** A complete, valid 12-field submission as URL-encoded form data. */
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

function req(form: FormData): Request {
  return new Request("https://x/reply", { method: "POST", body: form });
}

describe("POST /reply capture", () => {
  it("accepts a valid submission: 202 + exactly one pending/ record", async () => {
    const { store, map, putCalls } = memStore();
    const res = await handleReply(req(validForm()), deps(store));
    expect(res.status).toBe(202);
    const body = (await res.json()) as { id: string; visibility: string };
    expect(body.visibility).toBe("immediate-pending-badge"); // A3
    const keys = [...map.keys()];
    expect(keys).toHaveLength(1);
    expect(keys[0]).toMatch(/^pending\/20260705T090000Z-[0-9a-f]{8}$/);
    expect(putCalls()).toBe(1);
    const stored = JSON.parse(map.get(keys[0]!)!);
    expect(stored.signed_off_by).toBeNull();
    expect(stored.status).toBe("pending-review");
    expect(stored.submission.rail_name).toBe("Rail X Ltd");
  });

  it("is append-only: an identical re-POST does not overwrite or add a second write", async () => {
    const { store, map, putCalls } = memStore();
    await handleReply(req(validForm()), deps(store));
    const res2 = await handleReply(req(validForm()), deps(store));
    expect(res2.status).toBe(202);
    expect(((await res2.json()) as { duplicate: boolean }).duplicate).toBe(true);
    expect(map.size).toBe(1); // no second object
    expect(putCalls()).toBe(1); // head-guard short-circuited the second write
  });

  it("rejects a missing required field: 400 + zero writes", async () => {
    const { store, map } = memStore();
    const form = validForm();
    form.delete("public_reply");
    const res = await handleReply(req(form), deps(store));
    expect(res.status).toBe(400);
    expect(((await res.json()) as { error: string }).error).toBe("validation failed");
    expect(map.size).toBe(0);
  });

  it("rejects an unticked required consent checkbox: 400 + zero writes", async () => {
    const { store, map } = memStore();
    const form = validForm();
    form.delete("consent");
    const res = await handleReply(req(form), deps(store));
    expect(res.status).toBe(400);
    expect(map.size).toBe(0);
  });

  it("rejects a bad axis value: 400 + zero writes", async () => {
    const { store, map } = memStore();
    const res = await handleReply(req(validForm({ axis: "A9" })), deps(store));
    expect(res.status).toBe(400);
    expect(map.size).toBe(0);
  });

  it("rejects a filled honeypot silently: 400 + zero writes", async () => {
    const { store, map } = memStore();
    const res = await handleReply(req(validForm({ website: "http://spam" })), deps(store));
    expect(res.status).toBe(400);
    expect(map.size).toBe(0);
  });

  it("rejects a failed Turnstile: 400 + zero writes", async () => {
    const { store, map } = memStore();
    const res = await handleReply(req(validForm()), deps(store, async () => false));
    expect(res.status).toBe(400);
    expect(((await res.json()) as { error: string }).error).toContain("turnstile");
    expect(map.size).toBe(0);
  });

  it("enforces the 500-word public-reply cap: 400 + zero writes", async () => {
    const { store, map } = memStore();
    const tooLong = Array.from({ length: 501 }, (_, i) => `w${i}`).join(" ");
    const res = await handleReply(req(validForm({ public_reply: tooLong })), deps(store));
    expect(res.status).toBe(400);
    expect(map.size).toBe(0);
  });
});
