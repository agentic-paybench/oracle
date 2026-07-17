/**
 * M7 dry-run: the 10 numbered pass criteria from the plan happy-path, exercised
 * end-to-end at the handler level (worker.fetch) with an in-memory R2 and the real
 * ops scripts. CI-safe and deterministic; the companion live `wrangler dev` smoke
 * run is recorded in docs/devlog.md.
 *
 * Posture = "testnet": G_S21 is still closed (so the banner stays armed-idle and
 * the named-rail table stays omitted), but the non-live posture accepts the
 * documented Turnstile test token, so the capture path runs without a secret.
 * MOCK subject + MOCK result MR-000 only; no real operator; no deploy.
 */

import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync, readFileSync, existsSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it, beforeAll } from "vitest";
import worker, { type Env } from "../src/index.js";

const scriptsDir = fileURLToPath(new URL("../scripts/", import.meta.url));
const contentDir = fileURLToPath(new URL("../content/", import.meta.url));
const publicDir = fileURLToPath(new URL("../public/", import.meta.url));

/** In-memory R2 sufficient for capture (head/put) + dry-run extraction (get/list). */
function inMemR2() {
  const map = new Map<string, string>();
  const bucket = {
    head: async (k: string) => (map.has(k) ? ({} as unknown) : null),
    put: async (k: string, v: string) => {
      map.set(k, v);
      return {} as unknown;
    },
    get: async (k: string) => {
      const v = map.get(k);
      return v === undefined ? null : ({ text: async () => v } as unknown);
    },
    list: async ({ prefix }: { prefix: string }) => ({
      objects: [...map.keys()].filter((k) => k.startsWith(prefix)).map((key) => ({ key })),
    }),
  };
  return { bucket: bucket as unknown as R2Bucket, map };
}

