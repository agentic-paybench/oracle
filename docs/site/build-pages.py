"""Render the oracle's reader pages from the ASSEMBLED deploy tree (DES-103).

Called by build-site.sh after the served artefacts are copied into docs/site
and after the G_S21 decision has been applied. It reads only that tree: a
results page is rendered only if the gate copied results/ there, so with the
gate closed nothing under results/ exists and nothing links to it. Standard
library only; the renderer is the vendored family/family.py.

Outputs (build outputs, gitignored): results/<name>.html beside each
assembled results .md, results/index.html, capabilities/index.html,
tier2/statements.html, roadmap.html, adr/index.html, methodology/index.html.
The root index.html and 404.html are TRACKED rendered files built from the
tracked fragments under docs/site-content/ (outside the deployed tree, so the
sources are never served); this script rewrites them, and the Python
suite runs it in --check mode so a drift between fragment and page fails.

    python3 docs/site/build-pages.py --site docs/site --labels docs/results-labels.tsv [--check]
"""
from __future__ import annotations

import argparse
import base64
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The page sources live beside the deployed tree, never inside it.
CONTENT = HERE.parent / "site-content"
sys.path.insert(0, str(HERE / "family"))
import family  # noqa: E402  (the vendored renderer)

esc = family._esc

# The thirteen documented questions, in the fixed order the notice refers to
# (ingest/build_capabilities.py and roadmap.md agree on it).
QUESTIONS = [
    ("feeBearer", "Who pays the network fee", None),
    ("finalityModelClass", "Finality model class", None),
    ("retryIdempotency", "Retry and idempotency", None),
    ("ambiguityBound", "Ambiguity bound", None),
    ("outcomeKnowledge", "Outcome knowledge", None),
    ("bundle.refundSupport", "Restitution kinds (refund support)", None),
    ("observerPrivacyExposure", "Observer privacy exposure", None),
    ("specificationPin", "Specification pin", None),
    ("declaredRateLimits", "Declared rate limits", None),
    ("statusPage", "Status page", None),
    ("sdkLanguages", "SDK languages", None),
    ("errorCatalogue", "Error catalogue", None),
    ("offlineVerifiability", "Offline verifiability", None),
]
PENDING_FIELDS = [
    ("custodyModel", "Custody model"),
    ("supportedAssets", "Supported assets"),
    ("fees.headlineFee", "Headline fee"),
    ("fees.model", "Fee model"),
    ("bundle.authorizationModel", "Authorization model"),
    ("bundle.disputeMechanism", "Dispute mechanism"),
    ("bundle.sanctionsScreening", "Sanctions screening"),
]
CELL_KEYS = {"value", "disposition", "statement", "provenance"}


def b64json(part: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))


def load_subjects(site: Path) -> list[dict]:
    index = json.loads((site / "capabilities" / "index.json").read_text(encoding="utf-8"))
    subjects = []
    for rail in index["rails"]:
        vc = json.loads((site / rail["vc"]).read_text(encoding="utf-8"))
        jwt = vc["id"].split(",", 1)[1]
        payload = b64json(jwt.split(".")[1])
        subj = payload["credentialSubject"]
        subj["_vc"] = rail["vc"]
        subjects.append(subj)
    subjects.sort(key=lambda s: str(s.get("displayName", "")).casefold())
    return index, subjects


def dig(subj: dict, dotted: str):
    cur = subj
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def render_value(v) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        if URL_VALUE.fullmatch(v):
            return f'<a href="{esc(v)}">{esc(v)}</a>'
        return esc(v)
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, (int, float)):
        return esc(str(v))
    if isinstance(v, list):
        return "<ul>" + "".join(f"<li>{render_value(x)}</li>" for x in v) + "</ul>"
    if isinstance(v, dict):
        return "<ul>" + "".join(f"<li><strong>{esc(k)}:</strong> {render_value(x)}</li>" for k, x in v.items()) + "</ul>"
    return esc(str(v))


SLUG_VALUE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
URL_VALUE = re.compile(r"https?://[^\s<>\"]+")

# D3: each question's lead line is the FIRST sentence of the schema's own
# served description (schema/capability.schema.json), moved verbatim, except
# Restitution kinds, whose first sentence describes the schema's own structure
# rather than the fact.
LEAD_OMIT = {"bundle.refundSupport"}
FIRST_SENTENCE = re.compile(r"(.+?[.!?])(?=\s+[A-Z(]|\s*$)", re.S)


def lead_lines(site: Path) -> dict:
    schema = json.loads((site / "schema" / "capability.schema.json").read_text(encoding="utf-8"))
    props = schema["properties"]["credentialSubject"]["properties"]
    out = {}
    for key, _, _ in QUESTIONS:
        if key in LEAD_OMIT:
            continue
        node = props
        for part in key.split("."):
            node = node[part]
            if part != key.split(".")[-1]:
                node = node["properties"]
        m = FIRST_SENTENCE.match(node.get("description", ""))
        if m:
            out[key] = m.group(1)
    return out


