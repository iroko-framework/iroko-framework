#!/usr/bin/env python3
"""
update_index_counts.py — Sync hardcoded term counts in all three index files
against the live TTL vocabulary files.

Updates:
  index.html           (repo root — main site landing page)
  vocab/index.html     (vocab browse landing page)
  vocab/iroko-termlist.html  (full vocabulary index)

Usage:
    python update_index_counts.py                   # auto-detects paths
    python update_index_counts.py --vocab DIR       # explicit vocab/ dir
    python update_index_counts.py --root DIR        # explicit repo root
    python update_index_counts.py --dry-run         # print changes, no writes
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from rdflib import Graph, RDF, OWL, SKOS, Namespace
except ImportError:
    print("ERROR: rdflib not found. Install with: pip install rdflib --break-system-packages")
    sys.exit(1)

IROKO_NS = "https://ontology.irokosociety.org/iroko#"

MODULES = [
    "iroko-core",
    "iroko-agency",
    "iroko-authority",
    "iroko-epistemic",
    "iroko-narrative",
    "iroko-manifestation",
    "iroko-ewe",
    "iroko-nkisi",
    "iroko-travay",
    "iroko-ile",
    "iroko-marca",
    "iroko-ekpe",
    "iroko-veve",
    "iroko-ngoma",
    "iroko-sankofa",
    "iroko-qal",

    # Uncomment to include PROV-O alignment in counts
    # "iroko-align-prov",
]

# ---------------------------------------------------------------------------
# Counting
# ---------------------------------------------------------------------------

def count_module(ttl_path: Path) -> dict | None:
    g = Graph()
    try:
        g.parse(str(ttl_path), format="turtle")
    except Exception as e:
        print(f"  WARNING: Could not parse {ttl_path.name}: {e}")
        return None

    classes = sum(
        1 for uri in g.subjects(RDF.type, OWL.Class)
        if str(uri).startswith(IROKO_NS)
    )
    props = sum(
        1 for ptype in (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty)
        for uri in g.subjects(RDF.type, ptype)
        if str(uri).startswith(IROKO_NS)
    )
    schemes = sum(
        1 for uri in g.subjects(RDF.type, SKOS.ConceptScheme)
        if str(uri).startswith(IROKO_NS)
    )
    concepts = sum(
        1 for uri in g.subjects(SKOS.inScheme, None)
        if str(uri).startswith(IROKO_NS)
    )
    return {"classes": classes, "props": props, "schemes": schemes, "concepts": concepts}


# ---------------------------------------------------------------------------
# Patching helpers
# ---------------------------------------------------------------------------

def set_hstat(html: str, label: str, value: int) -> str:
    """Headline strip in main index.html: <span class="hstat-n">N</span><span class="hstat-label">LABEL</span>"""
    pattern = (r'(<span class="hstat-n">)\d+(</span>'
               r'<span class="hstat-label">' + re.escape(label) + r'</span>)')
    new_html, n = re.subn(pattern, rf'\g<1>{value}\g<2>', html)
    if n == 0:
        print(f"  WARNING: hstat '{label}' not found")
    return new_html


def set_combined_meta_pill(html: str, classes: int, props: int, concepts: int) -> str:
    """Combined meta-pill in vocab/index.html: NNN Classes · NNN Properties · NNN Concepts"""
    pattern = r'(<span class="meta-pill">)\d+ Classes · \d+ Properties · \d+ Concepts(</span>)'
    replacement = rf'\g<1>{classes} Classes · {props} Properties · {concepts} Concepts\g<2>'
    new_html, n = re.subn(pattern, replacement, html)
    if n == 0:
        print("  WARNING: combined Classes·Properties·Concepts meta-pill not found")
    return new_html


def set_meta_pill(html: str, label: str, value: int) -> str:
    """Individual meta-pill in iroko-termlist.html: <span class="meta-pill">NNN LABEL</span>"""
    pattern = (r'(<span class="meta-pill">)\d+( ' + re.escape(label) + r'</span>)')
    new_html, n = re.subn(pattern, rf'\g<1>{value}\g<2>', html)
    if n == 0:
        print(f"  WARNING: meta-pill '{label}' not found in termlist")
    return new_html


def set_termlist_total(html: str, value: int) -> str:
    """Total count in termlist hero paragraph: NNN terms total"""
    new_html, n = re.subn(r'\d[\d,]* terms total', f'{value:,} terms total', html)
    if n == 0:
        print("  WARNING: 'terms total' pattern not found in termlist")
    return new_html



def set_terms_across(html: str, value: int) -> str:
    """Footer termlist link in both index files: all N,NNN terms across 16 modules"""
    new_html, n = re.subn(r'all [\d,]+ terms across', f'all {value:,} terms across', html)
    if n == 0:
        print("  WARNING: 'terms across' pattern not found")
    return new_html

def set_module_stat(html: str, stem: str, label: str, value, href_prefix: str = "") -> str:
    """
    Per-module stat cell. Anchors on the module's .html browse link, then
    patches the stat-cell for the given label within the next 1200 chars.

    href_prefix: "vocab/" for main index.html, "" for vocab/index.html.
    value: int or "—"
    """
    anchor_str = f'{href_prefix}{stem}.html'
    anchor_match = re.search(re.escape(anchor_str), html)
    if not anchor_match:
        print(f"  WARNING: anchor '{anchor_str}' not found")
        return html

    start = anchor_match.start()
    window_end = min(start + 2500, len(html))
    window = html[start:window_end]

    # Try exact label first, then singular/plural variant
    for lbl in (label, label.rstrip("s") if label.endswith("s") else label + "s"):
        pattern = (r'(<span class="stat-n">)[^<]*(</span>'
                   r'<span class="stat-label">' + re.escape(lbl) + r'</span>)')
        new_window, n = re.subn(pattern, rf'\g<1>{value}\g<2>', window, count=1)
        if n:
            return html[:start] + new_window + html[window_end:]

    print(f"  WARNING: stat '{label}' not found in {stem} card")
    return html


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def find_vocab_dir(script_dir: Path, arg: str | None) -> Path:
    if arg:
        return Path(arg)
    candidates = [
        script_dir.parent / "vocab",
        script_dir / "vocab",
        Path.cwd() / "vocab",
        Path.cwd(),
        script_dir,
    ]
    result = next((d for d in candidates if (d / "iroko-core.ttl").exists()), None)
    if result is None:
        print("ERROR: Cannot find vocab dir. Use --vocab to specify.")
        sys.exit(1)
    return result


def find_root_dir(vocab_dir: Path, script_dir: Path, arg: str | None) -> Path:
    if arg:
        return Path(arg)
    candidates = [
        vocab_dir.parent,
        script_dir.parent,
        Path.cwd(),
        script_dir,
    ]
    result = next((d for d in candidates if (d / "index.html").exists()), None)
    if result is None:
        print("ERROR: Cannot find root index.html. Use --root to specify.")
        sys.exit(1)
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def set_ihs_metric(html: str, label: str, value: int) -> str:
    """IHS site metric: <span class='num'>N</span><span class='label'>LABEL</span>"""
    pattern = (r'(<span class="num">)\d+(</span>' +
               r'<span class="label">' + re.escape(label) + r'</span>)')
    new_html, n = re.subn(pattern, rf'\g<1>{value}\g<2>', html)
    if n == 0:
        print(f"  WARNING: IHS metric '{label}' not found")
    return new_html


# ---------------------------------------------------------------------------
# ARCHITECTURE.md patching
# ---------------------------------------------------------------------------

def _fmt(value: int, zero_dash: bool = True) -> str:
    """Return value as string; return em-dash for zero if zero_dash is True."""
    return "\u2014" if (zero_dash and value == 0) else str(value)


def patch_architecture_md(md_path, module_counts, totals, total_terms, dry_run=False):
    """Patch the stats table and totals sentence in ARCHITECTURE.md."""
    if not md_path.exists():
        print(f"  \u26a0 Not found, skipping: {md_path.name}")
        return False

    original = md_path.read_text(encoding="utf-8")
    patched  = original

    for stem, c in module_counts.items():
        pattern = (
            r"(\| " + re.escape(stem) + r" \| )"
            r"[\d\u2014]+( \| )[\d\u2014]+( \| )[\d\u2014]+( \| )[\d\u2014]+( \|)"
        )
        replacement = (
            r"\g<1>" + _fmt(c["classes"], False)
            + r"\g<2>" + _fmt(c["props"],   False)
            + r"\g<3>" + _fmt(c["schemes"],  True)
            + r"\g<4>" + _fmt(c["concepts"], True)
            + r"\g<5>"
        )
        patched, n = re.subn(pattern, replacement, patched)
        if n == 0:
            print(f"  WARNING: ARCHITECTURE.md row not found for {stem}")

    # Total row
    total_pattern = (
        r"(\| \*\*Total\*\* \| \*\*)" + r"\d+" +
        r"(\*\* \| \*\*)" + r"\d+" +
        r"(\*\* \| \*\*)" + r"\d+" +
        r"(\*\* \| \*\*)" + r"\d+" + r"(\*\* \|)"
    )
    total_replacement = (
        r"\g<1>" + str(totals["classes"]) +
        r"\g<2>" + str(totals["props"]) +
        r"\g<3>" + str(totals["schemes"]) +
        r"\g<4>" + str(totals["concepts"]) +
        r"\g<5>"
    )
    patched, n = re.subn(total_pattern, total_replacement, patched)
    if n == 0:
        print("  WARNING: ARCHITECTURE.md Total row not found")

    # Properties sentence
    patched = re.sub(
        r"All \d+ properties across all \d+ modules carry",
        "All " + str(totals["props"]) + " properties across all "
        + str(len(MODULES)) + " modules carry",
        patched
    )

    if patched == original:
        print(f"  \u2014 {md_path.name}: no changes needed")
    elif dry_run:
        print(f"  ~ {md_path.name}: would update stats table")
    else:
        md_path.write_text(patched, encoding="utf-8")
        print(f"  \u2713 {md_path.name}: stats table updated")
    return patched != original


# ---------------------------------------------------------------------------
# ARCHITECTURE.html patching
# ---------------------------------------------------------------------------

def patch_architecture_html(html_path, module_counts, totals, total_terms, dry_run=False):
    """Patch the stats table in ARCHITECTURE.html using full-row regex splicing."""
    if not html_path.exists():
        print(f"  \u26a0 Not found, skipping: {html_path.name}")
        return False

    original = html_path.read_text(encoding="utf-8")
    patched  = original
    NL  = "\n"
    TDS = '<td style="text-align: right;">'

    # Per-module rows — match full row atomically, no window arithmetic
    for stem, c in module_counts.items():
        pat = (
            r"<td>" + re.escape(stem) + r"</td>"
            r"\s*<td[^>]*>(?:\d+|\u2014)</td>"
            r"\s*<td[^>]*>(?:\d+|\u2014)</td>"
            r"\s*<td[^>]*>(?:\d+|\u2014)</td>"
            r"\s*<td[^>]*>(?:\d+|\u2014)</td>"
        )
        m = re.search(pat, patched)
        if not m:
            print(f"  WARNING: ARCHITECTURE.html row not found for {stem}")
            continue
        repl = (
            "<td>" + stem + "</td>" + NL
            + TDS + _fmt(c["classes"], False) + "</td>" + NL
            + TDS + _fmt(c["props"],   False) + "</td>" + NL
            + TDS + _fmt(c["schemes"], True)  + "</td>" + NL
            + TDS + _fmt(c["concepts"],True)  + "</td>"
        )
        patched = patched[:m.start()] + repl + patched[m.end():]

    # Total row
    tot_pat = (
        r"<td><strong>Total</strong></td>"
        r"\s*<td[^>]*><strong>(?:\d+)</strong></td>"
        r"\s*<td[^>]*><strong>(?:\d+)</strong></td>"
        r"\s*<td[^>]*><strong>(?:\d+)</strong></td>"
        r"\s*<td[^>]*><strong>(?:\d+)</strong></td>"
    )
    m = re.search(tot_pat, patched)
    if m:
        repl = (
            "<td><strong>Total</strong></td>" + NL
            + TDS + "<strong>" + str(totals["classes"])  + "</strong></td>" + NL
            + TDS + "<strong>" + str(totals["props"])    + "</strong></td>" + NL
            + TDS + "<strong>" + str(totals["schemes"])  + "</strong></td>" + NL
            + TDS + "<strong>" + str(totals["concepts"]) + "</strong></td>"
        )
        patched = patched[:m.start()] + repl + patched[m.end():]
    else:
        print("  WARNING: ARCHITECTURE.html Total row not found")

    # Properties sentence
    patched = re.sub(
        r"All \d+ properties across all \d+ modules carry",
        "All " + str(totals["props"]) + " properties across all "
        + str(len(MODULES)) + " modules carry",
        patched
    )

    if patched == original:
        print(f"  \u2014 {html_path.name}: no changes needed")
    elif dry_run:
        print(f"  ~ {html_path.name}: would update stats table")
    else:
        html_path.write_text(patched, encoding="utf-8")
        print(f"  \u2713 {html_path.name}: stats table updated")
    return patched != original


def build_parser():
    p = argparse.ArgumentParser(
        description="Sync term counts in index.html, vocab/index.html, and iroko-termlist.html."
    )
    p.add_argument("--vocab", metavar="DIR", help="Directory containing .ttl files")
    p.add_argument("--root",  metavar="DIR", help="Repo root (where main index.html lives)")
    p.add_argument("--ihs", metavar="PATH",
                   help="Path to IHS site index.html (irokosociety.org)")
    p.add_argument("--docs", metavar="DIR",
                   help="Path to docs/ directory (for ARCHITECTURE.md and .html)")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would change without writing files")
    return p


def main():
    args = build_parser().parse_args()
    script_dir = Path(__file__).resolve().parent

    vocab_dir    = find_vocab_dir(script_dir, args.vocab)
    root_dir     = find_root_dir(vocab_dir, script_dir, args.root)
    docs_dir     = Path(args.docs) if args.docs else root_dir / "docs"

    main_index_path  = root_dir / "index.html"
    vocab_index_path = vocab_dir / "index.html"
    termlist_path    = vocab_dir / "iroko-termlist.html"

    print(f"Vocab dir:         {vocab_dir}")
    print(f"Main index:        {main_index_path}")
    print(f"Vocab index:       {vocab_index_path}")
    print(f"Termlist:          {termlist_path}")
    arch_md   = docs_dir / "ARCHITECTURE.md"
    arch_html = docs_dir / "ARCHITECTURE.html"
    print(f"Architecture MD:   {arch_md}")
    print(f"Architecture HTML: {arch_html}")
    print()

    # ── Count all modules ────────────────────────────────────────────────
    module_counts = {}
    totals = {"classes": 0, "props": 0, "schemes": 0, "concepts": 0}

    for stem in MODULES:
        ttl = vocab_dir / f"{stem}.ttl"
        if not ttl.exists():
            print(f"  ⚠ Not found, skipping: {stem}.ttl")
            continue
        counts = count_module(ttl)
        if counts is None:
            continue
        module_counts[stem] = counts
        for k in totals:
            totals[k] += counts[k]
        print(f"  ✓ {stem:<24} "
              f"{counts['classes']} cls  "
              f"{counts['props']} prop  "
              f"{counts['schemes']} sch  "
              f"{counts['concepts']} concepts")

    total_terms = totals["classes"] + totals["props"] + totals["concepts"]
    print()
    print(f"  TOTALS: {totals['classes']} classes · {totals['props']} properties · "
          f"{totals['schemes']} schemes · {totals['concepts']} concepts · "
          f"{total_terms:,} terms")
    print()

    if args.dry_run:
        print("Dry run — no files written.")
        return

    # ── 0. IHS site index.html (irokosociety.org) ────────────────────────
    if args.ihs:
        ihs_path = Path(args.ihs)
        if not ihs_path.exists():
            print(f"WARNING: IHS index not found at {ihs_path} — skipping")
        else:
            html = ihs_path.read_text(encoding="utf-8")
            html = set_ihs_metric(html, "Ontology Classes", totals["classes"])
            html = set_ihs_metric(html, "Properties",       totals["props"])
            html = set_ihs_metric(html, "Concepts",         totals["concepts"])
            ihs_path.write_text(html, encoding="utf-8")
            print(f"  ✓ Updated {ihs_path.name} (IHS site)")

    # ── 1. Main index.html ───────────────────────────────────────────────
    if not main_index_path.exists():
        print(f"WARNING: {main_index_path} not found — skipping")
    else:
        html = main_index_path.read_text(encoding="utf-8")

        # Headline strip totals
        html = set_hstat(html, "Classes",    totals["classes"])
        html = set_hstat(html, "Properties", totals["props"])
        html = set_hstat(html, "Schemes",    totals["schemes"])
        html = set_hstat(html, "Concepts",   totals["concepts"])

        # Per-module cards (hrefs are "vocab/iroko-{stem}.html")
        for stem in MODULES:
            if stem not in module_counts:
                continue
            c = module_counts[stem]
            html = set_module_stat(html, stem, "Classes",    c["classes"],  href_prefix="vocab/")
            html = set_module_stat(html, stem, "Properties", c["props"],    href_prefix="vocab/")
            html = set_module_stat(html, stem, "Schemes",    c["schemes"],  href_prefix="vocab/")
            html = set_module_stat(html, stem, "Concepts",   c["concepts"], href_prefix="vocab/")

        html = set_terms_across(html, total_terms)
        main_index_path.write_text(html, encoding="utf-8")
        print(f"  ✓ Updated {main_index_path.name}")

    # ── 2. vocab/index.html ──────────────────────────────────────────────
    if not vocab_index_path.exists():
        print(f"WARNING: {vocab_index_path} not found — skipping")
    else:
        html = vocab_index_path.read_text(encoding="utf-8")

        # Combined meta-pill: "NNN Classes · NNN Properties · NNN Concepts"
        html = set_combined_meta_pill(html, totals["classes"], totals["props"], totals["concepts"])

        html = set_terms_across(html, total_terms)
        # Per-module cards (hrefs are "iroko-{stem}.html", no vocab/ prefix)
        for stem in MODULES:
            if stem not in module_counts:
                continue
            c = module_counts[stem]
            html = set_module_stat(html, stem, "Classes",    c["classes"],  href_prefix="")
            html = set_module_stat(html, stem, "Properties", c["props"],    href_prefix="")
            html = set_module_stat(html, stem, "Schemes",    c["schemes"],  href_prefix="")
            html = set_module_stat(html, stem, "Concepts",   c["concepts"], href_prefix="")

        vocab_index_path.write_text(html, encoding="utf-8")
        print(f"  ✓ Updated {vocab_index_path.name} (in vocab/)")

    # ── 3. iroko-termlist.html ───────────────────────────────────────────
    if not termlist_path.exists():
        print(f"WARNING: {termlist_path} not found — skipping (run generate_vocab_index.py first)")
    else:
        html = termlist_path.read_text(encoding="utf-8")

        html = set_meta_pill(html, "Classes",    totals["classes"])
        html = set_meta_pill(html, "Properties", totals["props"])
        html = set_meta_pill(html, "Concepts",   totals["concepts"])
        html = set_termlist_total(html, total_terms)

        termlist_path.write_text(html, encoding="utf-8")
        print(f"  ✓ Updated {termlist_path.name}")

    # ── 4. ARCHITECTURE.md ─────────────────────────────────────
    print()
    print("Patching ARCHITECTURE.md \u2026")
    patch_architecture_md(
        docs_dir / "ARCHITECTURE.md",
        module_counts, totals, total_terms,
        dry_run=args.dry_run
    )

    # ── 5. ARCHITECTURE.html ────────────────────────────────────
    print()
    print("Patching ARCHITECTURE.html \u2026")
    patch_architecture_html(
        docs_dir / "ARCHITECTURE.html",
        module_counts, totals, total_terms,
        dry_run=args.dry_run
    )

    print()
    print("Done.")


if __name__ == "__main__":
    main()
