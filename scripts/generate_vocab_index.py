#!/usr/bin/env python3
"""
generate_vocab_index.py — Generate the full Iroko Framework vocabulary index.

Reads all 16 TTL modules and produces a single-page HTML index of every
class, property, and concept — with a live search filter, type facets,
module facets, and direct anchor links into the individual browse pages.

Usage:
    python generate_vocab_index.py                  # writes vocab/iroko-termlist.html
    python generate_vocab_index.py --output PATH    # write to explicit path
    python generate_vocab_index.py --ttl-dir DIR    # read TTLs from DIR

The output page links at the bottom of index.html under "Full Vocabulary Index."
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from rdflib import Graph, RDF, OWL, SKOS, Namespace
    from rdflib.namespace import RDFS, DCTERMS
except ImportError:
    print("ERROR: rdflib not found. Install with: pip install rdflib --break-system-packages")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Module registry
# ---------------------------------------------------------------------------

IROKO = Namespace("https://ontology.irokosociety.org/iroko#")

MODULES = [
    # (display_name, tier, tag_label, ns, ttl_stem)
    ("Core",          "Foundation",     "Core",          "https://ontology.irokosociety.org/iroko#",          "iroko-core"),
    ("Agency",        "Governance",     "Agency",        "https://ontology.irokosociety.org/iroko#",        "iroko-agency"),
    ("Authority",     "Governance",     "Authority",     "https://ontology.irokosociety.org/iroko#",     "iroko-authority"),
    ("Epistemic",     "Governance",     "Epistemic",     "https://ontology.irokosociety.org/iroko#",     "iroko-epistemic"),
    ("Narrative",     "Governance",     "Narrative",     "https://ontology.irokosociety.org/iroko#",     "iroko-narrative"),
    ("Manifestation", "Governance",     "Manifestation", "https://ontology.irokosociety.org/iroko#", "iroko-manifestation"),
    ("Ewé",           "Domain",         "Botanical",     "https://ontology.irokosociety.org/iroko#",           "iroko-ewe"),
    ("Nkisi",         "Domain",         "Entities",      "https://ontology.irokosociety.org/iroko#",         "iroko-nkisi"),
    ("Travay",        "Domain",         "Ritual",        "https://ontology.irokosociety.org/iroko#",        "iroko-travay"),
    ("Ilé",           "Domain",         "Lineage",       "https://ontology.irokosociety.org/iroko#",           "iroko-ile"),
    ("Marca",         "Domain",         "Divination",    "https://ontology.irokosociety.org/iroko#",         "iroko-marca"),
    ("Ékpè",          "Domain",         "Societies",     "https://ontology.irokosociety.org/iroko#",          "iroko-ekpe"),
    ("Vèvè",          "Domain",         "Graphic",       "https://ontology.irokosociety.org/iroko#",          "iroko-veve"),
    ("Ngoma",         "Domain",         "Music",         "https://ontology.irokosociety.org/iroko#",         "iroko-ngoma"),
    ("Sankofa",       "Domain",         "Movements",     "https://ontology.irokosociety.org/iroko#",       "iroko-sankofa"),
    ("Qal",           "Domain",         "Language",      "https://ontology.irokosociety.org/iroko#",           "iroko-qal"),

    # Uncomment to include PROV-O alignment terms in the index
    # ("PROV-O Alignment", "Foundation", "Alignment", "https://ontology.irokosociety.org/iroko#", "iroko-align-prov"),
]

# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def first_sentence(text: str, maxlen: int = 75) -> str:
    """Return the first sentence of text, truncated to maxlen chars."""
    if not text:
        return ""
    text = text.strip().replace("\n", " ")
    # Split on sentence boundary
    match = re.search(r"(?<=[.!?])\s", text)
    sent = text[: match.start() + 1] if match else text
    if len(sent) <= maxlen:
        return sent
    # Truncate at word boundary
    return sent[: maxlen - 1].rsplit(" ", 1)[0] + "…"


def best_label(g, uri) -> str:
    """Return the best short label for a URI: rdfs:label → local name."""
    label = g.value(uri, RDFS.label)
    if label:
        return str(label)
    return str(uri).rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def best_def(g, uri) -> str:
    """Return first sentence of the best available definition."""
    for pred in (RDFS.comment, DCTERMS.description, SKOS.definition, RDFS.label):
        val = g.value(uri, pred)
        if val:
            return first_sentence(str(val))
    return ""


def local_id(uri: str) -> str:
    """Return the local name part of a URI."""
    return uri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]


def anchor(term_type: str, term_id: str) -> str:
    """Return the anchor fragment used in generated browse pages."""
    prefix = {"Class": "cls", "Property": "prop", "Concept": "concept"}[term_type]
    return f"{prefix}-{term_id}"


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

def extract_terms(ttl_path: Path, mod_name: str, ns: str) -> list[dict]:
    """Extract all classes, properties, and concepts from one TTL file."""
    g = Graph()
    g.parse(str(ttl_path), format="turtle")

    terms = []

    # Classes
    for uri in g.subjects(RDF.type, OWL.Class):
        if not str(uri).startswith(ns):
            continue
        tid = local_id(str(uri))
        terms.append({
            "id": tid,
            "label": best_label(g, uri),
            "type": "Class",
            "module": mod_name,
            "definition": best_def(g, uri),
        })

    # Properties
    for ptype in (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty):
        for uri in g.subjects(RDF.type, ptype):
            if not str(uri).startswith(ns):
                continue
            tid = local_id(str(uri))
            terms.append({
                "id": tid,
                "label": best_label(g, uri),
                "type": "Property",
                "module": mod_name,
                "definition": best_def(g, uri),
            })

    # Concepts (SKOS)
    for uri in g.subjects(SKOS.inScheme, None):
        if not str(uri).startswith(ns):
            continue
        tid = local_id(str(uri))
        definition = ""
        for pred in (SKOS.definition, SKOS.prefLabel, RDFS.label):
            val = g.value(uri, pred)
            if val and pred == SKOS.definition:
                definition = first_sentence(str(val))
                break
            elif val and pred != SKOS.definition:
                definition = str(val)
        terms.append({
            "id": tid,
            "label": best_label(g, uri),
            "type": "Concept",
            "module": mod_name,
            "definition": definition,
        })

    return terms


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

PAGE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Full Vocabulary Index — Iroko Framework</title>
  <link rel="stylesheet" href="../assets/iroko-style.css">
  <style>
    /* ── Index page overrides ───────────────────────────────────────── */
    .index-hero {{
      padding: 2rem 0 1.5rem;
      border-bottom: 1px solid var(--border);
      margin-bottom: 1.5rem;
    }}
    .index-hero h1 {{ font-size: 1.6rem; margin-bottom: .4rem; }}
    .index-hero p  {{ font-size: .85rem; color: var(--ink-soft); max-width: 70ch; }}

    /* ── Controls bar ───────────────────────────────────────────────── */
    .controls {{
      display: flex;
      gap: .75rem;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: 1.25rem;
    }}
    .search-box {{
      flex: 1 1 260px;
      padding: .45rem .75rem;
      border: 1px solid var(--border);
      border-radius: 5px;
      font-size: .85rem;
      background: var(--surface);
      color: var(--ink);
      font-family: inherit;
    }}
    .search-box:focus {{ outline: 2px solid var(--accent); outline-offset: 1px; }}

    .facet-group {{
      display: flex;
      gap: .35rem;
      flex-wrap: wrap;
    }}
    .facet-btn {{
      padding: .3rem .65rem;
      border: 1px solid var(--border);
      border-radius: 4px;
      font-size: .75rem;
      cursor: pointer;
      background: var(--surface);
      color: var(--ink-soft);
      font-family: inherit;
      transition: background .1s, color .1s, border-color .1s;
    }}
    .facet-btn:hover  {{ border-color: var(--accent); color: var(--accent); }}
    .facet-btn.active {{
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }}
    .result-count {{
      font-size: .78rem;
      color: var(--ink-soft);
      margin-left: auto;
      white-space: nowrap;
    }}

    /* ── Table ──────────────────────────────────────────────────────── */
    .vocab-index-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: .82rem;
    }}
    .vocab-index-table thead th {{
      text-align: left;
      padding: .5rem .75rem;
      border-bottom: 2px solid var(--border);
      font-size: .72rem;
      font-weight: 700;
      letter-spacing: .04em;
      text-transform: uppercase;
      color: var(--ink-soft);
      background: var(--surface);
      position: sticky;
      top: 0;
      z-index: 1;
    }}
    .vocab-index-table tbody tr {{
      border-bottom: 1px solid var(--border);
      transition: background .08s;
    }}
    .vocab-index-table tbody tr:hover {{ background: var(--surface); }}
    .vocab-index-table tbody tr.hidden {{ display: none; }}
    .vocab-index-table td {{
      padding: .45rem .75rem;
      vertical-align: top;
    }}
    .term-link {{
      font-family: var(--mono);
      font-size: .8rem;
      font-weight: 600;
      color: var(--accent);
      text-decoration: none;
    }}
    .term-link:hover {{ text-decoration: underline; }}
    .term-label {{
      font-size: .75rem;
      color: var(--ink-soft);
      margin-top: .1rem;
    }}

    /* Type badges */
    .type-badge {{
      display: inline-block;
      padding: .15rem .45rem;
      border-radius: 3px;
      font-size: .65rem;
      font-weight: 700;
      letter-spacing: .03em;
      white-space: nowrap;
    }}
    .type-class    {{ background: #e8f0e8; color: #2a5c1e; }}
    .type-property {{ background: #e8eaf6; color: #3949ab; }}
    .type-concept  {{ background: #fef3e2; color: #8a5a00; }}

    /* Module tag — reuse existing tag-* classes from iroko-style.css */
    .mod-link {{
      font-size: .75rem;
      text-decoration: none;
      color: var(--ink-soft);
    }}
    .mod-link:hover {{ color: var(--accent); }}

    .def-cell {{ color: var(--ink); max-width: 40ch; }}

    .no-results {{
      text-align: center;
      padding: 3rem;
      color: var(--ink-soft);
      font-size: .9rem;
    }}
  </style>
</head>
<body>

<div class="top-bar">
  <span class="top-bar-id">
    <img class="top-bar-logo" src="../assets/IHS-Logo.jpg" alt="Iroko Historical Society">
    Iroko Historical Society · Iroko Framework
  </span>
  <nav class="top-bar-links">
    <a href="../index.html">Home</a>
    <a href="https://www.irokosociety.org/" target="_blank" rel="noopener">IHS ↗</a>
    <a href="https://medjat.irokosociety.org/">Per Medjat</a>
    <a href="../whitepaper/">White Paper</a>
    <a href="../docs/">Docs</a>
    <a href="https://github.com/iroko-framework/iroko-framework" target="_blank" rel="noopener">GitHub ↗</a>
  </nav>
</div>

  <nav class="breadcrumb page-wrap">
    <a href="../index.html">Iroko Framework</a>
    <span>/</span>
    <a href="index.html">Vocabularies</a>
    <span>/</span>
    Full Index
  </nav>

  <div class="page-wrap">

    <div class="index-hero">
      <a href="../index.html">
        <img src="../assets/IHS-Logo.jpg" alt="Iroko Historical Society — Home"
             style="width:72px;height:auto;display:block;margin-bottom:1rem;">
      </a>
      <h1>Full Vocabulary Index</h1>
      <p>Every class, property, and concept across all 16 Iroko Framework modules —
         {total_terms:,} terms total. Links go directly to the term's definition
         on its module browse page.</p>
      <div class="header-meta" style="margin-top:.75rem;">
        <span class="meta-pill">v1.3.0</span>
        <span class="meta-pill">{n_classes} Classes</span>
        <span class="meta-pill">{n_props} Properties</span>
        <span class="meta-pill">{n_concepts} Concepts</span>
        <span class="meta-pill">16 Modules</span>
      </div>
    </div>

    <!-- Controls -->
    <div class="controls">
      <input class="search-box" type="search" id="termSearch"
             placeholder="Search terms, definitions…" autocomplete="off"
             aria-label="Filter vocabulary terms">

      <div class="facet-group" id="typeFacets" aria-label="Filter by type">
        <button class="facet-btn active" data-type="all">All types</button>
        <button class="facet-btn" data-type="Class">Classes</button>
        <button class="facet-btn" data-type="Property">Properties</button>
        <button class="facet-btn" data-type="Concept">Concepts</button>
      </div>

      <div class="facet-group" id="modFacets" aria-label="Filter by tier">
        <button class="facet-btn active" data-tier="all">All modules</button>
        <button class="facet-btn" data-tier="Foundation">Foundation</button>
        <button class="facet-btn" data-tier="Governance">Governance</button>
        <button class="facet-btn" data-tier="Domain">Domain</button>
      </div>

      <span class="result-count" id="resultCount">{total_terms:,} terms</span>
    </div>

    <!-- Index table -->
    <table class="vocab-index-table" id="vocabTable">
      <thead>
        <tr>
          <th style="width:22%">Term</th>
          <th style="width:10%">Type</th>
          <th style="width:14%">Module</th>
          <th>Meaning</th>
        </tr>
      </thead>
      <tbody id="vocabBody">
{rows}
      </tbody>
    </table>

    <div class="no-results" id="noResults" style="display:none;">
      No terms match your search.
    </div>

  </div><!-- /page-wrap -->

  <footer class="site-footer page-wrap">
    <div class="footer-left">
      Iroko Historical Society<br>
      Postcustodial Digital Archives for Afro-Atlantic Cultural Materials<br>
      License: CC0 1.0 Universal (Public Domain)
      <div class="footer-iao">Ilé Añá Olofí, Inc. 501(c)(3) · <a href="https://ileanaolofi.org" target="_blank" rel="noopener">ileanaolofi.org</a></div>
    </div>
    <div class="footer-links">
      <a href="https://www.irokosociety.org/" target="_blank" rel="noopener">IHS ↗</a>
      <a href="../index.html">Home</a>
      <a href="https://medjat.irokosociety.org/">Per Medjat</a>
      <a href="index.html">Vocabularies</a>
    </div>
  </footer>

  <script>
    // ── Live filter ───────────────────────────────────────────────────────
    const searchInput  = document.getElementById('termSearch');
    const resultCount  = document.getElementById('resultCount');
    const noResults    = document.getElementById('noResults');
    const tbody        = document.getElementById('vocabBody');
    const rows         = Array.from(tbody.querySelectorAll('tr'));

    let activeType = 'all';
    let activeTier = 'all';

    function applyFilters() {{
      const q = searchInput.value.toLowerCase().trim();
      let visible = 0;

      rows.forEach(row => {{
        const termText = (row.dataset.term + ' ' + row.dataset.def).toLowerCase();
        const typeOk = activeType === 'all' || row.dataset.type === activeType;
        const tierOk = activeTier === 'all' || row.dataset.tier === activeTier;
        const textOk = !q || termText.includes(q);

        if (typeOk && tierOk && textOk) {{
          row.classList.remove('hidden');
          visible++;
        }} else {{
          row.classList.add('hidden');
        }}
      }});

      resultCount.textContent = visible.toLocaleString() + ' term' + (visible !== 1 ? 's' : '');
      noResults.style.display = visible === 0 ? 'block' : 'none';
    }}

    // Search input
    searchInput.addEventListener('input', applyFilters);

    // Type facets
    document.getElementById('typeFacets').addEventListener('click', e => {{
      const btn = e.target.closest('.facet-btn');
      if (!btn) return;
      document.querySelectorAll('#typeFacets .facet-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeType = btn.dataset.type;
      applyFilters();
    }});

    // Module tier facets
    document.getElementById('modFacets').addEventListener('click', e => {{
      const btn = e.target.closest('.facet-btn');
      if (!btn) return;
      document.querySelectorAll('#modFacets .facet-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeTier = btn.dataset.tier;
      applyFilters();
    }});
  </script>

</body>
</html>
"""

