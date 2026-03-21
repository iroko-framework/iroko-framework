# Iroko Framework — Technical Architecture

**Version:** 1.2.0  
**Date:** February 2026  
**Maintainer:** Iroko Historical Society  
**Base URI:** `https://www.irokosociety.org/iroko-framework/`

---

## Overview

The Iroko Framework is a modular RDF/OWL vocabulary system for documenting sacred knowledge in Afro-Atlantic traditions. It implements a postcustodial archival architecture where communities maintain authority over their knowledge while enabling semantic interoperability with institutional repositories and linked data systems.

The framework is organized in three tiers. The Foundation (iroko-core) provides the infrastructure every module depends on. Five Governance Layer modules add composable sovereignty infrastructure — agency, authority, epistemic gating, narrative systems, and manifestation mode modeling. Ten Domain modules cover specific knowledge areas. Load only what your use case requires.

---

## Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TIER 1: FOUNDATION                           │
│  iroko-core   — access control · assertions · provenance ·     │
│                 concept schemes · narrative spine               │
└────────────────────────────┬────────────────────────────────────┘
                             │  all modules depend on core
┌────────────────────────────▼────────────────────────────────────┐
│                 TIER 2: GOVERNANCE LAYER                        │
│                                                                 │
│  iroko-agency        ag:    Sacred agents, spirits, ritual      │
│                             events, authorization chains        │
│                             references → authority              │
│                                                                 │
│  iroko-authority     auth:  Ritual authority, jurisdiction,     │
│                             authorization basis, recognition    │
│                             references → agency, epistemic      │
│                                                                 │
│  iroko-epistemic     ep:    Knowledge gating, disclosure        │
│                             permissions and restrictions        │
│                             references → authority              │
│                                                                 │
│  iroko-narrative     narr:  Story transmission chains,          │
│                             testimonies, fieldnotes,            │
│                             kinship claims, variants            │
│                             references → authority, agency,     │
│                                          epistemic, manifestation│
│                                                                 │
│  iroko-manifestation mani:  Agent manifestation modes           │
│                             and media                           │
│                             references → narrative, authority   │
└────────────────────────────┬────────────────────────────────────┘
                             │  dcterms:references (optional composition)
┌────────────────────────────▼────────────────────────────────────┐
│                  TIER 3: DOMAIN MODULES                         │
│                                                                 │
│  iroko-ewe       ewe:     Sacred plant knowledge (Darwin Core)  │
│  iroko-nkisi     nkisi:   Spiritual entities and kinship        │
│  iroko-travay    travay:  Ritual processes and ceremonies       │
│  iroko-ile       ile:     Religious houses and lineage          │
│  iroko-marca     marca:   Divination systems and verse corpora  │
│  iroko-ekpe      ekpe:    Initiatory societies and grades       │
│  iroko-veve      veve:    Graphic sign systems and diagrams     │
│  iroko-ngoma     ngoma:   Sacred music, rhythms, instruments    │
│  iroko-sankofa   sankofa: Reclamation movements, diaspora       │
│  iroko-qal       qal:     Sacred lexicons and liturgical lang.  │
└─────────────────────────────────────────────────────────────────┘
```

### Dependency declarations

All modules use `owl:imports` for hard dependencies (the module cannot function without it) and `dcterms:references` for optional composition (the module is designed to work with, but does not require, the referenced module).

Every domain module imports iroko-core. No domain module imports Governance Layer modules — they reference them. This means a researcher can load iroko-nkisi alone and have a functioning vocabulary; adding iroko-authority and iroko-narrative layers in additional granularity without breaking the base.

---

## Access Level System

### The six levels

Access levels are defined as SKOS concepts in `iroko:AccessLevelScheme`. Each concept carries a `skos:notation` value (integer) enabling numeric comparison in application filters.

| Concept URI | Label | Notation | Scope |
|---|---|---|---|
| `iroko:access-public-unrestricted` | Public — Unrestricted | 1 | Open publication, no restrictions |
| `iroko:access-public-attributed` | Public — Attributed | 2 | Open, with required source attribution |
| `iroko:access-community-only` | Community Only | 3 | Disclosed to initiated/affiliated members |
| `iroko:access-initiated-only` | Initiated Only | 4 | Disclosed only to initiated practitioners |
| `iroko:access-initiated-elder` | Initiated Elder | 5 | Disclosed only to senior initiates |
| `iroko:access-no-access` | No Access | 99 | Never exported to RDF; record existence only |

### Property-level annotation

Every property in every module carries `iroko:minimumAccessLevel`, which is declared as an `owl:AnnotationProperty` in Core. This annotation appears on the **property definition itself** in the vocabulary, not on data instances.

```turtle
# In iroko-narrative.ttl — property definition
narr:transmissionNote
    a owl:DatatypeProperty ;
    rdfs:label "transmission note"@en ;
    rdfs:range xsd:string ;
    iroko:minimumAccessLevel iroko:access-community-only ;
    rdfs:isDefinedBy <https://www.irokosociety.org/iroko-framework/narrative> .
