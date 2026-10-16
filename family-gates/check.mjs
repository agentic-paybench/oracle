// vendored from agentic-paybench/design-system-private@f2b1319 (packages/tokens, packages/family, packages/posture) by packages/family/vendor.mjs; do not edit here, re-vendor
// check.mjs: the network-log, layout and axe-core gates of the public page
// family (DES-100, founder-approved 2026-10-16). One script, the same in every
// page repository, vendored from design-system-private packages/family/gates.
//
//   node check.mjs --base http://127.0.0.1:8080 --paths / /capabilities/ ... [--out report.json] [--decided decided-assets.json]
//
// The allowlist rule (founder ruling 2026-10-16, Register Operating 80 item 8):
// a third-party asset is permitted only by a founder decision taken before it
// is incorporated; the gate passes exactly the decided entries. Run it against
// the repository's files AND against the live URL: a host can inject at the
// edge what the repository never ships.
//
// For each path, at 1280 and 390 wide, light and dark: every request the page
// makes is recorded and the gate FAILS on any request whose origin is not the
// page's own, unless it matches an entry of the decided-assets allowlist
// (decided-assets.json beside this script, or --decided <file>); it FAILS on
// any script unless its src matches a decided entry of kind "script" (an
// inline script never passes); scripts are counted three ways, from the
// served HTML, from the DOM after load and from every script the browser
// fetched, because a script can remove its own element once it has run
// (Cloudflare's email-decode script does); every decided asset it saw is
// REPORTED, so a reader can tell "allowed" from "absent"; it FAILS when the document is
// wider than the viewport at 390 (the no-sideways-scroll rule); it records the
// font families that loaded. At 1280 light, axe-core runs with the WCAG 2.0 A,
// AA and 2.1 AA tags and the gate FAILS on any violation of any impact. A path
// ending in "?" is optional: a 404 skips it (a gated surface may be absent).
// Exit 1 on any failure; the report names every one.

import { chromium } from "playwright";
import { AxeBuilder } from "@axe-core/playwright";
import { writeFileSync } from "node:fs";
import { loadDecided, matchDecided, describe, defaultDecidedPath } from "./decided.mjs";

const args = process.argv.slice(2);
const opt = (name, dflt) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : dflt;
};
const base = opt("--base", "http://127.0.0.1:8080").replace(/\/$/, "");
const out = opt("--out", "");
const pathsIdx = args.indexOf("--paths");
const paths = [];
if (pathsIdx >= 0) {
  for (const p of args.slice(pathsIdx + 1)) {
    if (p.startsWith("--")) break;
    paths.push(p);
  }
}
if (!paths.length) paths.push("/");
const origin = new URL(base).origin;
const decidedPath = opt("--decided", defaultDecidedPath);
const decided = loadDecided(decidedPath);
const seenDecided = new Map();
const sawDecided = (entry, a) => {
  const key = describe(a);
  entry.decidedSeen = entry.decidedSeen || [];
  if (!entry.decidedSeen.includes(key)) entry.decidedSeen.push(key);
  seenDecided.set(key, (seenDecided.get(key) || 0) + 1);
};

const browser = await chromium.launch();
const report = [];
let failures = 0;
const fail = (entry, why) => {
  entry.failures.push(why);
  failures += 1;
};

