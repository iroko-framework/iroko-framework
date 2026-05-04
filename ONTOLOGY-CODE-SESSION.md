# Iroko Framework — Ontology Build Pipeline Overhaul
## Seed Brief for Claude Code Session

**Project:** `iroko-framework` (GitHub: irokosociety/iroko-framework)
**Maintainer:** Délé Fágbèmí Ọ̀. (Ayodele Odiduro)
**Session goal:** Fix the HTML generation pipeline so that concept chips carry stable anchor IDs, add a tradition management CLI, and export a shared vocabulary endpoint that downstream tools (Per-Medjat catalog) can consume without scraping HTML.

---

## Repo Structure

```
iroko-framework/
├── vocab/
│   ├── iroko-core.ttl          ← source of truth for all concepts
│   ├── iroko-agency.ttl
│   ├── iroko-authority.ttl
│   ├── iroko-epistemic.ttl
│   ├── iroko-narrative.ttl
│   ├── iroko-manifestation.ttl
│   ├── iroko-ewe.ttl
│   ├── iroko-core.html         ← GENERATED — do not edit manually
│   ├── iroko-termlist.html     ← GENERATED
│   └── index.html
├── scripts/
│   ├── build_all.py            ← orchestrator (steps 1–4 + docs patching)
│   ├── generate_vocab_html.py  ← v8 rdflib generator (primary target)
│   ├── generate_vocab_index.py
│   ├── update_index_counts.py
│   ├── generate_serializations.py
│   ├── deploy.sh               ← validate → generate → commit → push
│   └── validate_ttl.sh
├── docs/
│   ├── index.html
│   ├── ARCHITECTURE.html
│   ├── REUSE.html
│   └── CONTRIBUTING.html
└── index.html                  ← root landing page
```

Current release: `VERSION = "1.3.0"`, `MONTH_YEAR = "March 2026"` (in `build_all.py`).

---

## Critical Bug: Chip Divs Have No `id` Attributes

**File:** `scripts/generate_vocab_html.py`, lines 1053–1057

The generator renders concept scheme chips like this:

```python
for c in scheme["concepts"]:
    A(f"""          <div class="chip">
        <span class="chip-label">{h(c['label'])}</span>
        <span class="chip-id">iroko:{h(c['id'])}</span>
      </div>""")
```

The `<div class="chip">` has no `id`. External tools that want to link directly to a concept (e.g., `iroko-core.html#tradition-lucumi`) get scrolled to the top of the page instead.

**Fix:** Add `id="{c['id']}"` to each chip div:

```python
A(f"""          <div class="chip" id="{h(c['id'])}">
    <span class="chip-label">{h(c['label'])}</span>
    <span class="chip-id">iroko:{h(c['id'])}</span>
  </div>""")
```

This is a one-line change. Verify it works for all schemes across all modules (not just `iroko-core`).

---

## Secondary Bug: Hash Navigation Interception in Generated Pages

The JS in `iroko-core.html` (and possibly other generated pages) intercepts `hashchange` events to power the sidebar panel. This means clicking an anchor like `iroko-core.html#tradition-lucumi` triggers the sidebar logic rather than scrolling to the chip.

**Fix options (evaluate in order):**
1. On `hashchange`, check if the target element is a `.chip` and, if so, call `element.scrollIntoView()` before or after any sidebar logic.
2. Add a `data-no-sidebar` attribute to chip divs and short-circuit the handler for those targets.
3. Restructure the hash namespace so sidebar IDs and chip IDs use distinct prefixes.

This fix goes into the JS block inside `generate_vocab_html.py` — not into the generated HTML directly. The generated file is overwritten on every build.

---

## Task: Export `TRADITION_VOCAB` as a Shared JSON Endpoint

The Per-Medjat library catalog (`medjat.irokosociety.org/library/`) currently maintains its own JavaScript lookup table (`TRADITION_VOCAB`) hardcoded in its HTML. This duplicates data from `iroko-core.ttl` and will drift.

**Goal:** Generate a static `vocab/tradition-vocab.json` file during the build pipeline (step 1 or as a new step 5) so downstream tools can `fetch()` it instead of maintaining their own copy.

**Shape:**

```json
{
  "iroko:tradition-lucumi": {
    "prefLabel": "Lucumi",
    "altLabels": ["Regla de Ocha", "Santeria"],
    "broader": "iroko:tradition-yoruba-derived",
    "anchorId": "tradition-lucumi",
    "pageUrl": "https://ontology.irokosociety.org/vocab/iroko-core.html"
  },
  ...
}
```

The `anchorId` field should match the `id` attribute added to chip divs above, making this the single source for both the anchor links and the catalog lookup. Add the generation step to `build_all.py`.

---

## Task: `add-tradition.py` CLI

A script that lets the maintainer add a new `skos:Concept` to `iroko-core.ttl` interactively, then triggers a targeted rebuild.

**Minimum viable interface:**

```
python scripts/add-tradition.py
```

Prompts for:
- `prefLabel` (English)
- `altLabels` (comma-separated)
- `skos:broader` (offer tab-completion from existing concepts)
- `skos:definition` (optional)

Writes the Turtle block to `vocab/iroko-core.ttl`, validates with `rapper` (or `rdflib` if rapper unavailable), then runs `build_all.py --step 1` and `build_all.py --step 4` to regenerate the vocab page and serializations.

**Slug convention:** `iroko:tradition-{kebab-case-preflabel}` — strip diacritics, lowercase, replace spaces with hyphens (e.g., "Haitian Vodou" → `tradition-haitian-vodou`).

---

## Missing Traditions (Spotted in Per-Medjat Catalog)

The following traditions appear as Zotero tags in the Per-Medjat collection but have no corresponding `skos:Concept` in `iroko-core.ttl`. They need to be added before the next build:

- **New Orleans Voodoo** (distinct from Haitian Vodou; Louisiana-specific lineage)
- **Obeah** (Caribbean, particularly Anglophone islands)
- **Spiritual Baptists** (Trinidad and Tobago; African-Christian synthesis)
- **Rastafari** (if not already present — check)
- **Cuban Spiritism** / **Espiritismo** (distinct from Palo Monte; Kardecist influence)
- **Umbanda** (Brazilian; Candomblé + Spiritism synthesis)

Add all of these through `add-tradition.py` once that script exists. For now, they can be added manually to `iroko-core.ttl` following the existing pattern.

---

## Pipeline State at Session Start

The build pipeline is functional. Running `python scripts/build_all.py` completes all four steps without errors (as of last session). The `deploy.sh` validates TTL with `rapper`, runs the generator, commits, and pushes to GitHub Pages.

The chip `id` bug is the only known pipeline defect. All other features (cross-module connections, sidebar panels, JSON-LD/RDF/N-Triples serializations, term list) work correctly.

---

## Session Scope — Ordered Priority

1. Fix chip `id` emission in `generate_vocab_html.py` (one-line change, high impact)
2. Fix hash navigation interception in the generated page JS
3. Add `tradition-vocab.json` generation to the build pipeline
4. Write `add-tradition.py` CLI
5. Add missing traditions to `iroko-core.ttl`
6. Update `TRADITION_VOCAB` in `Per-Medjat/library/index.html` to `fetch()` from the JSON endpoint instead of the hardcoded table

Do not update `VERSION` or `MONTH_YEAR` in `build_all.py` until all changes are tested and the full build passes.
