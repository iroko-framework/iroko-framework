# Iroko Scripts

This folder has one canonical public-site workflow:

```bash
bash scripts/validate_ttl.sh
python scripts/build_all.py
python scripts/check_site.py
```

For publishing, `bash scripts/deploy.sh` runs the same workflow and then asks before committing or pushing.

## Canonical Workflow

- `validate_ttl.sh` validates Turtle source files in `vocab/`.
- `build_all.py` runs the generated-site build in order.
- `check_site.py` checks generated HTML, links, JavaScript, RDF serializations, `robots.txt`, and `sitemap.xml`.
- `deploy.sh` wraps validation, build, check, commit, and optional push.

## Build Steps

`build_all.py` currently runs:

1. `generate_vocab_html.py`
2. `generate_vocab_index.py`
3. `update_index_counts.py`
4. `generate_serializations.py`
5. `generate_tradition_vocab.py`
6. `generate_uri_aliases.py`
7. `generate_sitemap.py`

It also patches version/date strings in maintained HTML pages.

## Supporting Generators

- `generate_md_html.py` converts Markdown docs into styled HTML.
- `generate_og_cards.py` creates Open Graph images and updates metadata.
- `update_ecosystem_links.py` updates broader ecosystem links when needed.

## Manager

`scripts/manage/` contains the local ontology manager. It edits Turtle source files and can run the canonical build, but it does not push to GitHub.

## Retired

- `nightly_export.sh` is retained only as a fail-fast notice. Its former data-export target is no longer present in this repository.
