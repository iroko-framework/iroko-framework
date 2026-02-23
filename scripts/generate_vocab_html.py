#!/usr/bin/env python3
"""
Generate human-readable HTML documentation from Turtle vocabulary files.
Uses iroko-style.css and the current Iroko Framework browse page structure.

Usage:
    python generate_vocab_html.py              # processes all configured .ttl in vocab/
    python generate_vocab_html.py iroko-ile    # process one file by stem
    python generate_vocab_html.py iroko-agency iroko-authority  # multiple stems

TTLs intentionally excluded (no MODULE_CONFIG entry):
  iroko-align-prov   — reference-only PROV-O alignment; 0 user-facing terms
  iroko-nkisi-patch  — broken syntax, superseded
  ewe-plants-v0_2_1  — legacy instance data file, not a vocabulary
  iroko-vocab-v0_2_1 — superseded version
"""

from rdflib import Graph, Namespace, RDF, RDFS, OWL, SKOS, URIRef
from rdflib.namespace import DCTERMS
from pathlib import Path
import sys
import html

IROKO = Namespace("https://www.irokosociety.org/iroko-framework/core#")

# ---------------------------------------------------------------------------
# MODULE_CONFIG
# Keys = TTL filename stem. tag_cls must match a .tag-* class in iroko-style.css.
# ---------------------------------------------------------------------------
MODULE_CONFIG = {

    # Layer 0 — Core
    "iroko-core": {
        "title":    "Core Vocabulary",
        "subtitle": "Cross-module governance infrastructure",
        "tag_cls":  "tag-core",
        "tag_text": "Core",
        "prefix":   "iroko:",
    },
    "iroko-core-v2": {
        "title":    "Core Vocabulary v2.0",
        "subtitle": "Assertion model · Temporal variation · Narrative spine · Access policies",
        "tag_cls":  "tag-core",
        "tag_text": "Core",
        "prefix":   "iroko:",
    },

    # Layer 1 — Infrastructure modules (cross-cutting)
    "iroko-agency": {
        "title":    "Agency Module — Sacred Agents & Events",
        "subtitle": "Sovereignty-aligned agency model: spirits, ritual events, authorization chains",
        "tag_cls":  "tag-agency",
        "tag_text": "Agency",
        "prefix":   "ag:",
    },
    "iroko-authority": {
        "title":    "Authority Module — Ritual Governance",
        "subtitle": "Authority types, jurisdictions, basis, and recognition networks",
        "tag_cls":  "tag-authority",
        "tag_text": "Authority",
        "prefix":   "auth:",
    },
    "iroko-epistemic": {
        "title":    "Epistemic Module — Knowledge Gating",
        "subtitle": "Disclosure constraints, permissions, and epistemic governance",
        "tag_cls":  "tag-epistemic",
        "tag_text": "Epistemic",
        "prefix":   "ep:",
    },
    "iroko-narrative": {
        "title":    "Narrative Module — Sacred Story Systems",
        "subtitle": "Transmission chains, variant relations, kinship claims, interpretive stances",
        "tag_cls":  "tag-narrative",
        "tag_text": "Narrative",
        "prefix":   "narr:",
    },

    # Layer 2 — Domain modules
    "iroko-ewe": {
        "title":    "Ewé Module — Sacred Plant Knowledge",
        "subtitle": "Ritual use governance over botanical data",
        "tag_cls":  "tag-botanical",
        "tag_text": "Botanical",
        "prefix":   "ewe:",
    },
    "iroko-nkisi": {
        "title":    "Nkisi Module — Spiritual Entities",
        "subtitle": "Spiritual entities and kinship across traditions",
        "tag_cls":  "tag-entities",
        "tag_text": "Entities",
        "prefix":   "nkisi:",
    },
    "iroko-travay": {
        "title":    "Travay Module — Ritual Processes",
        "subtitle": "Ritual processes, ceremonies, and initiatory rites",
        "tag_cls":  "tag-ritual",
        "tag_text": "Ritual",
        "prefix":   "travay:",
    },
    "iroko-ile": {
        "title":    "Ilé Module — Houses, Lineage & Religious Office",
        "subtitle": "Religious institutions, initiation genealogy, and office transmission",
        "tag_cls":  "tag-lineage",
        "tag_text": "Lineage",
        "prefix":   "ile:",
    },
    "iroko-ile-v2": {
        "title":    "Ilé Module v2 — Houses, Lineage & Religious Office",
        "subtitle": "ile:Authority renamed to ile:ReligiousOffice; aligned with authority module",
        "tag_cls":  "tag-lineage",
        "tag_text": "Lineage",
        "prefix":   "ile:",
    },
    "iroko-marca": {
        "title":    "Marca Module — Divination Systems",
        "subtitle": "Sacred signs, reading records, and verse corpora",
        "tag_cls":  "tag-divination",
        "tag_text": "Divination",
        "prefix":   "marca:",
    },
    "iroko-ekpe": {
        "title":    "Ékpè Module — Initiatory Societies",
        "subtitle": "Graded societies, esoteric governance, and masquerade traditions",
        "tag_cls":  "tag-societies",
        "tag_text": "Society",
        "prefix":   "ekpe:",
    },
    "iroko-veve": {
        "title":    "Vèvè Module — Graphic Sign Systems",
        "subtitle": "Sacred diagrams, signs, and esoteric scripts",
        "tag_cls":  "tag-graphic",
        "tag_text": "Graphic",
        "prefix":   "veve:",
    },
    "iroko-ngoma": {
        "title":    "Ngoma Module — Sacred Music",
        "subtitle": "Rhythms, songs, instruments, and musician lineages",
        "tag_cls":  "tag-music",
        "tag_text": "Music",
        "prefix":   "ngoma:",
    },
    "iroko-sankofa": {
        "title":    "Sankofa Module — Reclamation Movements",
        "subtitle": "Diaspora returns and reconstructed practice",
        "tag_cls":  "tag-upcoming",
        "tag_text": "Movements",
        "prefix":   "sankofa:",
    },
    "iroko-qal": {
        "title":    "Qal Module — Sacred Lexicons",
        "subtitle": "Liturgical language and esoteric terminology",
        "tag_cls":  "tag-language",
        "tag_text": "Language",
        "prefix":   "qal:",
    },
}

