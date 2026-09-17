# ADR 0002: Gender and dual-clock age as eldership and eligibility axes

**Status:** Proposed. Targets the v2.0.0 release line.
**Date:** 2026-09-16
**Affects:** `vocab/iroko-epistemic.ttl` (additive), `vocab/iroko-core.ttl` or
`vocab/iroko-ile.ttl` (additive, module placement is an open question),
`vocab/iroko-authority.ttl` (one possible additive concept).
**Supersedes:** nothing.

---

## Context

The request was to add two eldership markers to the access-tier system: gender as a
factor in who may hold certain offices, and initiatory age versus natal age as
competing clocks for seniority. Before drafting properties, I read the actual
tier definitions and the `RitualPractitioner`/`Authority`/`ReligiousOffice`
hierarchy on the `dev/v2.0.0` worktree (`iroko-framework-v2`, checked out from
`iroko-framework` as a git worktree, confirmed on branch `dev/v2.0.0`). Neither
axis is a blank slate, and the shape of what already exists should govern how the
new material is added.

### The six-tier system and where "elder" already sits

`iroko:AccessLevelScheme` in `iroko-core.ttl` is the six tiers: `access-public-unrestricted`
(1), `access-public-no-amplification` (2), `access-community-only` (3),
`access-initiated-only` (4), `access-initiated-elder` (5), and `access-no-access`
(99, operational sentinel, never exported). Tier 5 is already defined by social
recognition, not by a computed rule: "Requires elder designation within tradition,
recognized by community as having authority to access lineage-specific teachings."
Nothing currently feeds evidence into that designation. That is the gap the age
axis should fill, evidence, not an automatic gate, which matters for how it should
be modeled (see Decision, age).

`iroko:RitualPractitioner` (agency.ttl) is deliberately non-adjudicating: it covers
sanctioned and unsanctioned practitioners alike and explicitly defers legitimacy to
`iroko:Authority` (authority.ttl). `Authority` carries `authorityBasis`, drawn from
`AuthorityBasisScheme`: appointment, community-recognition, consecration, contested,
divinatory-selection, hereditary, succession. None of these is age-based, though
`basis-succession` and `authorityType-individual-elder` gesture at seniority without
formalizing it. `iroko:ReligiousOffice` (ile.ttl) is the third leg, the specific
held title, distinct from both `RitualPractitioner` (acting capacity) and
`Authority` (jurisdictional recognition). Any new property needs to pick the right
leg of this three-way split rather than blurring it.

### Gender is not a blank slate

Three mechanisms already touch gender, none of them general:

`iroko:basis-gender-regime` is already a `ConstraintBasis` in
`iroko-epistemic.ttl`'s `ConstraintBasisScheme`, defined exactly the way the
original proposal wanted it, tradition-specific, not a universal predicate, with
its own scope note pointing at `contestedStatus`/`assertionStatus` for disputed
cases. It is a classification concept, not yet wired to any actual constraint
instance.

`iroko:genderPolicy` (ekpe.ttl, domain `InitiatorySociety`) and
`iroko:genderRestriction` (marca.ttl, domain `DivinationSystem`) are free-text
datatype properties that already do the substantive work the proposal asked for,
documenting tradition-specific practice "without normative judgment." But each is
scoped to one module's class (initiatory societies for the first, divination
systems for the second), so a Lucumí Iyalorisha initiation, a Palo Tata Nganga
consecration, or a Vodou Houngan/Manbo ordination, none of them an
`InitiatorySociety` or `DivinationSystem` instance, has nowhere to record the same
kind of fact. Neither property is queryable across offices or traditions; both are
free text.