# Glossary terms, linked (dotted underline) on first use: per question block on
# the capabilities page, per page on the DIM-02 page.
CAP_TERMS = ["probabilistic finality", "deterministic finality", "finality", "idempotency", "ambiguity bound",
             "outcome knowledge", "restitution", "observer privacy exposure", "specification pin", "rate limit",
             "error catalogue", "offline verifiability", "documentation profile", "provenance label"]
DIM02_TERMS = ["authorization primitive", "payment validation", "challenge issuance", "local-complete",
               "network-dependent", "lognormal parameters", "confidence interval", "pre-registration"]


def link_terms(html_text: str, terms: list[str], used: set, prefix: str) -> str:
    """Wrap the first occurrence of each not-yet-used term in a glossary link.
    Only text outside tags and outside existing links is searched, and the
    text is re-split after every insertion, so a term is never matched inside a
    link already made (longer terms come first in the list)."""
    for term in terms:
        if term in used:
            continue
        pieces = re.split(r"(<a\b.*?</a>|<[^>]+>)", html_text, flags=re.S)
        for i, piece in enumerate(pieces):
            if not piece or piece.startswith("<"):
                continue
            m = re.search(r"(?<![\w-])(" + re.escape(term) + r")(?![\w-])", piece, re.I)
            if m:
                link = f'<a class="gloss" href="{prefix}glossary/#{family.slug(term)}">{m.group(1)}</a>'
                pieces[i] = piece[:m.start()] + link + piece[m.end():]
                used.add(term)
                html_text = "".join(pieces)
                break
    return html_text


def render_kv(d: dict) -> str:
    """One structured item as a compact key and value list (keys as served)."""
    return '<dl class="kv">' + "".join(
        f"<div><dt>{esc(k)}</dt><dd>{render_value(x)}</dd></div>" for k, x in d.items()) + "</dl>"


def render_record_value(v) -> tuple[str, str]:
    """Returns (css class, html). A short machine label (a slug or one lowercase
    word) is set as code so it reads as a defined term; a list of structured
    items becomes compact key and value blocks; anything else renders as text."""
    if isinstance(v, str) and SLUG_VALUE.fullmatch(v):
        return "value", f"<code>{esc(v)}</code>"
    if isinstance(v, list) and not v:
        return "value", "none listed"
    if isinstance(v, list) and all(isinstance(x, dict) for x in v):
        return "value structured", '<ul class="items">' + "".join(f"<li>{render_kv(x)}</li>" for x in v) + "</ul>"
    if isinstance(v, dict):
        return "value structured", render_kv(v)
    return "value", render_value(v)


def render_record(question_id: str, name: str, cell, question: str = "", reader_value: str | None = None) -> str:
    """One record card: the rail name, the value, the disposition and provenance
    as labelled tags, the statement, the sources behind a native details
    disclosure (closed by default; no script; the URLs stay in the page)."""
    rid = f"{question_id}-{family.slug(name)}"
    if not isinstance(cell, dict) or not CELL_KEYS & set(cell):
        cls, html_value = render_record_value(cell)
        return (f'<section class="record" id="{rid}"><h3>{esc(name)}</h3>'
                f'<div class="{cls}">{html_value}</div></section>')
    extras = {k: v for k, v in cell.items() if k not in CELL_KEYS}
    prov = cell.get("provenance", {}) or {}
    sources = prov.get("sources", []) or []
    cls, html_value = render_record_value(cell.get("value"))
    # A schema token (for example "mediated-then-trustless") is shown to readers
    # in the table's approved wording; the token stays in the signed record.
    if reader_value and isinstance(cell.get("value"), str) and SLUG_VALUE.fullmatch(cell["value"]):
        cls, html_value = "value", esc(reader_value)
    value = f'<div class="{cls}">{html_value}</div>'
    extras_html = ""
    if extras:
        extras_html = '<dl class="extras">' + "".join(
            f"<div><dt>{esc(k)}</dt><dd>{render_value(v)}</dd></div>" for k, v in extras.items()) + "</dl>"
    # D2 (2026-10-16): the disposition is not shown on the
    # reader card; it stays in the signed credential, where software needs it.
    tags = []
    if prov.get("label"):
        tags.append(f'<span class="tag"><span class="k">Provenance</span> {esc(str(prov["label"]))}</span>')
    tags_html = f'<p class="tags">{"".join(tags)}</p>' if tags else ""
    statement = f'<p class="statement">{esc(str(cell.get("statement", "")))}</p>' if cell.get("statement") else ""
    details = ""
    if sources:
        dates = sorted({str(s.get("retrievedAt", "")) for s in sources if s.get("retrievedAt")})
        when = f", retrieved {' and '.join(dates)}" if dates else ""
        items = "".join(f'<li><a href="{esc(s.get("url", ""))}">{esc(s.get("url", ""))}</a></li>' for s in sources)
        context = f'<span class="visually-hidden">: {esc(name)}, {esc(question)}</span>' if question else ""
        details = f"<details><summary>Sources ({len(sources)}){esc(when)}{context}</summary><ul>{items}</ul></details>"
    return f'<section class="record" id="{rid}"><h3>{esc(name)}</h3>{value}{extras_html}{tags_html}{statement}{details}</section>'


