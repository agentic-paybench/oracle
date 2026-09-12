#!/usr/bin/env node
/**
 * Pre-publication notice trigger, armed to the ADR-009 G_S21 gate.
 *
 * Standalone Node ops utility (eslint-ignored, run with `node`). It mirrors the
 * tiny PDP gate read against the shared config/ so it needs no build step:
 *   - published-rankings requires gate G_S21.
 *   - Fail-closed: a missing/malformed config, or G_S21 not explicitly "open",
 *     suppresses the notice.
 *
 * While G_S21 is closed this is a NO-OP: it logs that the gate is
 * closed and exits 0 without rendering or sending. When G_S21 is open it renders
 * the templated notice for a named subject and prints it. It NEVER actually emails;
 * a human sends the reviewed notice. It is never run against a real operator during
 * a build or dry-run.
 *
 * Config selection mirrors pdp/config.py:
 *   - ORACLE_POSTURE_CONFIG env overrides the config directory (default ../../config)
 *   - POSTURE_CONFIG env selects the named config (default "live")
 *
 * Placeholders are filled from NOTICE_* env vars; unset ones keep their token so a
 * dry-run shows the shape.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const workerDir = join(scriptDir, "..");
const configDir = process.env.ORACLE_POSTURE_CONFIG || join(workerDir, "..", "config");
const configName = process.env.POSTURE_CONFIG || "live";

const KNOWN_POSTURES = new Set([
  "OFFLINE_TESTNET_ONLY",
  "FIRST_PARTY_DEMO",
  "LIVE_AUTHORISED",
]);

/** Fail-closed config load (mirrors pdp.config.load_config). Returns null on any fault. */
function loadConfig() {
  try {
    const raw = JSON.parse(
      readFileSync(join(configDir, `regulatory_posture.${configName}.json`), "utf-8"),
    );
    if (!KNOWN_POSTURES.has(raw.regulatory_posture)) return null;
    if (!raw.gates || typeof raw.gates !== "object") return null;
    for (const v of Object.values(raw.gates)) {
      if (v !== "open" && v !== "closed") return null;
    }
    return raw;
  } catch {
    return null;
  }
}

/** canEmit('published-rankings'): its only gate is G_S21. Default deny. */
function canEmitPublishedRankings(config) {
  return !!config && config.gates && config.gates.G_S21 === "open";
}

function renderNotice() {
  const tmpl = readFileSync(join(workerDir, "content", "pre-publication-notice.md"), "utf-8");
  const slots = {
    subject_rail: process.env.NOTICE_SUBJECT_RAIL || "{{subject_rail}}",
    publication_ref: process.env.NOTICE_PUBLICATION_REF || "{{publication_ref}}",
    finding_summary: process.env.NOTICE_FINDING_SUMMARY || "{{finding_summary}}",
    respond_by: process.env.NOTICE_RESPOND_BY || "{{respond_by}}",
    right_of_reply_url: process.env.NOTICE_ROR_URL || "{{right_of_reply_url}}",
  };
  // Strip the internal HTML comment block; it is authoring guidance, not notice text.
  let body = tmpl.replace(/<!--[\s\S]*?-->\n?/, "");
  for (const [k, v] of Object.entries(slots)) {
    body = body.replaceAll(`{{${k}}}`, v);
  }
  return body;
}

const config = loadConfig();
if (!canEmitPublishedRankings(config)) {
  const id = config ? config.config_id : "none";
  console.log(
    `G_S21 closed under config '${id}' - notice suppressed (armed, moot; nothing sent).`,
  );
  process.exit(0);
}

console.log(`G_S21 open under config '${config.config_id}' - rendering pre-publication notice:\n`);
process.stdout.write(renderNotice());
console.log(
  "\n[render-only: a human reviews and sends this; the script never emails.]",
);
process.exit(0);