ACCESS_MAP = {
    "access-public-unrestricted":     ("access-public",    "Public"),
    "access-public-no-amplification": ("access-public",    "Public · No Amplification"),
    "access-community-only":          ("access-community", "Community Only"),
    "access-initiated-only":          ("access-initiated", "Initiated Only"),
    "access-initiated-elder":         ("access-initiated", "Initiated Elder"),
    "access-no-access":               ("access-none",      "No Access"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def h(text):
    return html.escape(str(text), quote=True)

def local(uri):
    uri = str(uri)
    return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]

def label_en(g, subject, predicate):
    """Return first @en literal for predicate on subject, or any lang, or local name."""
    if subject is None:
        return "—"
    en = fallback = None
    for obj in g.objects(subject, predicate):
        lang = getattr(obj, "language", None)
        val  = str(obj)
        if lang == "en":
            en = val
        elif fallback is None:
            fallback = val
    return en or fallback or local(str(subject))

def pref_label_en(g, s):  return label_en(g, s, SKOS.prefLabel)
def rdfs_label_en(g, s):  return label_en(g, s, RDFS.label)
def comment_en(g, s):     return label_en(g, s, RDFS.comment) if s else ""
def definition_en(g, s):  return label_en(g, s, SKOS.definition) if s else ""

def description_en(g, subject):
    """Pull dcterms:description preferring @en, fallback any lang."""
    en = fallback = None
    for obj in g.objects(subject, DCTERMS.description):
        lang = getattr(obj, "language", None)
        val  = str(obj)
        if lang == "en":
            en = val
        elif fallback is None:
            fallback = val
    return en or fallback or ""

def resolve_label(g, uri):
    """Resolve a domain/range URI to its label — tries this graph first, then local name."""
    if uri is None:
        return "—"
    label = g.value(uri, RDFS.label) or g.value(uri, SKOS.prefLabel)
    return str(label) if label else local(str(uri))

def access_badge(access_uri):
    key = local(str(access_uri))
    if key in ACCESS_MAP:
        css, lbl = ACCESS_MAP[key]
        return f'<span class="access-badge {css}">{h(lbl)}</span>'
    return ""


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def get_meta(g):
    uri = next(g.subjects(RDF.type, OWL.Ontology), None)
    if not uri:
        return {}
    return {
        "uri":      str(uri),
        "desc":     description_en(g, uri),
        "version":  str(g.value(uri, OWL.versionInfo) or "1.0.0"),
        "issued":   str(g.value(uri, DCTERMS.issued)   or ""),
        "modified": str(g.value(uri, DCTERMS.modified) or ""),
    }

def get_classes(g):
    out = []
    for cls in g.subjects(RDF.type, OWL.Class):
        supers = [resolve_label(g, s) for s in g.objects(cls, RDFS.subClassOf)]
        out.append({
            "id":      local(str(cls)),
            "label":   rdfs_label_en(g, cls),
            "comment": comment_en(g, cls),
            "supers":  supers,
        })
    return sorted(out, key=lambda x: x["label"])

def get_properties(g):
    out = []
    for ptype, plabel in [(OWL.ObjectProperty, "Object"),
                          (OWL.DatatypeProperty, "Datatype"),
                          (OWL.AnnotationProperty, "Annotation")]:
        for prop in g.subjects(RDF.type, ptype):
            access_uri = g.value(prop, IROKO.minimumAccessLevel)
            out.append({
                "id":         local(str(prop)),
                "label":      rdfs_label_en(g, prop),
                "comment":    comment_en(g, prop),
                "type":       plabel,
                "domain":     resolve_label(g, g.value(prop, RDFS.domain)),
                "range":      resolve_label(g, g.value(prop, RDFS.range)),
                "access_uri": str(access_uri) if access_uri else "",
            })
    return sorted(out, key=lambda x: x["label"])

def get_schemes(g):
    out = []
    for scheme in g.subjects(RDF.type, SKOS.ConceptScheme):
        # Try dcterms:description first (used in all Iroko TTLs), then skos:definition
        desc = description_en(g, scheme) or definition_en(g, scheme)
        concepts = []
        for concept in g.subjects(SKOS.inScheme, scheme):
            concepts.append({
                "id":         local(str(concept)),
                "label":      pref_label_en(g, concept),
                "definition": definition_en(g, concept),
                "alt_labels": [str(o) for o in g.objects(concept, SKOS.altLabel)
                               if getattr(o, "language", None) == "en"],
                "scope_note": str(g.value(concept, SKOS.scopeNote) or ""),
            })
        out.append({
            "id":       local(str(scheme)),
            "label":    rdfs_label_en(g, scheme),
            "desc":     desc,
            "concepts": sorted(concepts, key=lambda x: x["label"]),
        })
    return sorted(out, key=lambda x: x["label"])


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def generate_html(ttl_path, output_path, cfg):
    print(f"  Processing {ttl_path.name} …")
    g = Graph()
    try:
        g.parse(str(ttl_path), format="turtle")
    except Exception as e:
        print(f"  ERROR parsing {ttl_path}: {e}")
        return False

    meta    = get_meta(g)
    classes = get_classes(g)
    props   = get_properties(g)
    schemes = get_schemes(g)

    ns_uri   = meta.get("uri", "")
    ns_pfx   = ns_uri + "#" if ns_uri and not ns_uri.endswith("#") else ns_uri
    version  = meta.get("version", "1.0.0")
    title    = cfg["title"]
    subtitle = cfg["subtitle"]
    tag_cls  = cfg["tag_cls"]
    tag_text = cfg["tag_text"]
    prefix   = cfg["prefix"]
    ttl_name = ttl_path.name
    n_concepts = sum(len(s["concepts"]) for s in schemes)

    # Footer date line
    issued   = meta.get("issued", "")
    modified = meta.get("modified", "")
    date_str = ""
    if issued:
        date_str = f"Issued {issued}"
        if modified:
            date_str += f" · Revised {modified}"

    out = []
    W = out.append

    # ── <head> + top-bar ──────────────────────────────────────────────────
    W(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{h(title)} — Iroko Framework Vocabularies</title>
  <link rel="stylesheet" href="../assets/iroko-style.css">
</head>
<body>

<div class="top-bar">
  <span class="top-bar-id">Iroko Historical Society · Iroko Framework v{h(version)}</span>
  <nav class="top-bar-links">
    <a href="../index.html">Home</a>
    <a href="index.html">Vocabularies</a>
    <a href="https://www.irokosociety.org/iroko-framework">irokosociety.org ↗</a>
    <a href="https://github.com/iroko-framework/iroko-framework">GitHub ↗</a>
  </nav>
</div>

<div class="page-wrap">

  <p class="breadcrumb">
    <a href="../index.html">Iroko Framework</a>
    <span>/</span>
    <a href="index.html">Vocabularies</a>
    <span>/</span>
    {h(title)}
  </p>

  <header class="vocab-header">
    <div class="vocab-header-logo">
      <img src="../assets/IHS-Logo.jpg" alt="Iroko Historical Society">
    </div>
    <div>
      <span class="module-tag {h(tag_cls)}">{h(tag_text)}</span>
      <h1>{h(title)}</h1>
      <p class="subtitle">{h(subtitle)}</p>
      <div class="header-meta">
        <span class="meta-pill">{h(prefix)}&nbsp;&nbsp;{h(ns_pfx)}</span>
        <span class="meta-pill">v{h(version)}</span>
        <span class="meta-pill"><a href="{h(ttl_name)}" style="color:inherit;">Download TTL ↓</a></span>
        <span class="meta-pill"><a href="https://github.com/iroko-framework/iroko-framework" style="color:inherit;">GitHub ↗</a></span>
      </div>
    </div>
  </header>

  <div style="margin-top:1.5rem;">
    <p class="module-desc" style="max-width:80ch;margin-top:1.5rem;">{h(meta.get("desc",""))}</p>
    <div class="module-stats" style="margin-top:1rem;">
      <div class="stat-cell"><span class="stat-n">{len(classes)}</span><span class="stat-label">Classes</span></div>
      <div class="stat-cell"><span class="stat-n">{len(props)}</span><span class="stat-label">Properties</span></div>
      <div class="stat-cell"><span class="stat-n">{len(schemes)}</span><span class="stat-label">Schemes</span></div>
      <div class="stat-cell"><span class="stat-n">{n_concepts}</span><span class="stat-label">Concepts</span></div>
    </div>
  </div>""")

    # ── Classes ───────────────────────────────────────────────────────────
    if classes:
        W(f"""
  <div class="term-section">
    <div class="term-section-header">
      <span class="term-section-title">Classes</span>
      <span class="term-section-count">{len(classes)} class{"es" if len(classes)!=1 else ""}</span>
    </div>""")
        for cls in classes:
            hier = ""
            if cls["supers"]:
                hier = ('<div class="class-hierarchy">Subclass of: '
                        + ", ".join(f'<span style="color:var(--green-mid)">{h(s)}</span>'
                                    for s in cls["supers"])
                        + "</div>")
            W(f"""    <div class="class-card">
      <div class="class-name">{h(cls["id"])}</div>
      <div style="font-family:var(--serif);font-size:.95rem;font-weight:600;color:var(--ink);margin-top:.1rem;">{h(cls["label"])}</div>
      {hier}
      <p class="class-def">{h(cls["comment"])}</p>
    </div>""")
        W("  </div>")

    # ── Properties ────────────────────────────────────────────────────────
    if props:
        W(f"""
  <div class="term-section">
    <div class="term-section-header">
      <span class="term-section-title">Properties</span>
      <span class="term-section-count">{len(props)} propert{"ies" if len(props)!=1 else "y"}</span>
    </div>
    <table class="prop-table">
      <thead>
        <tr>
          <th>Property</th>
          <th>Type</th>
          <th>Domain → Range</th>
          <th>Access</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>""")
        for prop in props:
            type_css = "prop-type-obj" if prop["type"] == "Object" else "prop-type-data"
            badge    = access_badge(prop["access_uri"]) if prop["access_uri"] else ""
            W(f"""        <tr>
          <td><span class="prop-name">{h(prop["id"])}</span><br><span style="font-size:.75rem;color:var(--ink-soft);">{h(prop["label"])}</span></td>
          <td style="white-space:nowrap;"><span class="prop-type-badge {type_css}">{h(prop["type"])}</span></td>
          <td class="prop-domain-range">{h(prop["domain"])} → {h(prop["range"])}</td>
          <td style="white-space:nowrap;">{badge}</td>
          <td class="prop-desc">{h(prop["comment"])}</td>
        </tr>""")
        W("""      </tbody>
    </table>
  </div>""")

    # ── Concept Schemes ───────────────────────────────────────────────────
    if schemes:
        W(f"""
  <div class="term-section">
    <div class="term-section-header">
      <span class="term-section-title">Concept Schemes</span>
      <span class="term-section-count">{len(schemes)} scheme{"s" if len(schemes)!=1 else ""}</span>
    </div>""")
        for scheme in schemes:
            W(f"""    <div class="scheme-block">
      <div class="scheme-header">
        <span class="scheme-name">{h(scheme["label"])}</span>
        <span class="scheme-count">{len(scheme["concepts"])} concept{"s" if len(scheme["concepts"])!=1 else ""}</span>
      </div>""")
            if scheme["desc"]:
                W(f'      <p style="padding:.6rem 1.2rem;font-size:.82rem;color:var(--ink-soft);border-bottom:1px solid var(--rule);">{h(scheme["desc"])}</p>')
            W('      <div class="concept-list">')
            for concept in scheme["concepts"]:
                W(f"""        <div class="concept-item">
          <div class="concept-label">{h(concept["label"])}</div>
          <div style="font-family:var(--mono);font-size:.6rem;color:var(--ink-soft);margin-top:.1rem;">{h(concept["id"])}</div>
          <p class="concept-def">{h(concept["definition"])}</p>""")
                if concept["alt_labels"]:
                    W(f'          <p style="font-size:.75rem;color:var(--ink-soft);margin-top:.2rem;">Also known as: {h(", ".join(concept["alt_labels"]))}</p>')
                if concept["scope_note"]:
                    W(f'          <p style="font-size:.75rem;color:var(--ink-soft);font-style:italic;margin-top:.2rem;">{h(concept["scope_note"])}</p>')
                W("        </div>")
            W("      </div>\n    </div>")
        W("  </div>")

    # ── Footer ────────────────────────────────────────────────────────────
    date_line = f"      {h(date_str)}<br>\n" if date_str else ""
    W(f"""
  <footer class="site-footer">
    <div class="footer-left">
      Iroko Historical Society<br>
      Postcustodial Digital Archives for Afro-Atlantic Cultural Materials<br>
{date_line}      License: CC0 1.0 Universal (Public Domain)
    </div>
    <div class="footer-links">
      <a href="https://www.irokosociety.org">irokosociety.org</a>
      <a href="../index.html">Home</a>
      <a href="index.html">Vocabularies</a>
    </div>
  </footer>

</div>
</body>
</html>""")

    output_path.write_text("\n".join(out), encoding="utf-8")
    print(f"  ✓ {output_path.name}  "
          f"({len(classes)} cls, {len(props)} prop, "
          f"{len(schemes)} sch, {n_concepts} concepts)")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    script_dir = Path(__file__).resolve().parent
    vocab_dir  = script_dir.parent / "vocab"
    if not vocab_dir.exists():
        vocab_dir = Path.cwd() / "vocab"
    if not vocab_dir.exists():
        print(f"ERROR: vocab/ directory not found (tried {vocab_dir})")
        sys.exit(1)

    if len(sys.argv) > 1:
        ttl_files = []
        for stem in sys.argv[1:]:
            p = vocab_dir / (stem if stem.endswith(".ttl") else stem + ".ttl")
            if not p.exists():
                print(f"ERROR: {p} not found")
                sys.exit(1)
            ttl_files.append(p)
    else:
        ttl_files = sorted(vocab_dir.glob("*.ttl"))

    if not ttl_files:
        print("No .ttl files found in vocab/")
        sys.exit(1)

    print(f"Found {len(ttl_files)} TTL file(s)\n")
    ok = err = skipped = 0

    for ttl_path in ttl_files:
        stem = ttl_path.stem
        cfg  = MODULE_CONFIG.get(stem)
        if cfg is None:
            print(f"  SKIPPED {ttl_path.name} — not in MODULE_CONFIG")
            skipped += 1
            continue
        if generate_html(ttl_path, ttl_path.with_suffix(".html"), cfg):
            ok += 1
        else:
            err += 1

    print(f"\n{'─'*55}")
    print(f"Done: {ok} generated, {err} errors, {skipped} skipped")


if __name__ == "__main__":
    main()
