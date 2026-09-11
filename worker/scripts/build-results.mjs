#!/usr/bin/env node
/**
 * Generate a static result page that renders published (signed) replies ALONGSIDE
 * the result they answer, with the correct visibility badge. This is a build/ops
 * concern (like a static-site generator), so it is self-contained here.
 *
 * The reply-alongside always renders (the channel works regardless of gate state).
 * The NAMED-RAIL RESULTS TABLE section is gated on canEmit('published-rankings'): under a
 * closed G_S21 (the shipped default until the gate was opened) the table is omitted, fail-closed, and the page
 * says so; only when G_S21 is open is the table emitted.
 *
 * Usage: node build-results.mjs <published-dir> <result-meta.json> <out.html>
 * Config selection mirrors pdp/config.py (ORACLE_POSTURE_CONFIG / POSTURE_CONFIG).
 */

import { readFileSync, readdirSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const configDir =
  process.env.ORACLE_POSTURE_CONFIG || join(scriptDir, "..", "..", "config");
const configName = process.env.POSTURE_CONFIG || "live";

const [publishedDir, resultMetaPath, outPath] = process.argv.slice(2);
if (!publishedDir || !resultMetaPath || !outPath) {
  console.error("usage: build-results.mjs <published-dir> <result-meta.json> <out.html>");
  process.exit(1);
}

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
    for (const v of Object.values(raw.gates)) if (v !== "open" && v !== "closed") return null;
    return raw;
  } catch {
    return null;
  }
}
const config = loadConfig();
const tableAllowed = !!config && config.gates && config.gates.G_S21 === "open";

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const result = JSON.parse(readFileSync(resultMetaPath, "utf-8"));

// Only SIGNED, published records (not *.draft.json, not the result meta).
const replies = readdirSync(publishedDir)
  .filter((f) => f.endsWith(".json") && !f.endsWith(".draft.json"))
  .map((f) => JSON.parse(readFileSync(join(publishedDir, f), "utf-8")))
  .filter((r) => r.schema === "right-of-reply/reply/v1" && r.status === "published");

function badge(vis) {
  return vis === "immediate-pending-badge"
    ? '<span class="badge badge-pending">reply pending review</span>'
    : '<span class="badge badge-reviewed">reply reviewed</span>';
}

const replyHtml = replies
  .map(
    (r) => `<section class="reply">
  <h3>Rail reply (${esc(r.axis)}) ${badge(r.visibility)}</h3>
  <blockquote>${esc(r.public_reply)}</blockquote>
  <p class="attrib">Signed off by ${esc(r.signed_off_by)} on ${esc(r.signed_at)}.</p>
</section>`,
  )
  .join("\n");

const tableSection = tableAllowed
  ? `<section class="named-rail-table">
  <h2>Named-rail results</h2>
  <p>Named-rail measurements are published at <a href="https://oracle.agentic-paybench.dev/results/">oracle.agentic-paybench.dev/results/</a>. They are a measurement and not a recommendation, they carry no merit ordering, and no rail is endorsed.</p>
</section>`
  : `<section class="named-rail-table withheld">
  <h2>Named-rail results</h2>
  <p>Withheld: the named-rail results table is not published yet (G_S21 closed, fail-closed).</p>
</section>`;

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="robots" content="noindex" />
<title>${esc(result.title)}</title>
<link rel="stylesheet" href="/styles.css" />
</head>
<body>
<main>
<h1>${esc(result.title)}</h1>
<p class="result-finding">${esc(result.finding)}</p>
${tableSection}
<h2>Right-of-reply responses</h2>
${replies.length ? replyHtml : "<p>No published replies yet.</p>"}
<p><a href="/">Submit a right-of-reply</a></p>
</main>
</body>
</html>
`;

mkdirSync(dirname(outPath), { recursive: true });
writeFileSync(outPath, html);
console.log(
  `wrote ${outPath} (${replies.length} published repl${replies.length === 1 ? "y" : "ies"}; named-rail table ${tableAllowed ? "INCLUDED" : "OMITTED"}).`,
);
process.exit(0);
