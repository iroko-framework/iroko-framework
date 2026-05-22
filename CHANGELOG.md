# Changelog

All notable changes to the Iroko Framework are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows semantic versioning: MAJOR for breaking IRI changes, MINOR for backward-compatible additions, PATCH for corrections and documentation fixes.

---

## [1.4.0] — 2026-05-21

### Summary

Structural expansion across four modules. Adds a neutral root class, archival person class, date precision model, geographic tradition hierarchy, public title sovereignty annotation, manuscript/text content classes, contributor role vocabulary, and two new Sankofa properties. All changes are additive; no existing IRIs were removed or altered.

---

### iroko-core.ttl

**New classes**

- `iroko:Entity` — neutral root class for the entire framework. All module-specific classes are (directly or transitively) subclasses of this. Replaces `iroko:SacredEntity` as the top of the class hierarchy without removing or renaming it.
- `iroko:ArchivalPerson` — a person documented in archival records, defined by their documentary trace rather than personal attributes. Subclass of `iroko:Entity` (not `iroko:SacredEntity`). Designed for use with colonial records, notarial archives, and historical documentation projects such as "Havana to the Sabine."

**Modified classes**

- `iroko:SacredEntity` — added `rdfs:subClassOf iroko:Entity`. No other change; all existing subclass relationships are preserved.

**New annotation property**

- `iroko:publicTitleType` — sovereignty-relevant annotation on `dc:title` values, signaling when a title is a surrogate designation (colonial call number, archival label, institutional name) rather than a community-recognized name.

**New concept scheme: `iroko:PublicTitleTypeScheme`**

Five concepts: `iroko:title-archival-callnumber`, `iroko:title-colonial-designation`, `iroko:title-community-name`, `iroko:title-institutional-label`, `iroko:title-unknown`.

**New date precision properties**

- `iroko:datePrecision` (xsd:string) — controlled vocabulary: `exact`, `approximate`, `decade`, `century`, `unknown`.
- `iroko:dateCentury` (xsd:integer) — century as integer (e.g., `13` for thirteenth century). Use with `iroko:datePrecision "century"`.
- `iroko:dateUncertain` (xsd:boolean) — explicit uncertainty flag independent of precision level.
- `iroko:nativeDateExpression` (rdf:langString) — date as written in the source document, preserving original calendar system notation.

**Geographic tradition hierarchy**

Six new geographic region concepts added to `iroko:TraditionScheme` as top-level `skos:hasTopConcept` entries:

- `iroko:region-west-african`
- `iroko:region-central-african`
- `iroko:region-east-african`
- `iroko:region-southern-african`
- `iroko:region-north-african`
- `iroko:region-nile-valley`

Six Afro-Atlantic and syncretic traditions added as flat (non-regional) top concepts: `iroko:tradition-haitian-vodou`, `iroko:tradition-new-orleans-voodoo`, `iroko:tradition-obeah`, `iroko:tradition-pan-african`, `iroko:tradition-syncretic`, `iroko:tradition-afro-indigenous`.

`skos:broader` links added to existing mid-level concepts:

| Concept | Broader |
|---|---|
| `iroko:tradition-yoruba-derived` | `iroko:region-west-african` |
| `iroko:tradition-akan-derived` | `iroko:region-west-african` |
| `iroko:tradition-fon-ewe-derived` | `iroko:region-west-african` |
| `iroko:tradition-calabari` | `iroko:region-west-african` |
| `iroko:tradition-bantu-derived` | `iroko:region-central-african` |
| `iroko:tradition-kemetic` | `iroko:region-north-african` |

Note: `iroko:tradition-bantu-derived` carries a `skos:scopeNote` acknowledging that Bantu-speaking cultures span Central, East, and Southern Africa; the Central African placement reflects the geographic center of gravity of the attested Afro-Atlantic diaspora traditions, not a claim about the full extent of Bantu distribution.

---

### iroko-sankofa.ttl

**New object property**

- `iroko:sourceRegion` — the continental African geographic region toward which a movement, return event, or heritage relationship is oriented. Range: `skos:Concept` (intended: geographic region concepts from `iroko:TraditionScheme`). Distinct from `iroko:sourceTradition`, which links to a specific cultural-linguistic tradition concept.

