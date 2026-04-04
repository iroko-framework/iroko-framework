#!/usr/bin/env python3
"""
update_ecosystem_links.py — Iroko Framework
Batch-updates topbar and footer across all generated HTML files in the repo.

Run this once after any topbar/footer change to propagate updates
without needing to regenerate every module page from TTL.

Usage:
    python update_ecosystem_links.py              # from repo root
    python update_ecosystem_links.py --dry-run    # preview only
    python update_ecosystem_links.py --dir PATH   # explicit root path
"""

import argparse
import re
import sys
from pathlib import Path

# ── Topbar templates ──────────────────────────────────────────────────────────
# depth=1 = file is one level down from root (vocab/, docs/, whitepaper/)
# depth=0 = file is at root (index.html)

def make_topbar(depth):
    prefix = "../" if depth > 0 else ""
    return f'''<div class="top-bar">
  <span class="top-bar-id">
    <img class="top-bar-logo" src="{prefix}assets/IHS-Logo.jpg" alt="Iroko Historical Society">
    Iroko Historical Society · Iroko Framework
  </span>
  <nav class="top-bar-links">
    <a href="{prefix}index.html">Home</a>
    <a href="https://www.irokosociety.org/" target="_blank" rel="noopener">IHS ↗</a>
    <a href="https://medjat.irokosociety.org/">Per Medjat</a>
    <a href="{prefix}whitepaper/">White Paper</a>
    <a href="{prefix}docs/">Docs</a>
    <a href="https://github.com/iroko-framework/iroko-framework" target="_blank" rel="noopener">GitHub ↗</a>
  </nav>
</div>'''

def make_footer(depth):
    prefix = "../" if depth > 0 else ""
    return f'''<footer class="site-footer">
    <div class="footer-left">
      Iroko Historical Society<br>
      Postcustodial Digital Archives for Afro-Atlantic Cultural Materials<br>
      License: CC0 1.0 Universal (Public Domain)
      <div class="footer-iao">Ilé Añá Olofí, Inc. 501(c)(3) · <a href="https://ileanaolofi.org" target="_blank" rel="noopener">ileanaolofi.org</a></div>
    </div>
    <div class="footer-links">
      <a href="https://www.irokosociety.org/" target="_blank" rel="noopener">IHS ↗</a>
      <a href="{prefix}index.html">Home</a>
      <a href="https://medjat.irokosociety.org/">Per Medjat</a>
      <a href="{prefix}vocab/">Vocabularies</a>
    </div>
  </footer>'''

# ── Patterns ──────────────────────────────────────────────────────────────────
TOPBAR_PAT = re.compile(r'<div class="top-bar">.*?</div>', re.DOTALL)
FOOTER_PAT = re.compile(r'<footer class="site-footer[^"]*">.*?</footer>', re.DOTALL)

# ── Files to skip ─────────────────────────────────────────────────────────────
SKIP = {
    'iroko-style.css',
}

def process_file(path: Path, dry_run: bool) -> tuple[bool, list[str]]:
    """
    Update topbar and footer in one HTML file.
    Returns (changed: bool, messages: list[str]).
    """
    try:
        original = path.read_text(encoding='utf-8')
    except Exception as e:
        return False, [f"READ ERROR: {e}"]

    # Determine depth from root
    parts = path.parts
    try:
        # Find position relative to repo root by looking for known dirs
        depth = 0
        for part in parts:
            if part in ('vocab', 'docs', 'whitepaper', 'data'):
                depth = 1
                break
    except Exception:
        depth = 1

    new_topbar = make_topbar(depth)
    new_footer = make_footer(depth)

    content = original
    messages = []

    # Update topbar
    if TOPBAR_PAT.search(content):
        content = TOPBAR_PAT.sub(new_topbar, content, count=1)
        messages.append("topbar updated")
    else:
        # No topbar — insert after <body>
        if '<body>' in content:
            content = content.replace('<body>\n', f'<body>\n\n{new_topbar}\n\n', 1)
            content = content.replace('<body>\n\n\n', f'<body>\n\n{new_topbar}\n\n', 1)
            messages.append("topbar inserted")
        else:
            messages.append("WARNING: no <body> tag found, topbar not inserted")

    # Update footer
    if FOOTER_PAT.search(content):
        content = FOOTER_PAT.sub(new_footer, content, count=1)
        messages.append("footer updated")
    else:
        messages.append("WARNING: no .site-footer found, footer not updated")

    changed = content != original

    if changed and not dry_run:
        path.write_text(content, encoding='utf-8')

    return changed, messages


def main():
    parser = argparse.ArgumentParser(description='Update topbar/footer across all Framework HTML files')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing')
    parser.add_argument('--dir', default='.', help='Path to repo root (default: current directory)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show all files including unchanged')
    args = parser.parse_args()

    root = Path(args.dir).resolve()

    # Collect HTML files — repo root + known subdirs
    targets = []
    targets.extend(root.glob('*.html'))
    targets.extend(root.glob('vocab/*.html'))
    targets.extend(root.glob('docs/*.html'))
    targets.extend(root.glob('whitepaper/*.html'))
    targets.extend(root.glob('data/*.html'))

    targets = [p for p in targets if p.name not in SKIP]
    targets.sort()

    if args.dry_run:
        print(f"DRY RUN — {len(targets)} files found\n")
    else:
        print(f"Updating {len(targets)} files\n")

    changed_count = 0
    error_count = 0

    for path in targets:
        changed, messages = process_file(path, args.dry_run)
        rel = path.relative_to(root)

        if changed:
            changed_count += 1
            status = "UPDATED" if not args.dry_run else "WOULD UPDATE"
            print(f"  {status}  {rel}  ({', '.join(messages)})")
        elif args.verbose:
            print(f"  unchanged  {rel}")

        if any('ERROR' in m for m in messages):
            error_count += 1

    print(f"\n{'─' * 50}")
    action = "Updated" if not args.dry_run else "Would update"
    print(f"{action}: {changed_count} files | Errors: {error_count} | Total scanned: {len(targets)}")

    if args.dry_run:
        print("\nRun without --dry-run to apply changes.")


if __name__ == '__main__':
    main()
