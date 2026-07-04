#!/usr/bin/env python3
"""
generate_vocab_html.py  —  v8 rewrite
Generates v8-format interactive module pages for the Iroko Framework.

Each output page has:
  Zone 1  — class grid (clickable cards)
  Zone 2  — property panel (incoming left, outgoing right, always-visible defs)
  Zone 3  — concept scheme chips
  Sidebar — cross-module connections + share + BibTeX/RIS citation + format links

New in v8:
  - Cross-module incoming connection detection (scans all TTL files)
  - Inline JS CLASSES data object populated from actual TTL
  - iroko-style.css linked externally (no embedded palette)
  - Properties always-visible (no expand click)
  - BibTeX and RIS citation formats

Usage:
    python generate_vocab_html.py              # all modules
    python generate_vocab_html.py iroko-ewe    # single module
    python generate_vocab_html.py --vocab DIR  # explicit vocab path
"""

from rdflib import Graph, Namespace, RDF, RDFS, OWL, SKOS, URIRef, BNode
from rdflib.namespace import DCTERMS
from pathlib import Path
import sys, json, html as _html, re, argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Shared config: module registry, access map, version strings
from iroko_config import MODULE_CONFIG, ACCESS_MAP, KNOWN_SKIPS, FRAMEWORK_VERSION, IROKO_NS

IROKO = Namespace(IROKO_NS)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def h(t): return _html.escape(str(t), quote=True)
def local(uri):
    s = str(uri)
    return s.split("#")[-1] if "#" in s else s.split("/")[-1]

def label_en(g, s, pred):
    if s is None: return "—"
    en = fb = None
    for o in g.objects(s, pred):
        lang = getattr(o, "language", None)
        if lang == "en": en = str(o)
        elif fb is None: fb = str(o)
    return en or fb or local(str(s))

def comment_en(g, s):  return label_en(g, s, RDFS.comment)  if s else ""
def label_rdf(g, s):   return label_en(g, s, RDFS.label)    if s else ""
def pref_label(g, s):  return label_en(g, s, SKOS.prefLabel) if s else ""
def skos_def(g, s):    return label_en(g, s, SKOS.definition) if s else ""
def dcterms_desc(g, s):
    en = fb = None
    for o in g.objects(s, DCTERMS.description):
        lang = getattr(o, "language", None)
        if lang == "en": en = str(o)
        elif fb is None: fb = str(o)
    return en or fb or ""

def resolve_node(g, uri):
    """Resolve a domain or range URI to a readable string, handling owl:unionOf blank nodes."""
    if uri is None: return "—"
    if isinstance(uri, BNode):
        union = g.value(uri, OWL.unionOf)
        if union:
            members = []
            rest = union
            while rest and str(rest) != str(RDF.nil):
                first = g.value(rest, RDF.first)
                if first: members.append(local(str(first)))
                rest = g.value(rest, RDF.rest)
            if members: return " | ".join(members)
        return "—"
    lab = g.value(uri, RDFS.label) or g.value(uri, SKOS.prefLabel)
    return str(lab) if lab else local(str(uri))

def access_key(g, prop_uri):
    acc = g.value(prop_uri, IROKO.minimumAccessLevel)
    if acc is None: return ("pub", "Public")
    k = local(str(acc))
    return ACCESS_MAP.get(k, ("pub", "Public"))

def prop_type_key(ptype):
    if ptype == OWL.ObjectProperty: return "obj"
    if ptype == OWL.DatatypeProperty: return "data"
    return "ann"

# ---------------------------------------------------------------------------
# Cross-module index
# Scan all TTL files and build:
#   incoming_index[class_local_name] = [
#     {uri, label, type, access, def, domain, range, source_stem, source_title}
#   ]
# ---------------------------------------------------------------------------
def build_cross_module_index(all_ttl_paths):
    """
    For each property in every TTL, record its range as a key.
    Returns dict: local_class_name -> list of incoming property dicts.
    """
    index = {}  # class_local -> [prop_dict]

    for ttl_path in all_ttl_paths:
        stem = ttl_path.stem
        if stem in KNOWN_SKIPS or stem not in MODULE_CONFIG:
            continue
        g = Graph()
        try:
            g.parse(str(ttl_path), format="turtle")
        except Exception:
            continue

        cfg = MODULE_CONFIG[stem]
        mod_title = cfg["title"].split(" — ")[0]  # short name e.g. "Ewé Module"

        for ptype in (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty):
            for prop in g.subjects(RDF.type, ptype):
                if not str(prop).startswith(IROKO_NS):
                    continue
                range_uri = g.value(prop, RDFS.range)
                if range_uri is None or isinstance(range_uri, BNode):
                    continue
                if not str(range_uri).startswith(IROKO_NS):
                    continue
                range_local = local(str(range_uri))
                acc_key, acc_label = access_key(g, prop)
                entry = {
                    "uri":    "iroko:" + local(str(prop)),
                    "label":  label_rdf(g, prop) or local(str(prop)),
                    "type":   prop_type_key(ptype),
                    "access": acc_key,
                    "def":    comment_en(g, prop),
                    "domain": resolve_node(g, g.value(prop, RDFS.domain)),
                    "from":   "iroko:" + resolve_node(g, g.value(prop, RDFS.domain)),
                    "fromLabel": resolve_node(g, g.value(prop, RDFS.domain)),
                    "module": mod_title,
                    "stem":   stem,
                }
                index.setdefault(range_local, []).append(entry)

    return index


# ---------------------------------------------------------------------------
# Per-module extraction
# ---------------------------------------------------------------------------
def get_meta(g):
    ont = next(g.subjects(RDF.type, OWL.Ontology), None)
    if not ont: return {}
    return {
        "uri":      str(ont),
        "desc":     dcterms_desc(g, ont),
        "version":  str(g.value(ont, OWL.versionInfo) or "1.3.0"),
        "issued":   str(g.value(ont, DCTERMS.issued)   or ""),
        "modified": str(g.value(ont, DCTERMS.modified) or ""),
    }