for (const raw of paths) {
  const optional = raw.endsWith("?");
  const path = optional ? raw.slice(0, -1) : raw;
  const url = base + path;
  for (const width of [1280, 390]) {
    for (const scheme of ["light", "dark"]) {
      const ctx = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: scheme });
      const page = await ctx.newPage();
      const requests = [];
      const scriptRequests = [];
      page.on("request", (r) => {
        requests.push(r.url());
        if (r.resourceType() === "script") scriptRequests.push(r.url());
      });
      const entry = { path, width, scheme, failures: [] };
      const resp = await page.goto(url, { waitUntil: "load" });
      if (!resp || resp.status() >= 400) {
        if (optional && resp && resp.status() === 404) {
          entry.skipped = "optional path absent";
          report.push(entry);
          await ctx.close();
          continue;
        }
        fail(entry, `HTTP ${resp ? resp.status() : "no response"}`);
        report.push(entry);
        await ctx.close();
        continue;
      }
      const served = await resp.text();
      const htmlScripts = [...served.matchAll(/<script\b([^>]*)>/gi)].map((mm) => {
        const s = /\bsrc\s*=\s*["']?([^"' >]+)/i.exec(mm[1]);
        return s ? new URL(s[1], url).href : "";
      });
      await page.evaluate(() => document.fonts.ready);
      const m = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        scripts: [...document.querySelectorAll("script")].map((s) => s.src || ""),
        fonts: [...new Set([...document.fonts].filter((f) => f.status === "loaded").map((f) => f.family))],
      }));
      Object.assign(entry, m);
      const offOrigin = requests.filter((r) => new URL(r).origin !== origin);
      const undecided = [];
      for (const r of offOrigin) {
        const a = matchDecided(r, decided);
        if (a) sawDecided(entry, a);
        else undecided.push(r);
      }
      entry.requests = requests.length;
      entry.offOrigin = undecided;
      if (undecided.length) fail(entry, `off-origin request(s) not on the decided list: ${undecided.slice(0, 3).join(", ")}`);
      const domSrcs = m.scripts.filter(Boolean);
      const inline = Math.max(m.scripts.filter((s) => !s).length, htmlScripts.filter((s) => !s).length);
      const srcs = [...new Set([...domSrcs, ...htmlScripts.filter(Boolean), ...scriptRequests])];
      const badScripts = [];
      for (const src of srcs) {
        const a = matchDecided(src, decided, "script");
        if (a) sawDecided(entry, a);
        else badScripts.push(src);
      }
      for (let i = 0; i < inline; i++) badScripts.push("(inline)");
      entry.scriptsAll = { served: htmlScripts.map((s) => s || "(inline)"), dom: m.scripts.map((s) => s || "(inline)"), fetched: scriptRequests };
      entry.scripts = badScripts.length;
      if (badScripts.length) fail(entry, `${badScripts.length} script(s) not on the decided list: ${badScripts.slice(0, 3).join(", ")}`);
      if (m.scrollWidth > m.clientWidth) fail(entry, `document ${m.scrollWidth}px wide in a ${m.clientWidth}px viewport`);
      if (width === 1280 && scheme === "light") {
        const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
        entry.axeViolations = axe.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length, help: v.help }));
        entry.axePasses = axe.passes.length;
        if (axe.violations.length) fail(entry, `axe: ${axe.violations.map((v) => `${v.id} (${v.impact}, ${v.nodes.length})`).join("; ")}`);
      }
      report.push(entry);
      await ctx.close();
    }
  }
}
await browser.close();

for (const e of report) {
  const tag = e.skipped ? "SKIP" : e.failures.length ? "FAIL" : "OK  ";
  const detail = e.skipped ? e.skipped : `scroll=${e.scrollWidth}/${e.clientWidth} requests=${e.requests} offOrigin=${(e.offOrigin || []).length} scripts=${e.scripts} decided=${(e.decidedSeen || []).length} fonts=${(e.fonts || []).join("|")}` + (e.axeViolations ? ` axe=${e.axeViolations.length} violation(s), ${e.axePasses} rules passed` : "");
  console.log(`${tag} ${String(e.width).padStart(4)} ${e.scheme.padEnd(5)} ${e.path}  ${detail}`);
  for (const f of e.failures) console.log(`      ${f}`);
}
console.log(`decided-assets list: ${decidedPath} (${decided.length} entr${decided.length === 1 ? "y" : "ies"})`);
if (seenDecided.size) for (const [k, n] of seenDecided) console.log(`  decided asset SEEN and allowed: ${k}, in ${n} view(s)`);
else console.log("  no decided asset seen on these pages");
if (out) writeFileSync(out, JSON.stringify({ decidedList: decidedPath, decided, seenDecided: Object.fromEntries(seenDecided), views: report }, null, 2));
console.log(failures ? `family-gates: ${failures} failure(s)` : "family-gates: all checks passed");
process.exit(failures ? 1 : 0);
