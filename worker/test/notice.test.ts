import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const script = fileURLToPath(new URL("../scripts/send-notice.mjs", import.meta.url));

function run(env: Record<string, string>): { out: string; code: number } {
  try {
    const out = execFileSync("node", [script], {
      env: { ...process.env, ...env },
      encoding: "utf-8",
    });
    return { out, code: 0 };
  } catch (e) {
    const err = e as { status?: number; stdout?: string };
    return { out: err.stdout ?? "", code: err.status ?? 1 };
  }
}

/** Write a throwaway config dir with G_S21 open (never committed). */
function openConfigDir(): string {
  const dir = mkdtempSync(join(tmpdir(), "posture-open-"));
  writeFileSync(
    join(dir, "regulatory_posture.testnet.json"),
    JSON.stringify({
      config_id: "testnet",
      regulatory_posture: "FIRST_PARTY_DEMO",
      gates: { G_AUTH: "closed", G_QF: "closed", G_S21: "open", G_CUSTODY: "open" },
    }),
  );
  return dir;
}

describe("pre-publication notice, G_S21-gated", () => {
  it("renders under the real live config now that G_S21 is open (render only; the script sends nothing)", () => {
    const { out, code } = run({ POSTURE_CONFIG: "live" });
    expect(code).toBe(0);
    expect(out).not.toContain("notice suppressed");
    expect(out).toContain("Pre-publication notice");
  });

  it("is a no-op under the real testnet config too (G_S21 also closed there)", () => {
    const { out, code } = run({ POSTURE_CONFIG: "testnet" });
    expect(code).toBe(0);
    expect(out).toContain("notice suppressed");
  });

  it("renders the templated notice when G_S21 is open (throwaway config), filling placeholders", () => {
    const dir = openConfigDir();
    const { out, code } = run({
      ORACLE_POSTURE_CONFIG: dir,
      POSTURE_CONFIG: "testnet",
      NOTICE_SUBJECT_RAIL: "Rail X Ltd",
      NOTICE_RESPOND_BY: "2026-07-31",
    });
    expect(code).toBe(0);
    expect(out).toContain("rendering pre-publication notice");
    expect(out).toContain("# Pre-publication notice");
    expect(out).toContain("Rail X Ltd"); // placeholder filled
    expect(out).toContain("2026-07-31");
    expect(out).not.toContain("{{subject_rail}}"); // no unfilled required slot
    // The internal authoring comment block is stripped from the rendered notice.
    expect(out).not.toContain("DRAFT / PLACEHOLDER legal copy");
  });

  it("fails closed on a missing/unknown config (suppressed, not rendered)", () => {
    const { out, code } = run({ POSTURE_CONFIG: "does-not-exist" });
    expect(code).toBe(0);
    expect(out).toContain("notice suppressed");
  });

  it("uses only canonical names in the rendered notice", () => {
    const dir = openConfigDir();
    const { out } = run({ ORACLE_POSTURE_CONFIG: dir, POSTURE_CONFIG: "testnet" });
    expect(out).not.toMatch(/agent\s*pay/i);
  });
});