def get_classes(g):
    out = []
    for cls in g.subjects(RDF.type, OWL.Class):
        if not str(cls).startswith(IROKO_NS): continue
        if isinstance(cls, BNode): continue
        supers = []
        for s in g.objects(cls, RDFS.subClassOf):
            if not isinstance(s, BNode):
                supers.append(local(str(s)))
        out.append({
            "id":      local(str(cls)),
            "label":   label_rdf(g, cls),
            "hint":    " · ".join(f"subClassOf {s}" for s in supers) if supers else "",
            "def":     comment_en(g, cls),
        })
    return sorted(out, key=lambda x: x["label"])

def get_outgoing(g, cls_local):
    """Properties where domain = this class (or union containing it)."""
    target_uri = URIRef(IROKO_NS + cls_local)
    out = []
    for ptype in (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty):
        for prop in g.subjects(RDF.type, ptype):
            if not str(prop).startswith(IROKO_NS): continue
            domain = g.value(prop, RDFS.domain)
            if domain is None: continue
            # Direct match
            dom_match = str(domain) == str(target_uri)
            # Union match
            if not dom_match and isinstance(domain, BNode):
                union = g.value(domain, OWL.unionOf)
                rest = union
                while rest and str(rest) != str(RDF.nil):
                    first = g.value(rest, RDF.first)
                    if first and str(first) == str(target_uri):
                        dom_match = True
                        break
                    rest = g.value(rest, RDF.rest)
            if not dom_match: continue
            acc_k, _ = access_key(g, prop)
            rng = g.value(prop, RDFS.range)
            out.append({
                "uri":    "iroko:" + local(str(prop)),
                "label":  label_rdf(g, prop),
                "type":   prop_type_key(ptype),
                "range":  resolve_node(g, rng),
                "access": acc_k,
                "def":    comment_en(g, prop),
            })
    return sorted(out, key=lambda x: x["label"])

def get_schemes(g):
    out = []
    for scheme in g.subjects(RDF.type, SKOS.ConceptScheme):
        if not str(scheme).startswith(IROKO_NS): continue
        concepts = []
        for c in g.subjects(SKOS.inScheme, scheme):
            if not str(c).startswith(IROKO_NS): continue
            concepts.append({
                "id":    local(str(c)),
                "label": pref_label(g, c) or label_rdf(g, c),
            })
        out.append({
            "id":       local(str(scheme)),
            "label":    label_rdf(g, scheme) or pref_label(g, scheme),
            "count":    len(concepts),
            "concepts": sorted(concepts, key=lambda x: x["label"]),
        })
    return sorted(out, key=lambda x: x["label"])


# ---------------------------------------------------------------------------
# Build cross-module connections for sidebar
# ---------------------------------------------------------------------------
def get_cross_module_connections(classes, stem, incoming_index):
    """
    For each class, identify which other modules connect to it via incoming props.
    Also identify which other modules this module points to via outgoing range URIs.
    Returns dict: class_local -> [{"name", "dotCls", "via", "dir"}]
    """
    result = {}
    for cls in classes:
        cid = cls["id"]
        seen_modules = {}
        for entry in incoming_index.get(cid, []):
            mstem = entry["stem"]
            if mstem == stem: continue  # skip self-references
            cfg = MODULE_CONFIG.get(mstem, {})
            mname = cfg.get("title", mstem).split(" — ")[0]
            mdot  = cfg.get("dot_cls", "dot-other")
            if mstem not in seen_modules:
                seen_modules[mstem] = {
                    "name":   mname,
                    "dotCls": mdot,
                    "via":    entry["uri"],
                    "dir":    "referenced by",
                }
        result[cid] = list(seen_modules.values())
    return result


