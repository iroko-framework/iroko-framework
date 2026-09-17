# Where v2.0.0 actually stands

A working orientation document, not a decision record. Written because the volume of
open threads across the ontology, the corpora, the hosting layer, and the tooling had
become hard to hold in view at once. Read this before opening either ADR.

---

## The four layers, and which ones are actually coupled

Everything in this project sorts into four layers. The confusion is not that any one
of them is unclear on its own; it is that they get reasoned about together when only
two of them are actually dependent on each other.

**The ontology** (`iroko-framework`, this repo). Sixteen domain and governance TTL
modules plus two alignment modules, one shared namespace, published to Zenodo, CC0.
This is the vocabulary: what an eldership tier means, what a religious office is,
what an epistemic constraint is. It does not hold data.

**The corpora**. Three of them, at three different stages. The Medjat Library
(Zotero-backed public catalog, scaling toward 10,000 records, already has three
working Python tools) is the most mature. Ewé is pilot-stage, a single 47KB TTL
file, deliberately not pressed on yet. Hyatt is the real one: 16,225 extracted
records, currently living as atomic notes in the IHS-Vault, and the reason Obsidian
has become unusable when the framework and the corpus are transcluded together.

**Access and hosting**. The public sites (irokosociety.org, medjat.irokosociety.org,
ontology.irokosociety.org) are static HTML on GitHub Pages behind Cloudflare. Static
means no server-side code, ever, on that hosting. The decision to move Hyatt and Ewé
into PostgreSQL is a decision about where the *data* lives. It says nothing yet about
what serves gated queries against that data to a browser, and nothing in the current
toolset answers that. Medjat Steward, in particular, is a Streamlit app you run
yourself to review and tag records; it is not a public-facing backend, and I want to
correct an assumption from earlier in this thread that treated it as a plausible
serving layer. It isn't one.

**Tooling**. IHS Library Manager (desktop app, v0.2.2), medjat-tools (Acquire,
Steward, the static-site builder), and the ontology repo's own `scripts/build_all.py`
pipeline. These consume the ontology and the corpora; they do not make decisions
about either.

The load-bearing fact, and it is already your own decision, recorded in your own
notes: **the ontology overhaul and the Hyatt database run on separate timelines and
should not be coupled.** They are coupled in exactly one place, the access-tier and
tradition vocabulary the database will need to reference, and nowhere else. Treating
them as one undifferentiated "v2.0.0 problem" is very likely a real part of why this
feels unseeable. It is at least three separate problems wearing one label.

---

## Where each layer actually stands, right now, verified against source rather than the vault

**Ontology.** v1.4.0 is published and stable (Zenodo, CC0, 101 classes, 413
properties, 76 schemes, 650 concepts). `dev/v2.0.0` exists, branched from `main` on
August 19. It has exactly **one commit** beyond main: the tradition-axes ADR. No TTL
has changed. I added a second ADR today, on gender and dual-clock age as eldership
markers, currently sitting uncommitted in the worktree. Between the two ADRs there
are **twelve open questions**, none of them answered yet, and per both documents'
own terms, none of the underlying TTL should be written until they are.

**Corpora.** Medjat Library is live and growing. Ewé is a single pilot file.
Hyatt is extracted but architecturally homeless: too large for Obsidian
transclusion, not yet in Postgres, access tiers for it "to be assigned after seeing
the data," which has not fully happened yet.

**Access and hosting.** Solid on the public, unrestricted side: DNS, TLS, HSTS,
bot protection, and email authentication were all hardened as of August 25. Nothing
exists yet for gated access to anything beyond that. This is not a gap in a plan
you have not gotten to; it is a decision with no owner yet, and it is independent of
the ontology work.

**Tooling.** The most finished layer. Three working Python tools for the Medjat
side; a desktop app with a short, known punch list. Not blocking anything else.

---

## Concrete holes, the kind that trip you up quietly rather than loudly

A few things surfaced by actually reading the source rather than the summaries of it,
worth naming because each one is the sort of thing that costs a afternoon later if it
is not caught now.

The published `docs/ARCHITECTURE.md` and the actual vocabulary have already drifted
once. The architecture doc's access-tier table lists tier 2 as "Public, Attributed"
(open, with required source attribution). The TTL itself defines tier 2 as
`access-public-no-amplification`, "publicly viewable but should not be amplified,
shared widely, or used for commercial purposes." These are not the same rule. One is
about crediting a source; the other is about restricting redistribution. Nothing
enforces that documentation and vocabulary stay in lockstep, and here they didn't.

