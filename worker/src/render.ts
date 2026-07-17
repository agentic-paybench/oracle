/**
 * Server-rendered form + policy pages, built from the canonical content JSON.
 * Pure functions (content + a gate decision in, HTML string out) so they unit-test
 * without a runtime. The Worker calls these so the armed-vs-idle banner reflects
 * the LIVE gate (canEmit); static CSS is served by the ASSETS binding.
 *
 * Composes only from canonical content; introduces no proper nouns of its own
 * (enforced by the naming-consistency gate + tests).
 */

import { formFields, policy, taxonomy, type FormField } from "./content.js";
import type { Decision } from "./posture.js";

/** Minimal HTML escape for text interpolated into the page. */
export function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const DOC_HEAD = (title: string) => `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="robots" content="noindex" />
<title>${esc(title)}</title>
<link rel="stylesheet" href="/styles.css" />
</head>
<body>
<main>`;

const DOC_FOOT = `</main>
</body>
</html>
`;

/**
 * The armed-vs-idle banner. Driven by canEmit('published-rankings'): while G_S21 is
 * closed the named-rail table is not published, so the channel is armed but has
 * nothing to reply to yet; submissions are still accepted and queued.
 */
export function bannerHtml(rankingsGate: Decision): string {
  if (rankingsGate.allowed) {
    return `<div class="banner banner-active" role="status">Named results are published. Use this channel to respond to a specific published result.</div>`;
  }
  return `<div class="banner banner-idle" role="status">No named results are published yet. Replies are accepted and queued; this channel is armed and will activate when a named result is published.</div>`;
}

function fieldHtml(f: FormField): string {
  const req = f.required ? " required" : "";
  const reqMark = f.required ? ` <span class="req" aria-hidden="true">*</span>` : "";
  const label = `<label for="f_${esc(f.id)}">${esc(f.label)}${reqMark}</label>`;

  if (f.type === "checkbox") {
    return `<div class="field field-check">
  <input type="checkbox" id="f_${esc(f.id)}" name="${esc(f.id)}"${req} />
  ${label}
</div>`;
  }
  if (f.type === "axis-select") {
    const opts = (f.options ?? [])
      .map((id) => {
        const ax = taxonomy.axes.find((a) => a.id === id);
        const name = ax ? `${ax.id} ${ax.name}` : id;
        return `<label class="axis-opt"><input type="radio" name="${esc(f.id)}" value="${esc(id)}"${req} /> ${esc(name)}</label>`;
      })
      .join("\n    ");
    return `<fieldset class="field field-axis">
  <legend>${esc(f.label)}${reqMark}</legend>
    ${opts}
</fieldset>`;
  }
  const attrs = f.maxLength ? ` maxlength="${f.maxLength}"` : "";
  const control =
    f.type === "textarea"
      ? `<textarea id="f_${esc(f.id)}" name="${esc(f.id)}"${req}${attrs} rows="4"></textarea>`
      : `<input type="text" id="f_${esc(f.id)}" name="${esc(f.id)}"${req}${attrs} />`;
  return `<div class="field">
  ${label}
  ${control}
</div>`;
}

export interface FormRenderOpts {
  rankingsGate: Decision;
  turnstileSitekey: string;
}

export function renderFormPage(opts: FormRenderOpts): string {
  const fields = formFields.fields.map(fieldHtml).join("\n");
  return `${DOC_HEAD(formFields.title)}
<h1>${esc(formFields.title)}</h1>
<p class="intro">${esc(formFields.intro)}</p>
${bannerHtml(opts.rankingsGate)}
<p><a href="/policy">Read the response cap and visibility policy</a> before submitting.</p>
<form method="post" action="/reply" accept-charset="utf-8">
${fields}
  <!-- Honeypot: a real submitter leaves this empty; bots fill it. Hidden from users. -->
  <div class="hp" aria-hidden="true">
    <label for="f_website">Leave this field blank</label>
    <input type="text" id="f_website" name="website" tabindex="-1" autocomplete="off" />
  </div>
  <div class="cf-turnstile" data-sitekey="${esc(opts.turnstileSitekey)}"></div>
  <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
  <button type="submit">Submit reply</button>
</form>
${DOC_FOOT}`;
}

export function renderPolicyPage(): string {
  const points = policy.points
    .map(
      (p) =>
        `<li><strong>${esc(p.title)}.</strong> ${esc(p.text)}</li>`,
    )
    .join("\n");
  const axes = taxonomy.axes
    .map(
      (a) =>
        `<tr><td>${esc(a.id)}</td><td>${esc(a.name)}</td><td>${esc(a.target_response)}</td><td>${a.visibility === "pre-moderated" ? "pre-moderated" : "immediate + badge"}</td></tr>`,
    )
    .join("\n");
  return `${DOC_HEAD(policy.title)}
<h1>${esc(policy.title)}</h1>
<p class="framing">${esc(policy.framing)}</p>
<h2>Response cap and visibility (10 points)</h2>
<ol class="policy">
${points}
</ol>
<h2>Axes and target response times</h2>
<table class="axes">
<thead><tr><th>Axis</th><th>Name</th><th>Target response</th><th>Visibility</th></tr></thead>
<tbody>
${axes}
</tbody>
</table>
<p><a href="/">Back to the reply form</a></p>
${DOC_FOOT}`;
}
