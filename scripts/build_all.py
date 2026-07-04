#!/usr/bin/env python3
"""
build_all.py — Full HTML rebuild for the Iroko Framework site.

Runs all three generation scripts in sequence, then patches docs HTML
files for version and date strings.

Usage:
    python build_all.py                          # auto-detect paths, all steps
    python build_all.py --vocab DIR              # explicit vocab/ dir
    python build_all.py --root DIR               # explicit repo root
    python build_all.py --dry-run                # show what would change
    python build_all.py --step 3                 # run only step 3
    python build_all.py --step 2 --step 3        # run steps 2 and 3

Steps:
    1  generate_vocab_html.py         — v8 interactive module pages (iroko-*.html)
    2  generate_vocab_index.py        — vocab/iroko-termlist.html
    3  update_index_counts.py         — sync counts in all index files
    4  generate_serializations.py     — JSON-LD, RDF/XML, N-Triples from each TTL
    5  generate_tradition_vocab.py    — vocab/tradition-vocab.json (catalog lookup)
    6  generate_uri_aliases.py        — stable /iroko and /iroko-* URI landing pages
    +  update_docs_html()             — patch version/date in docs HTML

All scripts are located in the same directory as build_all.py.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Ensure Unicode characters (✓ ✗ ── etc.) render on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from iroko_config import FRAMEWORK_VERSION as VERSION, MONTH_YEAR

SCRIPT_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Docs HTML patching (not covered by the three vocab scripts)
# ---------------------------------------------------------------------------

def patch_docs_html(docs_dir: Path, root_dir: Path, dry_run: bool = False):
    """
    Patches version and date strings in all hand-maintained HTML files.
    Term counts are handled by update_index_counts.py (step 3) — not here.

    Files patched:
      docs/index.html         — meta-pill date
      docs/ARCHITECTURE.html  — top-bar version, meta-pill date, doc-meta line
      docs/REUSE.html         — top-bar version
      docs/CONTRIBUTING.html  — top-bar version
      vocab/index.html        — meta-pill date (version already set by generator)
      index.html              — top-bar version, meta-pill date (root landing page)
    """
    targets = [
        docs_dir / "index.html",
        docs_dir / "ARCHITECTURE.html",
        docs_dir / "REUSE.html",
        docs_dir / "CONTRIBUTING.html",
        root_dir / "vocab" / "index.html",
        root_dir / "index.html",
    ]

    version_pattern = re.compile(r'(Iroko Framework v)\d+\.\d+\.\d+')
    date_pattern    = re.compile(
        r'(<span class="meta-pill">)(January|February|March|April|May|June|'
        r'July|August|September|October|November|December) \d{4}(</span>)'
    )
    doc_meta_pattern = re.compile(r'(Iroko Framework v)\d+\.\d+\.\d+( · )'
                                   r'(January|February|March|April|May|June|'
                                   r'July|August|September|October|November|December) \d{4}')

    changed = 0
    for path in targets:
        if not path.exists():
            print(f"  ⚠ Not found, skipping: {path.name}")
            continue

        original = path.read_text(encoding="utf-8")
        patched  = original

        # Top-bar version string
        patched = version_pattern.sub(rf'\g<1>{VERSION}', patched)

        # Meta-pill date
        patched = date_pattern.sub(
            rf'\g<1>{MONTH_YEAR}\g<3>', patched
        )

        # Doc-meta line "v1.x.x · Month YYYY"
        patched = doc_meta_pattern.sub(
            rf'\g<1>{VERSION}\g<2>{MONTH_YEAR}', patched
        )

        if patched == original:
            print(f"  — {path.name}: no changes needed")
        elif dry_run:
            print(f"  ~ {path.name}: would update version/date strings")
            changed += 1
        else:
            path.write_text(patched, encoding="utf-8")
            print(f"  ✓ {path.name}: updated")
            changed += 1

    return changed


# ---------------------------------------------------------------------------
# Script runners
# ---------------------------------------------------------------------------

def run_script(name: str, extra_args: list[str] | None = None) -> int:
    script = SCRIPT_DIR / name
    if not script.exists():
        print(f"  ✗ {name} not found at {script}")
        return 1
    cmd = [sys.executable, str(script)] + (extra_args or [])
    result = subprocess.run(cmd)
    return result.returncode


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        description="Full HTML rebuild for the Iroko Framework."
    )
    p.add_argument("--vocab",  metavar="DIR", help="Path to vocab/ directory")
    p.add_argument("--root",   metavar="DIR", help="Path to repo root")
    p.add_argument("--docs",   metavar="DIR", help="Path to docs/ directory")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would change without writing")
    p.add_argument("--step", type=int, choices=[1, 2, 3, 4, 5, 6],
                   action="append", dest="steps", metavar="N",
                   help="Run only step N (1-6); repeat to run multiple, e.g. --step 2 --step 3")
    return p


def main():
    args = build_parser().parse_args()

    # Resolve paths
    root_dir = Path(args.root)  if args.root  else SCRIPT_DIR.parent
    vocab_dir = Path(args.vocab) if args.vocab else root_dir / "vocab"
    docs_dir  = Path(args.docs)  if args.docs  else root_dir / "docs"

    print(f"Iroko Framework — Full HTML Build")
    print(f"  Version:   {VERSION}")
    print(f"  Date:      {MONTH_YEAR}")
    print(f"  Root:      {root_dir}")
    print(f"  Vocab dir: {vocab_dir}")
    print(f"  Docs dir:  {docs_dir}")
    if args.dry_run:
        print("  Mode:      DRY RUN")
    print()

    steps = set(args.steps) if args.steps else None
    errors = 0

    # ── Step 1: Vocab browse pages ─────────────────────────────────────
    if steps is None or 1 in steps:
        print("── Step 1: Generating vocab browse pages ──────────────────────")
        extra = ["--vocab", str(vocab_dir)] if args.vocab else []
        if args.dry_run:
            print("  (dry run — would run generate_vocab_html.py)")
        else:
            rc = run_script("generate_vocab_html.py", extra)
            if rc != 0:
                print(f"  ✗ generate_vocab_html.py failed (exit {rc})")
                errors += 1
            else:
                print("  ✓ Vocab browse pages written")
        print()

    # ── Step 2: Vocab term list ────────────────────────────────────────
    if steps is None or 2 in steps:
        print("── Step 2: Generating vocab term list ─────────────────────────")
        extra = ["--ttl-dir", str(vocab_dir)] if args.vocab else []
        if args.dry_run:
            print("  (dry run — would run generate_vocab_index.py)")
        else:
            rc = run_script("generate_vocab_index.py", extra)
            if rc != 0:
                print(f"  ✗ generate_vocab_index.py failed (exit {rc})")
                errors += 1
            else:
                print("  ✓ iroko-termlist.html written")
        print()

    # ── Step 3: Sync index counts + ARCHITECTURE patches ─────────────
    if steps is None or 3 in steps:
        print("── Step 3: Syncing index counts + ARCHITECTURE ─────────────────")
        extra = []
        if args.vocab: extra += ["--vocab", str(vocab_dir)]
        if args.root:  extra += ["--root",  str(root_dir)]
        extra += ["--docs", str(docs_dir)]
        if args.dry_run: extra += ["--dry-run"]
        rc = run_script("update_index_counts.py", extra)
        if rc != 0:
            print(f"  ✗ update_index_counts.py failed (exit {rc})")
            errors += 1
        print()

    # ── Step 4: Alternate serializations ──────────────────────────────
    if steps is None or 4 in steps:
        print("── Step 4: Generating alternate serializations ────────────────")
        extra = ["--vocab", str(vocab_dir)]
        if args.dry_run:
            extra += ["--dry-run"]
        rc = run_script("generate_serializations.py", extra)
        if rc != 0:
            print(f"  \u2717 generate_serializations.py failed (exit {rc})")
            errors += 1
        elif not args.dry_run:
            print("  \u2713 JSON-LD, RDF/XML, N-Triples written")
        print()

    # ── Step 5: Tradition vocabulary JSON ─────────────────────────────
    if steps is None or 5 in steps:
        print("── Step 5: Generating tradition-vocab.json ────────────────────")
        extra = ["--vocab", str(vocab_dir)]
        if args.dry_run:
            extra += ["--check"]
        rc = run_script("generate_tradition_vocab.py", extra)
        if rc != 0:
            print(f"  ✗ generate_tradition_vocab.py failed (exit {rc})")
            errors += 1
        print()

    # ── Step 6: URI aliases ────────────────────────────────────────────────
    if steps is None or 6 in steps:
        print("── Step 6: Generating stable URI alias pages ───────────────────")
        extra = ["--root", str(root_dir)]
        if args.dry_run:
            extra += ["--dry-run"]
        rc = run_script("generate_uri_aliases.py", extra)
        if rc != 0:
            print(f"  ✗ generate_uri_aliases.py failed (exit {rc})")
            errors += 1
        print()

    # ── Docs HTML: version + date strings ─────────────────────────────────────
    if steps is None:
        print("── Docs HTML: patching version and date strings ───────────────")
        patch_docs_html(docs_dir, root_dir, dry_run=args.dry_run)
        print()

    # ── Summary ────────────────────────────────────────────────────────
    print("── Done " + ("(dry run)" if args.dry_run else "") + " " + "─" * 30)
    if errors:
        print(f"  {errors} step(s) failed — check output above")
        sys.exit(1)

    print(f"  All steps completed successfully")

    if steps is None:
        print()
        print("  ── This script does NOT handle ─────────────────────────────────")
        print("     For each modified TTL, also update by hand:")
        print("       scripts/iroko_config.py  — title and subtitle")
        print("       index.html               — module-subtitle, module-version, module-desc")
        print("       vocab/index.html         — same three fields")
        print("     Then rebuild that module's browse page:")
        print("       python scripts/generate_vocab_html.py iroko-<stem>")
        print()
        print("     Step 5 naming warnings (region-* / Palo / Vodou altLabels)")
        print("     are pre-existing data issues — fix via the Iroko Manager.")
        print()
        print("  ── Commit (PowerShell: two separate commands) ──────────────────")
        print("       git add -A")
        print(f"      git commit -m 'build: v{VERSION} full rebuild + serializations'")


if __name__ == "__main__":
    main()
