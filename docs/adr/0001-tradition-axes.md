# ADR 0001: Separate the tradition axes

**Status:** Proposed. Targets the v2.0.0 release line.
**Date:** 2026-08-18
**Affects:** `vocab/iroko-core.ttl` (breaking), `vocab/iroko-sankofa.ttl` (additive),
`vocab/tradition-vocab.json` (shape change), and two downstream repos.
**Supersedes:** nothing. First ADR in this repo.

---

## Context

`iroko:TraditionScheme` currently holds 50 concepts in a single `skos:broader`
hierarchy. That hierarchy is carrying at least four different relations at once, and
the four are not interchangeable.

**Regional geography.** `region-west-african`, `region-central-african`,
`region-east-african`, `region-north-african`, `region-southern-african`,
`region-nile-valley`. Three of these have no children at all.

**Ethnolinguistic substrate.** `tradition-bantu-derived`, `tradition-akan-derived`,
`tradition-fon-ewe-derived`, `tradition-yoruba-derived`, `tradition-calabari`. These
are classifications *of* traditions, not traditions. They are prefixed `tradition-`
and sit inside the tradition tree.

**Compositional or political property as parent.** `tradition-syncretic` parents
Hoodoo, Espiritismo and 21 Divisiones. `tradition-afro-indigenous` parents Myal,
Garifuna, Kumina and Obeah. `tradition-pan-african` parents Rastafari. Syncretism is
a property that every Afro-Atlantic tradition has; it is not a tradition that other
traditions belong to.

**Genuine subsumption.** Palo Monte under Palo, Vodou Rada under Haitian Vodou. This
is the only relation `skos:broader` should be carrying, and it is the minority case.

### What this already breaks

`rollupToParent()` in the Per-Medjat catalog walks `broader` to the top-level
concept and displays that label. `tradition-hoodoo` has `skos:broader
iroko:tradition-syncretic`, which is top-level, so **every Hoodoo record displays as
"Syncretic."** The Hyatt corpus is 13,209 items. Meanwhile
`tradition-new-orleans-voodoo` sits at top level with no parent and displays
correctly, so the more specific tradition is the one that renders as a residual
category.

Derivation is asserted inconsistently. `tradition-arara` and
`tradition-candomble-jeje` sit under `tradition-fon-ewe-derived`. `tradition-haitian-vodou`
does not, despite being the case where Fon and Ewe derivation is most extensively
documented. The same relation is expressed for two traditions and omitted for a third.

Two concepts denote one tradition. `tradition-lucumi` and `tradition-santeria` are
siblings under Yoruba-Derived. They are the same tradition under an insider and an
outsider name.

Stale altLabels duplicate real concepts. `tradition-Palo` carries altLabels "Palo
Mayombe" and "Palo Monte" while both exist as narrower concepts.
`tradition-haitian-vodou` carries "Vodou Ghede", "Vodou Petwo" and "Vodou Rada" for
the same reason. Already logged in the vault; still present.

### What it is about to break

Four corpora are queued: Hyatt (extracted, 16,225 records), further Hoodoo and New
Orleans Voodoo texts, Haitian Vodou, and Benin Vodun.

**There is currently no correct place to put Benin Vodun.** The nearest concept is
`tradition-fon-ewe-derived`, which is a substrate label rather than a living
tradition. Vodun in Benin is simultaneously a tradition practiced today and the
substrate from which Haitian Vodou derives. A single `broader` tree cannot express
both, and forcing the choice loses whichever half is not chosen.

### Evidence from the Hyatt corpus

Not decisive on its own, and the tags are unreviewed, but it bears on how the
Hoodoo and New Orleans Voodoo relation should be modeled rather than assumed.

Across 16,225 records including 2,229 from New Orleans and Algiers, "gris-gris"
appears zero times in any spelling, as do wanga, ouanga, juju, Legba and Damballa,
verified against raw text rather than tags. "Voodoo" as a spelling appears 22 times
corpus-wide and zero times in a New Orleans record. "Hoodoo" appears 1,688 times and
is used at 8.5 percent in New Orleans, higher than in Memphis.

The core charm repertoire is uniform across the South: mojo hand 5.6 to 10.9 percent
in every region with no gradient. What varies is liturgical and follows the
Mississippi rather than the coast. Candle usage runs 10.8 percent in New Orleans,
8.7 in the Gulf and Delta, 5.1 in Memphis, and 0.2 in coastal Georgia and South
Carolina. Saint, holy water, church and altar follow the same gradient. Memphis
sitting mid-gradient rules out urbanization as the explanation.

On this evidence the New Orleans difference in the 1930s field record is liturgical
and commercial rather than genealogical. That is a claim to model as an evidenced
assertion, not to encode as a hierarchy.

Caveats belong with it. Hyatt titled the work *Hoodoo, Conjuration, Witchcraft,
Rootwork*, so hoodoo was his frame and informants may have accommodated it. Absence
in Hyatt is not absence in New Orleans practice; gris-gris is well attested in
nineteenth-century Louisiana sources. This is a finding about one field record.

