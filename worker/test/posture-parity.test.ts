import { describe, expect, it } from "vitest";
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * ADR-009 parity guard (build-integrity, not a perimeter finding).
 *
 * G_S21 gates the EMISSION of the two perimeter-sensitive artefacts: the
 * named-rail results table (content/results/*) and the pre-publication notice.
 * Those are handled ONLY by the offline ops scripts (build-results.mjs /
 * send-notice.mjs), never by the deployed Worker. This test locks that in: no
 * Worker src module may import them, and the served ASSETS dir must not contain
 * them, so a future edit cannot quietly wire a gated artefact into the live
 * bundle where the G_S21 gate could be bypassed by mere presence.
 */
const srcDir = fileURLToPath(new URL("../src/", import.meta.url));
const publicDir = fileURLToPath(new URL("../public/", import.meta.url));

describe("ADR-009 parity: gated artefacts never enter the live bundle", () => {
  const srcFiles = readdirSync(srcDir).filter((f) => f.endsWith(".ts"));

  it("no Worker src module imports content/results/* or the pre-publication notice", () => {
    for (const f of srcFiles) {
      const text = readFileSync(join(srcDir, f), "utf-8");
      expect(text, `${f} imports a gated results artefact`).not.toMatch(
        /from\s+["'][^"']*content\/results\//,
      );
      expect(text, `${f} imports the pre-publication notice`).not.toMatch(
        /from\s+["'][^"']*pre-publication-notice/,
      );
    }
  });

  it("the served ASSETS dir (public/) contains no results or notice artefacts", () => {
    const served = existsSync(publicDir)
      ? (readdirSync(publicDir, { recursive: true }) as string[])
      : [];
    for (const entry of served) {
      const name = String(entry);
      expect(name, `served asset leaks a gated artefact: ${name}`).not.toMatch(
        /results|pre-publication-notice|MR-\d/i,
      );
    }
  });
});
