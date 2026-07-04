"""
iroko_config.py — Shared configuration for all Iroko Framework build scripts.

Import from this module rather than duplicating constants across scripts.
"""

# ---------------------------------------------------------------------------
# Release info — update these two lines each release
# ---------------------------------------------------------------------------
FRAMEWORK_VERSION = "1.4.0"
MONTH_YEAR        = "May 2026"

# ---------------------------------------------------------------------------
# Namespace
# ---------------------------------------------------------------------------
IROKO_NS = "https://ontology.irokosociety.org/iroko#"

# ---------------------------------------------------------------------------
# Module registry
# Used by: generate_vocab_index.py, update_index_counts.py, manage/app.py
# Tuple fields: (display_name, tier, tag_label, namespace_uri, ttl_stem)
# ---------------------------------------------------------------------------
MODULES = [
    ("Core",          "Foundation", "Core",          IROKO_NS, "iroko-core"),
    ("Agency",        "Governance", "Agency",        IROKO_NS, "iroko-agency"),
    ("Authority",     "Governance", "Authority",     IROKO_NS, "iroko-authority"),
    ("Epistemic",     "Governance", "Epistemic",     IROKO_NS, "iroko-epistemic"),
    ("Narrative",     "Governance", "Narrative",     IROKO_NS, "iroko-narrative"),
    ("Manifestation", "Governance", "Manifestation", IROKO_NS, "iroko-manifestation"),
    ("Ewé",           "Domain",     "Botanical",     IROKO_NS, "iroko-ewe"),
    ("Nkisi",         "Domain",     "Entities",      IROKO_NS, "iroko-nkisi"),
    ("Travay",        "Domain",     "Ritual",        IROKO_NS, "iroko-travay"),
    ("Ilé",           "Domain",     "Lineage",       IROKO_NS, "iroko-ile"),
    ("Marca",         "Domain",     "Divination",    IROKO_NS, "iroko-marca"),
    ("Ékpè",          "Domain",     "Societies",     IROKO_NS, "iroko-ekpe"),
    ("Vèvè",          "Domain",     "Graphic",       IROKO_NS, "iroko-veve"),
    ("Ngoma",         "Domain",     "Music",         IROKO_NS, "iroko-ngoma"),
    ("Sankofa",       "Domain",     "Movements",     IROKO_NS, "iroko-sankofa"),
    ("Qal",           "Domain",     "Language",      IROKO_NS, "iroko-qal"),
    ("PROV-O Alignment", "Alignment", "Alignment",   IROKO_NS, "iroko-align-prov"),
    ("Darwin Core Alignment", "Alignment", "Alignment", IROKO_NS, "iroko-align-dwc"),
]

# Stems only — useful when you just need to iterate TTL files
MODULE_STEMS = [stem for *_, stem in MODULES]