---

## Decision

Split the single hierarchy into four axes, each modeled with the relation that
actually fits it.

### Axis 1: TraditionScheme carries subsumption only

A concept stays in `iroko:TraditionScheme` if it names a tradition someone practices
or has practiced. `skos:broader` is used only where the narrower concept is a
variety of the broader one within the same tradition.

Consequences: `tradition-hoodoo` becomes top level. `tradition-haitian-vodou` stays
top level with its three rites narrower. Palo keeps its two houses. Candomblé keeps
its three nations. `region-*` concepts leave the scheme entirely.

### Axis 2: a new CulturalSubstrateScheme

New `skos:ConceptScheme` in `iroko-core` holding ethnolinguistic and regional origin
concepts, with a new object property `iroko:hasCulturalSubstrate` linking a tradition
to one or more substrates.

Many-to-many is the point. Lucumí draws on Yoruba substrate; Palo on Bantu; Haitian
Vodou on Fon, Ewe, Kongo and more. Under the current model each tradition gets one
parent and the rest of its formation is unsayable.

### Axis 3: tradition-to-tradition claims become evidenced assertions

`iroko-sankofa` already has the machinery and it is not being used for this:
`sankofa:HeritageRelationship`, `HeritageRelationshipTypeScheme`,
`sankofa:sourceTradition`, `sankofa:targetTradition`, `sankofa:corridorJurisdiction`,
`sankofa:sourceRegion`, `sankofa:tradePeriod`, `sankofa:evidenceBase`,
`sankofa:groundedIn`, `sankofa:communityRecognition` with a recognition-status scheme.

Derivation, influence and contested descent become `HeritageRelationship` instances
carrying evidence and a recognition status, not `skos:broader` edges carrying
nothing. Benin Vodun to Haitian Vodou becomes an instance with a corridor, a period
and sources. New Orleans Voodoo to Hoodoo becomes an instance whose evidence can be
argued with.

Additive work in sankofa: this needs vocabulary in
`HeritageRelationshipTypeScheme`, which should minimally distinguish derivation,
substrate contribution, liturgical overlay, regional variant, and contested descent.

### Axis 4: records carry attestations, not traditions

This is the one that changes how the corpora are ingested.

A Hyatt item does not attest a tradition. It attests a practice element, at a place,
at a time, from an informant. Traditions are inferences over attestations.

Therefore: do not write `tradition-hoodoo` onto 13,209 records as a data fact. The
tradition claim lives at corpus level as an `iroko:Assertion` whose
`assertionSubject` is the corpus, whose asserter is Hyatt, and whose evidence is the
attestations. This is honest, because Hyatt is the one who called it hoodoo, and it
leaves the question open rather than settling it in the schema.

The practice-element vocabulary stays tradition-neutral. The same charm-object
concept surfaces as a mojo hand in Hyatt, an nkisi in Palo, a paket in Vodou.
Tradition-scoped vocabulary makes that invisible; neutral vocabulary with tradition
as an attestation property makes cross-corpus comparison a query rather than a
schema migration. With four corpora queued this is the difference between the model
holding and the model being rebuilt on the second import.

---

## Migration

**No published URI is ever deleted.** The vocabulary is CC0 with a Zenodo DOI and a
resolvable namespace, which means anything already dereferenced may be cited
somewhere. Concepts that move out of TraditionScheme are deprecated in place with
`owl:deprecated true`, a `skos:historyNote` explaining the change, and
`dcterms:isReplacedBy` pointing at the successor. They keep resolving.

### Concept disposition, all 50

| Disposition | Count | Concepts |
|---|---|---|
| Remain traditions, top level | 22 | Candomble, Haitian Vodou, Hoodoo, New Orleans Voodoo, Shango Baptist, Espiritismo, 21 Divisiones, Myal, Garifuna, Kumina, Obeah, Rastafari, Kemetic, Lucumí, Trinidad Orisha, Yoruba (continental), Palo, Quimbanda, Umbanda, Kromanti, Winti, Arara |
| Remain traditions, narrower under a genuine parent | 12 | Palo Mayombe, Palo Monte under Palo; Vodou Ghede, Vodou Petwo, Vodou Rada under Haitian Vodou; Candomble Angola, Candomble Jeje, Candomble Ketu under Candomble; Ausar Auset, Kemetic Orthodoxy under Kemetic; Abakua, Ekpe under a retained Cross River concept |
| Move to CulturalSubstrateScheme | 5 | Bantu-Derived, Akan-Derived, Fon/Ewe-Derived, Yoruba-Derived, Calabari/Cross River |
| Move to a geographic scheme or retire | 6 | the six `region-*` concepts, three of which have no children |
| Retire as parents | 3 | Syncretic/Creole, Afro-Indigenous, Pan-African Political-Spiritual |
| Merge | 1 | Santeria into Lucumí |
| Pending an open question | 1 | Oyotunji, top level or narrower under Lucumí |
| **Total** | **50** | |

