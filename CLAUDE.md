# CLAUDE.md: iroko-framework

Ontology site for the Iroko Framework. Published at **ontology.irokosociety.org** (GitHub Pages, CNAME in repo root). Owner: Iroko Historical Society. Namespace: `https://ontology.irokosociety.org/iroko#`.

License posture is locked: **CC0 1.0** on the vocabulary (`dcterms:license <https://creativecommons.org/publicdomain/zero/1.0/>` in every TTL). The February 2026 CC BY 4.0 recommendation is superseded. CC0 on the vocabulary does not imply open access to community records; vocabulary and data are governed separately.

---

## The one rule that matters

**`vocab/*.ttl` is the only source of truth. Everything else in this repo is generated.**

Never hand-edit any of these. `validate.yml` regenerates and force-commits them on every push to `main`, so manual edits are silently destroyed:

- `vocab/*.jsonld`, `vocab/*.rdf`, `vocab/*.nt`
- `vocab/iroko-termlist.html`, `vocab/tradition-vocab.json`
- `iroko.html`, `iroko-*.html` (root module pages and URI alias landing pages)
- `iroko-framework/index.html`
- `sitemap.xml`
- version and date strings inside `docs/*.html`, `vocab/index.html`, and root `index.html`

Hand-maintained files: `vocab/*.ttl`, `docs/*.md`, `scripts/**`, `assets/**`, `README.md`, `CHANGELOG.md`, `robots.txt`.

---

## Layout

| Path | Contents |
|---|---|
| `vocab/` | 18 TTL files (16 modules + 2 alignments) plus their generated serializations |
| `scripts/` | Build, validation, and generation scripts; `iroko_config.py` is shared config |
| `scripts/manage/` | Local Flask ontology manager (`app.py`, `iroko_manager.py`, `launch-manager.bat`) |
| `docs/` | ARCHITECTURE, CONTRIBUTING, REUSE in both `.md` (source) and `.html` (generated) |
| `assets/` | Stylesheets, IHS logo, per-page Open Graph cards |
| `.github/workflows/` | `validate.yml`, `live-smoke.yml` |

### Module registry

Defined once, in `scripts/iroko_config.py` as `MODULES`. Do not duplicate the list anywhere else. Tuple fields are `(display_name, tier, tag_label, namespace_uri, ttl_stem)`.

- **Foundation (1):** Core
- **Governance (5):** Agency, Authority, Epistemic, Narrative, Manifestation
- **Domain (10):** Ewé, Nkisi, Travay, Ilé, Marca, Ékpè, Vèvè, Ngoma, Sankofa, Qal
- **Alignment (2):** PROV-O, Darwin Core

Sixteen modules plus two alignments. When the vault says "16 modules" it is excluding the alignments; both counts are correct in their own context.

---

## Build and publish

`scripts/deploy.sh` is the canonical publish helper and runs the whole sequence. Run it rather than invoking steps by hand.

```bash
bash scripts/validate_ttl.sh      # 1. rapper parse check on every vocab/*.ttl
python3 scripts/build_all.py      # 2. full regeneration, 7 steps
python3 scripts/check_site.py     # 3. site QA
```

`build_all.py` steps, in order:

1. `generate_vocab_html.py`: interactive module pages (`iroko-*.html`)
2. `generate_vocab_index.py`: `vocab/iroko-termlist.html`
3. `update_index_counts.py`: term counts across all index files
4. `generate_serializations.py`: JSON-LD, RDF/XML, N-Triples from each TTL
5. `generate_tradition_vocab.py`: `vocab/tradition-vocab.json` (consumed by the Per-Medjat catalog)
6. `generate_uri_aliases.py`: stable `/iroko` and `/iroko-*` landing pages
7. `generate_sitemap.py`: root `sitemap.xml`

Plus `update_docs_html()`, which patches version and date strings into the hand-maintained HTML.

Useful flags: `--dry-run`, `--step N` (repeatable), `--vocab DIR`, `--root DIR`.

`validate_ttl.sh` requires `rapper` from `raptor2-utils` (`sudo apt-get install raptor2-utils`, or `brew install raptor`). Python deps are in `requirements.txt`: rdflib, markdown, python-docx, Pillow, flask.

---

## CI

**`validate.yml`** runs on push and PR to `main` when workflow, assets, docs, scripts, vocab, or the root pages change. It installs rapper, validates TTL, runs `build_all.py`, runs `check_site.py`, and on push commits the generated artifacts back to `main` as "Auto-generate site artifacts". This is why hand-edited generated files do not survive.

**`live-smoke.yml`** runs daily at 06:17 UTC, after any Pages deployment, and on manual dispatch. It hits the live site with `check_site.py --no-local --live-base https://ontology.irokosociety.org`.

---

## Version state (verified 2026-08-09, needs reconciliation)

`scripts/iroko_config.py` declares `FRAMEWORK_VERSION = "1.4.0"` and `MONTH_YEAR = "May 2026"`. Actual `owl:versionInfo` in the TTL files:

