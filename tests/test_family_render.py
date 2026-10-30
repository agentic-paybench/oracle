"""The reader pages (DES-103): rendered from the assembled tree by the vendored
family layout, with the properties the public posture depends on.

The renderer runs into a temporary copy of docs/site so the working tree stays
clean; the G_S21 gate is exercised both ways by assembling results/ or not.
"""

import base64
import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SITE = REPO / "docs" / "site"
RESULTS_SRC = REPO / "docs" / "results"
LABELS = REPO / "docs" / "results-labels.tsv"
SNIPPET = SITE / "family" / "posture-snippet.html"

MEASUREMENT = [
    "These figures are a measurement, not a recommendation: no rail is endorsed, no ordering implies a best buy, and no rail is being suggested for use.",
    "Rails are listed alphabetically by rail name. That ordering is fixed and carries no performance meaning.",
    "The same measurement protocol was applied identically to every rail.",
]
DOCUMENTATION = "This is a documentation profile, not a recommendation: every cell states what a specification or an operator's own documentation says, no number in this document was produced by executing a payment, no rail is endorsed, no ordering implies a best buy, and no rail is being suggested for use."


def _assemble(tmp: Path, with_results: bool) -> Path:
    site = tmp / "site"
    shutil.copytree(SITE, site, ignore=shutil.ignore_patterns("schema", "adr", "methodology", "results"))
    shutil.copytree(REPO / "schema", site / "schema")
    shutil.copytree(REPO / "docs" / "adr", site / "adr")
    shutil.copytree(REPO / "docs" / "methodology" / "frozen", site / "methodology")
    if with_results:
        shutil.copytree(RESULTS_SRC, site / "results")
    rc = subprocess.run(
        [sys.executable, "-I", str(SITE / "build-pages.py"), "--site", str(site), "--labels", str(LABELS)],
        capture_output=True, text=True,
    )
    assert rc.returncode == 0, rc.stderr
    return site


@pytest.fixture(scope="module")
def site_with_results(tmp_path_factory):
    return _assemble(tmp_path_factory.mktemp("with"), with_results=True)


@pytest.fixture(scope="module")
def site_without_results(tmp_path_factory):
    return _assemble(tmp_path_factory.mktemp("without"), with_results=False)


def _generated_pages(site: Path):
    return sorted(p for p in site.rglob("*.html") if "family" not in p.parts)


def test_results_pages_carry_the_marker_before_the_doctype(site_with_results):
    """Each findings page is declared; the results index is not (it names no
    rail and reports no finding; 2026-10-18)."""
    pages = sorted((site_with_results / "results").glob("*.html"))
    assert any(p.name != "index.html" for p in pages)
    for p in pages:
        text = p.read_text(encoding="utf-8")
        if p.name == "index.html":
            assert not text.startswith("<!-- posture-class"), p
            for s in MEASUREMENT:
                assert s not in text, s
            assert "OSF.IO" not in text
        else:
            assert text.startswith("<!-- posture-class: level1-measurement -->\n<!doctype html>"), p


def test_capabilities_page_marker_and_documentation_set(site_with_results):
    text = (site_with_results / "capabilities" / "index.html").read_text(encoding="utf-8")
    assert text.startswith("<!-- posture-class: level1-documentation-profile -->\n<!doctype html>")
    assert DOCUMENTATION in text
    for s in MEASUREMENT[:1] + MEASUREMENT[2:]:
        assert s not in text, "the measurement set must not appear on the documentation page"


