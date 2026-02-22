# Iroko Ontology Profiles: Minimal

This document defines a minimal, sovereignty-aligned usage profile for the Iroko ontology stack. The minimal profile is designed to remain compatible with the elaborate profile without requiring retooling later.

## Purpose

- Provide a stable core for modeling ritual, cultural, and historical sovereignty.
- Support contested claims and provenance without forcing deep event modeling.
- Keep interoperability pathways open through reference-only alignment to PROV-O.

## Required modules

- `core.ttl` (Iroko core)
- Optional: `iroko-align-prov.ttl` (reference-only PROV alignments)

The minimal profile does not require loading `iroko-agency.ttl`, `iroko-manifestation.ttl`, or `iroko-epistemic.ttl`.

## Minimal commitments

### 1. Claim-first modeling

Use assertion nodes for contested or context-sensitive statements.

- `iroko:RelationshipAssertion`
- `iroko:AssertionStatusScheme`
- Optional qualifiers on assertions:
  - `iroko:temporalVariation` (if temporal regime matters)
  - `iroko:minimumAccessLevel` (jurisdiction and stewardship boundary)

### 2. Jurisdiction and access labeling

- Use `iroko:AccessLevelScheme` concepts.
- Use `iroko:minimumAccessLevel` with scheme concepts, not literals.

### 3. Temporal variation (optional but standardized)

If a claim varies by season, cycle, event, or context:

- use `iroko:temporalVariation` on the assertion node, or
- use `iroko:hasTemporalVariation` on a resource when you are not reifying the statement.

Use concepts from `iroko:TemporalVariationScheme`.

## What is intentionally excluded

- Detailed ritual event typing (RitualEvent subclasses)
- Manifestation modes and medium modeling
- Epistemic constraint modeling beyond access labels
- Authorization chains

These can be introduced later by adding the relevant modules, without changing existing URIs.

## Forward compatibility

The minimal profile is forward-compatible with the elaborate profile because it:

- keeps the same namespaces and identifiers
- treats advanced constructs as optional layers, not replacements
- uses claim nodes as the stable attachment point for future qualifiers
