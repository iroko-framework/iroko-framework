#!/usr/bin/env python3
"""
check_site.py

QA checks for the generated Iroko ontology site.

Default mode validates local generated artifacts:
  - required feature markers
  - term-list fragment links for classes, properties, and concepts
  - concept chip data consistency
  - generated JavaScript syntax with node --check
  - RDF serializations parse and match Turtle triple counts
  - sitemap.xml and robots.txt discovery policy

Live mode can be used after GitHub Pages deploys:
  python scripts/check_site.py --no-local --live-base https://ontology.irokosociety.org
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rdflib import Graph


SITE_BASE = "https://ontology.irokosociety.org"
MODULE_PAGE_EXCLUDES = {"iroko-termlist.html", "iroko-index.html"}
SITEMAP_REQUIRED_PATHS = [
    "/",
    "/iroko",
    "/iroko-core",
    "/vocab/",
    "/vocab/iroko-core.html",
    "/vocab/iroko-core.ttl",
    "/vocab/iroko-core.jsonld",
    "/vocab/iroko-termlist.html",
    "/docs/",
    "/whitepaper/",
]
REQUIRED_CORE_MARKERS = [
    'class="module-jump"',
    'href="#classes"',
    'href="#properties"',
    'id="classes"',
    'id="properties"',
    'id="concepts"',
    'id="concept-panel"',
    "function activateConcept",
    "function renderUsedBy",
    "function toggleConceptUsedBy",
    "function copyConcept",
    "const CONCEPTS",
    "cp-used-toggle",
    "Copy Turtle",
    'id="cls-AccessPolicy"',
]
LIVE_MARKERS = {
    "/vocab/iroko-core.html": [
        'class="module-jump"',
        'href="#classes"',
        'href="#properties"',
        'id="classes"',
        'id="properties"',
        'id="concepts"',
        'id="concept-panel"',
        "function activateConcept",
        "function renderUsedBy",
        "function toggleConceptUsedBy",
        "const CONCEPTS",
        "cp-used-toggle",
        "Copy Turtle",
    ],
    "/vocab/iroko-termlist.html": [
        "iroko-core.html#concept-access-public-unrestricted",
        "iroko-core.html#prop-accessLevel",
    ],
    "/vocab/iroko-core.ttl": [
        "iroko:AccessLevelScheme",
        "iroko:access-public-unrestricted",
    ],
    "/robots.txt": [
        "Sitemap: https://ontology.irokosociety.org/sitemap.xml",
        "User-agent: *",
        "User-agent: OAI-SearchBot",
        "Allow: /",
        "User-agent: GPTBot",
        "Disallow: /",
    ],
    "/sitemap.xml": [
        "https://ontology.irokosociety.org/",
        "https://ontology.irokosociety.org/iroko-core",
        "https://ontology.irokosociety.org/vocab/iroko-core.html",
        "https://ontology.irokosociety.org/vocab/iroko-core.ttl",
    ],
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


class SiteCheck:
    def __init__(self, root: Path, skip_js: bool = False, verbose: bool = False) -> None:
        self.root = root
        self.vocab = root / "vocab"
        self.skip_js = skip_js
        self.verbose = verbose
        self.errors: list[str] = []
        self.notes: list[str] = []
        self.page_cache: dict[str, dict] = {}

    def note(self, message: str) -> None:
        self.notes.append(message)
        if self.verbose:
            print(message)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def read_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def module_pages(self) -> list[Path]:
        return [
            p
            for p in sorted(self.vocab.glob("iroko-*.html"))
            if p.name not in MODULE_PAGE_EXCLUDES
        ]

    def parse_json_const(self, html: str, name: str, next_name: str) -> dict | list:
        pattern = rf"const {re.escape(name)} = (.*?);\nconst {re.escape(next_name)}"
        match = re.search(pattern, html, re.S)
        if not match:
            raise ValueError(f"missing JS constant {name}")
        return json.loads(match.group(1))

    def page_data(self, page_name: str) -> dict:
        if page_name in self.page_cache:
            return self.page_cache[page_name]
        path = self.vocab / page_name
        html = self.read_text(path)
        concepts = self.parse_json_const(html, "CONCEPTS", "MODULE_CROSS")
        properties = self.parse_json_const(html, "PROPERTIES", "CONCEPTS")
        ids = set(re.findall(r'id="([^"]+)"', html))
        prop_ids = {
            str(item.get("uri", "")).split(":")[-1]
            for item in properties
            if isinstance(item, dict) and item.get("uri")
        }
        data = {
            "html": html,
            "ids": ids,
            "concepts": concepts,
            "prop_ids": prop_ids,
        }
        self.page_cache[page_name] = data
        return data

    def check_required_files_and_markers(self) -> None:
        required = [
            self.root / "index.html",
            self.root / "robots.txt",
            self.root / "sitemap.xml",
            self.root / "iroko.html",
            self.root / "iroko-core.html",
            self.vocab / "iroko-core.html",
            self.vocab / "iroko-core.ttl",
            self.vocab / "iroko-core.jsonld",
            self.vocab / "iroko-core.rdf",
            self.vocab / "iroko-core.nt",
            self.vocab / "iroko-termlist.html",
            self.vocab / "iroko-index.html",
        ]
        for path in required:
            if not path.exists():
                self.error(f"missing required file: {path.relative_to(self.root)}")

        core_path = self.vocab / "iroko-core.html"
        if core_path.exists():
            core = self.read_text(core_path)
            for marker in REQUIRED_CORE_MARKERS:
                if marker not in core:
                    self.error(f"vocab/iroko-core.html missing marker: {marker}")
            if re.search(r'<div class="class-grid">\s*<span class="term-anchor"', core):
                self.error("class grid has standalone term anchors; this breaks compact class layout")

    def check_module_navigation(self) -> None:
        for path in self.module_pages():
            html = self.read_text(path)
            required = [
                'class="module-jump"',
                'href="#classes"',
                'href="#properties"',
                'id="classes"',
                'id="properties"',
            ]
            for marker in required:
                if marker not in html:
                    self.error(f"{path.name}: missing module navigation marker: {marker}")
            has_concepts = 'id="concept-panel"' in html
            if has_concepts and 'id="concepts"' not in html:
                self.error(f"{path.name}: concepts panel exists but concepts section anchor is missing")
            if 'href="#concepts"' in html and 'id="concepts"' not in html:
                self.error(f"{path.name}: concepts jump link points to a missing anchor")

    def check_concept_data(self) -> None:
        pages = self.module_pages()
        for path in pages:
            html = self.read_text(path)
            try:
                concepts = self.parse_json_const(html, "CONCEPTS", "MODULE_CROSS")
            except Exception as exc:
                self.error(f"{path.name}: {exc}")
                continue
            chips = re.findall(r'<div class="chip" id="concept-([^"]+)"', html)
            if chips and 'id="concept-panel"' not in html:
                self.error(f"{path.name}: concept chips exist but concept panel is missing")
            if len(chips) != len(concepts):
                self.error(
                    f"{path.name}: concept chip count {len(chips)} != CONCEPTS count {len(concepts)}"
                )
            if chips and 'onclick="activateConcept' not in html:
                self.error(f"{path.name}: concept chips are not clickable")
            for concept_id in chips:
                if concept_id not in concepts:
                    self.error(f"{path.name}: chip concept-{concept_id} missing from CONCEPTS")
            for concept_id, concept in concepts.items():
                if concept.get("scope") == concept_id:
                    self.error(f"{path.name}: concept {concept_id} has fake scope-note fallback")
        self.note(f"concept data checked for {len(pages)} module pages")

    def check_term_links(self) -> None:
        index_path = self.vocab / "iroko-termlist.html"
        if not index_path.exists():
            self.error("vocab/iroko-termlist.html missing")
            return
        parser = LinkParser()
        parser.feed(self.read_text(index_path))
        checked = 0
        for href in parser.links:
            if "#" not in href or not href.startswith("iroko-"):
                continue
            page_name, fragment = href.split("#", 1)
            page_path = self.vocab / page_name
            if not page_path.exists():
                self.error(f"term link target page missing: {href}")
                continue
            try:
                data = self.page_data(page_name)
            except Exception as exc:
                self.error(f"{page_name}: cannot parse page data for {href}: {exc}")
                continue
            checked += 1
            if fragment.startswith("concept-"):
                concept_id = fragment[len("concept-") :]
                if concept_id not in data["concepts"]:
                    self.error(f"term concept fragment missing: {href}")
            elif fragment.startswith("prop-"):
                prop_id = fragment[len("prop-") :]
                if prop_id not in data["prop_ids"]:
                    self.error(f"term property fragment missing: {href}")
            elif fragment.startswith("cls-"):
                if fragment not in data["ids"]:
                    self.error(f"term class fragment missing: {href}")
            elif fragment not in data["ids"]:
                self.error(f"term fragment missing: {href}")
        self.note(f"term-list fragment links checked: {checked}")

    def check_js_syntax(self) -> None:
        if self.skip_js:
            self.note("generated JavaScript syntax check skipped")
            return
        node = shutil.which("node")
        if not node:
            self.error("node executable not found; cannot run generated JavaScript syntax checks")
            return
        checked = 0
        for path in self.module_pages():
            html = self.read_text(path)
            for script in re.findall(r"<script>\n(.*?)\n</script>", html, re.S):
                checked += 1
                tmp_name = None
                try:
                    with tempfile.NamedTemporaryFile(
                        "w", suffix=".js", delete=False, encoding="utf-8"
                    ) as handle:
                        handle.write(script)
                        tmp_name = handle.name
                    result = subprocess.run(
                        [node, "--check", tmp_name],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if result.returncode:
                        message = result.stderr.strip() or result.stdout.strip()
                        self.error(f"{path.name}: generated JS syntax error: {message}")
                finally:
                    if tmp_name:
                        Path(tmp_name).unlink(missing_ok=True)
        self.note(f"generated JavaScript blocks checked: {checked}")

    def parse_graph(self, path: Path, fmt: str) -> Graph:
        graph = Graph()
        graph.parse(str(path), format=fmt)
        return graph

    def check_rdf(self) -> None:
        formats = {
            ".ttl": "turtle",
            ".jsonld": "json-ld",
            ".rdf": "xml",
            ".nt": "nt",
        }
        ttl_counts: dict[str, int] = {}
        ttl_files = sorted(self.vocab.glob("*.ttl"))
        for ttl in ttl_files:
            try:
                ttl_counts[ttl.stem] = len(self.parse_graph(ttl, "turtle"))
            except Exception as exc:
                self.error(f"{ttl.relative_to(self.root)} failed Turtle parse: {exc}")

        serializations_checked = 0
        for stem, ttl_count in ttl_counts.items():
            for ext, fmt in formats.items():
                if ext == ".ttl":
                    continue
                path = self.vocab / f"{stem}{ext}"
                if not path.exists():
                    continue
                serializations_checked += 1
                try:
                    count = len(self.parse_graph(path, fmt))
                except Exception as exc:
                    self.error(f"{path.relative_to(self.root)} failed RDF parse: {exc}")
                    continue
                if count != ttl_count:
                    self.error(
                        f"{path.relative_to(self.root)} triple count {count} != {stem}.ttl {ttl_count}"
                    )
        self.note(
            f"RDF checked: {len(ttl_files)} Turtle files, {serializations_checked} serializations"
        )

    def check_sitemap_and_robots(self) -> None:
        robots_path = self.root / "robots.txt"
        sitemap_path = self.root / "sitemap.xml"
        if not robots_path.exists() or not sitemap_path.exists():
            return

        robots = self.read_text(robots_path)
        robot_markers = [
            f"Sitemap: {SITE_BASE}/sitemap.xml",
            "User-agent: *",
            "Allow: /",
            "User-agent: OAI-SearchBot",
            "User-agent: ChatGPT-User",
            "User-agent: GPTBot",
            "User-agent: Google-Extended",
            "Disallow: /",
        ]
        for marker in robot_markers:
            if marker not in robots:
                self.error(f"robots.txt missing marker: {marker}")
        if re.search(r"User-agent:\s*OAI-SearchBot\s+Disallow:\s*/", robots, re.I):
            self.error("robots.txt blocks OAI-SearchBot; this reduces research discovery")
        if re.search(r"User-agent:\s*GPTBot\s+Allow:\s*/", robots, re.I):
            self.error("robots.txt allows GPTBot; expected AI-training opt-out")
        try:
            robots.encode("ascii")
        except UnicodeEncodeError:
            self.error("robots.txt should stay ASCII to avoid crawler parsing issues")

        sitemap_text = self.read_text(sitemap_path)
        try:
            sitemap = ET.fromstring(sitemap_text)
        except ET.ParseError as exc:
            self.error(f"sitemap.xml is not valid XML: {exc}")
            return

        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [node.text.strip() for node in sitemap.findall(".//sm:loc", ns) if node.text]
        if not locs:
            self.error("sitemap.xml has no <loc> entries")
            return
        if len(locs) != len(set(locs)):
            self.error("sitemap.xml contains duplicate <loc> entries")

        urls = set(locs)
        for loc in locs:
            parsed = urlparse(loc)
            if f"{parsed.scheme}://{parsed.netloc}" != SITE_BASE:
                self.error(f"sitemap.xml loc is outside canonical site: {loc}")
            if parsed.fragment:
                self.error(f"sitemap.xml loc contains a fragment: {loc}")
            if " " in loc:
                self.error(f"sitemap.xml loc contains an unescaped space: {loc}")

        expected = {SITE_BASE + path for path in SITEMAP_REQUIRED_PATHS}
        expected.update(SITE_BASE + f"/vocab/{path.name}" for path in self.module_pages())
        for ext in (".ttl", ".jsonld", ".rdf", ".nt"):
            expected.update(
                SITE_BASE + f"/vocab/{path.name}"
                for path in sorted(self.vocab.glob(f"iroko-*{ext}"))
            )
        expected.update(
            SITE_BASE + f"/{path.stem}"
            for path in sorted(self.root.glob("iroko*.html"))
            if path.name != "index.html"
        )
        if (self.root / "iroko-framework" / "index.html").exists():
            expected.add(SITE_BASE + "/iroko-framework/")

        missing = sorted(expected - urls)
        for loc in missing[:20]:
            self.error(f"sitemap.xml missing expected URL: {loc}")
        if len(missing) > 20:
            self.error(f"sitemap.xml missing {len(missing) - 20} additional expected URLs")

        if SITE_BASE + "/vocab/iroko-index.html" in urls:
            self.error("sitemap.xml should not index vocab/iroko-index.html redirect")
        self.note(f"sitemap checked: {len(locs)} URLs")

    def run_local(self) -> bool:
        self.check_required_files_and_markers()
        self.check_module_navigation()
        self.check_concept_data()
        self.check_term_links()
        self.check_js_syntax()
        self.check_rdf()
        self.check_sitemap_and_robots()
        return not self.errors


def fetch_text(url: str, timeout: int) -> tuple[int, str, str | None, str | None]:
    req = Request(
        url,
        headers={
            "User-Agent": "Iroko site smoke check",
            "Cache-Control": "no-cache",
        },
    )
    with urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8", "replace")
        return (
            response.status,
            body,
            response.headers.get("Last-Modified"),
            response.headers.get("ETag"),
        )


def run_live(base: str, timeout: int, verbose: bool = False) -> list[str]:
    errors: list[str] = []
    base = base.rstrip("/")
    for path, markers in LIVE_MARKERS.items():
        url = base + path
        try:
            status, body, last_modified, etag = fetch_text(url, timeout)
        except (HTTPError, URLError, TimeoutError) as exc:
            errors.append(f"{url}: fetch failed: {exc}")
            continue
        if status != 200:
            errors.append(f"{url}: expected 200, got {status}")
        if verbose:
            print(f"live {url}: {status}, {len(body)} bytes, {last_modified}, {etag}")
        for marker in markers:
            if marker not in body:
                errors.append(f"{url}: missing live marker: {marker}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check generated Iroko site artifacts.")
    parser.add_argument("--root", default=None, help="Repository root. Defaults to script parent.")
    parser.add_argument("--skip-js", action="store_true", help="Skip node --check for generated JS.")
    parser.add_argument("--no-local", action="store_true", help="Skip local generated artifact checks.")
    parser.add_argument("--live-base", default=None, help="Optional live site base URL to smoke check.")
    parser.add_argument("--live-timeout", type=int, default=30, help="Live check timeout in seconds.")
    parser.add_argument("--verbose", action="store_true", help="Print progress details.")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    all_errors: list[str] = []

    if not args.no_local:
        checker = SiteCheck(root=root, skip_js=args.skip_js, verbose=args.verbose)
        checker.run_local()
        for note in checker.notes:
            if not args.verbose:
                print(note)
        all_errors.extend(checker.errors)

    if args.live_base:
        live_errors = run_live(args.live_base, args.live_timeout, verbose=args.verbose)
        if not live_errors:
            print(f"live smoke check passed: {args.live_base.rstrip('/')}")
        all_errors.extend(live_errors)

    if all_errors:
        print("\nSITE CHECK FAILED")
        for error in all_errors:
            print(f" - {error}")
        return 1

    print("SITE CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