ROW_TEMPLATE = """\
        <tr data-term="{term_key}" data-def="{def_key}" data-type="{term_type}" data-tier="{tier}">
          <td>
            <a class="term-link" href="{browse_url}">{term_id}</a>
            {label_html}
          </td>
          <td><span class="type-badge type-{type_lower}">{term_type}</span></td>
          <td>
            <a class="mod-link" href="{mod_url}">{mod_name}</a>
          </td>
          <td class="def-cell">{definition}</td>
        </tr>"""


def html_escape(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def build_rows(all_terms: list[dict], mod_browse_urls: dict) -> str:
    lines = []
    for t in all_terms:
        mod_name = t["module"]
        term_id  = t["id"]
        term_type = t["type"]
        tier     = t["tier"]
        defn     = html_escape(t["definition"])
        label    = t["label"]

        browse_html = mod_browse_urls.get(mod_name, "index.html")
        frag = anchor(term_type, term_id)
        browse_url = f"{browse_html}#{frag}"

        # Suppress label if it's just the ID (camelCase == same as local name)
        label_html = ""
        if label and label.lower() != term_id.lower():
            label_html = f'<div class="term-label">{html_escape(label)}</div>'

        mod_url = browse_html

        lines.append(ROW_TEMPLATE.format(
            term_key   = html_escape(term_id.lower() + " " + label.lower()),
            def_key    = html_escape(t["definition"].lower()[:100]),
            term_type  = html_escape(term_type),
            type_lower = term_type.lower(),
            tier       = html_escape(tier),
            browse_url = browse_url,
            term_id    = html_escape(term_id),
            label_html = label_html,
            mod_name   = html_escape(mod_name),
            mod_url    = html_escape(mod_url),
            definition = defn,
        ))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate the Iroko Framework full vocabulary index page."
    )
    p.add_argument("--output", "-o", metavar="PATH",
                   help="Output HTML path (default: vocab/iroko-termlist.html alongside TTLs)")
    p.add_argument("--ttl-dir", metavar="DIR",
                   help="Directory containing the .ttl files (default: same dir as this script's parent/vocab/)")
    return p