def test_capabilities_page_lists_rails_alphabetically_with_every_question(site_with_results):
    index = json.loads((SITE / "capabilities" / "index.json").read_text(encoding="utf-8"))
    names = []
    for rail in index["rails"]:
        vc = json.loads((SITE / rail["vc"]).read_text(encoding="utf-8"))
        part = vc["id"].split(",", 1)[1].split(".")[1]
        subj = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))["credentialSubject"]
        names.append(subj["displayName"])
    text = (site_with_results / "capabilities" / "index.html").read_text(encoding="utf-8")
    questions = text.split('<section class="question"')[1:]
    assert len(questions) == 13
    for q in questions:
        positions = [q.index("<h3>" + n + "</h3>") for n in names]
        ordered = [n for _, n in sorted(zip(positions, names))]
        assert ordered == sorted(names, key=str.casefold)
    assert text.count('<section class="record"') == 13 * len(names)
    # The standard page width, so the family bar sits where it sits on every
    # page; only the table breaks out (2026-10-18).
    assert 'class="family-page"' in text and "family-page--wide" not in text
    # Indigo by the family-scope attribute, on the wrapper and the themed
    # island, never on <html> (2026-10-18).
    assert '<div class="family-page" data-accent="indigo">' in text
    assert '<section class="machine" data-theme="dark" data-accent="indigo"' in text
    assert "<html" in text and "data-accent" not in text.split("<html", 1)[1].split(">", 1)[0]
    # The Posture block directly below the table, before the first question
    # block, and only once (2026-10-18).
    assert text.count('<section class="posture-foot"') == 1
    assert text.index("</table>") < text.index('<section class="posture-foot"') < text.index('<section class="question"')
    # The cards show readers the table's wording, never a schema token; the
    # fee notice is one compact box (2026-10-18).
    assert '<div class="value"><code>' not in text
    assert text.count('<div class="value">mediated, then trustless</div>') == 4
    assert text.count('<div class="notes notice">') == 1
    # The SDK languages lead line: the schema's own first sentence.
    sdk = text.split('<h2 id="sdk-languages">', 1)[1].split('<div class="cards">', 1)[0]
    assert "Languages for which the protocol authors or the operator document an official SDK or reference implementation." in re.sub(r"<[^>]+>", "", sdk)
    assert "<details><summary>Sources (" in text and " open>" not in text
    # The table: thirteen rows by six rails, alphabetical,
    # every cell a link to that rail's entry; the old navigation is gone.
    table = text.split('<table class="cap-table"', 1)[1].split("</table>", 1)[0]
    head = re.findall(r'<th scope="col">([^<]+)</th>', table)
    assert head == sorted(names, key=str.casefold)
    assert table.count('<th scope="row">') == 13
    assert len(re.findall(r'<td><a href="#[^"]+">[^<]+</a></td>', table)) == 13 * len(names)
    assert '<nav class="toc"' not in text and 'class="by-rail"' not in text and "Facts not yet sourced" not in text
    assert text.count('<a href="#table">Back to the table</a>') == 13
    # The ruled sentences once, in the Posture foot block, above the machine panel.
    foot = text.index('<section class="posture-foot"')
    assert text.count(DOCUMENTATION) == 1 and text.index(DOCUMENTATION) > foot
    assert foot < text.index('id="machine-h"')
    assert "The same thirteen questions were put to all six rails, in the same fixed order" in text
    for heading in ("Who pays the network fee", "Finality model class", "Retry and idempotency", "Ambiguity bound",
                    "Outcome knowledge", "Restitution kinds (refund support)", "Observer privacy exposure",
                    "Specification pin", "Declared rate limits", "Status page", "SDK languages",
                    "Error catalogue", "Offline verifiability"):
        assert f">{heading}</h2>" in text, heading


def test_dim02_reader_names_r6_and_the_record_is_unchanged(site_with_results):
    """2026-10-18: the reader page names the rail behind R6; the dated record keeps its words."""
    page = (site_with_results / "results" / "dim02-authorization-latency.v1.1.level1.html").read_text(encoding="utf-8")
    record = (site_with_results / "results" / "dim02-authorization-latency.v1.1.level1.md").read_text(encoding="utf-8")
    assert "against which R6 (Google Cloud with AP2) was measured" in page
    assert "against which R6 was measured" in record and "(Google Cloud with AP2) was measured" not in record


def test_root_page_carries_no_posture_repeat_and_links_the_glossary(site_with_results):
    """2026-10-18: the root no longer repeats the required sentences;
    they stay on the two pages that present named-rail findings."""
    text = (site_with_results / "index.html").read_text(encoding="utf-8")
    for s in MEASUREMENT:
        assert s not in text, s
    assert 'href="glossary/"' in text and "The three tiers" in text


