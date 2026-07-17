import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync, existsSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it, beforeAll } from "vitest";

const scriptsDir = fileURLToPath(new URL("../scripts/", import.meta.url));
const contentDir = fileURLToPath(new URL("../content/", import.meta.url));
const s = (name: string) => join(scriptsDir, name);

function run(script: string, args: string[], env: Record<string, string> = {}) {
  try {
    const out = execFileSync("node", [s(script), ...args], {
      env: { ...process.env, ...env },
      encoding: "utf-8",
    });
    return { out, code: 0 };
  } catch (e) {
    const err = e as { status?: number; stdout?: string; stderr?: string };
    return { out: (err.stdout ?? "") + (err.stderr ?? ""), code: err.status ?? 1 };
  }
}

/** A pending record shaped exactly as the capture endpoint writes it (axis A3). */
const PENDING = {
  schema: "right-of-reply/pending/v1",
  id: "20260705T090000Z-abcd1234",
  received: "2026-07-05T09:00:00.000Z",
  axis: "A3",
  visibility: "immediate-pending-badge",
  status: "pending-review",
  signed_off_by: null,
  submission: {
    rail_name: "Rail X Ltd",
    challenged_passage: "The finality median row for Rail X.",
    public_reply: "We disagree with the weighting; here is an alternative metric.",
  },
};

let work: string;
let pendingPath: string;
let pubDir: string;

beforeAll(() => {
  work = mkdtempSync(join(tmpdir(), "ror-publish-"));
  pendingPath = join(work, "pending.json");
  writeFileSync(pendingPath, JSON.stringify(PENDING));
  pubDir = join(work, "published", "MR-000");
});

describe("L3 draft-only + human-sign publish path", () => {
  it("draft-reply produces an UNSIGNED draft and does NOT publish", () => {
    const { code } = run("draft-reply.mjs", [pendingPath, pubDir, "--result", "MR-000"]);
    expect(code).toBe(0);
    const draftJson = join(pubDir, `${PENDING.id}.draft.json`);
    expect(existsSync(draftJson)).toBe(true);
    // Crucially: no published (non-draft) record yet.
    expect(existsSync(join(pubDir, `${PENDING.id}.json`))).toBe(false);
    const draft = JSON.parse(readFileSync(draftJson, "utf-8"));
    expect(draft.signed_off_by).toBeNull();
    expect(draft.status).toBe("draft");
    // The filled template carries the reply text.
    expect(readFileSync(join(pubDir, `${PENDING.id}.draft.md`), "utf-8")).toContain(
      PENDING.submission.public_reply,
    );
  });

  it("sign-reply promotes the draft to a published, signed record", () => {
    const draftJson = join(pubDir, `${PENDING.id}.draft.json`);
    const { code } = run("sign-reply.mjs", [draftJson, "--by", "A. Reviewer"], {
      SIGN_AT: "2026-07-05T10:00:00.000Z",
    });
    expect(code).toBe(0);
    const pub = JSON.parse(readFileSync(join(pubDir, `${PENDING.id}.json`), "utf-8"));
    expect(pub.status).toBe("published");
    expect(pub.signed_off_by).toBe("A. Reviewer");
    expect(pub.signed_at).toBe("2026-07-05T10:00:00.000Z");
    expect(existsSync(join(pubDir, `${PENDING.id}.md`))).toBe(true);
  });

  it("build-results renders the signed reply ALONGSIDE MR-000 with the A3 pending-review badge, and OMITS the named-rail table while G_S21 closed", () => {
    const out = join(work, "MR-000.html");
    const { code } = run(
      "build-results.mjs",
      [pubDir, join(contentDir, "results", "MR-000.json"), out],
      { POSTURE_CONFIG: "live" },
    );
    expect(code).toBe(0);
    const html = readFileSync(out, "utf-8");
    expect(html).toContain("Mock settlement-finality result");
    expect(html).toContain(PENDING.submission.public_reply);
    expect(html).toContain("reply pending review"); // A3 immediate badge
    expect(html).toContain("A. Reviewer");
    // Named-rail table withheld under the live (G_S21 closed) config.
    expect(html).toContain("Withheld");
    expect(html).not.toMatch(/agent\s*pay/i);
  });

  it("build-results INCLUDES the named-rail table under a throwaway G_S21-open config", () => {
    const openDir = mkdtempSync(join(tmpdir(), "posture-open-"));
    writeFileSync(
      join(openDir, "regulatory_posture.testnet.json"),
      JSON.stringify({
        config_id: "testnet",
        regulatory_posture: "FIRST_PARTY_DEMO",
        gates: { G_AUTH: "closed", G_QF: "closed", G_S21: "open", G_CUSTODY: "open" },
      }),
    );
    const out = join(work, "MR-000-open.html");
    run("build-results.mjs", [pubDir, join(contentDir, "results", "MR-000.json"), out], {
      ORACLE_POSTURE_CONFIG: openDir,
      POSTURE_CONFIG: "testnet",
    });
    const html = readFileSync(out, "utf-8");
    expect(html).not.toContain("Withheld");
    expect(html).toContain("named-rail league table emitted");
  });

  it("posture-guard OMITs the table under live and INCLUDEs it under an open config", () => {
    expect(run("posture-guard.mjs", [], { POSTURE_CONFIG: "live" }).out).toContain("OMIT");
    const openDir = mkdtempSync(join(tmpdir(), "posture-open-"));
    writeFileSync(
      join(openDir, "regulatory_posture.testnet.json"),
      JSON.stringify({
        config_id: "testnet",
        regulatory_posture: "FIRST_PARTY_DEMO",
        gates: { G_S21: "open" },
      }),
    );
    const openRun = run("posture-guard.mjs", [], {
      ORACLE_POSTURE_CONFIG: openDir,
      POSTURE_CONFIG: "testnet",
    });
    expect(openRun.out).toContain("INCLUDE");
  });
});
