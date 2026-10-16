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
    return sorted(p for p in site.rglob("*.html") if "family" not in p.parts and "content" not in p.parts)


def test_results_pages_carry_the_marker_before_the_doctype(site_with_results):
    pages = sorted((site_with_results / "results").glob("*.html"))
    assert any(p.name != "index.html" for p in pages)
    for p in pages:
        text = p.read_text(encoding="utf-8")
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
    assert '<nav class="toc"' in text and 'class="family-page family-page--wide"' in text
    assert "<details><summary>Sources (" in text and " open>" not in text
    for heading in ("Who pays the network fee", "Finality model class", "Retry and idempotency", "Ambiguity bound",
                    "Outcome knowledge", "Restitution kinds (refund support)", "Observer privacy exposure",
                    "Specification pin", "Declared rate limits", "Status page", "SDK languages",
                    "Error catalogue", "Offline verifiability"):
        assert f">{heading}</h2>" in text, heading


def test_root_page_carries_the_measurement_set_once(site_with_results):
    text = (site_with_results / "index.html").read_text(encoding="utf-8")
    for s in MEASUREMENT:
        assert text.count(s) == 1, s
    assert 'data-posture-set="measurement"' in text


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
    """D2 (founder ruling 2026-10-16): the reader page shows no disposition; the
    signed credentials keep one on every one of the thirteen cells per rail."""
    text = (site_with_results / "capabilities" / "index.html").read_text(encoding="utf-8")
    assert "Disposition" not in text
    for word in ("confirmed-absence", "partial-absence"):
        assert word not in text, word
    for subj in _subjects():
        for key in QUESTION_KEYS:
            assert _dig(subj, key).get("disposition") in {"positive", "partial-absence", "confirmed-absence", "void"}, (subj["displayName"], key)


def test_lead_lines_are_the_schemas_first_sentences_with_two_omitted(site_with_results):
    """D3: eleven lead lines, each the first sentence of the served schema
    description, verbatim; none for Restitution kinds or SDK languages."""
    text = (site_with_results / "capabilities" / "index.html").read_text(encoding="utf-8")
    schema = json.loads((SITE / "schema" / "capability.schema.json").read_text(encoding="utf-8"))
    props = schema["properties"]["credentialSubject"]["properties"]
    leads = re.findall(r'<p class="lead">(.*?)</p>', text)
    assert len(leads) == 11
    for line in leads:
        assert any(line.replace("&#x27;", "'") in (props[k].get("description", "") if k in props else "")
                   for k in props), line
    sections = text.split('<section class="question"')[1:]
    for i in (5, 10):  # Restitution kinds, SDK languages (zero-based in the fixed order)
        assert '<p class="lead">' not in sections[i]


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
    by_rail = text.split('class="by-rail"', 1)[1].split("</nav>", 1)[0]
    assert len(re.findall(r'<a href="#', by_rail)) == 13 * 6
    for a in anchors:
        assert a in ids, a
