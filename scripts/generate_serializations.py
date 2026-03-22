#!/usr/bin/env python3
"""
generate_serializations.py — Iroko Framework
Generates JSON-LD, RDF/XML, and N-Triples serializations from each TTL file
in vocab/. Turtle is the source of truth; the other three are derived outputs.

Output files (alongside each TTL):
    iroko-ewe.ttl  →  iroko-ewe.jsonld
                       iroko-ewe.rdf
                       iroko-ewe.nt

Usage:
    python generate_serializations.py              # all TTLs in vocab/
    python generate_serializations.py iroko-ewe    # single module by stem
    python generate_serializations.py --vocab DIR  # explicit vocab path
    python generate_serializations.py --dry-run    # parse only, no output
    python generate_serializations.py --formats jsonld rdf  # subset of formats

Called by build_all.py as Step 4.
"""

import argparse
import sys
from pathlib import Path

try:
    from rdflib import Graph, ConjunctiveGraph
except ImportError:
    print("ERROR: rdflib not installed. Run: pip install rdflib")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Format definitions
# ---------------------------------------------------------------------------

FORMATS = {
    "jsonld": {
        "suffix":      ".jsonld",
        "rdflib_fmt":  "json-ld",
        "description": "JSON-LD",
    },
    "rdf": {
        "suffix":      ".rdf",
        "rdflib_fmt":  "xml",
        "description": "RDF/XML",
    },
    "nt": {
        "suffix":      ".nt",
        "rdflib_fmt":  "nt",
        "description": "N-Triples",
    },
}

# Modules intentionally excluded from serialization output
KNOWN_SKIPS = {
    "iroko-nkisi-patch",
    "ewe-plants-v0_2_1",
    "iroko-vocab-v0_2_1",
    "iroko-core-v2",
    "iroko-ile-v2",
}


# ---------------------------------------------------------------------------
# Core serialization
# ---------------------------------------------------------------------------

def serialize_ttl(ttl_path: Path, formats: list[str], dry_run: bool = False) -> dict:
    """
    Parse a single TTL and write requested serialization formats.
    Returns {format_key: True/False/None} where None = dry-run skipped.
    """
    g = Graph()
    try:
        g.parse(str(ttl_path), format="turtle")
    except Exception as e:
        print(f"  ERROR parsing {ttl_path.name}: {e}")
        return {f: False for f in formats}

    results = {}
    stem = ttl_path.stem

    for fmt_key in formats:
        fmt = FORMATS[fmt_key]
        out_path = ttl_path.with_suffix(fmt["suffix"])

        if dry_run:
            print(f"  ~ {out_path.name}  ({fmt['description']}) — would write")
            results[fmt_key] = None
            continue

        try:
            # JSON-LD benefits from a context that names the iroko: prefix
            if fmt_key == "jsonld":
                serialized = g.serialize(
                    format="json-ld",
                    context={
                        "iroko":  "https://ontology.irokosociety.org/iroko#",
                        "owl":    "http://www.w3.org/2002/07/owl#",
                        "rdf":    "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                        "rdfs":   "http://www.w3.org/2000/01/rdf-schema#",
                        "skos":   "http://www.w3.org/2004/02/skos/core#",
                        "dcterms":"http://purl.org/dc/terms/",
                        "xsd":    "http://www.w3.org/2001/XMLSchema#",
                    },
                    indent=2,
                )
            else:
                serialized = g.serialize(format=fmt["rdflib_fmt"])

            out_path.write_text(
                serialized if isinstance(serialized, str) else serialized.decode("utf-8"),
                encoding="utf-8",
            )
            size_kb = out_path.stat().st_size / 1024
            print(f"  ✓ {out_path.name}  ({size_kb:.1f} KB)")
            results[fmt_key] = True

        except Exception as e:
            print(f"  ✗ {out_path.name}  ERROR: {e}")
            results[fmt_key] = False

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate JSON-LD, RDF/XML, and N-Triples from Iroko TTL files."
    )
    parser.add_argument(
        "stems", nargs="*",
        help="Module stem(s) to process (e.g. iroko-ewe). Omit for all."
    )
    parser.add_argument(
        "--vocab", metavar="DIR",
        help="Path to vocab/ directory (auto-detected if omitted)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Parse and report without writing any files."
    )
    parser.add_argument(
        "--formats", nargs="+", choices=list(FORMATS.keys()),
        default=list(FORMATS.keys()),
        help="Subset of formats to generate (default: all three)."
    )
    args = parser.parse_args()

    # ── Locate vocab/ ──────────────────────────────────────────────────────
    script_dir = Path(__file__).resolve().parent
    if args.vocab:
        vocab_dir = Path(args.vocab)
    else:
        for candidate in [
            script_dir.parent / "vocab",
            script_dir / "vocab",
            Path.cwd() / "vocab",
            Path.cwd(),
        ]:
            if any(candidate.glob("iroko-*.ttl")):
                vocab_dir = candidate
                break
        else:
            print("ERROR: vocab/ directory not found. Use --vocab.")
            sys.exit(1)

    if not vocab_dir.exists():
        print(f"ERROR: vocab directory does not exist: {vocab_dir}")
        sys.exit(1)

    # ── Select TTL files ───────────────────────────────────────────────────
    if args.stems:
        ttl_files = []
        for stem in args.stems:
            stem = stem if not stem.endswith(".ttl") else stem[:-4]
            p = vocab_dir / f"{stem}.ttl"
            if not p.exists():
                print(f"ERROR: {p} not found")
                sys.exit(1)
            ttl_files.append(p)
    else:
        ttl_files = sorted(
            p for p in vocab_dir.glob("iroko-*.ttl")
            if p.stem not in KNOWN_SKIPS
        )

    if not ttl_files:
        print("No TTL files to process.")
        sys.exit(0)

    # ── Run ────────────────────────────────────────────────────────────────
    fmt_labels = ", ".join(FORMATS[f]["description"] for f in args.formats)
    print(f"Iroko Framework — Serialization Generator")
    print(f"  Vocab dir: {vocab_dir}")
    print(f"  Formats:   {fmt_labels}")
    print(f"  Files:     {len(ttl_files)}")
    if args.dry_run:
        print(f"  Mode:      DRY RUN")
    print()

    ok = err = skipped = 0

    for ttl_path in ttl_files:
        print(f"{ttl_path.name}")
        results = serialize_ttl(ttl_path, args.formats, dry_run=args.dry_run)
        for fmt_key, status in results.items():
            if status is True:
                ok += 1
            elif status is False:
                err += 1
            else:
                skipped += 1

    print()
    print("─" * 55)
    if args.dry_run:
        print(f"Dry run complete: {skipped} files would be written")
    else:
        total = len(ttl_files) * len(args.formats)
        print(f"Done: {ok}/{total} files written, {err} errors")
        if err:
            sys.exit(1)


if __name__ == "__main__":
    main()