def test_dim02_reader_page_rearranged_and_record_unchanged(site_with_results):
    """Content brief G: the reader page opens with one line, carries the ruled
    sentences once in the foot block, moves the version and correction text to
    the end; the Markdown record itself is served unchanged."""
    html = (site_with_results / "results" / "dim02-authorization-latency.v1.1.level1.html").read_text(encoding="utf-8")
    md = (site_with_results / "results" / "dim02-authorization-latency.v1.1.level1.md").read_text(encoding="utf-8")
    assert md == (RESULTS_SRC / "dim02-authorization-latency.v1.1.level1.md").read_text(encoding="utf-8")
    main = html.split("<main>", 1)[1]
    assert main.split("</h1>", 1)[1].lstrip().startswith("<p>Version 1.1, dated 2026-10-01, for the measurement run of 2026-06-28.</p>")
    for s in MEASUREMENT:
        assert html.count(s) == 1, s
        assert html.index(s) > html.index('<section class="posture-foot"')
    # The fourth ruled sentence is shown once, in the same foot block.
    assert html.count("No ranking is stated on this page") == 1
    assert html.index("No ranking is stated on this page") > html.index('<section class="posture-foot"')
    assert html.index("Correction of 2026-10-01.") > html.index('id="corrections-and-right-of-reply"')
    assert 'href="mailto:mblake@everydayai.link"' in html


def test_dim01_reader_page_posture_once_and_tables_reachable(site_with_results):
    """The DIM-01 reader page: one-line opening; the three ruled sentences and
    the "No ranking is stated..." sentence once each, in the foot block; every
    sideways-scrolling table box keyboard-reachable; the record served unchanged."""
    html = (site_with_results / "results" / "dim01-settlement-finality.level1.html").read_text(encoding="utf-8")
    md = (site_with_results / "results" / "dim01-settlement-finality.level1.md").read_text(encoding="utf-8")
    assert md == (RESULTS_SRC / "dim01-settlement-finality.level1.md").read_text(encoding="utf-8")
    main = html.split("<main>", 1)[1]
    assert main.split("</h1>", 1)[1].lstrip().startswith("<p>Version 1.0, for the confirmatory run of 2026-10-27 to 2026-10-28.</p>")
    foot = html.index('<section class="posture-foot"')
    for s in MEASUREMENT + ["No ranking is stated on this page, no winner is named, and there is no route from this page to transact on any rail."]:
        assert html.count(s) == 1, s
        assert html.index(s) > foot, s
    assert html.count('<div class="table-scroll">') == 0
    assert html.count('<div class="table-scroll" tabindex="0" role="region" aria-label="') == md.count("\n|---")


class _Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.loads = []
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "link" and a.get("href"):
            self.loads.append(a["href"])
        if tag == "script" and a.get("src"):
            self.loads.append(a["src"])
        if tag == "script":
            self.loads.append("<inline script>")
        if tag in ("a", "img") and (a.get("href") or a.get("src")):
            self.hrefs.append(a.get("href") or a.get("src"))


def test_no_third_party_load_and_no_script_in_any_generated_page(site_with_results):
    for p in _generated_pages(site_with_results):
        parser = _Refs()
        parser.feed(p.read_text(encoding="utf-8"))
        for ref in parser.loads:
            assert ref != "<inline script>", f"{p}: a script tag"
            assert not re.match(r"^(https?:)?//", ref), f"{p}: off-origin load {ref}"
    for css in (SITE / "family").glob("*.css"):
        assert "url(http" not in css.read_text(encoding="utf-8")


def test_every_relative_reference_resolves(site_with_results):
    for p in _generated_pages(site_with_results):
        parser = _Refs()
        parser.feed(p.read_text(encoding="utf-8"))
        for ref in parser.loads + parser.hrefs:
            if ref == "<inline script>" or re.match(r"^(https?:|mailto:|data:|#)", ref):
                continue
            if ref.startswith("/"):
                assert p.name == "404.html", f"{p}: root-relative {ref} outside the 404 page"
                target = site_with_results / ref.lstrip("/")
            else:
                target = (p.parent / ref.split("#")[0]).resolve()
            if ref.endswith("/"):
                target = target / "index.html"
            assert target.exists(), f"{p}: {ref} does not resolve"


def test_gate_closed_renders_no_results_page_and_no_results_link(site_without_results):
    assert not (site_without_results / "results").exists()
    text = (site_without_results / "index.html").read_text(encoding="utf-8")
    assert "results/dim02" not in text


