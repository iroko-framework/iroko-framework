"""
iroko_manager.py — RDFlib read/write layer for the Iroko Framework Management GUI.

All TTL mutations go through this module. Writes are atomic: a .tmp file is
written and validated before the live file is replaced.
"""

import sys
from pathlib import Path
from typing import Optional

from rdflib import Graph, Namespace, RDF, RDFS, OWL, SKOS, URIRef, Literal
from rdflib.namespace import DCTERMS, XSD

# Locate repo root (manage/ → scripts/ → repo root)
MANAGE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = MANAGE_DIR.parent
REPO_ROOT   = SCRIPTS_DIR.parent
VOCAB_DIR   = REPO_ROOT / "vocab"

sys.path.insert(0, str(SCRIPTS_DIR))
from iroko_config import MODULE_CONFIG, ACCESS_MAP, MODULES, IROKO_NS

IROKO = Namespace(IROKO_NS)
PROV  = Namespace("http://www.w3.org/ns/prov#")

# Standard Turtle prefixes written into every saved file header
TTL_PREFIXES = """\
@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:     <http://www.w3.org/2002/07/owl#> .
@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .
@prefix skos:    <http://www.w3.org/2004/02/skos/core#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix prov:    <http://www.w3.org/ns/prov#> .
@prefix iroko:   <https://ontology.irokosociety.org/iroko#> .
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def local(uri: str) -> str:
    s = str(uri)
    return s.split("#")[-1] if "#" in s else s.split("/")[-1]

def iroko_uri(local_id: str) -> URIRef:
    return URIRef(IROKO_NS + local_id)

def label_en(g: Graph, subject, pred) -> str:
    en = fb = None
    for o in g.objects(subject, pred):
        lang = getattr(o, "language", None)
        if lang == "en": en = str(o)
        elif fb is None: fb = str(o)
    return en or fb or ""

def pref_label(g: Graph, s) -> str:
    return label_en(g, s, SKOS.prefLabel) or label_en(g, s, RDFS.label)

def definition(g: Graph, s) -> str:
    return label_en(g, s, SKOS.definition) or label_en(g, s, RDFS.comment)

def scope_note(g: Graph, s) -> str:
    return label_en(g, s, SKOS.scopeNote)

def access_level_local(g: Graph, s) -> str:
    acc = g.value(s, IROKO.minimumAccessLevel)
    return local(str(acc)) if acc else "access-public-unrestricted"

# ---------------------------------------------------------------------------
# Module listing
# ---------------------------------------------------------------------------

def list_modules() -> list[dict]:
    """Return info about every module: stem, title, layer, ttl_path, exists, counts."""
    result = []
    for _name, _tier, _tag, _ns, stem in MODULES:
        cfg  = MODULE_CONFIG.get(stem, {})
        path = VOCAB_DIR / f"{stem}.ttl"
        info = {
            "stem":   stem,
            "title":  cfg.get("title", stem),
            "layer":  cfg.get("layer", _tier),
            "tag_cls":  cfg.get("tag_cls", "tag-upcoming"),
            "tag_text": cfg.get("tag_text", _tag),
            "prefix": cfg.get("prefix", "iroko:"),
            "path":   path,
            "exists": path.exists(),
            "classes": 0, "props": 0, "schemes": 0, "concepts": 0,
        }
        if path.exists():
            try:
                g = load_module(stem)
                counts = count_terms(g)
                info.update(counts)
            except Exception:
                pass
        result.append(info)
    return result

# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------

def load_module(stem: str) -> Graph:
    path = VOCAB_DIR / f"{stem}.ttl"
    g = Graph()
    g.parse(str(path), format="turtle")
    return g

def save_module(stem: str, g: Graph) -> None:
    """Serialize graph to Turtle and atomically replace the live TTL file."""
    path    = VOCAB_DIR / f"{stem}.ttl"
    tmp     = path.with_suffix(".tmp")

    # Serialize
    ttl = g.serialize(format="turtle")

    # Validate round-trip
    check = Graph()
    check.parse(data=ttl, format="turtle")

    tmp.write_text(ttl, encoding="utf-8")
    tmp.replace(path)

# ---------------------------------------------------------------------------
# Term counts
# ---------------------------------------------------------------------------

def count_terms(g: Graph) -> dict:
    n_cls  = len([s for s in g.subjects(RDF.type, OWL.Class)
                  if str(s).startswith(IROKO_NS)])
    n_prop = len([s for ptype in (OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty)
                  for s in g.subjects(RDF.type, ptype)
                  if str(s).startswith(IROKO_NS)])
    schemes = list(g.subjects(RDF.type, SKOS.ConceptScheme))
    n_sch   = len([s for s in schemes if str(s).startswith(IROKO_NS)])
    n_con   = len([s for s in g.subjects(SKOS.inScheme, None)
                   if str(s).startswith(IROKO_NS)])
    return {"classes": n_cls, "props": n_prop, "schemes": n_sch, "concepts": n_con}

# ---------------------------------------------------------------------------
# Concepts
# ---------------------------------------------------------------------------

def get_all_concepts(g: Graph) -> list[dict]:
    """Return all SKOS Concepts in a graph, with their scheme membership."""
    concepts = []
    for c in g.subjects(RDF.type, SKOS.Concept):
        if not str(c).startswith(IROKO_NS): continue
        scheme_uri = g.value(c, SKOS.inScheme)
        scheme_id  = local(str(scheme_uri)) if scheme_uri else ""
        scheme_lbl = pref_label(g, scheme_uri) or label_en(g, scheme_uri, RDFS.label) if scheme_uri else ""
        concepts.append({
            "uri":        str(c),
            "local_id":   local(str(c)),
            "label":      pref_label(g, c),
            "definition": definition(g, c),
            "scope_note": scope_note(g, c),
            "scheme_id":  scheme_id,
            "scheme_label": scheme_lbl,
            "access":     access_level_local(g, c),
        })
    return sorted(concepts, key=lambda x: (x["scheme_id"], x["label"]))

def get_concept(g: Graph, local_id: str) -> Optional[dict]:
    uri = iroko_uri(local_id)
    if (uri, RDF.type, SKOS.Concept) not in g:
        return None
    scheme_uri = g.value(uri, SKOS.inScheme)
    broader_uri = g.value(uri, SKOS.broader)
    alt_labels = sorted({str(o) for o in g.objects(uri, SKOS.altLabel)})
    return {
        "uri":        str(uri),
        "local_id":   local_id,
        "label":      pref_label(g, uri),
        "alt_labels": alt_labels,
        "definition": definition(g, uri),
        "scope_note": scope_note(g, uri),
        "scheme_id":  local(str(scheme_uri)) if scheme_uri else "",
        "access":     access_level_local(g, uri),
        "broader":    local(str(broader_uri)) if broader_uri else "",
    }

def get_all_schemes(g: Graph) -> list[dict]:
    schemes = []
    for s in g.subjects(RDF.type, SKOS.ConceptScheme):
        if not str(s).startswith(IROKO_NS): continue
        schemes.append({
            "uri":   str(s),
            "local_id": local(str(s)),
            "label": pref_label(g, s) or label_en(g, s, RDFS.label),
        })
    return sorted(schemes, key=lambda x: x["label"])

def upsert_concept(g: Graph, data: dict) -> None:
    """Add or update a SKOS Concept.
    data keys: local_id, label, alt_labels (list), definition, scope_note,
               scheme_id, access, broader.
    """
    uri = iroko_uri(data["local_id"])

    # Remove existing triples about this URI so we start clean
    for p, o in list(g.predicate_objects(uri)):
        g.remove((uri, p, o))

    g.add((uri, RDF.type, SKOS.Concept))

    if data.get("label"):
        g.add((uri, SKOS.prefLabel, Literal(data["label"], lang="en")))
        g.add((uri, RDFS.label, Literal(data["label"], lang="en")))

    for alt in data.get("alt_labels") or []:
        if alt:
            g.add((uri, SKOS.altLabel, Literal(alt, lang="en")))

    if data.get("definition"):
        g.add((uri, SKOS.definition, Literal(data["definition"], lang="en")))

    if data.get("scope_note"):
        g.add((uri, SKOS.scopeNote, Literal(data["scope_note"], lang="en")))

    if data.get("scheme_id"):
        g.add((uri, SKOS.inScheme, iroko_uri(data["scheme_id"])))

    if data.get("broader"):
        g.add((uri, SKOS.broader, iroko_uri(data["broader"])))

    if data.get("access"):
        g.add((uri, IROKO.minimumAccessLevel, iroko_uri(data["access"])))


def set_alt_labels(g: Graph, local_id: str, alt_labels: list[str]) -> bool:
    """Replace all skos:altLabel values on a concept. Returns False if concept not found."""
    uri = iroko_uri(local_id)
    if (uri, RDF.type, SKOS.Concept) not in g:
        return False
    for o in list(g.objects(uri, SKOS.altLabel)):
        g.remove((uri, SKOS.altLabel, o))
    for alt in alt_labels:
        if alt.strip():
            g.add((uri, SKOS.altLabel, Literal(alt.strip(), lang="en")))
    return True


def get_tradition_concepts(g: Graph) -> list[dict]:
    """Return all TraditionScheme concepts with labels and altLabels, sorted by prefLabel."""
    tradition_scheme = iroko_uri("TraditionScheme")
    concepts = []
    for c in g.subjects(SKOS.inScheme, tradition_scheme):
        if not str(c).startswith(IROKO_NS):
            continue
        broader_uri = g.value(c, SKOS.broader)
        alt_labels = sorted({str(o) for o in g.objects(c, SKOS.altLabel)})
        concepts.append({
            "local_id":   local(str(c)),
            "label":      pref_label(g, c),
            "alt_labels": alt_labels,
            "broader":    local(str(broader_uri)) if broader_uri else "",
            "definition": definition(g, c),
        })
    return sorted(concepts, key=lambda x: x["label"])


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

def get_all_classes(g: Graph) -> list[dict]:
    classes = []
    for c in g.subjects(RDF.type, OWL.Class):
        if not str(c).startswith(IROKO_NS): continue
        supers = [local(str(s)) for s in g.objects(c, RDFS.subClassOf)
                  if not hasattr(s, "n3") or not str(s).startswith("_:")]
        classes.append({
            "uri":        str(c),
            "local_id":   local(str(c)),
            "label":      label_en(g, c, RDFS.label),
            "definition": label_en(g, c, RDFS.comment),
            "superclasses": supers,
            "access":     access_level_local(g, c),
        })
    return sorted(classes, key=lambda x: x["label"])

def get_class(g: Graph, local_id: str) -> Optional[dict]:
    uri = iroko_uri(local_id)
    if (uri, RDF.type, OWL.Class) not in g:
        return None
    supers = [local(str(s)) for s in g.objects(uri, RDFS.subClassOf)
              if not str(s).startswith("_:")]
    return {
        "uri":        str(uri),
        "local_id":   local_id,
        "label":      label_en(g, uri, RDFS.label),
        "definition": label_en(g, uri, RDFS.comment),
        "superclasses": supers,
        "access":     access_level_local(g, uri),
    }

def upsert_class(g: Graph, data: dict) -> None:
    """Add or update an OWL Class. data keys: local_id, label, definition, superclasses (list), access."""
    uri = iroko_uri(data["local_id"])
    for p, o in list(g.predicate_objects(uri)):
        g.remove((uri, p, o))

    g.add((uri, RDF.type, OWL.Class))

    if data.get("label"):
        g.add((uri, RDFS.label, Literal(data["label"], lang="en")))

    if data.get("definition"):
        g.add((uri, RDFS.comment, Literal(data["definition"], lang="en")))

    for sup in data.get("superclasses", []):
        if sup.strip():
            g.add((uri, RDFS.subClassOf, iroko_uri(sup.strip())))

    if data.get("access"):
        g.add((uri, IROKO.minimumAccessLevel, iroko_uri(data["access"])))

# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

PROP_TYPE_MAP = {
    "ObjectProperty":     OWL.ObjectProperty,
    "DatatypeProperty":   OWL.DatatypeProperty,
    "AnnotationProperty": OWL.AnnotationProperty,
}

def get_all_properties(g: Graph) -> list[dict]:
    props = []
    for ptype_name, ptype_uri in PROP_TYPE_MAP.items():
        for p in g.subjects(RDF.type, ptype_uri):
            if not str(p).startswith(IROKO_NS): continue
            dom = g.value(p, RDFS.domain)
            rng = g.value(p, RDFS.range)
            props.append({
                "uri":        str(p),
                "local_id":   local(str(p)),
                "label":      label_en(g, p, RDFS.label),
                "definition": label_en(g, p, RDFS.comment),
                "prop_type":  ptype_name,
                "domain":     local(str(dom)) if dom and not str(dom).startswith("_:") else "",
                "range":      local(str(rng)) if rng and not str(rng).startswith("_:") else "",
                "access":     access_level_local(g, p),
            })
    return sorted(props, key=lambda x: x["label"])

def get_property(g: Graph, local_id: str) -> Optional[dict]:
    uri = iroko_uri(local_id)
    for ptype_name, ptype_uri in PROP_TYPE_MAP.items():
        if (uri, RDF.type, ptype_uri) in g:
            dom = g.value(uri, RDFS.domain)
            rng = g.value(uri, RDFS.range)
            return {
                "uri":        str(uri),
                "local_id":   local_id,
                "label":      label_en(g, uri, RDFS.label),
                "definition": label_en(g, uri, RDFS.comment),
                "prop_type":  ptype_name,
                "domain":     local(str(dom)) if dom and not str(dom).startswith("_:") else "",
                "range":      local(str(rng)) if rng and not str(rng).startswith("_:") else "",
                "access":     access_level_local(g, uri),
            }
    return None

def upsert_property(g: Graph, data: dict) -> None:
    """Add or update an OWL property. data keys: local_id, label, definition, prop_type, domain, range, access."""
    uri = iroko_uri(data["local_id"])
    for p, o in list(g.predicate_objects(uri)):
        g.remove((uri, p, o))

    ptype_uri = PROP_TYPE_MAP.get(data.get("prop_type", "ObjectProperty"), OWL.ObjectProperty)
    g.add((uri, RDF.type, ptype_uri))

    if data.get("label"):
        g.add((uri, RDFS.label, Literal(data["label"], lang="en")))

    if data.get("definition"):
        g.add((uri, RDFS.comment, Literal(data["definition"], lang="en")))

    if data.get("domain"):
        g.add((uri, RDFS.domain, iroko_uri(data["domain"])))

    if data.get("range"):
        g.add((uri, RDFS.range, iroko_uri(data["range"])))

    if data.get("access"):
        g.add((uri, IROKO.minimumAccessLevel, iroko_uri(data["access"])))

# ---------------------------------------------------------------------------
# Delete any term
# ---------------------------------------------------------------------------

def delete_term(g: Graph, local_id: str) -> bool:
    """Remove all triples where the term is subject or object. Returns True if anything was removed."""
    uri = iroko_uri(local_id)
    removed = 0
    for p, o in list(g.predicate_objects(uri)):
        g.remove((uri, p, o))
        removed += 1
    for s, p in list(g.subject_predicates(uri)):
        g.remove((s, p, uri))
        removed += 1
    return removed > 0

# ---------------------------------------------------------------------------
# Move term between modules
# ---------------------------------------------------------------------------

def move_term(local_id: str, from_stem: str, to_stem: str) -> tuple[bool, str]:
    """
    Move all triples about local_id from from_stem.ttl to to_stem.ttl.
    Returns (success, message).
    """
    uri = iroko_uri(local_id)
    try:
        g_from = load_module(from_stem)
        g_to   = load_module(to_stem)
    except Exception as e:
        return False, f"Could not load modules: {e}"

    # Collect all triples about this URI
    triples_as_subject = list(g_from.predicate_objects(uri))
    triples_as_object  = list(g_from.subject_predicates(uri))

    if not triples_as_subject:
        return False, f"iroko:{local_id} not found in {from_stem}"

    # Copy to destination
    for p, o in triples_as_subject:
        g_to.add((uri, p, o))
    for s, p in triples_as_object:
        g_to.add((s, p, uri))

    # Remove from source
    for p, o in triples_as_subject:
        g_from.remove((uri, p, o))
    for s, p in triples_as_object:
        g_from.remove((s, p, uri))

    save_module(from_stem, g_from)
    save_module(to_stem,   g_to)
    return True, f"Moved iroko:{local_id} from {from_stem} to {to_stem}"

# ---------------------------------------------------------------------------
# Create new module
# ---------------------------------------------------------------------------

def create_module(stem: str, title: str, description: str, layer: str,
                  prefix: str, tag_text: str) -> tuple[bool, str]:
    """Scaffold a new TTL file with ontology metadata header."""
    path = VOCAB_DIR / f"{stem}.ttl"
    if path.exists():
        return False, f"{stem}.ttl already exists"

    from iroko_config import FRAMEWORK_VERSION
    import datetime
    today = datetime.date.today().isoformat()

    ns_uri = f"https://ontology.irokosociety.org/{stem}"
    content = f"""\
