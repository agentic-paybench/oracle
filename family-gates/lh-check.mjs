// vendored from agentic-paybench/design-system-private@f2b1319 (packages/tokens, packages/family, packages/posture) by packages/family/vendor.mjs; do not edit here, re-vendor
// lh-check.mjs: the Lighthouse third-party and script budgets of the public
// page family, measured against the decided-assets allowlist.
//
// Lighthouse's own resource-summary budgets can only say "at most N", which
// would pass any undecided asset in place of a decided one; so lighthouserc.json
// keeps the score and size budgets, and this post-check reads every report
// lhci wrote (.lighthouseci/lhr-*.json) and FAILS on any network request whose
// origin is not the page's own, and on any script resource, unless it matches a
// decided entry (decided-assets.json beside this script, or --decided <file>).
// Every decided asset it saw is REPORTED. Run it straight after `lhci autorun`.
//
//   node lh-check.mjs [--dir .lighthouseci] [--decided decided-assets.json]

import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { loadDecided, matchDecided, describe, defaultDecidedPath } from "./decided.mjs";

const args = process.argv.slice(2);
const opt = (name, dflt) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : dflt;
};
const dir = opt("--dir", ".lighthouseci");
const decidedPath = opt("--decided", defaultDecidedPath);
const decided = loadDecided(decidedPath);

const reports = readdirSync(dir).filter((f) => /^lhr-.*\.json$/.test(f));
if (!reports.length) {
  console.log(`lh-check: no Lighthouse report in ${dir}`);
  process.exit(1);
}
let failures = 0;
const seen = new Map();
for (const f of reports.sort()) {
  const lhr = JSON.parse(readFileSync(join(dir, f), "utf8"));
  const page = lhr.finalDisplayedUrl || lhr.finalUrl || lhr.requestedUrl;
  const origin = new URL(page).origin;
  const items = lhr.audits?.["network-requests"]?.details?.items || [];
  const bad = [];
  for (const it of items) {
    if (!it.url || it.url.startsWith("data:")) continue;
    const thirdParty = new URL(it.url).origin !== origin;
    const script = it.resourceType === "Script";
    if (!thirdParty && !script) continue;
    const a = matchDecided(it.url, decided, script ? "script" : null);
    if (a) {
      const k = describe(a);
      seen.set(k, (seen.get(k) || 0) + 1);
    } else {
      bad.push(`${script ? "script" : "third-party"} ${it.url}`);
    }
  }
  if (bad.length) {
    failures += bad.length;
    console.log(`FAIL ${page} (${f}): ${bad.length} resource(s) not on the decided list`);
    for (const b of bad.slice(0, 5)) console.log(`      ${b}`);
  } else {
    console.log(`OK   ${page} (${f}): ${items.length} requests, no third-party or script resource beyond the decided list`);
  }
}
console.log(`decided-assets list: ${decidedPath} (${decided.length} entr${decided.length === 1 ? "y" : "ies"})`);
if (seen.size) for (const [k, n] of seen) console.log(`  decided asset SEEN and allowed: ${k}, ${n} request(s)`);
else console.log("  no decided asset seen in these reports");
console.log(failures ? `lh-check: ${failures} failure(s)` : "lh-check: all reports within the decided list");
process.exit(failures ? 1 : 0);