# ---------------------------------------------------------------------------
# HTML template  (v8 format)
# ---------------------------------------------------------------------------
PAGE_CSS = """
    /* ── Module page layout ──────────────────────────────────────── */
    .module-layout {
      display: grid;
      grid-template-columns: 1fr 280px;
      gap: 3rem;
      align-items: start;
      margin-top: 2.5rem;
    }
    .module-main { min-width: 0; }
    .zone-head {
      font-family: var(--mono);
      font-size: .62rem;
      letter-spacing: .16em;
      text-transform: uppercase;
      color: var(--ink-soft);
      border-bottom: 1px solid var(--rule-strong);
      padding-bottom: .4rem;
      margin-bottom: 1rem;
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }
    .zone-hint { font-size: .68rem; letter-spacing: 0; text-transform: none;
      color: var(--ink-soft); font-family: var(--serif); font-style: italic; opacity: .7; }

    /* Zone 1 */
    .class-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(175px, 1fr));
      gap: .5rem; margin-bottom: 2rem; }
    .cls-card { border: 1px solid var(--rule-strong); border-radius: 3px; padding: .75rem 1rem;
      background: var(--paper); cursor: pointer;
      transition: border-color .15s, background .15s, box-shadow .15s; position: relative; }
    .cls-card:hover { background: var(--paper-warm); border-color: var(--green-mid); }
    .cls-card.active { border-color: var(--green); background: var(--green-light);
      box-shadow: 0 2px 8px rgba(46,74,30,.12); }
    .cls-card.active::after { content:''; position:absolute; bottom:-1px; left:50%;
      transform:translateX(-50%); width:0; height:0;
      border-left:7px solid transparent; border-right:7px solid transparent;
      border-bottom:7px solid var(--paper-warm); }
    .cls-uri { font-family: var(--mono); font-size: .7rem; color: var(--green-mid);
      display: block; margin-bottom: .2rem; }
    .cls-label { font-family: var(--serif); font-size: .95rem; font-weight: 600;
      color: var(--ink); display: block; line-height: 1.2; }
    .cls-hint { font-size: .67rem; color: var(--ink-soft); margin-top: .2rem;
      display: block; font-style: italic; }

    /* Zone 2 */
    .prop-placeholder { background: var(--paper-warm); border: 1px dashed var(--rule-strong);
      border-radius: 3px; padding: 1.25rem 1.5rem; color: var(--ink-soft); font-size: .84rem;
      font-style: italic; margin-bottom: 2rem; display: flex; align-items: center; gap: .75rem; }
    .prop-placeholder.hidden { display: none; }
    .prop-panel { display: none; border: 1px solid var(--rule-strong); border-radius: 3px;
      margin-bottom: 2rem; overflow: hidden; animation: panelIn 160ms ease forwards; }
    .prop-panel.visible { display: block; }
    @keyframes panelIn { from { opacity:0; transform:translateY(-4px); } to { opacity:1; transform:translateY(0); } }
    .pp-head { background: var(--green); color:#fff; padding:.9rem 1.25rem;
      display:flex; justify-content:space-between; align-items:baseline; gap:1rem; }
    .pp-uri { font-family: var(--mono); font-size: .72rem; color: rgba(255,255,255,.65); }
    .pp-label { font-family: var(--serif); font-size: 1.2rem; font-weight: 600; color: #fff; }
    .pp-close { background:none; border:none; color:rgba(255,255,255,.5); cursor:pointer;
      font-size:1.1rem; line-height:1; padding:.1rem; transition:color .15s;
      margin-left:auto; flex-shrink:0; }
    .pp-close:hover { color:#fff; }
    .pp-def { padding:.85rem 1.25rem; font-size:.85rem; color:var(--ink-mid); line-height:1.6;
      border-bottom:1px solid var(--rule); background:var(--paper-warm); }
    .pp-cols { display:grid; grid-template-columns:1fr 1fr; background:var(--paper); }
    .pp-col { padding:1.1rem 1.25rem; }
    .pp-col:first-child { border-right:1px solid var(--rule); }
    .pp-col-label { font-family:var(--mono); font-size:.6rem; letter-spacing:.12em;
      text-transform:uppercase; color:var(--ink-soft); margin-bottom:.75rem;
      display:flex; align-items:center; gap:.35rem; }
    .dir-arrow { color: var(--green-mid); }
    .pr-item { padding:.6rem .8rem; border:1px solid var(--rule); border-radius:3px;
      background:var(--paper); margin-bottom:.4rem; }
    .pr-top { display:flex; align-items:center; gap:.5rem; flex-wrap:wrap; }
    .pr-uri { font-family:var(--mono); font-size:.72rem; color:var(--green-mid); flex:1; }
    .pr-type { font-family:var(--mono); font-size:.55rem; letter-spacing:.04em;
      padding:.1em .4em; border-radius:2px; flex-shrink:0; }
    .pr-type-obj  { background:#e8e0f0; color:#5c3d8f; }
    .pr-type-data { background:#e0ecf8; color:#1a4a5e; }
    .pr-type-ann  { background:var(--gold-light,#f5edd8); color:var(--gold,#a07830); }
    .pr-label { font-size:.8rem; color:var(--ink-soft); margin-top:.1rem; }
    .pr-meta { font-family:var(--mono); font-size:.65rem; color:var(--ink-soft); margin-top:.3rem; }
    .pr-def { font-size:.78rem; color:var(--ink-mid); margin-top:.35rem; line-height:1.45; }
    .pr-source { font-family:var(--mono); font-size:.65rem; color:var(--ink-soft); font-style:italic; margin-top:.2rem; }
    .no-props { font-size:.8rem; color:var(--ink-soft); font-style:italic; }
    .ab { display:inline-block; font-family:var(--mono); font-size:.55rem; letter-spacing:.05em; padding:.1em .45em; border-radius:2px; }
    .ab-pub  { background:var(--green-light); color:var(--green); }
    .ab-comm { background:var(--gold-light,#f5edd8); color:var(--gold,#a07830); }
    .ab-init { background:#fde8e0; color:var(--terracotta,#8b3a1a); }
    .pp-cite { padding:.85rem 1.25rem; border-top:1px solid var(--rule);
      display:flex; align-items:center; justify-content:space-between;
      gap:1rem; flex-wrap:wrap; background:var(--paper-warm); }
    .pp-cite-text { font-family:var(--mono); font-size:.7rem; color:var(--ink-soft);
      flex:1; min-width:200px; }
    .btn-copy-sm { font-family:var(--mono); font-size:.68rem; letter-spacing:.08em;
      text-transform:uppercase; background:var(--green); color:#fff; border:none;
      border-radius:2px; padding:.4em 1em; cursor:pointer; transition:background .15s;
      flex-shrink:0; white-space:nowrap; }
    .btn-copy-sm:hover { background:var(--ink); }
    .btn-copy-sm.copied { background:var(--green-mid); }

    /* Zone 3 */
    .scheme-block { margin-bottom: 1.5rem; }
    .scheme-head { background:var(--paper-warm); border:1px solid var(--rule-strong);
      border-radius:3px 3px 0 0; padding:.6rem 1rem;
      display:flex; justify-content:space-between; align-items:baseline; gap:1rem; }
    .sh-uri { font-family:var(--mono); font-size:.75rem; color:var(--green-mid); }
    .sh-label { font-family:var(--serif); font-size:.92rem; font-weight:600; color:var(--ink); }
    .sh-count { font-family:var(--mono); font-size:.62rem; color:var(--ink-soft); white-space:nowrap; }
    .concept-chips { border:1px solid var(--rule-strong); border-top:none;
      border-radius:0 0 3px 3px; display:grid;
      grid-template-columns:repeat(auto-fill,minmax(185px,1fr)); overflow:hidden; }
    .chip { padding:.55rem .9rem; border-right:1px solid var(--rule);
      border-bottom:1px solid var(--rule); background:var(--paper); transition:background .12s; }
    .chip:hover { background:var(--paper-warm); }
    .chip-label { font-family:var(--sans); font-size:.82rem; font-weight:400; color:var(--ink); display:block; }
    .chip-id { font-family:var(--mono); font-size:.65rem; color:var(--green-mid); margin-top:.15rem; display:block; }

    /* Sidebar */
    .module-sidebar { position:sticky; top:2rem; }
    .sidebar-panel { border:1px solid var(--rule-strong); border-radius:3px; overflow:hidden; margin-bottom:1.25rem; }
    .sp-head { background:var(--paper-warm); border-bottom:1px solid var(--rule-strong);
      padding:.6rem 1rem; display:flex; justify-content:space-between; align-items:center; }
    .sp-title { font-family:var(--mono); font-size:.62rem; letter-spacing:.12em;
      text-transform:uppercase; color:var(--ink-soft); }
    .sp-active-uri { font-family:var(--mono); font-size:.67rem; color:var(--green); display:none; }
    .sp-body { padding:.75rem 1rem; }
    .conn-card { border:1px solid var(--rule); border-radius:3px; padding:.55rem .75rem;
      margin-bottom:.4rem; background:var(--paper); text-decoration:none; display:block;
      transition:border-color .15s, background .15s; }
    .conn-card:hover { border-color:var(--green-mid); background:var(--paper-warm); }
    .cc-row { display:flex; align-items:center; gap:.4rem; }
    .cc-dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; }
    .dot-core        { background:var(--green); }
    .dot-agency      { background:#6b3a10; }
    .dot-authority   { background:#3a4a5e; }
    .dot-epistemic   { background:#1a4a40; }
    .dot-narrative   { background:#5e3a2a; }
    .dot-manifestation { background:#5c3d8f; }
    .dot-botanical   { background:#3a5e28; }
    .dot-entities    { background:#5c3d8f; }
    .dot-ritual      { background:var(--terracotta,#8b3a1a); }
    .dot-lineage     { background:#4a3010; }
    .dot-divination  { background:#1a4a5e; }
    .dot-societies   { background:#5e1a3a; }
    .dot-graphic     { background:#3a3a1a; }
    .dot-music       { background:#1a3a5e; }
    .dot-language    { background:#2a1a5e; }
    .dot-other       { background:var(--ink-soft); }
    .cc-name { font-family:var(--serif); font-size:.88rem; font-weight:600; color:var(--ink); }
    .cc-via { font-family:var(--mono); font-size:.65rem; color:var(--ink-soft); margin-top:.15rem; display:block; }
    .cc-dir { font-size:.68rem; color:var(--ink-soft); font-style:italic; }
    .share-row { display:flex; gap:.4rem; margin-bottom:1.25rem; }
    .share-btn { flex:1; display:flex; flex-direction:column; align-items:center; gap:.25rem;
      padding:.5rem .25rem; background:var(--paper-warm); border:1px solid var(--rule-strong);
      border-radius:3px; cursor:pointer; font-family:var(--mono); font-size:.6rem;
      letter-spacing:.06em; text-transform:uppercase; color:var(--ink-soft); text-decoration:none;
      transition:border-color .15s, background .15s, color .15s; }
    .share-btn:hover { background:var(--green-light); border-color:var(--green-mid); color:var(--green); }
    .share-btn.copied { background:var(--green-light); border-color:var(--green); color:var(--green); }
    .share-btn svg { width:16px; height:16px; }
    .sidebar-cite { background:var(--paper-warm); border:1px solid var(--rule-strong);
      border-radius:3px; padding:.85rem 1rem; }
    .cite-head { font-family:var(--mono); font-size:.62rem; letter-spacing:.1em;
      text-transform:uppercase; color:var(--ink-soft); margin-bottom:.5rem; }
    .cite-tabs { display:flex; gap:0; margin-bottom:.6rem; border:1px solid var(--rule-strong);
      border-radius:3px; overflow:hidden; }
    .cite-tab { flex:1; font-family:var(--mono); font-size:.62rem; letter-spacing:.1em;
      text-transform:uppercase; padding:.35em 0; background:var(--paper); border:none;
      border-right:1px solid var(--rule-strong); color:var(--ink-soft);
      cursor:pointer; transition:background .15s, color .15s; }
    .cite-tab:last-child { border-right:none; }
    .cite-tab:hover { background:var(--paper-warm); color:var(--ink); }
    .cite-tab.active { background:var(--green-light); color:var(--green); font-weight:500; }
    .cite-text { font-family:var(--mono); font-size:.7rem; line-height:1.55;
      color:var(--ink-mid); font-style:italic; margin-bottom:.65rem; }
    .cite-text pre { font-family:var(--mono); font-size:.68rem; line-height:1.55;
      white-space:pre-wrap; word-break:break-all; margin:0; font-style:normal; }
    .btn-cite-copy { width:100%; font-family:var(--mono); font-size:.68rem; letter-spacing:.1em;
      text-transform:uppercase; background:var(--green); color:#fff; border:none;
      border-radius:2px; padding:.45em 0; cursor:pointer; transition:background .15s; }
    .btn-cite-copy:hover { background:var(--ink); }
    .btn-cite-copy.copied { background:var(--green-mid); }
    .format-links { margin-top:.65rem; display:flex; flex-direction:column; gap:.25rem; }
    .fmt-link { display:flex; justify-content:space-between; align-items:center;
      font-family:var(--mono); font-size:.7rem; padding:.35rem .6rem;
      border:1px solid var(--rule); border-radius:3px; background:var(--paper);
      color:var(--green-mid); text-decoration:none; transition:background .15s, border-color .15s; }
    .fmt-link:hover { background:var(--paper-warm); border-color:var(--rule-strong); color:var(--green); }
    .fmt-arrow { color:var(--ink-soft); }
    .sidebar-dynamic { transition:opacity 120ms ease; }
    .sidebar-dynamic.fading { opacity:0; pointer-events:none; }
    .active-class-card { background:var(--green-light); border:1px solid var(--green-mid);
      border-radius:3px; padding:.6rem .75rem; margin-bottom:.65rem; }
    .acc-uri { font-family:var(--mono); font-size:.67rem; color:var(--green-mid); display:block; margin-bottom:.1rem; }
    .acc-label { font-family:var(--serif); font-size:.9rem; font-weight:600; color:var(--ink); }
    @media (max-width:900px) {
      .module-layout { grid-template-columns:1fr; }
      .module-sidebar { position:static; }
      .pp-cols { grid-template-columns:1fr; }
      .pp-col:first-child { border-right:none; border-bottom:1px solid var(--rule); }
    }
"""

