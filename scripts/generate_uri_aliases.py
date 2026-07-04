#!/usr/bin/env python3
"""
generate_uri_aliases.py - publish stable URI landing pages.

The ontology uses hash term IRIs under:
    https://ontology.irokosociety.org/iroko#Term

It also declares module ontology IRIs such as:
    https://ontology.irokosociety.org/iroko-core

GitHub Pages is a static host, so this script creates lightweight HTML
documents that make those IRIs dereferenceable and preserve existing public
identifiers without changing the RDF namespace.
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from iroko_config import FRAMEWORK_VERSION, IROKO_NS, MODULES, MODULE_CONFIG, MONTH_YEAR

SITE = "https://ontology.irokosociety.org"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def module_alias_page(stem: str, title: str) -> str:
    target = f"vocab/{stem}.html"
    target_abs = f"{SITE}/{target}"
    ttl = f"vocab/{stem}.ttl"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} - Iroko Framework</title>
  <link rel="canonical" href="{esc(target_abs)}">
  <link rel="alternate" type="text/turtle" href="{esc(ttl)}">
  <link rel="alternate" type="application/ld+json" href="vocab/{esc(stem)}.jsonld">
  <link rel="alternate" type="application/rdf+xml" href="vocab/{esc(stem)}.rdf">
  <link rel="alternate" type="application/n-triples" href="vocab/{esc(stem)}.nt">
  <meta http-equiv="refresh" content="0; url={esc(target)}">
  <script>
    location.replace('{target}' + location.hash);
  </script>
</head>
<body>
  <p><a href="{esc(target)}">Continue to {esc(title)}</a>.</p>
</body>
</html>
"""


def namespace_page() -> str:
    rows = []
    for display, tier, _tag, _ns, stem in MODULES:
        cfg = MODULE_CONFIG.get(stem, {})
        title = cfg.get("title", display).replace("&amp;", "&")
        rows.append(
            f"""        <li>
          <a href="vocab/{esc(stem)}.html">{esc(title)}</a>
          <span class="formats">
            <a href="vocab/{esc(stem)}.ttl">TTL</a>
            <a href="vocab/{esc(stem)}.jsonld">JSON-LD</a>
            <a href="vocab/{esc(stem)}.rdf">RDF/XML</a>
            <a href="vocab/{esc(stem)}.nt">N-Triples</a>
          </span>
          <span class="tier">{esc(tier)}</span>
        </li>"""
        )

    module_list = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Canonical RDF namespace document for Iroko Framework terms.">
  <title>Iroko RDF Namespace - Iroko Framework</title>
  <link rel="canonical" href="{SITE}/iroko">
  <link rel="stylesheet" href="assets/iroko-style.css">
  <link rel="alternate" type="text/turtle" href="vocab/iroko-core.ttl">
  <link rel="alternate" type="application/ld+json" href="vocab/iroko-core.jsonld">
  <link rel="alternate" type="application/rdf+xml" href="vocab/iroko-core.rdf">
  <style>
    main {{ max-width: 920px; margin: 0 auto; padding: 3rem 1.5rem; }}
    code {{ font-family: var(--mono); }}
    .namespace-box {{ border: 1px solid var(--rule-strong); padding: 1rem; background: var(--paper-warm); }}
    .module-list {{ list-style: none; padding: 0; margin: 1.5rem 0; }}
    .module-list li {{ border-top: 1px solid var(--rule); padding: .75rem 0; }}
    .formats {{ display: inline-flex; gap: .6rem; margin-left: .75rem; font-size: .8rem; }}
    .tier {{ color: var(--ink-soft); font-size: .8rem; margin-left: .75rem; }}
  </style>
</head>
<body>
  <main>
    <p><a href="index.html">Iroko Framework</a> / RDF Namespace</p>
    <h1>Iroko RDF Namespace</h1>
    <div class="namespace-box">
      <p>Canonical term namespace:</p>
      <p><code>{esc(IROKO_NS)}</code></p>
      <p>Example term IRI: <code>{SITE}/iroko#SacredEntity</code></p>
    </div>
    <p>
      The Iroko Framework publishes one shared hash namespace for classes,
      properties, and SKOS concepts across all modules. Turtle is the source
      vocabulary format; JSON-LD, RDF/XML, and N-Triples are generated from it.
    </p>
    <p>Framework version {esc(FRAMEWORK_VERSION)}; namespace document generated {esc(MONTH_YEAR)}.</p>
    <h2>Vocabulary Modules</h2>
    <ul class="module-list">
{module_list}
    </ul>
  </main>
</body>
</html>
"""


def framework_alias_page() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Iroko Framework</title>
  <link rel="canonical" href="{SITE}/">
  <meta http-equiv="refresh" content="0; url=/">
  <script>location.replace('/');</script>
</head>
<body>
  <p><a href="/">Continue to the Iroko Framework home page</a>.</p>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate stable URI alias pages.")
    parser.add_argument("--root", metavar="DIR", help="Repository root")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parent.parent
    targets: dict[Path, str] = {
        root / "iroko.html": namespace_page(),
        root / "iroko-framework" / "index.html": framework_alias_page(),
    }
    for display, _tier, _tag, _ns, stem in MODULES:
        cfg = MODULE_CONFIG.get(stem, {})
        title = cfg.get("title", display).replace("&amp;", "&")
        targets[root / f"{stem}.html"] = module_alias_page(stem, title)

    changed = 0
    for path, content in sorted(targets.items()):
        if args.dry_run:
            status = "would update" if (not path.exists() or path.read_text(encoding="utf-8") != content) else "unchanged"
            print(f"  {status}: {path.relative_to(root)}")
            continue
        if write_if_changed(path, content):
            changed += 1
            print(f"  updated: {path.relative_to(root)}")

    if not args.dry_run:
        print(f"URI alias pages complete ({changed} changed).")


if __name__ == "__main__":
    main()
