# vendored from agentic-paybench/design-system-private@3afcc30 (packages/tokens, packages/family, packages/posture) by packages/family/vendor.mjs; do not edit here, re-vendor
"""family.py: the shared page renderer of the public page family.

One file, Python 3.11 or later, standard library only. It wraps a content file
(a Markdown file in the small subset below, or an HTML fragment) in the family
skeleton: the head with the two vendored stylesheets, the family bar, the
content, the posture block when asked (the ruled sentences copied from
posture-snippet.html at render time, never retyped), the engine-room panel
"For agents and software" when asked, and the footer line. The family bar and
the footer exist only here, so every surface carries the same markup.

Markdown subset, which is exactly what the family's content files use:
ATX headings 1 to 3; paragraphs; pipe tables with a header separator; bullet
and numbered lists (one line per item); [text](url) links; <https://...>
autolinks; **bold**; `code`; an HTML comment on a line of its own; and a
first-line marker ``posture-class: <class>`` (bare or inside an HTML comment),
emitted as ``<!-- posture-class: <class> -->`` before the doctype so the
ADR-010 PUBSCAN scanner's marker regex still matches. Anything else is an
error: the renderer is strict so that no construct passes through unseen.
Every piece of text, table cells and code spans included, is HTML-escaped.

Command line::

    python3 family.py render --content page.md --out page.html \
        --surface oracle --posture measurement --family ../family/ \
        [--title T] [--description D] [--machine paths.json] [--extra-head file] [--check]

``--check`` renders to memory and exits 1 if the file at ``--out`` differs,
which is the drift gate a repository's CI runs. Importable as a module:
``md_to_html``, ``render_page``, ``posture_block``, ``machine_panel``,
``write_or_check``.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

ENTITY = "Everyday AI Ltd"
SURFACES = (
    ("everydayai", "https://everydayai.link/", "everydayai.link"),
    ("index", "https://agentic-paybench.dev/", "agentic-paybench.dev"),
    ("oracle", "https://oracle.agentic-paybench.dev/", "oracle.agentic-paybench.dev"),
)
POSTURE_SETS = ("measurement", "documentation", "none")
PLACEHOLDER_POSTURE = "<!-- family:posture -->"
# The same block, set as the labelled "Posture" block the oracle pages use
# (small type, its own heading): the page places it where it belongs.
PLACEHOLDER_POSTURE_LABELLED = "<!-- family:posture labelled -->"
PLACEHOLDER_MACHINE = "<!-- family:machine -->"

MARKER_RE = re.compile(r"^\s*(?:<!--\s*)?posture-class:\s*([A-Za-z0-9_-]+)\s*(?:-->)?\s*$")
HEADING_RE = re.compile(r"^(#{1,3}) (.+?)\s*$")
BULLET_RE = re.compile(r"^- (.+)$")
NUMBERED_RE = re.compile(r"^\d+\. (.+)$")
SEPARATOR_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
NUMERIC_CELL_RE = re.compile(r"^(-|-?\d[\d.,]*|-?\d[\d.,]* to -?\d[\d.,]*|R\d+)$")
CODE_SPLIT_RE = re.compile(r"(`[^`\n]+`)")
AUTOLINK_RE = re.compile(r"&lt;(https?://[^&\s]+)&gt;")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
# Emphasis: *word* or *a few words*, the asterisks hugging the text and not
# touching a word character outside, so "2 * 3" and a lone "*" stay literal.
EM_RE = re.compile(r"(?<![*\w])\*(?![\s*])(.+?)(?<![\s*])\*(?![*\w])")


class MarkdownError(ValueError):
    """A construct outside the subset, with the line number."""


def _esc(text: str) -> str:
    return html.escape(text, quote=False)


def inline(text: str) -> str:
    """Inline Markdown to HTML with every character escaped first."""
    out: list[str] = []
    for i, seg in enumerate(CODE_SPLIT_RE.split(text)):
        if i % 2 == 1:
            out.append("<code>" + _esc(seg[1:-1]) + "</code>")
            continue
        seg = _esc(seg)
        seg = AUTOLINK_RE.sub(lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', seg)
        seg = LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', seg)
        seg = BOLD_RE.sub(r"<strong>\1</strong>", seg)
        seg = EM_RE.sub(r"<em>\1</em>", seg)
        out.append(seg)
    return "".join(out)


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "section"


def _split_cells(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [c.strip() for c in body.split("|")]


def md_to_html(text: str) -> tuple[str | None, str, str | None]:
    """Return (marker, body_html, first_h1_text)."""
    lines = text.split("\n")
    marker = None
    i = 0
    if lines and MARKER_RE.match(lines[0]):
        marker = MARKER_RE.match(lines[0]).group(1)
        i = 1
    out: list[str] = []
    title: str | None = None
    used_ids: dict[str, int] = {}
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            body = m.group(2)
            if level == 1 and title is None:
                title = re.sub(r"[*`]", "", body)
            # Ids are unique per page: a repeated heading (the results page
            # repeats "Work class" under each primitive) gets a numeric suffix.
            base_id = slug(body)
            used_ids[base_id] = used_ids.get(base_id, 0) + 1
            hid = base_id if used_ids[base_id] == 1 else f"{base_id}-{used_ids[base_id]}"
            out.append(f'<h{level} id="{hid}">{inline(body)}</h{level}>')
            i += 1
            continue
        if line.lstrip().startswith("<!--"):
            if "-->" not in line:
                raise MarkdownError(f"line {i + 1}: an HTML comment must close on its own line")
            out.append(line.strip())
            i += 1
            continue
        if line.startswith("|"):
            rows: list[str] = []
            while i < n and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            if len(rows) < 2 or not SEPARATOR_RE.match(rows[1]):
                raise MarkdownError(f"line {i + 1 - len(rows)}: a table needs a header row and a separator row")
            header = _split_cells(rows[0])
            parts = ['<div class="table-scroll"><table><thead><tr>']
            parts.append("".join(f"<th>{inline(c)}</th>" for c in header))
            parts.append("</tr></thead><tbody>")
            for row in rows[2:]:
                cells = _split_cells(row)
                tds = []
                for c in cells:
                    cls = ' class="num"' if NUMERIC_CELL_RE.match(c) else ""
                    tds.append(f"<td{cls}>{inline(c)}</td>")
                parts.append("<tr>" + "".join(tds) + "</tr>")
            parts.append("</tbody></table></div>")
            out.append("".join(parts))
            continue
        if BULLET_RE.match(line) or NUMBERED_RE.match(line):
            ordered = bool(NUMBERED_RE.match(line))
            rx = NUMBERED_RE if ordered else BULLET_RE
            items: list[str] = []
            while i < n and rx.match(lines[i]):
                items.append(rx.match(lines[i]).group(1))
                i += 1
                # Continuation lines of the same item: indented, not a new item.
                while i < n and lines[i].startswith(("  ", "\t")) and lines[i].strip() \
                        and not rx.match(lines[i].lstrip()):
                    items[-1] += " " + lines[i].strip()
                    i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(it)}</li>" for it in items) + f"</{tag}>")
            continue
        if line.startswith("```"):
            # A fenced block: shown as preformatted text, escaped, never interpreted.
            j = i + 1
            while j < n and not lines[j].startswith("```"):
                j += 1
            if j >= n:
                raise MarkdownError(f"line {i + 1}: an unclosed fence")
            out.append("<pre><code>" + _esc("\n".join(lines[i + 1:j])) + "</code></pre>")
            i = j + 1
            continue
        if line.startswith(">"):
            # A block quote: the quoted lines are rendered with the same subset.
            quoted: list[str] = []
            while i < n and lines[i].startswith(">"):
                quoted.append(lines[i][2:] if lines[i].startswith("> ") else lines[i][1:])
                i += 1
            _m, inner, _t = md_to_html("\n".join(quoted))
            out.append("<blockquote>" + inner + "</blockquote>")
            continue
        if line.lstrip().startswith("<") and not line.lstrip().startswith("<http"):
            raise MarkdownError(f"line {i + 1}: raw HTML is outside the subset")
        if line.startswith(("    ", "\t")):
            raise MarkdownError(f"line {i + 1}: indented code is outside the subset")
        para: list[str] = []
        while i < n and lines[i].strip() and not HEADING_RE.match(lines[i]) and not lines[i].startswith("|") \
                and not BULLET_RE.match(lines[i]) and not NUMBERED_RE.match(lines[i]) \
                and not lines[i].lstrip().startswith("<!--") and not lines[i].startswith((">", "```")):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>" + inline(" ".join(para)) + "</p>")
    return marker, "\n".join(out), title


def posture_block(set_name: str, snippet_path: Path) -> str:
    """The ruled sentences for one set, copied verbatim from the shared snippet."""
    if set_name == "none":
        return ""
    if set_name not in POSTURE_SETS:
        raise ValueError(f"unknown posture set {set_name!r}")
    text = snippet_path.read_text(encoding="utf-8")
    m = re.search(
        r'<div class="posture" data-posture-set="' + re.escape(set_name) + r'">.*?</div>', text, re.S
    )
    if not m:
        raise ValueError(f"posture set {set_name!r} not found in {snippet_path}")
    return m.group(0)


def machine_panel(paths: list[dict], intro: str | None = None) -> str:
    """The engine-room panel. Each entry: {href, path, note}."""
    if not paths:
        return ""
    lis = []
    for p in paths:
        href = _esc(p["href"]).replace('"', "&quot;")
        lis.append(
            f'<li><a href="{href}"><code>{_esc(p["path"]).replace("/", "/<wbr>")}</code></a> <span>{_esc(p.get("note", ""))}</span></li>'
        )
    lead = _esc(intro) if intro else "The same facts as data, at these paths."
    return (
        f'<section class="machine" data-theme="dark" data-accent="{ACCENT}" aria-labelledby="machine-h">\n'
        '<h2 id="machine-h">For agents and software</h2>\n'
        f"<p>{lead}</p>\n"
        '<ul class="paths">\n' + "\n".join(lis) + "\n</ul>\n</section>"
    )


# The public family's accent (founder ruling, 2026-10-18): indigo, carried by
# the family-scope data-accent attribute on the page wrapper and on every
# themed island, never on <html> (under the OS-dark media query the theme
# block on :root outranks a single-attribute accent rule there). No token
# value changes; the demo shell keeps its own accent.
ACCENT = "indigo"


def family_bar(surface: str, at_root: bool = True) -> str:
    """The one-line family bar. The current surface's link carries
    aria-current: "page" on that surface's root page (the link IS this page),
    "true" on any other page of the surface (the link is the current site,
    not this page)."""
    links = []
    for key, href, label in SURFACES:
        cur = (' aria-current="page"' if at_root else ' aria-current="true"') if key == surface else ""
        links.append(f'  <a href="{href}"{cur}>{label}</a>')
    return (
        '<nav class="fam" aria-label="Family">\n'
        f'  <span class="who">{ENTITY}</span>\n' + "\n".join(links) + "\n</nav>"
    )


def footer_line() -> str:
    e, i, o = SURFACES
    return (
        '<footer class="foot">A family of three: '
        f'<a href="{e[1]}">{e[2]}</a> (the person), '
        f'<a href="{i[1]}">{i[2]}</a> (the research index), '
        f'<a href="{o[1]}">{o[2]}</a> (the data). {ENTITY}.</footer>'
    )


def _insert(body: str, placeholder: str, block: str, after_first_paragraph: bool) -> str:
    if placeholder in body:
        return body.replace(placeholder, block, 1)
    if not block:
        return body
    if after_first_paragraph:
        h1_end = body.find("</h1>")
        p_end = body.find("</p>", h1_end if h1_end >= 0 else 0)
        if p_end >= 0:
            p_end += len("</p>")
            return body[:p_end] + "\n" + block + body[p_end:]
    return body + "\n" + block


def render_page(
    body: str,
    *,
    title: str,
    description: str,
    surface: str,
    posture: str,
    family_prefix: str,
    snippet_path: Path,
    machine: list[dict] | None = None,
    machine_intro: str | None = None,
    marker: str | None = None,
    extra_head: str = "",
    lang: str = "en",
    layout: str = "measure",
    at_root: bool = True,
) -> str:
    """layout "measure" (every page by default) or "wide" (a data page: the
    container widens, prose inside it keeps the reading measure, one left edge)."""
    if surface not in {s[0] for s in SURFACES}:
        raise ValueError(f"unknown surface {surface!r}")
    if layout not in ("measure", "wide"):
        raise ValueError(f"unknown layout {layout!r}")
    page_class = "family-page family-page--wide" if layout == "wide" else "family-page"
    if PLACEHOLDER_POSTURE_LABELLED in body:
        block = posture_block(posture, snippet_path)
        body = body.replace(PLACEHOLDER_POSTURE_LABELLED,
                            '<section class="posture-foot" aria-labelledby="posture-h"><h2 id="posture-h">Posture</h2>\n'
                            + block + "\n</section>", 1)
    else:
        body = _insert(body, PLACEHOLDER_POSTURE, posture_block(posture, snippet_path), True)
    body = _insert(body, PLACEHOLDER_MACHINE, machine_panel(machine or [], machine_intro), False)
    head_marker = f"<!-- posture-class: {marker} -->\n" if marker else ""
    extra = (extra_head.strip() + "\n") if extra_head.strip() else ""
    # The two typefaces are preloaded so the swap happens before first paint
    # (no layout shift); an empty favicon stops the browser's /favicon.ico
    # request unless the page's own head names an icon.
    preload = (
        f'<link rel="preload" href="{family_prefix}fonts/hanken-grotesk-latin.woff2" as="font" type="font/woff2" crossorigin>\n'
        f'<link rel="preload" href="{family_prefix}fonts/ibm-plex-mono-400-latin.woff2" as="font" type="font/woff2" crossorigin>\n'
    )
    icon = "" if 'rel="icon"' in extra else '<link rel="icon" href="data:,">\n'
    return (
        f"{head_marker}<!doctype html>\n"
        f'<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_esc(title)}</title>\n"
        f'<meta name="description" content="{_esc(description).replace(chr(34), "&quot;")}">\n'
        f"{preload}"
        f'<link rel="stylesheet" href="{family_prefix}tokens.css">\n'
        f'<link rel="stylesheet" href="{family_prefix}family.css">\n'
        f"{icon}{extra}</head>\n<body>\n"
        f'<div class="{page_class}" data-accent="{ACCENT}">\n'
        f"{family_bar(surface, at_root)}\n<main>\n{body}\n</main>\n{footer_line()}\n</div>\n</body>\n</html>\n"
    )


def first_paragraph_text(body_html: str) -> str:
    m = re.search(r"<p>(.*?)</p>", body_html, re.S)
    if not m:
        return ""
    text = re.sub(r"<[^>]+>", "", m.group(1))
    text = html.unescape(text)
    return text if len(text) <= 240 else text[:237].rstrip() + "..."


def write_or_check(out: Path, content: str, check: bool) -> int:
    if check:
        current = out.read_text(encoding="utf-8") if out.exists() else None
        if current != content:
            print(f"family: {out} differs from a fresh render", file=sys.stderr)
            return 1
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render a page of the public page family.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--content", required=True, help="a Markdown file, or an HTML fragment when the name ends .html")
    r.add_argument("--out", required=True)
    r.add_argument("--surface", required=True, choices=[s[0] for s in SURFACES])
    r.add_argument("--posture", default="none", choices=POSTURE_SETS)
    r.add_argument("--family", default="family/", help="relative URL prefix of the vendored family directory")
    r.add_argument("--title")
    r.add_argument("--description")
    r.add_argument("--machine", help="a JSON file, or inline JSON: a list of {href, path, note}")
    r.add_argument("--machine-intro")
    r.add_argument("--extra-head", help="a file whose lines go into <head> after the stylesheets")
    r.add_argument("--lang", default="en")
    r.add_argument("--lead-first", action="store_true", help="set the first top-level paragraph of a Markdown page in the lead style")
    r.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    here = Path(__file__).resolve().parent
    # Vendored: the snippet sits beside this file. In the design-system
    # repository itself it lives in the sibling packages/posture.
    snippet = here / "posture-snippet.html"
    if not snippet.exists():
        snippet = here.parent / "posture" / "posture-snippet.html"
    content_path = Path(a.content)
    text = content_path.read_text(encoding="utf-8")
    if content_path.suffix.lower() == ".html":
        marker = None
        first = text.split("\n", 1)[0]
        if MARKER_RE.match(first):
            marker = MARKER_RE.match(first).group(1)
            text = text.split("\n", 1)[1] if "\n" in text else ""
        body, title_in = text.strip(), None
        m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        if m:
            title_in = html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))
    else:
        try:
            marker, body, title_in = md_to_html(text)
        except MarkdownError as e:
            print(f"family: {content_path}: {e}", file=sys.stderr)
            return 2
        if a.lead_first:
            # Top-level elements sit on their own lines; a block quote's inner
            # paragraphs do not start a line, so this is the first top-level one.
            body = re.sub(r"(?m)^<p>", '<p class="lead">', body, count=1)
    machine = None
    if a.machine:
        mp = Path(a.machine)
        machine = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else json.loads(a.machine)
    extra_head = Path(a.extra_head).read_text(encoding="utf-8") if a.extra_head else ""
    title = a.title or title_in
    if not title:
        print("family: no --title and no h1 in the content", file=sys.stderr)
        return 2
    page = render_page(
        body,
        title=title,
        description=a.description or first_paragraph_text(body),
        surface=a.surface,
        posture=a.posture,
        family_prefix=a.family,
        snippet_path=snippet,
        machine=machine,
        machine_intro=a.machine_intro,
        marker=marker,
        extra_head=extra_head,
        lang=a.lang,
    )
    return write_or_check(Path(a.out), page, a.check)


if __name__ == "__main__":
    sys.exit(main())