`CLAUDE.md`, the repo's own instructions file, was last verified against the TTL on
August 9, ten days before the `dev/v2.0.0` branch existed. It does not mention the
branch, the ADRs, or that the branch is where the next breaking change is supposed
to land. Anyone, including a future Claude Code session, reading `CLAUDE.md` cold
would not know this branch exists.

The release-manifest idea, `vocab/release.json`, pinning which module version
composes each framework release, is already written up in `CLAUDE.md` as "the
correct next change." It still doesn't exist. Its absence is exactly why the
framework release label and the per-module version numbers can look like the same
number and not be, which `CLAUDE.md` also already flags as the source of the
vault's version confusion.

The vault's own hub page is already known to report wrong version numbers for this
framework (v1.2.0, plus a fictitious Core/Agency/Ewe conflict at v2.0.0 and v2.1.0
that doesn't match this repo at all). If planning ever gets done by consulting the
vault instead of the repo, it will be planning against numbers that are already
wrong.

`CLAUDE.md` warns, in its own words, that a tradition-vocabulary rename propagates
to two other repos, Per-Medjat and medjat-tools, and that this needs a coordinated
change, not three separate ones. ADR 0001 already proposes deprecating and renaming
a large share of the fifty tradition concepts. That warning is no longer
hypothetical; it describes work that is now actually queued.

The gender-eligibility question in the second ADR exists because three
uncoordinated, partial mechanisms for it were already in the vocabulary before I
looked: a generalized constraint-basis concept in the epistemic module, and two
free-text properties bolted onto two unrelated domain classes in Ekpe and Marca.
None of the three can see the other two. Left alone, a fourth module solving the
same problem its own way is the likely next state, not a hypothetical risk.

And the biggest one: there is no serving-layer decision for gated Postgres access
behind a static site. This is not an ontology question and answering the twelve
open ADR questions will not touch it. It needs to be scoped on its own.

---

## What actually blocks what

In dependency order, not priority order:

1. The twelve open questions across the two ADRs get answered. This is a scoping
   conversation, not implementation, and per your own workflow it belongs in chat.
2. TTL gets written against those answers, validated with `rapper`, and run through
   `build_all.py`. `iroko-core.ttl` goes to 2.0.0 per ADR 0001's own versioning
   call; other touched modules bump per whatever actually changed in them.
3. `tradition-vocab.json` regenerates, and Per-Medjat and medjat-tools get updated
   in the same coordinated push `CLAUDE.md` already warns about. Not after; in the
   same push.
4. Only once the vocabulary is stable does it make sense to finalize Hyatt and Ewé
   tagging against it, and lock a Postgres schema that encodes the access tiers and
   tradition terms correctly the first time.
5. The serving-layer question (how a static site talks to gated Postgres) gets
   decided on its own track, in parallel with 1 through 4, not after them. It has no
   ontology dependency at all.
6. The Obsidian slowdown is a symptom of step 4 not having happened yet, the Hyatt
   corpus has nowhere else to live. It resolves as a side effect of the Postgres
   migration, not as its own project.

Steps 1 through 4 are the only truly sequential chain. Step 5 is independent and has
been sitting unowned. Step 6 is not a separate problem at all.

---

## What "done" looks like for v2.0.0

Concretely, using the release checklist already written into `CLAUDE.md`: the ADR
questions resolved, TTL changed only in the modules that actually changed, versions
bumped per the module-independent policy (not a blanket bump, that policy is
already decided and correct), `scripts/deploy.sh` run clean, Per-Medjat and
medjat-tools updated in step with the vocabulary change rather than after it, a
`CHANGELOG.md` entry naming exactly which modules moved, and a new Zenodo deposit.
The framework release label becomes 2.0.0, which also respects staying inside the
v2.x range rather than creeping further.

That is the ontology track's finish line. The Hyatt/Postgres track's finish line is
a separate, later document: a locked schema, a resolved serving-layer decision, and
tiered data migrated out of Obsidian. It does not need to wait for the ontology
track to close, only for the vocabulary it references to stop moving.

---

## The one next action

Everything above funnels to one honest bottleneck: nothing else can move until the
twelve open questions in `docs/adr/0001-tradition-axes.md` and
`docs/adr/0002-eldership-eligibility-axes.md` get answered. That is a short,
bounded conversation, not a research task, and it is the only thing standing between
where this is now and a TTL that can actually be written.