```

At the data instance level, individual records carry `iroko:accessLevel` (an ObjectProperty defined in Core) on each instance:

```turtle
# In an archive's data graph — record instance
:record-2024-HAV-007
    a iroko:SacredEntity ;
    iroko:accessLevel iroko:access-community-only ;
    nkisi:syncreticIdentity :syncId-007 ;   # public property — OK
    travay:operationalSequence "..." ;       # community-only property — filtered
    ...
```

---

## The Enforcement Contract

**The vocabulary declares intent. Enforcement is the responsibility of the consuming application.**

OWL cannot enforce access at query time. `iroko:minimumAccessLevel` annotations on property definitions are machine-readable declarations that communicate the access requirements designed into the framework. Applications must implement filtering based on these annotations.

This is the correct architectural separation: the vocabulary defines what level each property requires; the archive or API decides what level the authenticated user holds; the application enforces the filter.

### SPARQL filter pattern

The following pattern shows how an application implementing the Iroko access model translates a user's access level into a query-time filter. The filter uses numeric notation values to exclude triples whose predicate requires a higher access level than the user holds.

```sparql
PREFIX iroko: <https://www.irokosociety.org/iroko-framework/core#>
PREFIX skos:  <http://www.w3.org/2004/02/skos/core#>

# Step 1: Retrieve the numeric notation for the user's access level.
# This would typically come from your authentication system.
# Example: user holds "community-only" access = notation 3.