# ---------------------------------------------------------------------------
# Module config — rich metadata for HTML generation
# Used by: generate_vocab_html.py, manage/app.py
# ---------------------------------------------------------------------------
MODULE_CONFIG = {
    "iroko-core": {
        "title":    "Core Vocabulary",
        "subtitle": "Cross-module governance infrastructure: access control, assertions, provenance, concept schemes",
        "tag_cls":  "tag-core", "tag_text": "Core",
        "prefix":   "iroko:", "dot_cls": "dot-core",
        "layer":    "Foundation",
    },
    "iroko-agency": {
        "title":    "Agency Module — Sacred Agents & Events",
        "subtitle": "Sovereignty-aligned agency model: spirits, ritual events, authorization chains",
        "tag_cls":  "tag-agency", "tag_text": "Agency",
        "prefix":   "ag:", "dot_cls": "dot-agency",
        "layer":    "Governance",
    },
    "iroko-authority": {
        "title":    "Authority Module — Ritual Governance",
        "subtitle": "Authority types, jurisdictions, basis, and recognition networks",
        "tag_cls":  "tag-authority", "tag_text": "Authority",
        "prefix":   "auth:", "dot_cls": "dot-authority",
        "layer":    "Governance",
    },
    "iroko-epistemic": {
        "title":    "Epistemic Module — Knowledge Gating",
        "subtitle": "Disclosure constraints, permissions, and epistemic governance",
        "tag_cls":  "tag-epistemic", "tag_text": "Epistemic",
        "prefix":   "ep:", "dot_cls": "dot-epistemic",
        "layer":    "Governance",
    },
    "iroko-narrative": {
        "title":    "Narrative Module — Sacred Story Systems",
        "subtitle": "Transmission chains, variant relations, kinship claims, interpretive stances",
        "tag_cls":  "tag-narrative", "tag_text": "Narrative",
        "prefix":   "narr:", "dot_cls": "dot-narrative",
        "layer":    "Governance",
    },
    "iroko-manifestation": {
        "title":    "Manifestation Module — Sacred Agent Modes",
        "subtitle": "Manifestation modes and media: possession, dream, divination, symbolic presence",
        "tag_cls":  "tag-manifestation", "tag_text": "Manifestation",
        "prefix":   "mani:", "dot_cls": "dot-manifestation",
        "layer":    "Governance",
    },
    "iroko-ewe": {
        "title":    "Ewé Module — Sacred Plant Knowledge",
        "subtitle": "Ritual, medicinal, and access governance over botanical data. Darwin Core integration via iroko-align-dwc.",
        "tag_cls":  "tag-botanical", "tag_text": "Botanical",
        "prefix":   "ewe:", "dot_cls": "dot-botanical",
        "layer":    "Domain",
    },
    "iroko-nkisi": {
        "title":    "Nkisi Module — Spiritual Entities",
        "subtitle": "Spiritual entities, orisa, lwa, mpungo, and cross-tradition kinship",
        "tag_cls":  "tag-entities", "tag_text": "Entities",
        "prefix":   "nkisi:", "dot_cls": "dot-entities",
        "layer":    "Domain",
    },
    "iroko-travay": {
        "title":    "Travay Module — Ritual Processes",
        "subtitle": "Ritual processes, ceremonies, initiatory rites, and sequential protocol",
        "tag_cls":  "tag-ritual", "tag_text": "Ritual",
        "prefix":   "travay:", "dot_cls": "dot-ritual",
        "layer":    "Domain",
    },
    "iroko-ile": {
        "title":    "Ilé Module — Houses, Lineage & Religious Office",
        "subtitle": "Religious institutions, initiation genealogy, and office transmission",
        "tag_cls":  "tag-lineage", "tag_text": "Lineage",
        "prefix":   "ile:", "dot_cls": "dot-lineage",
        "layer":    "Domain",
    },
    "iroko-marca": {
        "title":    "Marca Module — Divination Systems",
        "subtitle": "Sacred signs, reading records, and verse corpora",
        "tag_cls":  "tag-divination", "tag_text": "Divination",
        "prefix":   "marca:", "dot_cls": "dot-divination",
        "layer":    "Domain",
    },
    "iroko-ekpe": {
        "title":    "Ékpè Module — Initiatory Societies",
        "subtitle": "Graded societies, esoteric governance, society status, and masquerade traditions",
        "tag_cls":  "tag-societies", "tag_text": "Societies",
        "prefix":   "ekpe:", "dot_cls": "dot-societies",
        "layer":    "Domain",
    },
    "iroko-veve": {
        "title":    "Vèvè Module — Graphic Sign Systems",
        "subtitle": "Sacred diagrams, signs, and esoteric scripts",
        "tag_cls":  "tag-graphic", "tag_text": "Graphic",
        "prefix":   "veve:", "dot_cls": "dot-graphic",
        "layer":    "Domain",
    },
    "iroko-ngoma": {
        "title":    "Ngoma Module — Sacred Music",
        "subtitle": "Rhythms, songs, instruments, musician lineages, and possession triggers",
        "tag_cls":  "tag-music", "tag_text": "Music",
        "prefix":   "ngoma:", "dot_cls": "dot-music",
        "layer":    "Domain",
    },
    "iroko-sankofa": {
        "title":    "Sankofa Module — Documentary Apparatus &amp; Reclamation Movements",
        "subtitle": "Colonial slave paper, diaspora returns, reconstructed practice, and heritage relationships",
        "tag_cls":  "tag-upcoming", "tag_text": "Movements",
        "prefix":   "sankofa:", "dot_cls": "dot-other",
        "layer":    "Domain",
    },
    "iroko-qal": {
        "title":    "Qal Module — Sacred Lexicons",
        "subtitle": "Liturgical language, esoteric terminology, and sacred lexicography",
        "tag_cls":  "tag-language", "tag_text": "Language",
        "prefix":   "qal:", "dot_cls": "dot-language",
        "layer":    "Domain",
    },
    "iroko-align-prov": {
        "title":    "PROV-O Alignment",
        "subtitle": "Alignment of Iroko Framework agency and event classes to W3C PROV-O",
        "tag_cls":  "tag-core", "tag_text": "Alignment",
        "prefix":   "iroko:", "dot_cls": "dot-core",
        "layer":    "Alignment",
    },
    "iroko-align-dwc": {
        "title":    "Darwin Core Alignment",
        "subtitle": "Alignment of Iroko Framework plant classes and properties to Darwin Core",
        "tag_cls":  "tag-core", "tag_text": "Alignment",
        "prefix":   "iroko:", "dot_cls": "dot-core",
        "layer":    "Alignment",
    },
}

# ---------------------------------------------------------------------------
# Access level map
# Used by: generate_vocab_html.py, manage/app.py
# ---------------------------------------------------------------------------
ACCESS_MAP = {
    "access-public-unrestricted":     ("pub",  "Public"),
    "access-public-no-amplification": ("pub",  "Public · No Amplification"),
    "access-public-attributed":       ("pub",  "Public · Attributed"),
    "access-community-only":          ("comm", "Community"),
    "access-initiated-only":          ("init", "Initiated"),
    "access-initiated-elder":         ("init", "Initiated Elder"),
    "access-no-access":               ("none", "No Access"),
}

# Stems of TTL files that should not be processed by the HTML generator
KNOWN_SKIPS = {
    "iroko-nkisi-patch",
    "ewe-plants-v0_2_1",
    "iroko-vocab-v0_2_1",
    "iroko-core-v2",
    "iroko-ile-v2",
}