def test_tracked_root_and_404_pages_match_a_fresh_render():
    rc = subprocess.run(
        [sys.executable, "-I", str(SITE / "build-pages.py"), "--site", str(SITE), "--labels", str(LABELS), "--check"],
        capture_output=True, text=True,
    )
    # On a fresh clone the gitignored pages do not exist, so --check reports
    # them too; this test judges only the two TRACKED pages, by exact path.
    tracked = {str(SITE / "index.html"), str(SITE / "404.html")}
    drifted = [line for line in rc.stderr.splitlines()
               if line.endswith(" differs from a fresh render")
               and line.split("family: ", 1)[-1].rsplit(" differs", 1)[0] in tracked]
    assert not drifted, "\n".join(drifted)


QUESTION_KEYS = ["feeBearer", "finalityModelClass", "retryIdempotency", "ambiguityBound", "outcomeKnowledge",
                 "bundle.refundSupport", "observerPrivacyExposure", "specificationPin", "declaredRateLimits",
                 "statusPage", "sdkLanguages", "errorCatalogue", "offlineVerifiability"]


def _subjects():
    index = json.loads((SITE / "capabilities" / "index.json").read_text(encoding="utf-8"))
    out = []
    for rail in index["rails"]:
        vc = json.loads((SITE / rail["vc"]).read_text(encoding="utf-8"))
        part = vc["id"].split(",", 1)[1].split(".")[1]
        out.append(json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))["credentialSubject"])
    return out


def _dig(d, dotted):
    for k in dotted.split("."):
        d = d[k]
    return d


def test_disposition_off_the_reader_cards_and_kept_in_every_credential(site_with_results):
    """D2 (2026-10-16): the reader page shows no disposition; the
    signed credentials keep one on every one of the thirteen cells per rail."""
    text = (site_with_results / "capabilities" / "index.html").read_text(encoding="utf-8")
    assert "Disposition" not in text
    for word in ("confirmed-absence", "partial-absence"):
        assert word not in text, word
    for subj in _subjects():
        for key in QUESTION_KEYS:
            assert _dig(subj, key).get("disposition") in {"positive", "partial-absence", "confirmed-absence", "void"}, (subj["displayName"], key)


def test_lead_lines_are_the_schemas_first_sentences_with_one_omitted(site_with_results):
    """D3: twelve lead lines, each the first sentence of the served schema
    description, verbatim; none for Restitution kinds."""
    text = (site_with_results / "capabilities" / "index.html").read_text(encoding="utf-8")
    # The fixture's assembled copy (built from the tracked schema/), never
    # docs/site/schema/, which is gitignored and absent on a fresh clone.
    schema = json.loads((site_with_results / "schema" / "capability.schema.json").read_text(encoding="utf-8"))
    props = schema["properties"]["credentialSubject"]["properties"]
    leads = [re.sub(r"<[^>]+>", "", x) for x in re.findall(r'<p class="lead">(.*?)</p>', text)]
    assert len(leads) == 12
    for line in leads:
        assert any(line.replace("&#x27;", "'") in (props[k].get("description", "") if k in props else "")
                   for k in props), line
    sections = text.split('<section class="question"')[1:]
    assert '<p class="lead">' not in sections[5]  # Restitution kinds (zero-based in the fixed order)
    assert '<p class="lead">' in sections[10]  # SDK languages


def test_family_bar_marks_the_page_only_on_the_root(site_with_results):
    root = (site_with_results / "index.html").read_text(encoding="utf-8")
    assert 'href="https://oracle.agentic-paybench.dev/" aria-current="page"' in root
    for rel in ("capabilities/index.html", "404.html", "roadmap.html"):
        page = (site_with_results / rel).read_text(encoding="utf-8")
        assert 'aria-current="page"' not in page, rel
        assert 'href="https://oracle.agentic-paybench.dev/" aria-current="true"' in page, rel


def test_every_in_page_link_on_the_capabilities_page_resolves(site_with_results):
    text = (site_with_results / "capabilities" / "index.html").read_text(encoding="utf-8")
    ids = set(re.findall(r'id="([^"]+)"', text))
    anchors = re.findall(r'href="#([^"]+)"', text)
    assert len(anchors) >= 13 * 6 + 13 + 13
    for a in anchors:
        assert a in ids, a
    for g in set(re.findall(r'href="\.\./glossary/#([^"]+)"', text)):
        assert f'id="{g}"' in (site_with_results / "glossary" / "index.html").read_text(encoding="utf-8"), g