**New datatype property**

- `iroko:geographicLocus` — the city, country, or region where a movement, return event, or reconstructed practice was primarily based or most active. Range: `rdf:langString`.

**Module description update**

Added scope note: "The use of terms such as 'return', 'diaspora', and 'reclamation' reflects the self-description of the movements documented here, not a normative position of the Iroko Framework on questions of African identity or belonging."

---

### iroko-manifestation.ttl

**New classes**

- `iroko:ManuscriptObject` — a physical manuscript carrier (FRBR Object / vHMML Object level). Subclass of `iroko:DocumentaryEvidence`. Represents the physical artifact: a specific codex, scroll, or bound volume.
- `iroko:TextContent` — an intellectual or textual work carried by a manuscript (FRBR Work / vHMML Contents level). Subclass of `iroko:SacredEntity`. Represents the text as a distinct intellectual entity independent of any particular physical carrier.

**New properties**

- `iroko:carriersText` (object) — links a `ManuscriptObject` to the `TextContent` it carries. Range: `iroko:TextContent`.
- `iroko:carriedBy` (object) — inverse of `iroko:carriersText`. Links a `TextContent` to the `ManuscriptObject` that carries it.
- `iroko:physicalSupport` (object) — the material support of a `ManuscriptObject`. Range: `skos:Concept` (intended: `iroko:PhysicalSupportScheme`).
- `iroko:textLanguage` (datatype) — language of a `TextContent`. Range: `xsd:string` (BCP 47 tag or descriptive label for undocumented languages).
- `iroko:textScript` (datatype) — writing system of a `TextContent`. Range: `xsd:string` (ISO 15924 code or descriptive label).
- `iroko:uniformTitle` (datatype) — standardized title for a `TextContent` for disambiguation and cross-reference. Range: `rdf:langString`.

**New concept scheme: `iroko:PhysicalSupportScheme`**

Ten concepts: `iroko:support-parchment`, `iroko:support-paper`, `iroko:support-papyrus`, `iroko:support-stone`, `iroko:support-ostracon`, `iroko:support-textile`, `iroko:support-metal`, `iroko:support-wood`, `iroko:support-clay`, `iroko:support-other`.

Note: `iroko:support-ostracon` carries a `skos:scopeNote` noting its prevalence in Nubian (DBMNT) documentary materials.

---

### iroko-authority.ttl

**New class**

- `iroko:ContributorRole` — a subclass of `skos:Concept` representing the specific function of a person in the production, transmission, or reception of a manuscript or text. Derived from the vHMML contributor role taxonomy (CC BY 4.0). Distinct from `iroko:RitualRole`.

**New object property**

- `iroko:hasContributorRole` — links a participant to their `ContributorRole` in a documentary context. Range: `iroko:ContributorRole`. For persons linked to specific manuscripts, reification or an `iroko:Assertion` pattern is recommended to attach role context.

**New concept scheme: `iroko:ContributorRoleScheme`**

Fourteen concepts (all prefixed `role-contrib-` to avoid collision with existing `iroko:RitualRole` concepts):

`iroko:role-contrib-scribe`, `iroko:role-contrib-patron`, `iroko:role-contrib-commissioner`, `iroko:role-contrib-translator`, `iroko:role-contrib-compiler`, `iroko:role-contrib-artist`, `iroko:role-contrib-notary`, `iroko:role-contrib-editor`, `iroko:role-contrib-dedicatee`, `iroko:role-contrib-recipient`, `iroko:role-contrib-bookseller`, `iroko:role-contrib-publisher`, `iroko:role-contrib-unspecified`, `iroko:role-contrib-attributed`.

Note: `iroko:role-contrib-notary` carries a `skos:scopeNote` on its particular importance for colonial-era documentation in Spanish and French notarial archives.

---

### iroko-ewe.ttl

**Version normalization only** — no content changes. Version corrected from the anomalous `2.1.0` to `1.4.0` for consistency with the framework-wide versioning scheme. `owl:priorVersion` points to `iroko-ewe/2.1.0` to preserve the version history record.

---

## [1.3.0] — 2026-02-25

Initial stable multi-module release. Established core architecture, governance layer, domain modules, and alignment modules. See commit history for full detail.

---