def main():
    args = build_parser().parse_args()

    script_dir = Path(__file__).resolve().parent

    # Locate TTL files
    if args.ttl_dir:
        ttl_dir = Path(args.ttl_dir)
    else:
        # Try a few sensible locations
        candidates = [
            script_dir.parent / "vocab",
            script_dir / "vocab",
            script_dir,
            Path.cwd() / "vocab",
            Path.cwd(),
        ]
        ttl_dir = next((d for d in candidates if (d / "iroko-core.ttl").exists()), None)
        if ttl_dir is None:
            print("ERROR: Cannot find iroko-core.ttl. Use --ttl-dir to specify location.")
            sys.exit(1)

    # Locate output path
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = ttl_dir / "iroko-termlist.html"

    print(f"Reading TTLs from: {ttl_dir}")
    print(f"Writing index to:  {out_path}")

    # Module browse URL map (relative to vocab/ directory)
    mod_browse_urls = {mod_name: f"{stem}.html"
                       for mod_name, _, _, _, stem in MODULES}

    # Extract all terms
    all_terms = []
    for mod_name, tier, tag_label, ns, stem in MODULES:
        ttl_path = ttl_dir / f"{stem}.ttl"
        if not ttl_path.exists():
            print(f"  ⚠ Not found, skipping: {ttl_path.name}")
            continue
        terms = extract_terms(ttl_path, mod_name, ns)
        for t in terms:
            t["tier"] = tier
        all_terms.extend(terms)
        print(f"  ✓ {stem:<24} {len(terms):>4} terms")

    # Sort alphabetically by term ID, then by module within ties
    all_terms.sort(key=lambda t: (t["id"].lower(), t["module"]))

    # Counts
    n_classes  = sum(1 for t in all_terms if t["type"] == "Class")
    n_props    = sum(1 for t in all_terms if t["type"] == "Property")
    n_concepts = sum(1 for t in all_terms if t["type"] == "Concept")
    total      = len(all_terms)

    rows_html = build_rows(all_terms, mod_browse_urls)

    page = PAGE_HTML.format(
        total_terms = total,
        n_classes   = n_classes,
        n_props     = n_props,
        n_concepts  = n_concepts,
        rows        = rows_html,
    )

    out_path.write_text(page, encoding="utf-8")
    print(f"\nDone. {total:,} terms indexed ({n_classes} classes, {n_props} properties, {n_concepts} concepts).")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