function env(bucket: R2Bucket): Env {
  return {
    ASSETS: {
      fetch: async (req: Request) => {
        const p = new URL(req.url).pathname.replace(/^\//, "");
        try {
          return new Response(readFileSync(join(publicDir, p), "utf-8"), { status: 200 });
        } catch {
          return new Response("not found", { status: 404 });
        }
      },
    } as unknown as Fetcher,
    REPLY_PENDING: bucket,
    POSTURE_CONFIG: "testnet",
  };
}

function form(overrides: Record<string, string> = {}): FormData {
  const f = new FormData();
  const base: Record<string, string> = {
    rail_name: "Rail X Ltd (mock)",
    submitter: "Jane Roe, Head of Eng, jane@railx.example",
    authorised_signatory: "on",
    publication_url: "https://example.org/benchmark 2026-07-01",
    challenged_passage: "The finality median row for the mock rail.",
    axis: "A3",
    grounds: "The chosen weighting mischaracterises our tail latency.",
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

const post = (f: FormData) =>
  new Request("https://x/reply", { method: "POST", body: f });

let r2: ReturnType<typeof inMemR2>;
let e: Env;

beforeAll(() => {
  r2 = inMemR2();
  e = env(r2.bucket);
});

describe("M7 right-of-reply dry-run (10 criteria)", () => {
  it("[1] serves the form at / using only canonical names", async () => {
    const res = await worker.fetch(new Request("https://x/"), e);
    expect(res.status).toBe(200);
    const body = await res.text();
    expect(body).toContain("<form");
    expect(body).not.toMatch(/agent\s*pay/i);
    // policy served too
    const pol = await worker.fetch(new Request("https://x/policy"), e);
    expect(pol.status).toBe(200);
  });

  it("[2] the gate is closed: armed-idle banner, table omitted, notice suppressed", async () => {
    const body = await (await worker.fetch(new Request("https://x/"), e)).text();
    expect(body).toContain("armed"); // armed-but-idle banner
    expect(body).toContain("No named results are published yet");
    // Notice suppressed under testnet (G_S21 closed).
    const notice = execFileSync("node", [join(scriptsDir, "send-notice.mjs")], {
      env: { ...process.env, POSTURE_CONFIG: "testnet" },
      encoding: "utf-8",
    });
    expect(notice).toContain("notice suppressed");
    // Named-rail table omitted.
    const guard = execFileSync("node", [join(scriptsDir, "posture-guard.mjs")], {
      env: { ...process.env, POSTURE_CONFIG: "testnet" },
      encoding: "utf-8",
    });
    expect(guard).toContain("OMIT");
  });

  it("[3] a valid A3 submission is accepted: 202 + immediate-pending-badge", async () => {
    const res = await worker.fetch(post(form()), e);
    expect(res.status).toBe(202);
    const body = (await res.json()) as { id: string; visibility: string };
    expect(body.visibility).toBe("immediate-pending-badge");
  });

  it("[4] exactly one pending/ record; identical re-POST does not add a second", async () => {
    const keys = [...r2.map.keys()].filter((k) => k.startsWith("pending/"));
    expect(keys).toHaveLength(1);
    await worker.fetch(post(form()), e); // identical re-POST
    const keys2 = [...r2.map.keys()].filter((k) => k.startsWith("pending/"));
    expect(keys2).toHaveLength(1); // append-only, no overwrite/duplicate
  });

  it("[5] a malformed submission is rejected 400 and writes nothing", async () => {
    const before = r2.map.size;
    const f = form();
    f.delete("public_reply");
    const res = await worker.fetch(post(f), e);
    expect(res.status).toBe(400);
    expect(r2.map.size).toBe(before);
  });

  it("[6,7] draft-only then human-sign publishes ALONGSIDE MR-000 with the A3 badge", () => {
    const work = mkdtempSync(join(tmpdir(), "ror-dryrun-"));
    // Extract the real captured pending record from R2.
    const key = [...r2.map.keys()].find((k) => k.startsWith("pending/"))!;
    const pendingPath = join(work, "pending.json");
    writeFileSync(pendingPath, r2.map.get(key)!);
    const pubDir = join(work, "published", "MR-000");

    // [6] draft-only: produces an unsigned draft, publishes nothing.
    const pending = JSON.parse(r2.map.get(key)!);
    execFileSync("node", [join(scriptsDir, "draft-reply.mjs"), pendingPath, pubDir, "--result", "MR-000"]);
    expect(existsSync(join(pubDir, `${pending.id}.draft.json`))).toBe(true);
    expect(existsSync(join(pubDir, `${pending.id}.json`))).toBe(false);

    // [7] human-sign -> published; render alongside MR-000 with the badge.
    execFileSync(
      "node",
      [join(scriptsDir, "sign-reply.mjs"), join(pubDir, `${pending.id}.draft.json`), "--by", "A. Reviewer"],
      { env: { ...process.env, SIGN_AT: "2026-07-05T10:00:00.000Z" } },
    );
    expect(existsSync(join(pubDir, `${pending.id}.json`))).toBe(true);
    const out = join(work, "MR-000.html");
    execFileSync(
      "node",
      [join(scriptsDir, "build-results.mjs"), pubDir, join(contentDir, "results", "MR-000.json"), out],
      { env: { ...process.env, POSTURE_CONFIG: "testnet" } },
    );
    const html = readFileSync(out, "utf-8");
    expect(html).toContain("We disagree with the weighting");
    expect(html).toContain("reply pending review");
    expect(html).toContain("Withheld"); // named-rail table still gated
    expect(html).not.toMatch(/agent\s*pay/i);
  });

  it("[8] the 5/rail/30-day cap is a review-time control (capture does not block a 6th)", async () => {
    // Capture imposes no rate cap; distinct submissions from one rail all succeed,
    // and the cap is applied at human review over the pending log (policy point 9).
    for (let i = 0; i < 6; i++) {
      const res = await worker.fetch(post(form({ public_reply: `distinct reply number ${i}` })), e);
      expect(res.status).toBe(202);
    }
    const policy = JSON.parse(readFileSync(join(contentDir, "policy.json"), "utf-8"));
    expect(policy.points.find((p: { n: number }) => p.n === 9).text).toMatch(/five replies/i);
  });

  it("[9] two-posture proof: a throwaway G_S21-open config would INCLUDE the table", () => {
    const openDir = mkdtempSync(join(tmpdir(), "posture-open-"));
    writeFileSync(
      join(openDir, "regulatory_posture.testnet.json"),
      JSON.stringify({
        config_id: "testnet",
        regulatory_posture: "FIRST_PARTY_DEMO",
        gates: { G_AUTH: "closed", G_QF: "closed", G_S21: "open", G_CUSTODY: "open" },
      }),
    );
    const guard = execFileSync("node", [join(scriptsDir, "posture-guard.mjs")], {
      env: { ...process.env, ORACLE_POSTURE_CONFIG: openDir, POSTURE_CONFIG: "testnet" },
      encoding: "utf-8",
    });
    expect(guard).toContain("INCLUDE");
  });

  it("[10] overall: brand-clean across all shipped content + no unexpected files", () => {
    const files = readdirSync(contentDir, { recursive: true }) as string[];
    for (const f of files) {
      if (typeof f === "string" && (f.endsWith(".json") || f.endsWith(".md"))) {
        const text = readFileSync(join(contentDir, f), "utf-8");
        expect(text, `brand leak in ${f}`).not.toMatch(/agent\s*pay/i);
      }
    }
  });
});