SELECT ?subject ?predicate ?object
WHERE {
  # Your data graph
  GRAPH <https://archive.example.org/data/> {
    ?subject ?predicate ?object .
  }

  # Vocabulary graph — look up the access requirement for each predicate
  GRAPH <https://www.irokosociety.org/iroko-framework/vocab/> {
    OPTIONAL {
      ?predicate iroko:minimumAccessLevel ?requiredLevel .
      ?requiredLevel skos:notation ?requiredNotation .
    }
  }

  # Filter: include the triple only if:
  #   (a) the predicate has no access annotation (structural/public), OR
  #   (b) the required notation is <= the user's notation
  # USER_NOTATION should be bound to the authenticated user's level (e.g., 3)
  FILTER (
    !BOUND(?requiredNotation) ||
    ?requiredNotation <= 3    # replace 3 with USER_NOTATION from auth context
  )
}
```

### Access level notation reference for filter logic

```
notation 1 = public-unrestricted   → include for all users
notation 2 = public-attributed     → include for all users (apply attribution rule)  
notation 3 = community-only        → include for members and above
notation 4 = initiated-only        → include for initiated practitioners and above
notation 5 = initiated-elder       → include for senior initiates only
notation 99 = no-access            → never include; existence-only record
```

### Instance-level access filtering

For records that carry `iroko:accessLevel` on the instance (rather than inferring it from the predicate), an additional filter on the subject node is appropriate:

```sparql
# Exclude entire records marked above the user's threshold
FILTER (
  !EXISTS {
    ?subject iroko:accessLevel ?instanceLevel .
    ?instanceLevel skos:notation ?instanceNotation .
    FILTER (?instanceNotation > 3)   # USER_NOTATION
  }
)
```

### The `no-access` case

Properties annotated `iroko:access-no-access` (notation 99) are never exported to RDF in IHS's own publications. The record may appear with identifying metadata (a URI, a label) but the sensitive property values are withheld entirely. Consuming applications should never receive notation-99 triples; if they appear, treat as an export error.

---

## Module Combination Guide

The Governance Layer is designed to compose. The following table shows which modules to load for common archive use cases.

| Use Case | Core | Agency | Authority | Epistemic | Narrative | Manifestation | Domain |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| Minimal botanical archive | ✓ | | | | | | ewe |
| Spiritual entity catalog (public) | ✓ | | | | | | nkisi |
| Spirit entity catalog with assertion governance | ✓ | ✓ | ✓ | | ✓ | | nkisi |
| Ceremony documentation with access tiers | ✓ | | ✓ | ✓ | | | travay |
| House and lineage registry | ✓ | | ✓ | ✓ | | | ile |
| Divination corpus (verse restricted) | ✓ | | ✓ | | ✓ | | marca |
| Initiatory society with grade restrictions | ✓ | | ✓ | ✓ | | | ekpe |
| Graphic sign system with transmission docs | ✓ | | ✓ | | ✓ | | veve |
| Sacred music with consecrated instrument agency | ✓ | ✓ | ✓ | | ✓ | | ngoma |
| Reclamation movement with contested heritage | ✓ | | ✓ | | ✓ | | sankofa |
| Sacred lexicon with secret name gating | ✓ | | | ✓ | ✓ | | qal |
| Full sovereignty stack (all modules) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | any |
| Fieldwork archive with manifestation documentation | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | nkisi + travay |

**The "full sovereignty stack"** — Core + all five Governance Layer modules + any domain — is the recommended configuration for archives undertaking active fieldwork documentation where all governance dimensions are in play simultaneously.

### Governance Layer cross-reference graph

```
agency ──references──► authority
authority ──references──► agency, epistemic
epistemic ──references──► authority
narrative ──references──► authority, agency, epistemic, manifestation
manifestation ──references──► narrative, authority
```

All five modules are aware of each other. Loading all five means each module's composition points are fully resolved. Loading a subset still works — unresolved references simply have no data.

---

## Namespace Prefixes

All namespaces follow the pattern `https://www.irokosociety.org/iroko-framework/{module}#`.

```turtle
@prefix iroko:   <https://www.irokosociety.org/iroko-framework/core#> .
@prefix ag:      <https://www.irokosociety.org/iroko-framework/agency#> .
@prefix auth:    <https://www.irokosociety.org/iroko-framework/authority#> .
@prefix ep:      <https://www.irokosociety.org/iroko-framework/epistemic#> .
@prefix narr:    <https://www.irokosociety.org/iroko-framework/narrative#> .
@prefix mani:    <https://www.irokosociety.org/iroko-framework/manifestation#> .
@prefix ewe:     <https://www.irokosociety.org/iroko-framework/ewe#> .
@prefix nkisi:   <https://www.irokosociety.org/iroko-framework/nkisi#> .
@prefix travay:  <https://www.irokosociety.org/iroko-framework/travay#> .
@prefix ile:     <https://www.irokosociety.org/iroko-framework/ile#> .
@prefix marca:   <https://www.irokosociety.org/iroko-framework/marca#> .
@prefix ekpe:    <https://www.irokosociety.org/iroko-framework/ekpe#> .
@prefix veve:    <https://www.irokosociety.org/iroko-framework/veve#> .
@prefix ngoma:   <https://www.irokosociety.org/iroko-framework/ngoma#> .
@prefix sankofa: <https://www.irokosociety.org/iroko-framework/sankofa#> .
@prefix qal:     <https://www.irokosociety.org/iroko-framework/qal#> .
```

