# Git Push — Troubleshooting Brief
## For Claude Code Session

**Goal:** Commit and push all pending changes in two repos to GitHub so that
`ontology.irokosociety.org` and `medjat.irokosociety.org/library/` reflect the
latest work. Both repos use HTTPS remotes under the `iroko-framework` GitHub org.

---

## Current State (as of May 2026)

Both repos show `Your branch is up to date with 'origin/main'` but have many
**unstaged, uncommitted** changes. The prior `git push` returned "Everything
up-to-date" because nothing had been staged. The VS Code commit visible in the
log predates this session's work.

### iroko-framework
- Remote: `https://github.com/iroko-framework/iroko-framework.git`
- Last commit: `752d4c6 updates`
- Uncommitted changes include: `vocab/iroko-core.ttl`, all generated `vocab/*.html`,
  `vocab/tradition-vocab.json` (new file — not yet tracked), `scripts/build_all.py`,
  `scripts/generate_tradition_vocab.py` (new file — not yet tracked)

### Per-Medjat
- Remote: `https://github.com/iroko-framework/Per-Medjat.git`
- Last commit: `101035c Minor Edit`
- Uncommitted changes include: `library/index.html` (catalog — primary change),
  plus many `ewe/plant/Plant*.html` files (pre-existing)

---

## What Needs to Go Out

### iroko-framework — minimum viable push
```bash
cd "C:\Users\Dele Fatbemi\Documents\github active\iroko-framework"
git add vocab/iroko-core.ttl
git add vocab/iroko-core.html
git add vocab/tradition-vocab.json
git add scripts/build_all.py
git add scripts/generate_tradition_vocab.py
git add scripts/generate_vocab_html.py
git commit -m "build: add tradition-vocab.json generation; fix Shango Baptist concept; step 5 pipeline"
git push
```

Or to push everything that changed:
```bash
git add -A
git commit -m "build: v1.3.0 full rebuild + tradition-vocab.json endpoint"
git push
```

### Per-Medjat — minimum viable push
```bash
cd "C:\Users\Dele Fatbemi\Documents\github active\Per-Medjat"
git add library/index.html
git commit -m "catalog: load tradition vocab from ontology JSON; Live Growing status badge"
git push
```

---

## Likely Push Failure Causes

**1. Authentication (most common on Windows HTTPS)**
GitHub stopped accepting passwords in 2021. HTTPS pushes require either:
- A Personal Access Token (PAT) stored in Windows Credential Manager, or
- GitHub CLI (`gh auth login`)

Check whether credentials are stored:
```
git credential-manager list
```
If nothing appears, or if you get a 403/authentication error, the token has
expired or was never set. Fix:
```
gh auth login
```
or generate a new PAT at https://github.com/settings/tokens (needs `repo` scope)
and re-enter credentials when prompted on next push.

**2. Nothing to push**
If `git push` says "Everything up-to-date", the changes were never committed.
Run `git status` first — if files show as `modified` under "Changes not staged
for commit", they need `git add` and `git commit` before `git push` will do
anything.

**3. Branch mismatch**
Both repos should be on `main`. Verify with `git branch`. If you're on a
different branch, either switch to main or push the current branch explicitly:
```
git push origin HEAD:main
```

---

## After Pushing iroko-framework

GitHub Pages rebuilds automatically. Wait 1–2 minutes, then verify:
```
https://ontology.irokosociety.org/vocab/tradition-vocab.json
```
If that URL returns JSON, the Per-Medjat catalog will resolve tradition badges
correctly on next page load — no further changes needed.

---

## Outstanding Data Fixes (do in the ontology manager, then rebuild + push again)

These three warnings fire every time `build_all.py` runs until fixed:

1. Rename concept `Santeria` → `tradition-santeria` in manager
2. Rename concept `Shango-Baptist` → `tradition-shango-baptist` in manager
3. Remove altLabel `"Shango Baptist"` from `tradition-trinidad-orisha` in manager
4. Add altLabel `"Abakuá"` (with accent) to `tradition-abakua` in manager —
   this is why Abakuá tradition badges are not showing in the catalog

After each manager fix: Run Build → git add/commit/push iroko-framework.