PAGE_JS = r"""
// ── JS data injected by generator ──────────────────────────────────────────
const MODULE_STEM = "{{STEM}}";
const MOD_TITLE_SHORT = "{{MOD_TITLE_SHORT}}";
const CLASSES = {{CLASSES_JSON}};
const MODULE_CROSS = {{MODULE_CROSS_JSON}};
const CITE_FORMATS = {{CITE_JSON}};

// ── Access badge ─────────────────────────────────────────────────────────────
function accessBadge(a) {
  if (a==='pub')  return '<span class="ab ab-pub">Public</span>';
  if (a==='comm') return '<span class="ab ab-comm">Community</span>';
  if (a==='init') return '<span class="ab ab-init">Initiated</span>';
  return '';
}
function typeBadge(t) {
  if (t==='obj')  return '<span class="pr-type pr-type-obj">Object</span>';
  if (t==='data') return '<span class="pr-type pr-type-data">Datatype</span>';
  if (t==='ann')  return '<span class="pr-type pr-type-ann">Annotation</span>';
  return '';
}

// ── Render property item ──────────────────────────────────────────────────────
function renderProp(p, isIncoming) {
  const meta = isIncoming
    ? `<div class="pr-source">from ${p.from} · ${p.module}</div>`
    : `<div class="pr-meta">${p.range||''}</div>`;
  return `<div class="pr-item">
    <div class="pr-top">
      <span class="pr-uri">${p.uri}</span>
      ${isIncoming ? '' : typeBadge(p.type)}
      ${isIncoming ? '' : accessBadge(p.access)}
    </div>
    <div class="pr-label">${p.label}</div>
    ${meta}
    <div class="pr-def">${p.def||''}</div>
  </div>`;
}

// ── State ─────────────────────────────────────────────────────────────────────
let activeClass = null;
let activeCiteFormat = 'plain';

function activateClass(key) {
  if (activeClass === key) { closePanel(); return; }
  activeClass = key;
  document.querySelectorAll('.cls-card').forEach(c=>c.classList.remove('active'));
  document.getElementById('card-'+key)?.classList.add('active');
  const d = CLASSES[key];
  if (!d) return;
  document.getElementById('prop-placeholder').classList.add('hidden');
  document.getElementById('z2-hint').textContent = 'Click class again to close';
  document.getElementById('pp-uri').textContent  = d.uri;
  document.getElementById('pp-label').textContent = d.label;
  document.getElementById('pp-def').textContent   = d.definition||'';
  const inEl  = document.getElementById('pp-incoming');
  inEl.innerHTML = d.incoming && d.incoming.length
    ? d.incoming.map(p=>renderProp(p,true)).join('')
    : '<p class="no-props">No incoming connections detected in this module.</p>';
  const outEl = document.getElementById('pp-outgoing');
  outEl.innerHTML = d.outgoing && d.outgoing.length
    ? d.outgoing.map(p=>renderProp(p,false)).join('')
    : '<p class="no-props">No outgoing properties.</p>';
  document.getElementById('pp-cite-text').textContent =
    'https://ontology.irokosociety.org/iroko#'+key;
  document.getElementById('pp-cite-btn').dataset.uri  =
    'https://ontology.irokosociety.org/iroko#'+key;
  const panel = document.getElementById('prop-panel');
  panel.classList.remove('visible');
  void panel.offsetWidth;
  panel.classList.add('visible');
  panel.scrollIntoView({behavior:'smooth',block:'nearest'});
  updateSidebar(key, d);
}

function closePanel() {
  activeClass = null;
  document.querySelectorAll('.cls-card').forEach(c=>c.classList.remove('active'));
  document.getElementById('prop-placeholder').classList.remove('hidden');
  document.getElementById('prop-panel').classList.remove('visible');
  document.getElementById('z2-hint').textContent = 'Click a class card above';
  resetSidebar();
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
function updateSidebar(key, d) {
  const body = document.getElementById('sb-body');
  body.classList.add('fading');
  setTimeout(()=>{
    document.getElementById('sb-title').textContent = 'External links';
    document.getElementById('sb-active-uri').style.display = 'block';
    document.getElementById('sb-active-uri').textContent = d.uri;
    document.getElementById('sb-module-view').style.display = 'none';
    document.getElementById('sb-class-view').style.display  = 'block';
    document.getElementById('sb-active-card').innerHTML =
      `<div class="active-class-card"><span class="acc-uri">${d.uri}</span><span class="acc-label">${d.label}</span></div>`;
    const conns = (d.cross||[]);
    const connsEl = document.getElementById('sb-class-conns');
    connsEl.innerHTML = conns.length
      ? conns.map(c=>`<div class="conn-card">
          <div class="cc-row"><span class="cc-dot ${c.dotCls}"></span><span class="cc-name">${c.name}</span><span class="cc-dir" style="margin-left:auto;">${c.dir}</span></div>
          <span class="cc-via">${c.via}</span>
        </div>`).join('')
      : '<p class="no-props">No cross-module connections for this class.</p>';
    body.classList.remove('fading');
  },120);
}

function resetSidebar() {
  const body = document.getElementById('sb-body');
  body.classList.add('fading');
  setTimeout(()=>{
    document.getElementById('sb-title').textContent = 'Connected Modules';
    document.getElementById('sb-active-uri').style.display = 'none';
    document.getElementById('sb-module-view').style.display = 'block';
    document.getElementById('sb-class-view').style.display  = 'none';
    body.classList.remove('fading');
  },120);
}

// ── Citation ──────────────────────────────────────────────────────────────────
function setCiteFormat(fmt, btn) {
  activeCiteFormat = fmt;
  document.querySelectorAll('.cite-tab').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  const display = document.getElementById('cite-display');
  if (fmt==='plain') {
    display.innerHTML = CITE_FORMATS.plainHTML;
  } else {
    display.innerHTML = `<pre>${CITE_FORMATS[fmt].replace(/</g,'&lt;')}</pre>`;
  }
}

function copyModuleCite() {
  const text = activeCiteFormat==='plain' ? CITE_FORMATS.plain : CITE_FORMATS[activeCiteFormat];
  navigator.clipboard.writeText(text).then(()=>{
    const btn = document.getElementById('module-cite-btn');
    btn.textContent = '✓ Copied';
    btn.classList.add('copied');
    setTimeout(()=>{btn.textContent='Copy Citation';btn.classList.remove('copied');},2000);
  });
}

function copyCite() {
  const btn = document.getElementById('pp-cite-btn');
  navigator.clipboard.writeText(btn.dataset.uri).then(()=>{
    btn.textContent='✓ Copied'; btn.classList.add('copied');
    setTimeout(()=>{btn.textContent='Copy URI';btn.classList.remove('copied');},2000);
  });
}

function copyLink(btn) {
  navigator.clipboard.writeText(window.location.href).then(()=>{
    btn.classList.add('copied');
    btn.lastChild.textContent='Copied';
    setTimeout(()=>{btn.classList.remove('copied');btn.lastChild.textContent='Copy Link';},2000);
  });
}

// ── Fragment URI auto-open ────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded',()=>{
  const hash = window.location.hash.replace('#','');
  if (hash && CLASSES[hash]) {
    activateClass(hash);
    document.getElementById('card-'+hash)?.scrollIntoView({behavior:'smooth',block:'center'});
  }
});
"""


