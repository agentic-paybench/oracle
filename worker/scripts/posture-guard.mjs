#!/usr/bin/env node
/**
 * Publish/site-build guard for the named-rail results table.
 *
 * Reads the shared PDP config and applies canEmit('published-rankings')
 * (its only gate is G_S21). Prints the decision and exits 0. A site build (or
 * build-results.mjs) consults this to decide whether to EMIT the named-rail
 * league table. Fail-closed: a missing/unknown config, or G_S21 not "open",
 * yields OMIT.
 *
 * Config selection mirrors pdp/config.py: ORACLE_POSTURE_CONFIG overrides the
 * config dir; POSTURE_CONFIG selects the named config (default "live").
 *
 * Exit code is always 0 (it reports, it does not fail the build); the decision is
 * on stdout as the first token: INCLUDE or OMIT.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const configDir =
  process.env.ORACLE_POSTURE_CONFIG || join(scriptDir, "..", "..", "config");
const configName = process.env.POSTURE_CONFIG || "live";

const KNOWN_POSTURES = new Set([
  "OFFLINE_TESTNET_ONLY",
  "FIRST_PARTY_DEMO",
  "LIVE_AUTHORISED",
]);

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

const config = loadConfig();
const allowed = !!config && config.gates && config.gates.G_S21 === "open";
const id = config ? config.config_id : "none";

if (allowed) {
  console.log(`INCLUDE named-rail results table (G_S21 open under '${id}').`);
} else {
  console.log(`OMIT named-rail results table (G_S21 closed under '${id}'; fail-closed).`);
}
process.exit(0);
