#!/usr/bin/env python3
"""
generate_md_html.py — Convert Markdown documentation files to styled HTML
for the Iroko Framework documentation site.

Uses iroko-style.css and generates pages that match the framework's look.
Tables, fenced code blocks, and a linked table of contents are all supported.

Usage:
    python generate_md_html.py                          # convert all .md in docs/
    python generate_md_html.py ARCHITECTURE             # convert docs/ARCHITECTURE.md
    python generate_md_html.py ARCHITECTURE REUSE       # convert multiple files
    python generate_md_html.py --input path/to/file.md # explicit path

Output:
    Writes .html alongside the .md file by default.
    Use --output-dir to redirect all output to a specific directory.

Options:
    --input PATH        Explicit input path (overrides positional stem lookup)
    --output-dir DIR    Write all output files to DIR instead of alongside source
    --no-toc            Skip the table of contents sidebar
    --css-depth N       How many directory levels up to the assets/ folder (default: 1)
                        Use 0 if the HTML will live in the same folder as assets/
    --dry-run           Print what would be generated without writing files
"""

import argparse
import sys
import re
from pathlib import Path
from datetime import date
import html as html_module

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import markdown
    from markdown.extensions.toc import TocExtension
except ImportError:
    print("ERROR: 'markdown' package not found. Install with:")
    print("    pip install markdown --break-system-packages")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Docs directory to search for .md files when no stems are provided
DOCS_DIR = Path(__file__).parent / "docs"

# Fallback search paths when a stem is given without an explicit --input
SEARCH_PATHS = [
    Path(__file__).parent / "docs",
    Path(__file__).parent,
]

# Markdown extensions to enable
MD_EXTENSIONS = [
    "tables",
    "fenced_code",
    "attr_list",
    "def_list",
    TocExtension(
        permalink=True,
        permalink_class="toc-anchor",
        title="Contents",
        toc_depth=3,
    ),
]

# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — Iroko Framework</title>
  <link rel="stylesheet" href="{css_path}iroko-style.css">
  <style>
    /* ── Doc page layout ──────────────────────────────────────────── */
    .doc-wrap {{
      display: grid;
      grid-template-columns: 220px 1fr;
      gap: 3rem;
      align-items: start;
      max-width: 1100px;
      margin: 0 auto;
      padding: 2rem 1.5rem 4rem;
    }}
    @media (max-width: 768px) {{
      .doc-wrap {{ grid-template-columns: 1fr; }}
      .doc-toc  {{ display: none; }}
    }}

    /* ── TOC sidebar ──────────────────────────────────────────────── */
    .doc-toc {{
      position: sticky;
      top: 2rem;
      font-size: .8rem;
      line-height: 1.6;
      max-height: 85vh;
      overflow-y: auto;
      padding-right: .5rem;
    }}
    .doc-toc .toctitle {{
      font-size: .65rem;
      font-weight: 700;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: var(--ink-soft);
      margin-bottom: .5rem;
    }}
    .doc-toc ul  {{ list-style: none; margin: 0; padding: 0; }}
    .doc-toc li  {{ margin: .2rem 0; }}
    .doc-toc a   {{ color: var(--ink-soft); text-decoration: none; }}
    .doc-toc a:hover {{ color: var(--accent); }}
    .doc-toc ul ul {{ padding-left: .9rem; }}

    /* ── Doc content ──────────────────────────────────────────────── */
    .doc-content h1 {{ font-size: 1.8rem; margin-bottom: .25rem; }}
    .doc-content h2 {{
      font-size: 1.1rem;
      margin-top: 2.5rem;
      padding-bottom: .4rem;
      border-bottom: 1px solid var(--border);
    }}
    .doc-content h3 {{ font-size: .95rem; margin-top: 1.75rem; }}
    .doc-content p  {{ max-width: 72ch; line-height: 1.7; }}
    .doc-content code {{
      font-family: var(--mono);
      font-size: .82em;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 3px;
      padding: .1em .35em;
    }}
    .doc-content pre {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1rem 1.25rem;
      overflow-x: auto;
      font-size: .78rem;
      line-height: 1.55;
    }}
    .doc-content pre code {{
      background: none;
      border: none;
      padding: 0;
      font-size: inherit;
    }}
    .doc-content table {{
      border-collapse: collapse;
      font-size: .82rem;
      margin: 1.25rem 0;
      width: 100%;
    }}
    .doc-content th {{
      background: var(--surface);
      font-weight: 600;
      text-align: left;
      padding: .45rem .75rem;
      border: 1px solid var(--border);
    }}
    .doc-content td {{
      padding: .4rem .75rem;
      border: 1px solid var(--border);
      vertical-align: top;
    }}
    .doc-content td:first-child {{ white-space: nowrap; }}
    .doc-content tr:nth-child(even) td {{ background: var(--surface); }}
    .doc-content ul, .doc-content ol {{
      padding-left: 1.4rem;
      line-height: 1.7;
    }}
    .doc-content li {{ margin: .25rem 0; }}
    .doc-content blockquote {{
      border-left: 3px solid var(--accent);
      margin: 1rem 0;
      padding: .5rem 1rem;
      color: var(--ink-soft);
      background: var(--surface);
      border-radius: 0 4px 4px 0;
    }}
    .toc-anchor {{
      font-size: .65em;
      margin-left: .4rem;
      opacity: 0;
      color: var(--ink-soft);
      text-decoration: none;
    }}
    h2:hover .toc-anchor,
    h3:hover .toc-anchor {{ opacity: 1; }}
    .doc-meta {{
      font-size: .78rem;
      color: var(--ink-soft);
      margin-bottom: 2rem;
    }}
  </style>
