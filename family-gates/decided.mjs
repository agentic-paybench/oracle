// vendored from agentic-paybench/design-system-private@f2b1319 (packages/tokens, packages/family, packages/posture) by packages/family/vendor.mjs; do not edit here, re-vendor
// decided.mjs: read the decided-assets allowlist and match a URL against it.
// Shared by check.mjs (the browser gate) and lh-check.mjs (the Lighthouse
// post-check), so both judge "decided" identically.
//
// An entry matches a URL when the URL's origin equals the entry's origin
// EXACTLY and its path equals the entry's path_prefix or continues it at a
// path-segment boundary ("/beacon.min.js" matches "/beacon.min.js" and
// "/beacon.min.js/v4abc", never "/beacon.min.jsx" or "/other.js"). Query
// strings and fragments are ignored. Nothing else passes.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export const defaultDecidedPath = join(dirname(fileURLToPath(import.meta.url)), "decided-assets.json");

export function loadDecided(path = defaultDecidedPath) {
  const data = JSON.parse(readFileSync(path, "utf8"));
  const assets = Array.isArray(data.assets) ? data.assets : [];
  for (const a of assets) {
    if (!a.origin || !a.path_prefix || !a.kind || !a.decided || !a.register) {
      throw new Error(`decided-assets: an entry lacks origin, path_prefix, kind, decided or register: ${JSON.stringify(a)}`);
    }
    if (new URL(a.origin).origin !== a.origin) throw new Error(`decided-assets: origin is not a bare origin: ${a.origin}`);
    if (!a.path_prefix.startsWith("/")) throw new Error(`decided-assets: path_prefix must start with "/": ${a.path_prefix}`);
  }
  return assets;
}

export function matchDecided(url, assets, kind = null) {
  let u;
  try {
    u = new URL(url);
  } catch {
    return null;
  }
  for (const a of assets) {
    if (kind && a.kind !== kind) continue;
    if (u.origin !== a.origin) continue;
    const p = a.path_prefix.replace(/\/$/, "");
    if (u.pathname === p || u.pathname.startsWith(p + "/")) return a;
  }
  return null;
}

export const describe = (a) => `${a.origin}${a.path_prefix} (${a.kind}; decided ${a.decided}, Register ${a.register})`;