`iroko:governance-gender-divided` (ile.ttl, `GovernanceModelScheme`) is a different
thing again: an institution-level governance classification ("male and female
authorities govern separate domains"), not an individual eligibility rule.

One more thing worth flagging so it is not conflated with any of this: `iroko-nkisi.ttl`
has a "Polarity and Gender Modality" scheme that is explicitly about spirit and
cosmological gender in ritual address, not human practitioner eligibility. Its own
definition says so directly. The eldership work below has nothing to do with it.

### Age is a genuine blank slate, and it exposes a pre-existing gap

There is no birth date, no age property, anywhere in the framework, on `foaf:Person`
or `ArchivalPerson`. That part of the proposal really is new.

`iroko:InitiationEvent` (ile.ttl) is the natural anchor for "date of initiation,"
and it is already a first-class dated-event class in spirit, but it has no date
property of its own. Compare `iroko:conferralDate` (domain `ReligiousOffice`) and
`iroko:consecrationDate` (domain `SacredInstrument`, ngoma.ttl): the framework's own
pattern is a narrowly domain-scoped date property per event-bearing class, not one
shared generic property. `InitiationEvent` is the exception that fell through.
It is also not aligned to `prov:Activity` in `iroko-align-prov.ttl`, where
`RitualEvent` and `FieldworkEvent` are; `InitiationEvent` sits as a bare
`SacredEntity` subclass, parallel to `RitualEvent` rather than under it. This is a
pre-existing gap, independent of this request, but the age axis is what exposes it.

`iroko:governance-age-grade` already exists (`GovernanceModelScheme`, ile.ttl):
"Authority structured by seniority within initiation grade rather than individual
title." That is the closest existing concept to the ritual-clock idea, but it
classifies a House or society's governance model, not a person's standing, and
nothing currently reads it.

The framework already has a real answer to "how do you record an uncertain
historical date" for `ArchivalPerson`: `datePrecision`, `dateUncertain`,
`dateCentury`. A birth or initiation date property for eldership purposes should
carry that same apparatus rather than a bare `xsd:date`, for the same reason it
exists there: a documented nineteenth-century Palo initiate rarely has an exact,
undisputed birth date.

---

## Decision

### Axis 1: gender as a tradition-and-role-scoped eligibility constraint

Two ways to wire this in, in increasing order of surface area. I am not picking one;
this is the fork that most needs the author's judgment.

**Option A, minimal.** Add two object properties directly usable on the existing
`iroko:EpistemicConstraint`: `iroko:constraintTradition` (range: a `TraditionScheme`
concept) and `iroko:constrainsRole` (range: `iroko:RitualRole` or
`iroko:ReligiousOffice`). No new class. This works because most of these
restrictions are, at bottom, about who may be entrusted with restricted knowledge
(who may be taught the Ifá corpus, who may hold Ekpe secrets), which is what
`EpistemicConstraint` already governs. Then a gender-scoped constraint is: an
`EpistemicConstraint` instance, `hasConstraintBasis basis-gender-regime` (already
exists), `constraintTradition <tradition-X>`, `constrainsRole <role-Y>`, plus the
existing `constraintCondition` free text and `contestedStatus`/`assertionStatus`
for disputed cases. Two new properties, one module, no class hierarchy decision.

**Option B, fuller.** Add `iroko:EligibilityConstraint` as a new class, sibling to
`DisclosurePermission`/`DisclosureRestriction`/`SanctionedDisclosure`, all under
`EpistemicConstraint`. This keeps "who may know" and "who may hold or perform a
role" conceptually distinct, at the cost of a real class-hierarchy question: is
eligibility to hold office actually a kind of epistemic constraint (about
knowledge), or does it deserve its own abstract superclass alongside
`EpistemicConstraint`? `EpistemicConstraint`'s own module header says it "does NOT
encode ritual instructions... encodes governance claims about who may access what
knowledge," which is knowledge-access language, not office-eligibility language.
Forcing eligibility under it may be the same kind of category mismatch ADR 0001
found in the tradition tree.

Either option leaves `genderPolicy` and `genderRestriction` in place as optional
free-text summaries on their host classes; the new mechanism is what makes the
fact queryable across the whole framework rather than within one module. Whether to
eventually deprecate the two ad hoc properties is an open question below, not a
decision made here.

### Axis 2: natal age and initiatory age

Recommendation: do not add `hasNatalAge`/`hasInitiatoryAge` as stored integer-years
properties, the shape the original proposal suggested. An age computed relative to
today is the one kind of fact the rest of this framework does not store this way;
everything else is a dated fact or a dated event, precisely because the corpus is
historical and ages go stale the moment they are written down. Store the dates,
derive the age.

Concretely: add `iroko:birthDate` on `foaf:Person`, carrying the same
`datePrecision`/`dateUncertain`/`dateCentury` apparatus already used for
`ArchivalPerson`. Close the pre-existing gap by giving `iroko:InitiationEvent` its
own `iroko:initiationDate` (mirroring `conferralDate` and `consecrationDate`),
with the same precision apparatus, and add `InitiationEvent` to
`iroko-align-prov.ttl` under `prov:Activity` alongside `RitualEvent` and
`FieldworkEvent`. Natal age and initiatory age then become values computed from
these two dates against a reference date, not properties that need maintenance.

For "which clock this tradition or house counts by," the existing
`governance-age-grade` concept names the phenomenon but nothing reads it as a rule.
A minimal-diff alternative worth weighing against inventing a new property:
`AuthorityBasisScheme` already exists on `iroko:Authority` and already has
`basis-hereditary` and `basis-succession` sitting right next to where an
age-seniority basis would go. Adding `iroko:basis-age-seniority` ("authority
derives from ritual seniority order, counted by initiation date or age grade
rather than consecration or appointment") wires straight into `Authority` through
the property that already exists, `authorityBasis`, with zero new object
properties. The tradeoff: it answers "why is this person recognized as senior"
but not "which clock does this house use," which is a separate, house-level fact
that `governance-age-grade` was already reaching for. Both may be worth doing.

### How this feeds tier 5

`access-initiated-elder` stays exactly what it already is: a socially recognized
designation, not a computed boolean. The dated facts above (`birthDate`,
`initiationDate`) and the scoped gender constraint are evidence a curator or
community can point to when asserting elder recognition or an `Authority` record
with `basis-age-seniority`; none of it should auto-derive tier-5 status. That is
the same posture the framework already takes toward `RefusalEvent` and
`ContestedAuthority`: document the claim and its basis, do not adjudicate it in
the schema.

---

## Open questions for the author

1. Option A or Option B for the gender axis, direct properties on
   `EpistemicConstraint`, or a new `EligibilityConstraint` sibling class. This is
   the biggest single decision in this ADR.
2. Deprecate `genderPolicy` (ekpe.ttl) and `genderRestriction` (marca.ttl) once the
   general mechanism exists, keep both as free-text summaries alongside it, or
   leave them alone as module-local conveniences.
3. Does `birthDate` belong in Core (reusable beyond `foaf:Person` later) or is
   `foaf:Person`-only scope, defined in whichever module first needs it, enough?
   Same question for `initiationDate`: added to `iroko-ile.ttl` where
   `InitiationEvent` already lives, or promoted to Core alongside `eventDate`?
4. Fix the `InitiationEvent` date-and-PROV-alignment gap as part of this change, or
   file it separately since it predates and is independent of this request?
5. `basis-age-seniority` on `Authority`, a `seniorityBasis` property on `House`
   reusing `governance-age-grade`, or both? A tradition's default may not hold for
   every house within it, which argues for the house-level property regardless of
   what happens with `basis-age-seniority`.
6. Once natal and initiatory age are derivable from dates, does the Postgres layer
   (the Hyatt/Ewé migration already underway) need a materialized age column for
   query performance, or is computing it at query time sufficient? This reaches
   past the ontology into the database work, flagging it here so it is not lost.

None of these are blocking for the branch. All of them should be settled before any
TTL is written.

---

## References

- `vocab/iroko-core.ttl`, `AccessLevelScheme`, `RitualAuthority`, `ArchivalPerson`
  date-precision cluster (`datePrecision`, `dateUncertain`, `dateCentury`)
- `vocab/iroko-agency.ttl`, `RitualPractitioner`, `RefusalEvent`
- `vocab/iroko-authority.ttl`, `Authority`, `AuthorityBasisScheme`, `RitualRoleScheme`
- `vocab/iroko-epistemic.ttl`, `EpistemicConstraint`, `ConstraintBasisScheme`,
  `basis-gender-regime`
- `vocab/iroko-ile.ttl`, `ReligiousOffice`, `InitiationEvent`, `GovernanceModelScheme`
  (`governance-age-grade`, `governance-gender-divided`)
- `vocab/iroko-ekpe.ttl`, `genderPolicy`; `vocab/iroko-marca.ttl`, `genderRestriction`
- `vocab/iroko-align-prov.ttl`, current `prov:Activity` alignments
- `docs/adr/0001-tradition-axes.md`, precedent for this ADR's format and for
  treating culturally contested classifications as evidenced, contestable
  assertions rather than schema-level facts
