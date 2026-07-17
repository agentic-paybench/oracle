import { describe, expect, it } from "vitest";
import worker, { type Env } from "../src/index.js";

/** Minimal Env stub: ASSETS echoes the requested path so passthrough is observable. */
function stubEnv(overrides: Partial<Env> = {}): Env {
  return {
    ASSETS: {
      fetch: async (req: Request) =>
        new Response(`asset:${new URL(req.url).pathname}`, { status: 200 }),
    } as unknown as Fetcher,
    REPLY_PENDING: {} as unknown as R2Bucket,
    POSTURE_CONFIG: "live",
    ...overrides,
  };
}

describe("worker routing", () => {
  it("serves the health route", async () => {
    const res = await worker.fetch(new Request("https://x/healthz"), stubEnv());
    expect(res.status).toBe(200);
    expect(await res.text()).toBe("ok\n");
  });

  it("server-renders the form at /", async () => {
    const res = await worker.fetch(new Request("https://x/"), stubEnv());
    expect(res.status).toBe(200);
    expect(res.headers.get("content-type")).toContain("text/html");
    const body = await res.text();
    expect(body).toContain("<form");
    expect(body).toContain('action="/reply"');
  });

  it("server-renders the policy at /policy", async () => {
    const res = await worker.fetch(new Request("https://x/policy"), stubEnv());
    expect(res.status).toBe(200);
    expect(await res.text()).toContain("visibility policy");
  });

  it("passes static asset paths through to the ASSETS binding", async () => {
    const res = await worker.fetch(new Request("https://x/styles.css"), stubEnv());
    expect(await res.text()).toBe("asset:/styles.css");
  });

  it("wires POST /reply to the capture handler (rejects an empty body with 400, not 404)", async () => {
    const res = await worker.fetch(
      new Request("https://x/reply", { method: "POST" }),
      stubEnv(),
    );
    // Handled (not a 404 passthrough): no form body / no turnstile => 400.
    expect(res.status).toBe(400);
  });
});