QUESTION_SET_SENTENCE = ("The same thirteen questions were put to all six rails, in the same fixed order, against each rail's "
                         "own primary documentation, between the dates of 2026-10-09 and 2026-10-10.")


def capabilities_body(index: dict, subjects: list[dict], leads: dict | None = None, short: dict | None = None) -> str:
    """Content brief section E (2026-10-18): the lead, the question-set sentence,
    ONE table (thirteen questions by six rails, short values linking to the full
    entries), the Posture block directly below the table, the thirteen question
    blocks each ending with a back link, then the machine panel. No posture box at the top, no
    by-rail block, no thirteen-questions list, no 'Facts not yet sourced'."""
    leads = leads or {}
    short = short or {}
    notice = index.get("notice", {})
    names = [str(s.get("displayName", s.get("railName", ""))) for s in subjects]
    parts = [
        '<h1 id="capability-records">Capability records: documented facts per rail</h1>',
        "<p>Thirteen documented structural facts for each of six payment rails, read from each rail's own primary documentation and served as signed credentials. This page renders them for readers, one card per rail under each question, rails in alphabetical order, with each card's sources folded beneath it; the signed records themselves are <a href=\"#machine-h\">listed at the end for software</a>.</p>",
        f'<p id="question-set">{esc(QUESTION_SET_SENTENCE)}</p>',
    ]
    # The table.
    order = short.get("rails", names)
    assert order == names, f"short-values rail order {order} does not match the credentials {names}"
    head = "".join(f'<th scope="col">{esc(n)}</th>' for n in names)
    rows = []
    for key, label, _ in QUESTIONS:
        qid = family.slug(label)
        vals = short.get("values", {}).get(key) or ["see entry"] * len(names)
        cells = "".join(
            f'<td><a href="#{qid}-{family.slug(n)}">{esc(v)}</a></td>' for n, v in zip(names, vals))
        rows.append(f'<tr><th scope="row"><a href="#{qid}">{esc(label)}</a></th>{cells}</tr>')
    cols = '<colgroup><col class="q">' + "<col>" * len(names) + "</colgroup>"
    parts.append(
        f'<div class="table-scroll cap-table-wrap" id="table"><table class="cap-table" aria-describedby="question-set">{cols}'
        f'<thead><tr><th scope="col"><span class="visually-hidden">Question</span></th>{head}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>')
    # The Posture block directly below the table it protects, before the
    # first question block: the required sentences once, the source-and-retrieval sentence inside the
    # box (moved there by posture_extra after rendering).
    sources_sentence = notice.get("sourcesStatement", "")
    parts.append('<section class="posture-foot" aria-labelledby="posture-h"><h2 id="posture-h">Posture</h2>')
    parts.append(family.PLACEHOLDER_POSTURE)
    parts.append("</section>")
    if sources_sentence:
        parts.append(f"<!-- posture-extra: {esc(sources_sentence)} -->")
    fee = notice.get("feeQuotation", {}) or {}
    for key, label, _ in QUESTIONS:
        reader_values = short.get("values", {}).get(key) or [None] * len(names)
        qid = family.slug(label)
        used: set = set()
        parts.append(f'<section class="question" aria-labelledby="{qid}">')
        parts.append(f'<h2 id="{qid}">{esc(label)}</h2>')
        if leads.get(key):
            parts.append(link_terms(f'<p class="lead">{esc(leads[key])}</p>', CAP_TERMS, used, "../"))
        if key == "feeBearer" and fee:
            notes = "".join(f'<p class="meta">{esc(fee[k])}</p>'
                            for k in ("quotationStatement", "sourceStatement", "evenHandedStatement") if fee.get(k))
            if notes:
                parts.append(f'<div class="notes notice">{notes}</div>')
        parts.append('<div class="cards">')
        for s, reader_value in zip(subjects, reader_values):
            rec = render_record(qid, str(s.get("displayName", s.get("railName", ""))), dig(s, key), label, reader_value)
            rec = re.sub(r'(<p class="statement">)(.*?)(</p>)',
                         lambda m: m.group(1) + link_terms(m.group(2), CAP_TERMS, used, "../") + m.group(3), rec, count=1, flags=re.S)
            parts.append(rec)
        parts.append('</div><p class="back"><a href="#table">Back to the table</a></p></section>')
    parts.append(family.PLACEHOLDER_MACHINE)
    return "\n".join(parts)


