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
tracked fragments under content/; this script rewrites them, and the Python
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
# served description (schema/capability.schema.json), moved verbatim. Two are
# omitted by the founder's ruling of 2026-10-16 (Register Operating 80 item
# 14): Restitution kinds (its first sentence is schema-internal) and SDK
# languages.
LEAD_OMIT = {"bundle.refundSupport", "sdkLanguages"}
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


def render_record(question_id: str, name: str, cell, question: str = "") -> str:
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
    value = f'<div class="{cls}">{html_value}</div>'
    extras_html = ""
    if extras:
        extras_html = '<dl class="extras">' + "".join(
            f"<div><dt>{esc(k)}</dt><dd>{render_value(v)}</dd></div>" for k, v in extras.items()) + "</dl>"
    # D2 (founder ruling 2026-10-16): the disposition is not shown on the
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


def capabilities_body(index: dict, subjects: list[dict], leads: dict | None = None) -> str:
    leads = leads or {}
    notice = index.get("notice", {})
    parts = [
        '<div class="lede"><div class="intro">',
        '<h1 id="capability-records">Capability records: documented facts per rail</h1>',
        "<p>Thirteen documented structural facts for each of six payment rails, read from each rail's own primary documentation and served as signed credentials. This page renders them for readers, one card per rail under each question, rails in alphabetical order, with each card's sources folded beneath it; the signed records themselves are <a href=\"#machine-h\">listed at the end for software</a>.</p>",
        family.PLACEHOLDER_POSTURE,
    ]
    if notice.get("evenHandedStatement"):
        parts.append(f"<p>{esc(notice['evenHandedStatement'])}</p>")
    if notice.get("sourcesStatement"):
        parts.append(f"<p>{esc(notice['sourcesStatement'])}</p>")
    fee = notice.get("feeQuotation", {}) or {}
    toc = "".join(f'<li><a href="#{family.slug(label)}">{esc(label)}</a></li>' for _, label, _ in QUESTIONS)
    parts.append("</div>")
    extra = ('<ul class="extra"><li><a href="#pending-facts">Facts not yet sourced</a></li>'
             '<li><a href="#machine-h">For agents and software</a></li></ul>')
    parts.append(f'<nav class="toc" aria-labelledby="questions"><h2 id="questions">The thirteen questions</h2><ol>{toc}</ol>{extra}</nav>')
    parts.append("</div>")
    rows = []
    for s in subjects:
        name = str(s.get("displayName", s.get("railName", "")))
        links = "".join(
            f'<a href="#{family.slug(label)}-{family.slug(name)}" title="{esc(label)}">{n}<span class="visually-hidden">, {esc(name)}: {esc(label)}</span></a>'
            for n, (_, label, _) in enumerate(QUESTIONS, 1))
        rows.append(f"<div><dt>{esc(name)}</dt><dd>{links}</dd></div>")
    parts.append(f'<nav class="by-rail" aria-labelledby="by-rail"><h2 id="by-rail">By rail</h2><dl>{"".join(rows)}</dl></nav>')
    for key, label, _ in QUESTIONS:
        qid = family.slug(label)
        parts.append(f'<section class="question" aria-labelledby="{qid}">')
        parts.append(f'<h2 id="{qid}">{esc(label)}</h2>')
        if leads.get(key):
            parts.append(f'<p class="lead">{esc(leads[key])}</p>')
        if key == "feeBearer" and fee:
            notes = "".join(f'<p class="meta">{esc(fee[k])}</p>'
                            for k in ("quotationStatement", "sourceStatement", "evenHandedStatement") if fee.get(k))
            if notes:
                parts.append(f'<div class="notes">{notes}</div>')
        parts.append('<div class="cards">')
        for s in subjects:
            parts.append(render_record(qid, str(s.get("displayName", s.get("railName", ""))), dig(s, key), label))
        parts.append("</div></section>")
    parts.append('<h2 id="pending-facts">Facts not yet sourced</h2>')
    parts.append('<p class="meta">These fields are served as "pending" in every credential: roadmap, no measurement, never invented.</p>')
    parts.append('<div class="table-scroll"><table><thead><tr><th>Field</th><th>Status across the six rails</th></tr></thead><tbody>')
    for key, label in PENDING_FIELDS:
        vals = {json.dumps(dig(s, key), sort_keys=True) for s in subjects}
        status = "pending for every rail" if vals == {'"pending"'} else "; ".join(sorted(esc(v) for v in vals))
        parts.append(f"<tr><td>{esc(label)}</td><td>{status}</td></tr>")
    parts.append("</tbody></table></div>")
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
        body = wrap_posture_run(body)
        body += "\n" + family.PLACEHOLDER_MACHINE
        machine = [
            {"href": md.name, "path": f"results/{md.name}", "note": "this page as the served Markdown artefact, the record the scanner and the right of reply refer to"},
            {"href": "../index.json", "path": "index.json", "note": "the machine index of every served surface"},
        ]
        rc |= page(site, f"results/{md.with_suffix('.html').name}", body, title=title or md.stem, posture="none",
                   machine=machine, marker=marker, check=check)
    if results_md:
        items = [(md.with_suffix(".html").name, titles.get(md.name, md.name), labels.get(md.name, "")) for md in current_md]
        body = listing_body("Named-rail measurements", "Each measurement is a dated, frozen artefact: a correction or a re-measurement is published as a new dated version and the earlier one is kept, as Markdown, below. Pages are rendered for readers; every Markdown record is listed for software.", items)
        # The listing sits under results/, which the gate classifies as a
        # measurement artefact by path, so it carries the measurement set and
        # the pre-registration pointers the profile requires, and the marker.
        body = body.replace(
            family.PLACEHOLDER_MACHINE,
            '<p class="meta">The measurement methods are published and pre-registered on the Open Science Framework: '
            '<a href="https://doi.org/10.17605/OSF.IO/UFQG5">10.17605/OSF.IO/UFQG5</a> (authorization latency), '
            '<a href="https://doi.org/10.17605/OSF.IO/XGFUJ">10.17605/OSF.IO/XGFUJ</a> (settlement finality, method) and '
            '<a href="https://doi.org/10.17605/OSF.IO/UETFW">10.17605/OSF.IO/UETFW</a> (settlement finality, test-network confirmatory data).</p>\n'
            + family.PLACEHOLDER_MACHINE, 1)
        machine = [{"href": md.name, "path": f"results/{md.name}", "note": labels.get(md.name, "")} for md in results_md]
        rc |= page(site, "results/index.html", body, title="Named-rail measurements", posture="measurement",
                   machine=machine, marker="level1-measurement", check=check)

    # Capabilities reader page.
    if assembled or (site / "capabilities" / "index.json").exists():
        index, subjects = load_subjects(site)
        body = capabilities_body(index, subjects, lead_lines(site))
        rc |= page(site, "capabilities/index.html", body, title="Capability records: documented facts per rail",
                   posture="documentation", machine=machine_for_capabilities(index, subjects, "../"),
                   marker="level1-documentation-profile", check=check,
                   machine_intro="The same facts as signed data, verifiable offline against the published key.",
                   layout="wide")

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

    # Directory indexes for the copied trees.
    for rel, title, intro in (
        ("adr", "Decision records", "Why the oracle is intent-free (ADR-007) and how its gates work (ADR-009)."),
        ("methodology", "Settlement-finality methodology (frozen v1.2)", "The frozen method, harness and calibrated fixtures, byte-verifiable against the anchored manifest. The method only; no results table."),
    ):
        d = site / rel
        if d.is_dir():
            files = sorted(p for p in d.rglob("*") if p.is_file() and p.name != "index.html")
            items = [(str(p.relative_to(d)), str(p.relative_to(d)), "") for p in files]
            body = listing_body(title, intro, items)
            machine = [{"href": str(p.relative_to(d)), "path": f"{rel}/{p.relative_to(d)}", "note": ""} for p in files[:40]]
            rc |= page(site, f"{rel}/index.html", body, title=title, posture="none", machine=machine, marker=None, check=check)

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
    frag = (HERE / "content" / "index.html").read_text(encoding="utf-8")
    rc |= page(site, "index.html", frag, title="agentic-paybench capability oracle", posture="measurement",
               machine=root_machine, marker=None, check=check, at_root=True,
               description="Published facts and measurements about the payment rails that software agents use, signed so they can be checked, with nothing on this site that tells you which rail to use.")
    frag404 = (HERE / "content" / "404.html").read_text(encoding="utf-8")
    rc |= page(site, "404.html", frag404, title="Not found: agentic-paybench oracle", posture="none", machine=None,
               marker=None, check=check, root_relative=True, description="No such artefact on this surface.")
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=str(HERE))
    ap.add_argument("--labels", default=str(HERE.parent / "results-labels.tsv"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    return build(Path(a.site).resolve(), Path(a.labels) if a.labels else None, a.check)


if __name__ == "__main__":
    sys.exit(main())