Eleven concepts currently hang off a substrate or a property and become top-level
traditions linked by `hasCulturalSubstrate`: Palo, Quimbanda, Umbanda, Kromanti,
Winti, Arara, Myal, Garifuna, Kumina, Obeah, and the three under Syncretic.

Substrate concepts are deprecated at their `tradition-` URIs and replaced by
`substrate-` URIs. The `region-*` concepts are the weakest part of the current scheme
and retiring them in favour of TGN and GeoNames identifiers is the better linked-data
answer, which the external-alignment work would deliver anyway.

**Clean altLabels (2 concepts):** remove "Palo Mayombe" and "Palo Monte" from
`tradition-Palo`; remove "Vodou Ghede", "Vodou Petwo" and "Vodou Rada" from
`tradition-haitian-vodou`. Both duplicate real narrower concepts. Already logged in
the vault as pending data fixes; still present.

**Rename for consistency (2 concepts):** `tradition-Palo` to `tradition-palo` and
`tradition-Candomble-general` to `tradition-candomble`, with the capitalised forms
deprecated and redirected. Every other local name is lowercase.

**Add (1 concept, minimum):** a Benin Vodun concept as a top-level tradition, with
`hasCulturalSubstrate` to the Fon and Ewe substrate and a `HeritageRelationship` to
Haitian Vodou. This is the concept the current model cannot express and the reason
the change should not wait for the corpus to arrive.

---

## Consequences

### Breaking, and what breaks

This is a major change to `iroko-core`, so under the repo's versioning policy
`iroko-core.ttl` goes to **2.0.0**. `iroko-sankofa.ttl` gains vocabulary and goes to
**1.4.0**, a minor bump. No other module changes, and per policy no other module's
version moves. The framework release label becomes **2.0.0**.

`vocab/tradition-vocab.json` changes shape, because a tradition now has substrates
and relations rather than a single `broader` string. Its consumers:

1. **Per-Medjat** `library/index.html`, client-side `loadTraditionVocab()`,
   `TRADITION_LOOKUP`, `rollupToParent()`. The rollup logic needs revisiting rather
   than patching, since the reason it produced "Syncretic" is being removed.
2. **medjat-tools** `build_library/build_library.py` `resolve_tradition()`, plus
   `framework_vocab.py` and `framework_vocab.json`, which mirror framework terms for
   Acquire and Steward.

The repo's own CLAUDE.md warns that a term rename propagates to two other repos.
This ADR renames and deprecates a substantial set, so those two repos need a
coordinated change and should not be allowed to pick up a v2.0.0
`tradition-vocab.json` from a `main` they were not updated for. That is an argument
for doing this on a branch and merging deliberately, which is the plan.

### Not breaking

Nothing published is deleted. Every deprecated URI resolves and carries a
`dcterms:isReplacedBy`. A consumer pinned to `iroko-core` 1.4.0 is unaffected until
it chooses to move.

### Rejected alternatives

**Keep one tree and special-case the rollup.** Rejected. It treats the symptom. The
tree would still be unable to represent Benin Vodun, and every future corpus would
add another exception.

**Use `skos:related` throughout and abandon hierarchy.** Rejected. Palo Monte really
is a variety of Palo and Vodou Rada really is a rite within Haitian Vodou. Flattening
loses real structure to avoid modeling the rest.

**Defer until the Haitian and Benin corpora arrive.** Rejected. The migration cost is
proportional to how much data has been ingested under the wrong model. 16,225 Hyatt
records is the cheapest this will ever be.

---

## Open questions for the author

1. Does Oyotunji sit under Lucumí, or top level as a distinct reconstructionist
   tradition? This is a substantive claim either way.
2. Lucumí and Santeria: merge, or keep distinct with a scope note saying why?
3. Do the `region-*` concepts survive at all, or is TGN plus GeoNames the better
   answer once external alignment lands?
4. Is Kemetic/Revivalist a tradition in the same sense as the others, or a distinct
   category of modern reconstruction that deserves its own axis alongside substrate?
5. What is the correct name for the Benin concept: Vodun, Vodún, Benin Vodun?
6. Does the Cross River concept survive as a tradition parent for Abakuá and Ékpè, or
   does it move to substrate with both promoted to top level?

None of these are blocking for the branch. All of them should be settled before any
TTL is written.

---

## References

- `vocab/iroko-core.ttl`, `TraditionScheme`, 50 concepts as of v1.4.0
- `vocab/iroko-sankofa.ttl`, `HeritageRelationship` and related properties
- `docs/ARCHITECTURE.md`
- Vault: `Main-Vault/07_Corpus/Hoodoo/hyatt-corpus-structure.md` for the corpus figures
- Vault: `Main-Vault/11_Library/Per_Medjat/Hyatt/hyatt-access-architecture.md`