| Version | Modules |
|---|---|
| 1.4.0 | Core, Ewé |
| 1.3.1 | Authority, Manifestation, Sankofa |
| 1.3.0 | Agency, Epistemic, Narrative, Ékpè, Ilé, Marca, Ngoma, Nkisi, Qal, Travay, Vèvè, PROV-O alignment |
| 1.0.0 | Darwin Core alignment |

Two things are stale and should be fixed before the next release:

1. `MONTH_YEAR` still reads "May 2026". It is patched into every generated page, so the whole published site currently carries a May date.
2. The vault hub (`Main-Vault/00_Maps/002_Iroko_Framework_Hub`) records v1.2.0 and reports a Core/Agency/Ewe conflict at v2.0.0 and v2.1.0. Neither figure matches this repo. The repo is authoritative on version; update the vault, not the reverse.

---

## Versioning policy (decided 2026-08-09)

**Modules version independently. The framework version is a release label, not a module version. They are different kinds of thing and must never be reconciled to a single number.**

Uneven module versions are the correct state, not drift. Marca sitting at 1.3.0 while Core sits at 1.4.0 is the system working.

### Why module-independent

Each TTL is a separately dereferenceable OWL ontology with its own `owl:versionIRI`. A consumer imports `iroko-marca`, not "the framework." Bumping all eighteen files whenever one changes destroys the only signal `versionInfo` carries: a consumer pinned to marca 1.3.0 would see 1.4.0, diff it, and find nothing changed. Do that a few times and downstream consumers stop trusting the version field, which is the failure mode this policy exists to prevent.

This follows OBO Foundry practice, where each ontology versions on its own cadence and releases are coordinated dated snapshots. It is the opposite of the schema.org model, which uses one monotonic version across an entire vocabulary. The schema.org approach works for a single-authority vocabulary published as one artifact; it does not work for a modular framework whose modules are meant to be adopted separately. Bounded adoption of individual modules is the whole point of the architecture.

### The two version fields

| Field | Lives in | Semantics | Bumps when |
|---|---|---|---|
| `owl:versionInfo` | each `vocab/*.ttl` | Semantic version of that module | That module's terms change. Patch for editorial, minor for added terms, major for a breaking change to an existing term |
| `FRAMEWORK_VERSION` | `scripts/iroko_config.py` | Release label for the coordinated publication as a whole | Any release ships. Monotonic |

The confusion recorded in the vault comes from these two numbers currently reading the same, 1.4.0, which makes them look like the same measurement. They are not.

### What closes this properly: a release manifest

Add `vocab/release.json`, generated at build time, pinning which module versions compose each framework release:

```json
{
  "framework": "1.4.0",
  "released": "2026-08-09",
  "modules": {
    "iroko-core": "1.4.0",
    "iroko-ewe": "1.4.0",
    "iroko-authority": "1.3.1",
    "iroko-marca": "1.3.0"
  }
}
```

With that file, "which framework version is this module in" stops being a question anyone has to reason about, the Zenodo deposit gets an exact composition to cite, and the vault stops needing to track module versions at all; it just points at the manifest. Not yet implemented. It is the correct next change to `build_all.py`.

### Release checklist

1. In the changed TTL only: bump `owl:versionInfo`, `owl:versionIRI`, and `dcterms:modified`. Leave every unchanged module alone.
2. In `iroko_config.py`: bump `FRAMEWORK_VERSION` and set `MONTH_YEAR` to the actual release month.
3. Run `bash scripts/deploy.sh`.
4. Record the release in `CHANGELOG.md`, naming which modules moved and which did not.

`iroko-authority.ttl`, `iroko-manifestation.ttl`, and `iroko-sankofa.ttl` carry an in-file comment block with the same procedure.

---

## Downstream coupling

`vocab/tradition-vocab.json` is consumed by the Per-Medjat catalog build. `medjat-tools/framework_vocab.py` and `framework_vocab.json` mirror framework terms for the Acquire and Steward tools. A term rename here propagates to two other repos. Check before renaming.

The v1.3.0 patch items tracked in the vault are `iroko:lapseCondition`, `iroko:successorAuthority`, `iroko:societyStatus`, `iroko:publicTitleType`, a domain broadening on `iroko:possessionTrigger`, and `ile:ForcedDissolution`. Confirm current status against the TTL before treating any of these as outstanding.

---

## Working conventions

- Never use em dashes in any prose written into this repo.
- Iroko terminology is exact. Do not substitute generalist synonyms for postcustodial, Iroko module, access tier, RefusalEvent, or StewardshipMandate.
- Do not use "diaspora" or "diasporic" in any prose. Use Afro-Atlantic, Atlantic world, or the specific geographic framing.
- The public posture is a published, usable vocabulary with a growth path, not a finished standard.
- DOI for the framework deposit: 10.5281/zenodo.18826673.
