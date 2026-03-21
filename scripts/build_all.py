#!/usr/bin/env python3
"""
build_all.py — Full HTML rebuild for the Iroko Framework site.

Runs all three generation scripts in sequence, then patches docs HTML
files for version and date strings.

Usage:
    python build_all.py                          # auto-detect paths
    python build_all.py --vocab DIR              # explicit vocab/ dir
    python build_all.py --root DIR               # explicit repo root
    python build_all.py --dry-run                # show what would change
    python build_all.py --step 3                 # run only step 3

Steps:
    1  generate_vocab_html.py      — vocab browse pages (iroko-*.html)
    2  generate_vocab_index.py     — vocab/iroko-termlist.html
    3  update_index_counts.py      — sync counts in all index files
    +  update_docs_html()          — patch version/date in docs HTML

All scripts are located in the same directory as build_all.py.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# Current release info — update these two lines each release
VERSION    = "1.3.0"
MONTH_YEAR = "March 2026"


# ---------------------------------------------------------------------------
# Docs HTML patching (not covered by the three vocab scripts)
# ---------------------------------------------------------------------------

def patch_docs_html(docs_dir: Path, root_dir: Path, dry_run: bool = False):
    """
    Patches version and date strings in the hand-maintained docs HTML files.
    Does not touch vocab HTML files (those are handled by generate_vocab_html.py).

    Files patched:
      docs/index.html      — meta-pill date
      docs/ARCHITECTURE.html — top-bar version, meta-pill date
      docs/REUSE.html      — top-bar version
      docs/CONTRIBUTING.html — top-bar version
    """
    targets = [
        docs_dir / "index.html",
        docs_dir / "ARCHITECTURE.html",
        docs_dir / "REUSE.html",
        docs_dir / "CONTRIBUTING.html",
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
    p.add_argument("--step", type=int, choices=[1, 2, 3],
                   help="Run only this step (1, 2, or 3)")
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

    only = args.step
    errors = 0

    # ── Step 1: Vocab browse pages ─────────────────────────────────────
    if only is None or only == 1:
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
    if only is None or only == 2:
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

    # ── Step 3: Sync index counts ──────────────────────────────────────
    if only is None or only == 3:
        print("── Step 3: Syncing index counts ───────────────────────────────")
        extra = []
        if args.vocab: extra += ["--vocab", str(vocab_dir)]
        if args.root:  extra += ["--root",  str(root_dir)]
        if args.dry_run: extra += ["--dry-run"]
        rc = run_script("update_index_counts.py", extra)
        if rc != 0:
            print(f"  ✗ update_index_counts.py failed (exit {rc})")
            errors += 1
        print()

    # ── Docs HTML: version + date strings ─────────────────────────────
    if only is None:
        print("── Docs HTML: patching version and date strings ───────────────")
        patch_docs_html(docs_dir, root_dir, dry_run=args.dry_run)
        print()

    # ── Summary ────────────────────────────────────────────────────────
    print("── Done " + ("(dry run)" if args.dry_run else "") + " ─" * 30)
    if errors:
        print(f"  {errors} step(s) failed — check output above")
        sys.exit(1)
    else:
        print(f"  All steps completed successfully")
        print()
        print(f"  Next: git add -A && git commit -m 'chore: v{VERSION} HTML rebuild'")


if __name__ == "__main__":
    main()
