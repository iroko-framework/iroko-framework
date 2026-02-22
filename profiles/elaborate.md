# Iroko Ontology Profiles: Elaborate

This document defines an elaborate, sovereignty-aligned usage profile for the Iroko ontology stack. The elaborate profile extends the minimal profile with explicit modeling of sacred agency, ritual events, manifestation, and epistemic constraints.

## Purpose

- Model sacred agents as participants in governance, action, and disclosure regimes.
- Represent ritual events as structured activities that can generate claims, policies, and records.
- Capture temporal regimes and context dependence without flattening plural truths.
- Preserve interoperability pathways through PROV-O compatible structure, while maintaining Iroko semantic sovereignty.

## Recommended modules

- `core.ttl` (Iroko core)
- `iroko-align-prov.ttl` (reference-only PROV alignments)
- `iroko-agency.ttl`
- `iroko-manifestation.ttl` (optional, when manifestation detail is needed)
- `iroko-epistemic.ttl` (optional, when knowledge gating must be modeled)

## Elaborate commitments

### 1. Sacred agency

- Use `iroko-ag:SacredAgent` and `iroko-ag:Spirit` for non-human agency.
- Use `iroko-ag:RitualEvent` as a base class for ritual activities.
- Use event subclasses when needed:
  - `iroko-ag:ManifestationEvent`
  - `iroko-ag:AuthorizationEvent`
  - `iroko-ag:RefusalEvent`

### 2. Event to outcome linkage

Ritual events should be able to produce outcomes:

- Use `iroko-ag:hasOutcome` to link an event to:
  - `iroko:RelationshipAssertion`
  - `iroko:AccessPolicy`
  - `iroko-ep:EpistemicConstraint` (if used)
  - other outcome entities

### 3. Manifestation modeling (optional module)

When a spirit presence claim requires structure:

- `iroko-ma:ManifestationModeScheme` provides controlled terms.
- Use `iroko-ma:hasManifestationMode` and `iroko-ma:manifestsThroughMedium`.
- Use `iroko-ma:hasTemporalVariation` when manifestation varies by season, cycle, or event.

### 4. Epistemic constraints (optional module)

When secrecy and disclosure conditions must be modeled beyond access labels:

- Use `iroko-ep:EpistemicConstraint` and subclasses.
- Use `iroko-ep:ConstraintBasisScheme` to record basis types.
- Attach constraints to policies, records, or assertions with `iroko-ep:hasEpistemicConstraint`.
- Use `iroko-ep:hasTemporalVariation` when constraints vary by time or context.

### 5. Temporal variation as a cross-cutting qualifier

Temporal regime qualifiers should be attached consistently:

- Prefer attaching `iroko:temporalVariation` to assertion nodes.
- Attach `iroko:hasTemporalVariation` to resources or events when not using assertion reification.

## Interoperability posture

- Use subclass alignments to PROV-O classes via `iroko-align-prov.ttl`.
- Avoid equivalence axioms that collapse Iroko semantics into external semantics.
- Prefer external property reuse in instance data when needed, while keeping Iroko extensions orthogonal.

## Backward compatibility

Existing minimal-profile graphs remain valid under this profile. Elaborate graphs simply add more structure, using the same stable identifiers and schemes.
