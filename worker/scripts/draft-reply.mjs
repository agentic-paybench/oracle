#!/usr/bin/env node
/**
 * L3 draft step (draft-only; never publishes).
 *
 * Reads a pending submission record (as written by the capture endpoint into R2
 * pending/), selects the axis response template, fills its placeholders, and
 * writes a DRAFT reply record with `signed_off_by: null`. It does NOT create the
 * published record; a human must sign it (sign-reply.mjs). This is the L3
 * "draft-only, human-sign" boundary of the Path C-tight ladder.
 *
 * Usage: node draft-reply.mjs <pending-record.json> <out-dir> [--result MR-000]
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const workerDir = join(scriptDir, "..");

const [pendingPath, outDir] = process.argv.slice(2);
const resultFlag = process.argv.indexOf("--result");
const resultId = resultFlag > -1 ? process.argv[resultFlag + 1] : "MR-000";

if (!pendingPath || !outDir) {
  console.error("usage: draft-reply.mjs <pending-record.json> <out-dir> [--result <id>]");
  process.exit(1);
}

const pending = JSON.parse(readFileSync(pendingPath, "utf-8"));
const sub = pending.submission;
const axis = pending.axis;
const replyId = pending.id;

// Fill the axis response template.
const tmpl = readFileSync(join(workerDir, "content", "templates", `${axis}.md`), "utf-8");
const filled = tmpl
  .replaceAll("{{rail_name}}", sub.rail_name)
  .replaceAll("{{challenged_passage}}", sub.challenged_passage)
  .replaceAll("{{received}}", pending.received)
  .replaceAll("{{public_reply}}", sub.public_reply);

const draft = {
  schema: "right-of-reply/reply/v1",
  status: "draft",
  reply_id: replyId,
  result_id: resultId,
  axis,
  visibility: pending.visibility,
  rail_name: sub.rail_name,
  public_reply: sub.public_reply,
  received: pending.received,
  signed_off_by: null,
  signed_at: null,
};

mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, `${replyId}.draft.json`), JSON.stringify(draft, null, 2));
writeFileSync(join(outDir, `${replyId}.draft.md`), filled);

console.log(`DRAFT written (unsigned; not published): ${join(outDir, replyId + ".draft.json")}`);
console.log("Sign with: node scripts/sign-reply.mjs <draft.json> --by \"<reviewer>\"");
process.exit(0);