</head>
<body>

  <nav class="breadcrumb page-wrap">
    <a href="{root_path}index.html">Iroko Framework</a>
    <span>/</span>
    <a href="{root_path}docs/">Documentation</a>
    <span>/</span>
    {title}
  </nav>

  <div class="doc-wrap">

    {toc_html}

    <div class="doc-content">
      <p class="doc-meta">Iroko Framework v1.4.0 · {today}</p>
      {content_html}
    </div>

  </div><!-- /doc-wrap -->

  <footer class="site-footer page-wrap">
    <div class="footer-copy">
      © 2026 Iroko Historical Society · CC0 1.0 Universal (Public Domain)
    </div>
    <div class="footer-links">
      <a href="https://www.irokosociety.org">irokosociety.org</a>
      <a href="https://github.com/iroko-framework/iroko-framework">GitHub</a>
      <a href="{root_path}vocab/">Vocabularies</a>
    </div>
  </footer>

</body>
</html>
"""

TOC_WRAPPER = """\
<nav class="doc-toc">
  <div class="toctitle">Contents</div>
  {toc_html}
</nav>
"""

# ---------------------------------------------------------------------------
# Conversion logic
# ---------------------------------------------------------------------------

def md_to_html(md_path: Path, css_depth: int = 1, include_toc: bool = True) -> str:
    """Convert a single Markdown file to a complete HTML page string."""

    source = md_path.read_text(encoding="utf-8")

    # Extract title from first H1, fall back to filename
    title_match = re.search(r"^#\s+(.+)$", source, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else md_path.stem

    # Strip the title line — it will be rendered naturally in the content
    # (keeping it avoids duplication with the breadcrumb)

    md = markdown.Markdown(extensions=MD_EXTENSIONS)
    content_html = md.convert(source)
    toc_html_raw = getattr(md, "toc", "")

    # Build css path prefix (e.g. "../" or "../../")
    css_prefix = "../" * css_depth if css_depth > 0 else ""
    root_prefix = "../" * css_depth if css_depth > 0 else ""

    # TOC sidebar
    if include_toc and toc_html_raw and toc_html_raw.strip() != "<div class=\"toc\"></div>":
        toc_block = TOC_WRAPPER.format(toc_html=toc_html_raw)
    else:
        toc_block = ""

    return HTML_TEMPLATE.format(
        title=html_module.escape(title),
        css_path=css_prefix + "assets/",
        root_path=root_prefix,
        toc_html=toc_block,
        content_html=content_html,
        today=date.today().strftime("%B %Y"),
    )


def resolve_input(stem: str, search_paths: list[Path]) -> Path | None:
    """Find a .md file by stem across search paths."""
    for directory in search_paths:
        candidate = directory / f"{stem}.md"
        if candidate.exists():
            return candidate
    return None


def convert_file(
    md_path: Path,
    output_dir: Path | None,
    css_depth: int,
    include_toc: bool,
    dry_run: bool,
) -> Path:
    """Convert one Markdown file and write output. Returns the output path."""

    out_dir = output_dir if output_dir else md_path.parent
    out_path = out_dir / (md_path.stem + ".html")

    html_content = md_to_html(md_path, css_depth=css_depth, include_toc=include_toc)

    if dry_run:
        print(f"  [dry-run] Would write {out_path}  ({len(html_content):,} chars)")
    else:
        out_path.write_text(html_content, encoding="utf-8")
        print(f"  ✓  {md_path.name}  →  {out_path}")

    return out_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Convert Markdown docs to styled Iroko Framework HTML pages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "stems",
        nargs="*",
        metavar="STEM",
        help="File stem(s) to convert, e.g. ARCHITECTURE REUSE. "
             "Omit to convert all .md files in docs/.",
    )
    p.add_argument(
        "--input", "-i",
        metavar="PATH",
        help="Explicit path to a single .md file (overrides stem lookup).",
    )
    p.add_argument(
        "--output-dir", "-o",
        metavar="DIR",
        help="Write all output HTML files to this directory.",
    )
    p.add_argument(
        "--no-toc",
        action="store_true",
        help="Skip the table of contents sidebar.",
    )
    p.add_argument(
        "--css-depth",
        type=int,
        default=1,
        metavar="N",
        help="Directory levels up to assets/ folder. "
             "Use 1 if HTML lives in docs/ (default). Use 0 if same folder as assets/.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files.",
    )
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Collect files to convert
    targets: list[Path] = []

    if args.input:
        p = Path(args.input)
        if not p.exists():
            print(f"ERROR: {p} not found.")
            sys.exit(1)
        targets.append(p)

    elif args.stems:
        for stem in args.stems:
            found = resolve_input(stem, SEARCH_PATHS)
            if not found:
                # Maybe it's a direct path with .md extension
                direct = Path(stem)
                if direct.exists() and direct.suffix == ".md":
                    found = direct
            if not found:
                print(f"ERROR: Cannot find '{stem}.md' in search paths:")
                for sp in SEARCH_PATHS:
                    print(f"  {sp}")
                sys.exit(1)
            targets.append(found)

    else:
        # No stems given — convert all .md in docs/
        if not DOCS_DIR.exists():
            print(f"ERROR: Default docs directory not found: {DOCS_DIR}")
            print("Pass a stem or --input path explicitly.")
            sys.exit(1)
        targets = sorted(DOCS_DIR.glob("*.md"))
        if not targets:
            print(f"No .md files found in {DOCS_DIR}")
            sys.exit(0)

    print(f"Converting {len(targets)} file(s)...")
    for md_path in targets:
        convert_file(
            md_path=md_path,
            output_dir=output_dir,
            css_depth=args.css_depth,
            include_toc=not args.no_toc,
            dry_run=args.dry_run,
        )

    print("Done.")


if __name__ == "__main__":
    main()