# -*- coding: utf-8 -*-
# ==========================================================================
# Iroko Framework — {title}  v{FRAMEWORK_VERSION}
# ==========================================================================
# Namespace: {IROKO_NS}
# Prefix:    {prefix}
# Layer:     {layer}
# ==========================================================================

@prefix rdf:     <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:     <http://www.w3.org/2002/07/owl#> .
@prefix xsd:     <http://www.w3.org/2001/XMLSchema#> .
@prefix skos:    <http://www.w3.org/2004/02/skos/core#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix iroko:   <{IROKO_NS}> .

<{ns_uri}>
    a owl:Ontology ;
    dcterms:title "{title}"@en ;
    dcterms:description "{description}"@en ;
    dcterms:creator "Iroko Historical Society" ;
    dcterms:issued "{today}"^^xsd:date ;
    dcterms:modified "{today}"^^xsd:date ;
    owl:versionInfo "{FRAMEWORK_VERSION}" ;
    owl:versionIRI <{ns_uri}/{FRAMEWORK_VERSION}> ;
    dcterms:license <https://creativecommons.org/publicdomain/zero/1.0/> ;
    dcterms:isPartOf <https://ontology.irokosociety.org/iroko-framework/> ;
    dcterms:requires <https://ontology.irokosociety.org/iroko-core> ;
    rdfs:seeAlso <https://ontology.irokosociety.org/iroko-framework/> .


# ===========================================================================
# Add classes, properties, and concept schemes below
# ===========================================================================
"""
    path.write_text(content, encoding="utf-8")
    return True, f"Created {stem}.ttl"

# ---------------------------------------------------------------------------
# Utility: all scheme IDs in a module (for concept form dropdowns)
# ---------------------------------------------------------------------------

def get_scheme_options(g: Graph) -> list[tuple[str, str]]:
    """Return [(local_id, label)] for all ConceptSchemes in graph."""
    opts = []
    for s in g.subjects(RDF.type, SKOS.ConceptScheme):
        if not str(s).startswith(IROKO_NS): continue
        opts.append((local(str(s)), pref_label(g, s) or label_en(g, s, RDFS.label) or local(str(s))))
    return sorted(opts, key=lambda x: x[1])

def get_class_options(g: Graph) -> list[tuple[str, str]]:
    """Return [(local_id, label)] for all OWL Classes in graph."""
    opts = []
    for c in g.subjects(RDF.type, OWL.Class):
        if not str(c).startswith(IROKO_NS): continue
        opts.append((local(str(c)), label_en(g, c, RDFS.label) or local(str(c))))
    return sorted(opts, key=lambda x: x[1])
