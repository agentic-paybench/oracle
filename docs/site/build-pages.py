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


def render_cell_row(name: str, cell) -> str:
    if not isinstance(cell, dict) or not CELL_KEYS & set(cell):
        return f"<tr><td>{esc(name)}</td><td colspan=\"4\">{render_value(cell)}</td></tr>"
    extras = {k: v for k, v in cell.items() if k not in CELL_KEYS}
    value = render_value(cell.get("value"))
    if extras:
        value += "<ul>" + "".join(f"<li><strong>{esc(k)}:</strong> {render_value(v)}</li>" for k, v in extras.items()) + "</ul>"
    prov = cell.get("provenance", {}) or {}
    sources = prov.get("sources", []) or []
    src_html = "<ul>" + "".join(
        f'<li><a href="{esc(s.get("url", ""))}">{esc(s.get("url", ""))}</a> <small>(retrieved {esc(s.get("retrievedAt", ""))})</small></li>'
        for s in sources
    ) + "</ul>" if sources else ""
    label = esc(prov.get("label", ""))
    return (
        f"<tr><td>{esc(name)}</td><td>{value}</td><td>{esc(str(cell.get('disposition', '')))}</td>"
        f"<td>{esc(str(cell.get('statement', '')))}</td><td>{label}{src_html}</td></tr>"
    )


def capabilities_body(index: dict, subjects: list[dict]) -> str:
    notice = index.get("notice", {})
    parts = [
        '<h1 id="capability-records">Capability records: documented facts per rail</h1>',
        "<p>Thirteen documented structural facts for each of six payment rails, read from each rail's own primary documentation and served as signed credentials. This page renders them for readers; the signed records themselves are listed at the end for software.</p>",
        family.PLACEHOLDER_POSTURE,
    ]
    if notice.get("evenHandedStatement"):
        parts.append(f"<p>{esc(notice['evenHandedStatement'])}</p>")
    if notice.get("sourcesStatement"):
        parts.append(f"<p>{esc(notice['sourcesStatement'])}</p>")
    fee = notice.get("feeQuotation", {}) or {}
    for key, label, _ in QUESTIONS:
        parts.append(f'<h2 id="{family.slug(label)}">{esc(label)}</h2>')
        if key == "feeBearer" and fee:
            for k in ("quotationStatement", "sourceStatement", "evenHandedStatement"):
                if fee.get(k):
                    parts.append(f'<p class="meta">{esc(fee[k])}</p>')
        parts.append('<div class="table-scroll"><table><thead><tr><th>Rail</th><th>Value</th><th>Disposition</th><th>Statement</th><th>Provenance and sources</th></tr></thead><tbody>')
        for s in subjects:
            parts.append(render_cell_row(str(s.get("displayName", s.get("railName", ""))), dig(s, key)))
        parts.append("</tbody></table></div>")
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
         machine_intro: str | None = None) -> int:
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
        body = capabilities_body(index, subjects)
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
    if current_md:
        root_machine.insert(2, {"href": f"results/{current_md[-1].name}", "path": f"results/{current_md[-1].name}", "note": "the current named-rail measurement as Markdown"})
    frag = (HERE / "content" / "index.html").read_text(encoding="utf-8")
    rc |= page(site, "index.html", frag, title="agentic-paybench capability oracle", posture="measurement",
               machine=root_machine, marker=None, check=check,
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
