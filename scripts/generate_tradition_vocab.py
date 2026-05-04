#!/usr/bin/env python3
"""
generate_tradition_vocab.py — Export TraditionScheme concepts as JSON.

Reads iroko-core.ttl and writes vocab/tradition-vocab.json with every
skos:Concept in iroko:TraditionScheme.  The catalog (Per-Medjat) fetches
this file at runtime — no hardcoded lookup table needed.

Usage:
    python generate_tradition_vocab.py              # auto-detect paths
    python generate_tradition_vocab.py --vocab DIR  # explicit vocab dir
    python generate_tradition_vocab.py --check      # validate only, no write
"""

import argparse
import json
import sys
from pathlib import Path

from rdflib import Graph, Namespace, SKOS, RDFS

IROKO_NS  = "https://ontology.irokosociety.org/iroko#"
VOCAB_URL = "https://ontology.irokosociety.org/vocab/iroko-core.html"
IROKO     = Namespace(IROKO_NS)

SCRIPT_DIR = Path(__file__).resolve().parent


def build_parser():
    p = argparse.ArgumentParser(
        description="Export TraditionScheme concepts to tradition-vocab.json"
    )
    p.add_argument("--vocab",  metavar="DIR", help="Path to vocab/ directory")
    p.add_argument("--check",  action="store_true",
                   help="Validate and report only; do not write output file")
    return p


def generate(vocab_dir: Path) -> tuple[list[dict], list[str]]:
    ttl_path = vocab_dir / "iroko-core.ttl"
    if not ttl_path.exists():
        print(f"  ✗ iroko-core.ttl not found at {ttl_path}")
        sys.exit(1)

    g = Graph()
    g.parse(str(ttl_path), format="turtle")

    concepts = []
    warnings = []

    for s in sorted(g.subjects(SKOS.inScheme, IROKO.TraditionScheme), key=str):
        local_name = str(s).split("#")[-1]

        # Convention check — all tradition concepts should follow tradition-* pattern
        if not local_name.startswith("tradition-"):
            warnings.append(
                f"  ⚠ Naming: '{local_name}' does not follow tradition-* convention"
                f" — rename to 'tradition-{local_name.lower().replace(' ', '-')}'"
                f" in the manager to fix anchor links"
            )

        pref = str(g.value(s, SKOS.prefLabel) or g.value(s, RDFS.label) or local_name)
        alts = sorted({str(o) for o in g.objects(s, SKOS.altLabel)})

        # Warn if this concept's prefLabel appears as an altLabel on another concept
        # (indicates a split that wasn't cleaned up — e.g. Shango Baptist as altLabel
        # on Trinidad Orisha after Shango Baptist became its own concept)
        for other in g.subjects(SKOS.altLabel, g.value(s, SKOS.prefLabel)):
            if other != s:
                other_local = str(other).split("#")[-1]
                warnings.append(
                    f"  ⚠ Data: '{pref}' is still listed as altLabel on '{other_local}'"
                    f" — remove it from that concept in the manager"
                )

        broader_node = g.value(s, SKOS.broader)
        broader = str(broader_node).split("#")[-1] if broader_node else None
        defn      = str(g.value(s, SKOS.definition) or "")
        scope     = str(g.value(s, SKOS.scopeNote)  or "")

        concepts.append({
            "localName":  local_name,
            "prefLabel":  pref,
            "altLabels":  alts,
            "uri":        str(s),
            "anchorUrl":  f"{VOCAB_URL}#{local_name}",
            "broader":    broader,
            "definition": defn,
            "scopeNote":  scope,
        })

    return concepts, warnings


def main():
    args = build_parser().parse_args()
    vocab_dir = Path(args.vocab) if args.vocab else SCRIPT_DIR.parent / "vocab"

    print("── Generating tradition-vocab.json ────────────────────────────")
    concepts, warnings = generate(vocab_dir)

    for w in warnings:
        print(w)

    if args.check:
        print(f"  — Check only: {len(concepts)} concepts found"
              f"{', ' + str(len(warnings)) + ' warning(s)' if warnings else ', no warnings'}")
        return

    out_path = vocab_dir / "tradition-vocab.json"
    out_path.write_text(
        json.dumps(concepts, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  ✓ {len(concepts)} concepts → {out_path.name}")
    if warnings:
        print(f"  {len(warnings)} warning(s) above — fix via the manager")


if __name__ == "__main__":
    main()