def js_str(s):
    """Escape a string for JS single-quoted string or JSON."""
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def generate_html(ttl_path, output_path, cfg, incoming_index):
    stem     = ttl_path.stem
    print(f"  Processing {ttl_path.name} …", end="", flush=True)

    g = Graph()
    try:
        g.parse(str(ttl_path), format="turtle")
    except Exception as e:
        print(f"\n  ERROR: {e}")
        return False

    meta    = get_meta(g)
    classes = get_classes(g)
    schemes = get_schemes(g)

    version  = meta.get("version", "1.3.0")
    title    = cfg["title"]
    subtitle = cfg["subtitle"]
    tag_cls  = cfg["tag_cls"]
    tag_text = cfg["tag_text"]
    prefix   = cfg["prefix"]
    ttl_name = ttl_path.name
    issued   = meta.get("issued",   "")
    modified = meta.get("modified", "")
    ns_uri   = meta.get("uri", "https://ontology.irokosociety.org/iroko-" + stem.replace("iroko-", ""))
    n_props_total = 0

    # Short title for citation (e.g. "Ewé Module")
    mod_short = title.split(" — ")[0] if " — " in title else title

    # Build per-class data for JS
    classes_js = {}
    for cls in classes:
        cid  = cls["id"]
        out  = get_outgoing(g, cid)
        inc  = incoming_index.get(cid, [])
        cross = get_cross_module_connections([cls], stem, incoming_index).get(cid, [])
        n_props_total += len(out)
        classes_js[cid] = {
            "uri":        f"iroko:{cid}",
            "label":      cls["label"],
            "definition": cls["def"],
            "outgoing":   out,
            "incoming":   inc,
            "cross":      cross,
        }

    # Module-level cross connections (for sidebar at rest)
    all_cross = {}  # stem -> {name, dotCls, count}
    for cid, data in classes_js.items():
        for c in data["cross"]:
            mstem = next((k for k, v in MODULE_CONFIG.items()
                         if v.get("title","").split(" — ")[0] == c["name"]), None)
            if mstem and mstem not in all_cross:
                all_cross[mstem] = {
                    "name":   c["name"],
                    "dotCls": c["dotCls"],
                    "via":    c["via"],
                    "dir":    c["dir"],
                }
    module_cross_list = list(all_cross.values())

    # Counts
    n_classes  = len(classes)
    n_schemes  = len(schemes)
    n_concepts = sum(s["count"] for s in schemes)
    n_props    = n_props_total

    # Date line
    date_line = ""
    if issued:
        date_line = f"Issued {issued}"
        if modified: date_line += f" · Revised {modified}"

    # Citation strings
    page_url = f"https://ontology.irokosociety.org/vocab/{ttl_path.stem}.html"
    year = (modified or issued or "2026")[:4]
    cite_plain = (f"Iroko Historical Society. ({year}). {mod_short} (v{version}). "
                  f"{page_url}. CC0 1.0 Universal.")
    bib_key = stem.replace("-", "_")
    if bib_key.startswith("iroko_"): bib_key = bib_key[len("iroko_"):]
    cite_bibtex = (f"@misc{{iroko_{bib_key}_{year},\n"
                   f"  author    = {{{{Iroko Historical Society}}}},\n"
                   f"  title     = {{{{Iroko Framework: {mod_short}}}}},\n"
                   f"  year      = {{{year}}},\n"
                   f"  version   = {{{version}}},\n"
                   f"  url       = {{{page_url}}},\n"
                   f"  note      = {{CC0 1.0 Universal}}\n}}")
    cite_ris = (f"TY  - DATA\n"
                f"AU  - Iroko Historical Society\n"
                f"TI  - Iroko Framework: {mod_short}\n"
                f"PY  - {year}\n"
                f"UR  - {page_url}\n"
                f"VL  - {version}\n"
                f"N1  - CC0 1.0 Universal\n"
                f"ER  -")
    cite_plain_html = (f"Iroko Historical Society. ({year}). <em>Iroko Framework: {h(mod_short)}</em> "
                       f"(v{h(version)}). {h(page_url)}. CC0 1.0 Universal.")

    cite_json = json.dumps({
        "plain":     cite_plain,
        "plainHTML": cite_plain_html,
        "bibtex":    cite_bibtex,
        "ris":       cite_ris,
    }, ensure_ascii=False)

    classes_json = json.dumps(classes_js, ensure_ascii=False)
    module_cross_json = json.dumps(module_cross_list, ensure_ascii=False)

    # ── Build HTML ────────────────────────────────────────────────────────
    W = []
    A = W.append

    og_title = f"{title} — Iroko Framework Vocabularies"
    og_desc  = subtitle or f"Controlled vocabulary module of the Iroko Framework for Afro-Atlantic sacred knowledge systems: {mod_short}."
    og_image = "https://ontology.irokosociety.org/assets/og-iroko-framework.png"

    A(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{h(og_desc)}">
  <title>{h(title)} — Iroko Framework Vocabularies</title>
  <link rel="icon" type="image/svg+xml" href="../assets/IHS-Logo.svg">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Iroko Historical Society">
  <meta property="og:title" content="{h(og_title)}">
  <meta property="og:description" content="{h(og_desc)}">
  <meta property="og:url" content="{h(page_url)}">
  <meta property="og:image" content="{h(og_image)}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:type" content="image/png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{h(og_title)}">
  <meta name="twitter:description" content="{h(og_desc)}">
  <meta name="twitter:image" content="{h(og_image)}">
  <link rel="stylesheet" href="../assets/iroko-style.css">
  <style>{PAGE_CSS}
  </style>
</head>
<body>

<div class="top-bar">
  <span class="top-bar-id">
    <img class="top-bar-logo" src="../assets/IHS-Logo.jpg" alt="Iroko Historical Society">
    Iroko Historical Society · Iroko Framework v{h(FRAMEWORK_VERSION)}
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
      <a href="../index.html"><img src="../assets/IHS-Logo.jpg" alt="Iroko Historical Society — Home"></a>
    </div>
    <div>
      <span class="module-tag {h(tag_cls)}">{h(tag_text)}</span>
      <h1>{h(title)}</h1>
      <p class="subtitle">{h(subtitle)}</p>
      <div class="header-meta">
        <span class="meta-pill">{h(prefix)}&nbsp; {h(ns_uri)}#</span>
        <span class="meta-pill">v{h(version)}</span>
        <span class="meta-pill"><a href="{h(ttl_name)}" style="color:inherit;">Download TTL ↓</a></span>
        <span class="meta-pill"><a href="https://github.com/iroko-framework/iroko-framework" style="color:inherit;">GitHub ↗</a></span>
      </div>
    </div>
  </header>

  <div class="module-stats" style="margin-top:1.5rem;">
    <div class="stat-cell"><span class="stat-n">{n_classes}</span><span class="stat-label">Classes</span></div>
    <div class="stat-cell"><span class="stat-n">{n_props}</span><span class="stat-label">Properties</span></div>
    <div class="stat-cell"><span class="stat-n">{n_schemes}</span><span class="stat-label">Schemes</span></div>
    <div class="stat-cell"><span class="stat-n">{n_concepts}</span><span class="stat-label">Concepts</span></div>
  </div>

  <div class="module-layout">
    <main class="module-main">
""")

    # Zone 1 — class grid
    A("""      <!-- ZONE 1: Classes -->
      <div class="zone-head">
        Classes
        <span class="zone-hint">Select a class to explore its properties</span>
      </div>
      <div class="class-grid">""")
    for cls in classes:
        A(f"""        <div class="cls-card" id="card-{h(cls['id'])}" onclick="activateClass('{h(cls['id'])}')">
          <span class="cls-uri">iroko:{h(cls['id'])}</span>
          <span class="cls-label">{h(cls['label'])}</span>
          {f'<span class="cls-hint">{h(cls["hint"])}</span>' if cls['hint'] else ''}
        </div>""")
    A("      </div>")

    # Zone 2 — property panel shell
    A("""
      <!-- ZONE 2: Property panel -->
      <div class="zone-head" style="margin-top:0;">
        Properties
        <span class="zone-hint" id="z2-hint">Click a class card above</span>
      </div>
      <div class="prop-placeholder" id="prop-placeholder">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        No class selected. Click any class card above to see incoming and outgoing properties.
      </div>
      <div class="prop-panel" id="prop-panel">
        <div class="pp-head">
          <div>
            <div class="pp-uri" id="pp-uri"></div>
            <div class="pp-label" id="pp-label"></div>
          </div>
          <button class="pp-close" onclick="closePanel()" title="Close">&#x2715;</button>
        </div>
        <div class="pp-def" id="pp-def"></div>
        <div class="pp-cols">
          <div class="pp-col">
            <div class="pp-col-label"><span class="dir-arrow">&#8592;</span> Incoming <span style="font-style:italic;text-transform:none;letter-spacing:0;font-weight:400;">(range = this class)</span></div>
            <div id="pp-incoming"></div>
          </div>
          <div class="pp-col">
            <div class="pp-col-label"><span class="dir-arrow">&#8594;</span> Outgoing <span style="font-style:italic;text-transform:none;letter-spacing:0;font-weight:400;">(domain = this class)</span></div>
            <div id="pp-outgoing"></div>
          </div>
        </div>
        <div class="pp-cite">
          <span class="pp-cite-text" id="pp-cite-text"></span>
          <button class="btn-copy-sm" id="pp-cite-btn" onclick="copyCite()">Copy URI</button>
        </div>
      </div>
""")

    # Zone 3 — concept schemes
    if schemes:
        A("""      <!-- ZONE 3: Concept Schemes -->
      <div class="zone-head" style="margin-top:1rem;">
        Concept Schemes
        <span class="zone-hint">""" + f"{n_concepts} concepts across {n_schemes} scheme{'s' if n_schemes!=1 else ''}" + """</span>
      </div>""")
        for scheme in schemes:
            A(f"""      <div class="scheme-block">
        <div class="scheme-head">
          <div>
            <span class="sh-uri">iroko:{h(scheme['id'])}</span>
            <span class="sh-label">{h(scheme['label'])}</span>
          </div>
          <span class="sh-count">{scheme['count']} concept{'s' if scheme['count']!=1 else ''}</span>
        </div>
        <div class="concept-chips">""")
            for c in scheme["concepts"]:
                A(f"""          <div class="chip">
            <span class="chip-label">{h(c['label'])}</span>
            <span class="chip-id">iroko:{h(c['id'])}</span>
          </div>""")
            A("        </div>\n      </div>")

    A("    </main><!-- /module-main -->")

    # Sidebar
    # Module-level conn cards
    if module_cross_list:
        mod_conns_html = "\n".join(
            f"""            <div class="conn-card">
              <div class="cc-row"><span class="cc-dot {h(c['dotCls'])}"></span>
                <span class="cc-name">{h(c['name'])}</span>
                <span class="cc-dir" style="margin-left:auto;">{h(c['dir'])}</span>
              </div>
              <span class="cc-via">{h(c['via'])}</span>
            </div>"""
            for c in module_cross_list
        )
    else:
        mod_conns_html = '<p class="no-props" style="font-size:.8rem;color:var(--ink-soft);font-style:italic;">No external connections detected.</p>'

    page_title_safe = h(title).replace('"', '&quot;')
    page_url_encoded = page_url.replace("&", "%26")

    A(f"""
    <!-- SIDEBAR -->
    <aside class="module-sidebar">

      <div class="share-row">
        <a class="share-btn" href="mailto:?subject=Iroko%20Framework%20%E2%80%94%20{h(mod_short).replace(' ','%20')}&amp;body={page_url_encoded}" title="Share via email">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 7 10 7 10-7"/></svg>
          Email
        </a>
        <button class="share-btn" onclick="window.print()" title="Print">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9V2h12v7"/><rect x="6" y="14" width="12" height="8"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/></svg>
          Print
        </button>
        <button class="share-btn" id="link-btn" onclick="copyLink(this)" title="Copy link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
          Copy Link
        </button>
      </div>

      <div class="sidebar-panel">
        <div class="sp-head">
          <span class="sp-title" id="sb-title">Connected Modules</span>
          <span class="sp-active-uri" id="sb-active-uri"></span>
        </div>
        <div class="sp-body sidebar-dynamic" id="sb-body">
          <div id="sb-module-view">
{mod_conns_html}
          </div>
          <div id="sb-class-view" style="display:none;">
            <div id="sb-active-card"></div>
            <div id="sb-class-conns"></div>
          </div>
        </div>
      </div>

      <div class="sidebar-cite">
        <div class="cite-head">Cite the {h(mod_short)}</div>
        <div class="cite-tabs">
          <button class="cite-tab active" onclick="setCiteFormat('plain',this)">Plain</button>
          <button class="cite-tab" onclick="setCiteFormat('bibtex',this)">BibTeX</button>
          <button class="cite-tab" onclick="setCiteFormat('ris',this)">RIS</button>
        </div>
        <div class="cite-text" id="cite-display">
          Iroko Historical Society. ({h(year)}). <em>Iroko Framework: {h(mod_short)}</em> (v{h(version)}). {h(page_url)}. CC0 1.0 Universal.
        </div>
        <button class="btn-cite-copy" id="module-cite-btn" onclick="copyModuleCite()">Copy Citation</button>
        <div class="format-links">
          <a class="fmt-link" href="{h(ttl_name)}">Turtle (.ttl) <span class="fmt-arrow">&#8595;</span></a>
          <a class="fmt-link" href="{h(ttl_path.stem)}.jsonld">JSON-LD (.jsonld) <span class="fmt-arrow">&#8595;</span></a>
          <a class="fmt-link" href="{h(ttl_path.stem)}.rdf">RDF/XML (.rdf) <span class="fmt-arrow">&#8595;</span></a>
          <a class="fmt-link" href="{h(ttl_path.stem)}.nt">N-Triples (.nt) <span class="fmt-arrow">&#8595;</span></a>
        </div>
      </div>

    </aside>
  </div><!-- /module-layout -->

  <footer class="site-footer">
    <div class="footer-left">
      Iroko Historical Society<br>
      Postcustodial Digital Archives for Afro-Atlantic Cultural Materials<br>
      {h(date_line) + '<br>' if date_line else ''}License: CC0 1.0 Universal (Public Domain)
      <div class="footer-iao">Ilé Añá Olofí, Inc. 501(c)(3) · <a href="https://ileanaolofi.org" target="_blank" rel="noopener">ileanaolofi.org</a></div>
    </div>
    <div class="footer-links">
      <a href="https://www.irokosociety.org/" target="_blank" rel="noopener">IHS ↗</a>
      <a href="../index.html">Home</a>
      <a href="https://medjat.irokosociety.org/">Per Medjat</a>
      <a href="index.html">Vocabularies</a>
    </div>
  </footer>

</div><!-- /page-wrap -->
""")

    # JS — inject data
    js = PAGE_JS.replace("{{STEM}}", stem)
    js = js.replace("{{MOD_TITLE_SHORT}}", mod_short.replace('"', '\\"'))
    js = js.replace("{{CLASSES_JSON}}", classes_json)
    js = js.replace("{{MODULE_CROSS_JSON}}", module_cross_json)
    js = js.replace("{{CITE_JSON}}", cite_json)
    A(f"<script>\n{js}\n</script>\n</body>\n</html>")

    output_path.write_text("\n".join(W), encoding="utf-8")
    print(f" ✓  ({n_classes} cls, {n_props} prop, {n_schemes} sch, {n_concepts} concepts)")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Generate v8 module browse pages from TTL files.")
    parser.add_argument("stems", nargs="*", help="Module stem(s) e.g. iroko-ewe")
    parser.add_argument("--vocab", metavar="DIR", help="Path to vocab/ directory")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, no output")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    if args.vocab:
        vocab_dir = Path(args.vocab)
    else:
        for candidate in [script_dir.parent/"vocab", script_dir/"vocab",
                          Path.cwd()/"vocab", Path.cwd()]:
            if (candidate/"iroko-core.ttl").exists():
                vocab_dir = candidate
                break
        else:
            print("ERROR: vocab/ directory not found. Use --vocab.")
            sys.exit(1)

    all_ttl = sorted(vocab_dir.glob("*.ttl"))
    if not all_ttl:
        print("No TTL files found.")
        sys.exit(1)

    # Decide which files to process
    if args.stems:
        targets = []
        for s in args.stems:
            stem = s if not s.endswith(".ttl") else s[:-4]
            p = vocab_dir / f"{stem}.ttl"
            if not p.exists():
                print(f"ERROR: {p} not found")
                sys.exit(1)
            targets.append(p)
    else:
        targets = [p for p in all_ttl if p.stem not in KNOWN_SKIPS and p.stem in MODULE_CONFIG]

    print(f"Building cross-module incoming index from {len(all_ttl)} TTL files …")
    incoming_index = build_cross_module_index(all_ttl)
    print(f"  Index built: {sum(len(v) for v in incoming_index.values())} incoming connections "
          f"across {len(incoming_index)} classes\n")

    if args.dry_run:
        print("Dry run — no files written.")
        return

    print(f"Generating {len(targets)} module page(s) …\n")
    ok = err = 0
    for ttl_path in targets:
        stem = ttl_path.stem
        cfg  = MODULE_CONFIG.get(stem)
        if cfg is None:
            print(f"  SKIPPED {ttl_path.name} — not in MODULE_CONFIG")
            continue
        out_path = ttl_path.with_suffix(".html")
        if generate_html(ttl_path, out_path, cfg, incoming_index):
            ok += 1
        else:
            err += 1

    print(f"\n{'─'*55}")
    print(f"Done: {ok} generated, {err} errors")


if __name__ == "__main__":
    main()