def machine_for_capabilities(index: dict, subjects: list[dict], prefix: str) -> list[dict]:
    paths = [
        {"href": f"{prefix}capabilities/index.json", "path": "capabilities/index.json", "note": "the index of the six signed credentials, with the notice"},
    ]
    for s in subjects:
        paths.append({"href": f"{prefix}{s['_vc']}", "path": s["_vc"], "note": f"{s.get('displayName', '')}: the signed credential (ES256 over P-256)"})
    paths += [
        {"href": f"{prefix}tier2/statements.md", "path": "tier2/statements.md", "note": "the statements every served cell carries"},
        {"href": f"{prefix}schema/capability.schema.json", "path": "schema/capability.schema.json", "note": "the JSON Schema every record conforms to"},
        {"href": f"{prefix}schema/capability.context.jsonld", "path": "schema/capability.context.jsonld", "note": "the vocabulary, a JSON-LD context"},
        {"href": f"{prefix}.well-known/did.json", "path": ".well-known/did.json", "note": "the signing key as a DID document"},
    ]
    return paths


def wrap_posture_run(body: str) -> str:
    """Wrap the three ruled sentences, where a frozen artefact carries them as
    consecutive paragraphs, in the family's posture block with the data-posture
    markers. The sentence text is untouched; only the wrapper is added."""
    import re as _re
    block = family.posture_block("measurement", HERE / "family" / "posture-snippet.html")
    sentences = _re.findall(r'<p data-posture="([a-z-]+)">(.*?)</p>', block)
    run = "\n".join(f"<p>{text}</p>" for _key, text in sentences)
    if run in body:
        body = body.replace(run, block, 1)
    return body


# The DIM-02 reader page. The Markdown record is NOT
# changed: it is the frozen, dated artefact. Only its reader rendering is
# rearranged: a one-line opening; the version and correction paragraphs moved
# to after "Corrections and right of reply", shortened only by removing whole
# sentences the page already carries; the ruled sentences and the
# "No ranking is stated..." sentence removed from the top and the ruled
# sentences placed once in the Posture foot block; the email as a mailto.
DIM02_READER = {"dim02-authorization-latency.v1.1.level1.md"}
DIM02_OPENING = "Version 1.1, dated 2026-10-01, for the measurement run of 2026-06-28."


def dim02_reader(body: str) -> str:
    paras = re.findall(r"<p>.*?</p>", body, re.S)
    version_p = next(p for p in paras if p.startswith("<p>Version 1.1, dated 2026-10-01"))
    correction_p = next(p for p in paras if p.startswith("<p>Correction of 2026-10-01."))
    no_rank_p = next(p for p in paras if p.startswith("<p>No ranking is stated on this page"))
    body = body.replace(version_p, f"<p>{esc(DIM02_OPENING)}</p>", 1)
    body = body.replace(correction_p, "", 1)
    body = body.replace(no_rank_p, "", 1)
    block = family.posture_block("measurement", HERE / "family" / "posture-snippet.html")
    sentences = re.findall(r'<p data-posture="[a-z-]+">(.*?)</p>', block)
    for s in sentences:
        body = body.replace(f"<p>{s}</p>", "", 1)
    # The moved paragraphs, shortened by removing whole repeated sentences only.
    # Kept whole: removing its first sentence would leave "It corrects ..."
    # with no subject, and rewording it would be new wording.
    version_moved = version_p
    repeated = (" The dated record shows that the method was refined during the pilot runs of 22 to 28 June 2026, "
                "which are the runs this page reports, and was frozen and externally anchored afterwards, on 29 and 30 June 2026.")
    assert repeated in correction_p, "the correction paragraph no longer carries the sentence the Provenance section repeats"
    correction_moved = correction_p.replace(repeated, "", 1)
    body = body.replace("mblake@everydayai.link", '<a href="mailto:mblake@everydayai.link">mblake@everydayai.link</a>', 1)
    # R6 named on the reader page only (2026-10-18); the dated record is unchanged.
    assert body.count("against which R6 was measured") == 1
    body = body.replace("against which R6 was measured", "against which R6 (Google Cloud with AP2) was measured", 1)
    # The DOIs and the reply address, as links (markup only; the text unchanged).
    body = re.sub(r"(?<![\w/\">])(10\.17605/OSF\.IO/[A-Z0-9]+)", r'<a href="https://doi.org/\1">\1</a>', body)
    body = body.replace("https://reply.agentic-paybench.dev/.", '<a href="https://reply.agentic-paybench.dev/">https://reply.agentic-paybench.dev/</a>.', 1)
    used: set = set()
    body = "\n".join(link_terms(chunk, DIM02_TERMS, used, "../") if chunk.startswith(("<p>", "<ul>", "<li>")) else chunk
                     for chunk in re.split(r"(?=<p>|<ul>|<h[1-3])", body))
    body += ("\n" + version_moved + "\n" + correction_moved)
    body += ('\n<section class="posture-foot" aria-labelledby="posture-h"><h2 id="posture-h">Posture</h2>\n'
             + block + "\n</section>\n" + family.PLACEHOLDER_MACHINE)
    return body