---

## External Vocabulary Alignments

The framework integrates with and extends the following external vocabularies:

| Vocabulary | Prefix | Use |
|---|---|---|
| OWL 2 | `owl:` | Class and property definitions throughout |
| SKOS | `skos:` | Concept schemes, controlled vocabularies, notation |
| Dublin Core Terms | `dcterms:` | Module metadata, provenance, title, creator |
| PROV-O | `prov:` | Provenance alignment (iroko-align-prov.ttl, optional) |
| Darwin Core | `dwc:` | Botanical specimen data (iroko-ewe) |
| FOAF | `foaf:` | Person/organization modeling (iroko-ile) |
| schema.org | `schema:` | Organization extension (iroko-ile) |
| OntoLex-Lemon | `ontolex:` | Lexicographic infrastructure (iroko-qal) |
| Music Ontology | `mo:` | Music documentation alignment (iroko-ngoma) |

The PROV-O alignment file (`iroko-align-prov.ttl`) is provided as a reference-only module mapping Iroko agency and event classes to PROV-O equivalents. Load it when interoperability with PROV-O-consuming systems is required.

---

## Vocabulary Statistics (v1.2.0)

| Module | Classes | Properties | Schemes | Concepts |
|---|---:|---:|---:|---:|
| iroko-core | 16 | 58 | 10 | 96 |
| iroko-agency | 10 | 8 | — | — |
| iroko-authority | 5 | 11 | 3 | 19 |
| iroko-epistemic | 5 | 5 | 1 | 8 |
| iroko-narrative | 5 | 22 | 5 | 35 |
| iroko-manifestation | 3 | 4 | 2 | 14 |
| iroko-ewe | 3 | 22 | 5 | 62 |
| iroko-nkisi | 4 | 31 | 6 | 54 |
| iroko-travay | 4 | 23 | 5 | 42 |
| iroko-ile | 6 | 38 | 5 | 58 |
| iroko-marca | 5 | 29 | 4 | 34 |
| iroko-ekpe | 6 | 34 | 4 | 30 |
| iroko-veve | 4 | 21 | 5 | 48 |
| iroko-ngoma | 5 | 28 | 4 | 33 |
| iroko-sankofa | 4 | 22 | 5 | 32 |
| iroko-qal | 6 | 23 | 5 | 37 |
| **Total** | **91** | **379** | **69** | **602** |

All 379 properties across all 16 modules carry `iroko:minimumAccessLevel` annotations.

---

## Design Principles

**Vocabularies declare; applications enforce.** The framework defines what level each property requires. Archive implementations decide what each authenticated user's level is. This separation keeps the vocabulary reusable across institutions with different access policies.

**The existence of restriction is public. The content is not.** A record marked `access-no-access` may still appear in a public index — its URI, type, and label are public. What is withheld is the property values that carry restricted content.

**Assertions, not facts.** Contested knowledge is modeled through `iroko:Assertion` reification rather than direct property assertions. Multiple lineage positions on the same claim can coexist. The framework does not adjudicate; it documents.

**Refusal is a positive act.** `ag:RefusalEvent` and `ag:StewardshipMandate` model community authority to withhold knowledge as first-class assertions, not merely as negative access flags. A community's refusal to disclose is as documentable as its disclosure.

**Researcher voice is structurally distinct from community voice.** `narr:Fieldnote` and `narr:Testimony` are separate classes. Archives cannot present researcher interpretation as community assertion.

---

## Contact and Citation

**Iroko Historical Society**  
Postcustodial Digital Archives for Afro-Atlantic Cultural Materials  
[www.irokosociety.org](https://www.irokosociety.org)

**Citation:**  
Iroko Historical Society. (2026). *Iroko Framework: Semantic Vocabularies for Afro-Atlantic Sacred Knowledge Systems* (v1.2.0). https://www.irokosociety.org/iroko-framework. CC0 1.0 Universal.
