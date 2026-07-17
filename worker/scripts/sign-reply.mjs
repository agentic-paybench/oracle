#!/usr/bin/env node
/**
 * L3 human-sign step: promote a DRAFT reply to a published record.
 *
 * A human reviews the draft, then runs this to set `signed_off_by` and write the
 * published record (`<reply-id>.json` + `.md`) alongside the draft. Only signed
 * records are picked up by build-results.mjs; nothing publishes without this step.
 *
 * Usage: node sign-reply.mjs <draft.json> --by "<reviewer name>"
 * (SIGN_AT env pins the signature timestamp for reproducible runs.)
 */

import { readFileSync, writeFileSync, renameSync, existsSync } from "node:fs";
import { dirname, join, basename } from "node:path";

const args = process.argv.slice(2);
const draftPath = args[0];
const byFlag = args.indexOf("--by");
const by = byFlag > -1 ? args[byFlag + 1] : "";

if (!draftPath || !by) {
  console.error('usage: sign-reply.mjs <draft.json> --by "<reviewer name>"');
  process.exit(1);
}

const draft = JSON.parse(readFileSync(draftPath, "utf-8"));
if (draft.status !== "draft" || draft.signed_off_by !== null) {
  console.error("refusing to sign: not an unsigned draft.");
  process.exit(1);
}

const signedAt = process.env.SIGN_AT || new Date().toISOString();
const published = {
  ...draft,
  status: "published",
  signed_off_by: by,
  signed_at: signedAt,
};

const dir = dirname(draftPath);
const replyId = draft.reply_id;
writeFileSync(join(dir, `${replyId}.json`), JSON.stringify(published, null, 2));

// Promote the draft markdown to the published markdown, if present.
const draftMd = join(dir, `${replyId}.draft.md`);
if (existsSync(draftMd)) renameSync(draftMd, join(dir, `${replyId}.md`));

console.log(`PUBLISHED: ${join(dir, replyId + ".json")} (signed off by ${by} at ${signedAt})`);
console.log(`draft record retained: ${basename(draftPath)}`);
process.exit(0);