# The DIM-01 reader page, on the DIM-02 pattern. The Markdown record is NOT
# changed. Only its reader rendering is rearranged: a one-line opening; the
# version paragraph moved to the end; the ruled sentences and the "No ranking
# is stated..." sentence removed from the top and the ruled sentences placed
# once in the Posture foot block; the DOIs, the reply address and the email as
# links.
DIM01_READER = {"dim01-settlement-finality.level1.md"}
DIM01_OPENING = "Version 1.0, for the confirmatory run of 2026-10-27 to 2026-10-28."
DIM01_TERMS = ["pre-registration", "rate limit", "finality"]


def dim01_reader(body: str) -> str:
    paras = re.findall(r"<p>.*?</p>", body, re.S)
    version_p = next(p for p in paras if p.startswith("<p>" + DIM01_OPENING))
    no_rank_p = next(p for p in paras if p.startswith("<p>No ranking is stated on this page"))
    body = body.replace(version_p, f"<p>{esc(DIM01_OPENING)}</p>", 1)
    body = body.replace(no_rank_p, "", 1)
    block = family.posture_block("measurement", HERE / "family" / "posture-snippet.html")
    sentences = re.findall(r'<p data-posture="[a-z-]+">(.*?)</p>', block)
    for s in sentences:
        assert body.count(f"<p>{s}</p>") == 1, "a ruled sentence is missing from, or repeated on, the DIM-01 page"
        body = body.replace(f"<p>{s}</p>", "", 1)
    body = body.replace("mblake@everydayai.link", '<a href="mailto:mblake@everydayai.link">mblake@everydayai.link</a>', 1)
    body = re.sub(r"(?<![\w/\">])(10\.17605/OSF\.IO/[A-Z0-9]+)", r'<a href="https://doi.org/\1">\1</a>', body)
    body = body.replace("https://reply.agentic-paybench.dev/.", '<a href="https://reply.agentic-paybench.dev/">https://reply.agentic-paybench.dev/</a>.', 1)
    body = re.sub(r"(?<![\"\w])(https://github\.com/agentic-paybench/payhelm/blob/[^\s<),]+)",
                  r'<a href="\1">\1</a>', body)
    used: set = set()
    body = "\n".join(link_terms(chunk, DIM01_TERMS, used, "../") if chunk.startswith(("<p>", "<ul>", "<li>")) else chunk
                     for chunk in re.split(r"(?=<p>|<ul>|<h[1-3])", body))
    # A 64-character hash is one unbreakable word that widens the page on a
    # phone; soft break points let it wrap and copy as the same 64 characters.
    body = re.sub(r"\b([0-9a-f]{64})\b", lambda m: "<wbr>".join(m.group(1)[i:i + 16] for i in range(0, 64, 16)), body)
    # A table box that scrolls sideways must be reachable by keyboard (axe
    # scrollable-region-focusable); each is a labelled region named after the
    # heading above it.
    parts = re.split(r'(<div class="table-scroll">)', body)
    heading = "Table"
    for i, part in enumerate(parts):
        if part == '<div class="table-scroll">':
            parts[i] = f'<div class="table-scroll" tabindex="0" role="region" aria-label="{esc(heading)}">'
        else:
            found = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", part, re.S)
            if found:
                heading = re.sub(r"<[^>]+>", "", found[-1])
    body = "".join(parts)
    body += "\n" + version_p
    body += ('\n<section class="posture-foot" aria-labelledby="posture-h"><h2 id="posture-h">Posture</h2>\n'
             + block + "\n</section>\n" + family.PLACEHOLDER_MACHINE)
    return body


def read_labels(labels: Path | None) -> dict[str, str]:
    if not labels or not labels.exists():
        return {}
    out = {}
    with labels.open(encoding="utf-8", newline="") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) >= 2:
                out[row[0]] = row[1]
    return out


def listing_body(title: str, intro: str, items: list[tuple[str, str, str]]) -> str:
    lis = "".join(
        f'<li><a href="{esc(href)}">{esc(text)}</a>' + (f' <span class="label">{esc(label)}</span>' if label else "") + "</li>"
        for href, text, label in items
    )
    return f'<h1 id="{family.slug(title)}">{esc(title)}</h1>\n<p>{esc(intro)}</p>\n<ul class="dir">{lis}</ul>\n{family.PLACEHOLDER_MACHINE}'


