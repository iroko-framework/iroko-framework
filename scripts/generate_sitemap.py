#!/usr/bin/env python3
"""
generate_sitemap.py - Generate the public sitemap for the Iroko ontology site.

The sitemap is intentionally broad: it includes the main researcher-facing pages,
stable ontology URI aliases, module browse pages, and RDF serialization files.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from html import escape
from pathlib import Path
from urllib.parse import quote


BASE_URL = "https://ontology.irokosociety.org"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
MODULE_PAGE_EXCLUDES = {"iroko-index.html"}
SERIALIZATION_EXTS = (".ttl", ".jsonld", ".rdf", ".nt")


@dataclass(frozen=True)
class SitemapEntry:
    path: str
    changefreq: str
    priority: str


def normalize_path(path: str) -> str:
    path = path.strip()
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return path


def public_url(path: str) -> str:
    normalized = normalize_path(path)
    return BASE_URL + quote(normalized, safe="/-._~")


def add_entry(entries: list[SitemapEntry], seen: set[str], path: str, changefreq: str, priority: str) -> None:
    normalized = normalize_path(path)
    if normalized in seen:
        return
    seen.add(normalized)
    entries.append(SitemapEntry(normalized, changefreq, priority))


def discover_entries(root: Path) -> list[SitemapEntry]:
    entries: list[SitemapEntry] = []
    seen: set[str] = set()
    vocab = root / "vocab"

    add_entry(entries, seen, "/", "monthly", "1.0")
    add_entry(entries, seen, "/vocab/", "monthly", "0.9")
    add_entry(entries, seen, "/vocab/iroko-termlist.html", "monthly", "0.8")
    add_entry(entries, seen, "/docs/", "monthly", "0.7")
    add_entry(entries, seen, "/docs/ARCHITECTURE.html", "monthly", "0.6")
    add_entry(entries, seen, "/docs/CONTRIBUTING.html", "yearly", "0.5")
    add_entry(entries, seen, "/docs/REUSE.html", "yearly", "0.5")
    add_entry(entries, seen, "/whitepaper/", "yearly", "0.7")

    pdfs = sorted((root / "whitepaper").glob("*.pdf"))
    for pdf in pdfs:
        add_entry(entries, seen, f"/whitepaper/{pdf.name}", "yearly", "0.5")

    if (root / "iroko-framework" / "index.html").exists():
        add_entry(entries, seen, "/iroko-framework/", "monthly", "0.7")

    for alias in sorted(root.glob("iroko*.html")):
        if alias.name == "index.html":
            continue
        add_entry(entries, seen, f"/{alias.stem}", "monthly", "0.7")

    if vocab.exists():
        for page in sorted(vocab.glob("iroko-*.html")):
            if page.name in MODULE_PAGE_EXCLUDES:
                continue
            add_entry(entries, seen, f"/vocab/{page.name}", "monthly", "0.8")

        for ext in SERIALIZATION_EXTS:
            for rdf_file in sorted(vocab.glob(f"iroko-*{ext}")):
                add_entry(entries, seen, f"/vocab/{rdf_file.name}", "monthly", "0.5")

    return entries


def render_sitemap(entries: list[SitemapEntry]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<urlset xmlns="{SITEMAP_NS}">',
    ]
    for entry in entries:
        lines.extend(
            [
                "  <url>",
                f"    <loc>{escape(public_url(entry.path))}</loc>",
                f"    <changefreq>{entry.changefreq}</changefreq>",
                f"    <priority>{entry.priority}</priority>",
                "  </url>",
            ]
        )
    lines.append("</urlset>")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate sitemap.xml for the public ontology site.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "sitemap.xml"
    entries = discover_entries(root)
    sitemap = render_sitemap(entries)

    if args.dry_run:
        print(f"Would write {len(entries)} URLs to {output}")
        return 0

    output.write_text(sitemap, encoding="utf-8", newline="\n")
    print(f"Wrote {len(entries)} URLs to {output.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