def posture_extra(html: str) -> str:
    """Move a '<!-- posture-extra: S -->' sentence inside the posture box that
    the renderer inserted, as its last paragraph, so every sentence of the foot
    block sits in one box (as on the DIM-02 page)."""
    m = re.search(r"<!-- posture-extra: (.*?) -->", html)
    if not m:
        return html
    html = html.replace(m.group(0), "", 1)
    i = html.index('<section class="posture-foot"')
    j = html.index("</div>", html.index('<div class="posture"', i))
    return html[:j] + f"<p>{m.group(1)}</p>\n" + html[j:]


def page(site: Path, rel_out: str, body: str, *, title: str, posture: str, machine: list[dict] | None,
         marker: str | None, description: str | None = None, check: bool, root_relative: bool = False,
         machine_intro: str | None = None, layout: str = "measure", at_root: bool = False) -> int:
    depth = rel_out.count("/")
    prefix = "/family/" if root_relative else ("../" * depth) + "family/"
    html = family.render_page(
        body,
        title=title,
        description=description or family.first_paragraph_text(body),
        surface="oracle",
        posture=posture,
        family_prefix=prefix,
        snippet_path=HERE / "family" / "posture-snippet.html",
        machine=machine,
        machine_intro=machine_intro,
        marker=marker,
        layout=layout,
        at_root=at_root,
    )
    html = posture_extra(html)
    return family.write_or_check(site / rel_out, html, check)


def build(site: Path, labels_path: Path | None, check: bool, assembled: bool = True) -> int:
    rc = 0
    labels = read_labels(labels_path)

    # Results: only what the gate assembled.
    results = site / "results"
    results_md = sorted(results.glob("*.md")) if results.is_dir() else []
    # A superseded version (its label says so in docs/results-labels.tsv) stays a
    # Markdown-only record: it is kept unaltered, and the gate exempts its
    # superseded sentence by its repository path, not by an assembled one.
    current_md = [md for md in results_md if "superseded" not in labels.get(md.name, "").casefold()]
    titles: dict[str, str] = {}
    for md in current_md:
        marker, body, title = family.md_to_html(md.read_text(encoding="utf-8"))
        titles[md.name] = title or md.stem
        if md.name in DIM02_READER:
            body = dim02_reader(body)
        elif md.name in DIM01_READER:
            body = dim01_reader(body)
        else:
            body = wrap_posture_run(body)
            body += "\n" + family.PLACEHOLDER_MACHINE
        machine = [
            {"href": md.name, "path": f"results/{md.name}", "note": "this page as the served Markdown artefact, the record the scanner and the right of reply refer to"},
            {"href": "../index.json", "path": "index.json", "note": "the machine index of every served surface"},
        ]
        rc |= page(site, f"results/{md.with_suffix('.html').name}", body, title=title or md.stem, posture="none",
                   machine=machine, marker=marker, check=check)
    if results_md:
        # De-declared (2026-10-18): the index names no rail and
        # reports no finding, so it carries no gate marker, no posture sentences
        # and no OSF line; one reader line per measurement.
        reader_lines = {
            "dim01-settlement-finality.level1.md":
                "Settlement finality (DIM-01) on test networks, five rails. Version 1.0, for the confirmatory run of 2026-10-27 to 2026-10-28.",
            "dim02-authorization-latency.v1.1.level1.md":
                "Authorization-primitive latency (DIM-02), six rails. Version 1.1 (2026-10-01) is current; version 1.0 is kept unaltered as the record.",
        }
        lis = []
        for md in current_md:
            line = reader_lines.get(md.name)
            if line:
                first, rest = line.split(". ", 1)
                lis.append(f'<li><a href="{esc(md.with_suffix(".html").name)}">{esc(first)}</a>. {esc(rest)}</li>')
            else:
                lis.append(f'<li><a href="{esc(md.with_suffix(".html").name)}">{esc(titles.get(md.name, md.name))}</a></li>')
        body = ('<h1 id="named-rail-measurements">Named-rail measurements</h1>\n'
                '<p>Each measurement is a dated, frozen artefact: a correction or a re-measurement is published as a new dated version and the earlier one is kept, as Markdown, below. Pages are rendered for readers; every Markdown record is listed for software.</p>\n'
                f'<ul class="dir">{"".join(lis)}</ul>\n' + family.PLACEHOLDER_MACHINE)
        machine = [{"href": md.name, "path": f"results/{md.name}", "note": labels.get(md.name, "")} for md in results_md]
        rc |= page(site, "results/index.html", body, title="Named-rail measurements", posture="none",
                   machine=machine, marker=None, check=check)

    # Capabilities reader page.
    if assembled or (site / "capabilities" / "index.json").exists():
        index, subjects = load_subjects(site)
        short_path = CONTENT / "short-values.json"
        short = json.loads(short_path.read_text(encoding="utf-8")) if short_path.exists() else {}
        body = capabilities_body(index, subjects, lead_lines(site), short)
        rc |= page(site, "capabilities/index.html", body, title="Capability records: documented facts per rail",
                   posture="documentation", machine=machine_for_capabilities(index, subjects, "../"),
                   marker="level1-documentation-profile", check=check,
                   machine_intro="The same facts as signed data, verifiable offline against the published key.")

    # Statements and roadmap as reader pages beside their Markdown.
    for rel in ("tier2/statements.md", "roadmap.md"):
        src = site / rel
        if src.exists():
            marker, body, title = family.md_to_html(src.read_text(encoding="utf-8"))
            body += "\n" + family.PLACEHOLDER_MACHINE
            depth = rel.count("/")
            machine = [{"href": src.name, "path": rel, "note": "this page as the served Markdown artefact"},
                       {"href": ("../" * depth) + "index.json", "path": "index.json", "note": "the machine index of every served surface"}]
            rc |= page(site, rel[:-3] + ".html", body, title=title or src.stem, posture="none", machine=machine,
                       marker=marker, check=check)

    # Decision records and the methodology: an explainer
    # or the ruled sentences above the list, the Markdown rendered for readers
    # beside the unchanged originals, every file listed once, for software.
    rc |= decision_records(site, check)
    rc |= methodology_pages(site, check)
    rc |= glossary_page(site, check)

    # The root page and the 404 page, from tracked fragments.
    root_machine = [
        {"href": "index.json", "path": "index.json", "note": "the machine index of every served surface"},
        {"href": "capabilities/index.json", "path": "capabilities/index.json", "note": "the six signed capability credentials, one per rail"},
        {"href": "schema/capability.schema.json", "path": "schema/capability.schema.json", "note": "the JSON Schema every record conforms to"},
        {"href": "schema/capability.context.jsonld", "path": "schema/capability.context.jsonld", "note": "the vocabulary, a JSON-LD context"},
        {"href": ".well-known/did.json", "path": ".well-known/did.json", "note": "the signing key as a DID document"},
        {"href": "posture.json", "path": "posture.json", "note": "which surfaces are live and which are switched off"},
        {"href": "tier2/statements.md", "path": "tier2/statements.md", "note": "the statements every served cell carries"},
        {"href": "roadmap.md", "path": "roadmap.md", "note": "declared directions, none of them measured"},
    ]
    # The root page is a TRACKED rendered file, so it must not depend on
    # whether the gate assembled results/: the reader list links results/ as
    # the page always has, and index.json carries the gated pointer.
    frag = (CONTENT / "index.html").read_text(encoding="utf-8")
    rc |= page(site, "index.html", frag, title="agentic-paybench capability oracle", posture="none",
               machine=root_machine, marker=None, check=check, at_root=True,
               description="Published facts and measurements about the payment rails that software agents use, signed so they can be validated.")
    frag404 = (CONTENT / "404.html").read_text(encoding="utf-8")
    rc |= page(site, "404.html", frag404, title="Not found: agentic-paybench oracle", posture="none", machine=None,
               marker=None, check=check, root_relative=True, description="No such artefact on this surface.")
    return rc


RENDERING_BANNER = "Rendering of a frozen file; the original at {path} is the record and matches the anchored manifest."


def render_md_file(src: Path) -> tuple[str, str]:
    """A Markdown file as reader HTML through the family renderer; a construct
    the strict subset cannot render falls back to the text in a pre block, so
    nothing is ever dropped or altered."""
    text = src.read_text(encoding="utf-8")
    try:
        _marker, body, title = family.md_to_html(text)
        return body, title or src.stem
    except Exception:  # noqa: BLE001
        return f"<pre>{esc(text)}</pre>", src.stem


def decision_records(site: Path, check: bool) -> int:
    d = site / "adr"
    if not d.is_dir():
        return 0
    rc = 0
    mds = sorted(p for p in d.glob("*.md"))
    items = []
    for md in mds:
        body, title = render_md_file(md)
        body += "\n" + family.PLACEHOLDER_MACHINE
        machine = [{"href": md.name, "path": f"adr/{md.name}", "note": "the decision record as Markdown"}]
        rc |= page(site, f"adr/{md.with_suffix('.html').name}", body, title=title, posture="none", machine=machine, marker=None, check=check)
        items.append(f'<li><a href="{esc(md.with_suffix(".html").name)}">{esc(title)}</a></li>')
    body = ('<h1 id="decision-records">Decision records</h1>\n'
            '<p class="lead">A scored query, an answer that would score rails for a particular payment, exists in the code and is switched off on this site.</p>\n'
            '<p>Why the oracle is intent-free (ADR-007) and how its gates work (ADR-009).</p>\n'
            '<p>Which surfaces are live and which are switched off is published as data at <a href="../posture.json"><code>posture.json</code></a>, which shows the gates.</p>\n'
            f'<ul class="dir">{"".join(items)}</ul>\n' + family.PLACEHOLDER_MACHINE)
    machine = [{"href": md.name, "path": f"adr/{md.name}", "note": "the decision record as Markdown"} for md in mds]
    rc |= page(site, "adr/index.html", body, title="Decision records", posture="none", machine=machine, marker=None, check=check)
    return rc


METHODOLOGY_EXPLAINER = (
    "Settlement-finality methodology, version 1.2. The method, its analysis plan, the harness and the calibrated fixtures were "
    "frozen as one artefact set on 2026-06-06 and anchored in three independent places: an OpenTimestamps proof in Bitcoin block "
    "952636, a Rekor transparency-log entry (1740328355) and a public registration on the Open Science Framework "
    "(10.17605/OSF.IO/XGFUJ). The files below are byte-identical to that set; the manifest lists their hashes. Read first: the "
    "methodology text. Then the calibration plan. The fixtures and provenance files are the inputs; the harness code is what ran. "
    "No results table is published on this page; the test-network measurement of settlement finality is listed under results/.")


def methodology_pages(site: Path, check: bool) -> int:
    d = site / "methodology"
    if not d.is_dir():
        return 0
    rc = 0
    read_first = [("methodology/methodology.md", "The methodology text"), ("calibration/calibration-plan.md", "The calibration plan")]
    links = []
    for rel, label in read_first:
        src = d / rel
        if not src.exists():
            continue
        body, title = render_md_file(src)
        banner = f'<p class="rendering">{esc(RENDERING_BANNER.format(path="methodology/" + rel))}</p>\n'
        depth = ("methodology/" + rel).count("/")
        machine = [{"href": src.name, "path": f"methodology/{rel}", "note": "the frozen original"},
                   {"href": "../prereg-manifest.sha256", "path": "methodology/prereg-manifest.sha256", "note": "the anchored manifest of hashes"}]
        rc |= page(site, f"methodology/{rel[:-3]}.html", banner + body + "\n" + family.PLACEHOLDER_MACHINE, title=title,
                   posture="none", machine=machine, marker=None, check=check)
        links.append(f'<li><a href="{esc(rel[:-3] + ".html")}">{esc(label)}</a></li>')
    files = sorted(p for p in d.rglob("*") if p.is_file() and p.suffix != ".html")
    body = ('<h1 id="settlement-finality-methodology-frozen-v1-2">Settlement-finality methodology (frozen v1.2)</h1>\n'
            f'<p class="lead">{esc(METHODOLOGY_EXPLAINER.split(". ", 1)[0])}.</p>\n'
            '<p>' + esc(METHODOLOGY_EXPLAINER.split(". ", 1)[1]).replace("10.17605/OSF.IO/XGFUJ", '<a href="https://doi.org/10.17605/OSF.IO/XGFUJ">10.17605/OSF.IO/XGFUJ</a>') + '</p>\n'
            f'<ul class="dir">{"".join(links)}</ul>\n' + family.PLACEHOLDER_MACHINE)
    machine = [{"href": str(p.relative_to(d)), "path": f"methodology/{p.relative_to(d)}", "note": ""} for p in files]
    rc |= page(site, "methodology/index.html", body, title="Settlement-finality methodology (frozen v1.2)", posture="none",
               machine=machine, marker=None, check=check)
    return rc


def glossary_page(site: Path, check: bool) -> int:
    src = CONTENT / "glossary.json"
    if not src.exists():
        return 0
    entries = sorted(json.loads(src.read_text(encoding="utf-8"))["entries"], key=lambda e: e["term"].casefold())
    letters = []
    for e in entries:
        ch = e["term"][0].upper()
        if ch not in [l for l, _ in letters]:
            letters.append((ch, family.slug(e["term"])))
    az = "".join(f'<li><a href="#{slug}">{esc(ch)}</a></li>' for ch, slug in letters)
    dl = "".join(f'<dt id="{family.slug(e["term"])}">{esc(e["term"])}</dt><dd>{esc(e["text"])}</dd>' for e in entries)
    body = ('<h1 id="glossary">Glossary</h1>\n'
            f'<ul class="az" aria-label="Terms by first letter">{az}</ul>\n'
            f'<dl class="glossary">{dl}</dl>\n' + family.PLACEHOLDER_MACHINE)
    machine = [{"href": "../index.json", "path": "index.json", "note": "the machine index of every served surface"}]
    return page(site, "glossary/index.html", body, title="Glossary", posture="none", machine=machine, marker=None, check=check,
                description="Plain-word definitions of the terms used on the oracle's capability and measurement pages.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=str(HERE))
    ap.add_argument("--labels", default=str(HERE.parent / "results-labels.tsv"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    return build(Path(a.site).resolve(), Path(a.labels) if a.labels else None, a.check)


if __name__ == "__main__":
    sys.exit(main())
