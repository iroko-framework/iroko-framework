# Iroko Framework Manager

Local web tool for managing the Iroko Framework ontology. Edits the TTL files
in `vocab/` directly. Does not touch any public-facing HTML.

---

## Launch

```bash
# From the repo root:
cd "C:\Users\Dele Fatbemi\Documents\github active\iroko-framework"
pip install -r requirements.txt
python scripts\manage\app.py
```

Open **http://localhost:5050** in any browser.

---

## What you can do

| Task | Where |
|------|-------|
| View all modules with term counts | Dashboard (/) |
| Add/edit/delete a tradition or any SKOS concept | Module → Concepts section → Edit or + Add Concept |
| Add/edit/delete an OWL class | Module → Classes section |
| Add/edit/delete a property | Module → Properties section |
| Move a term from one module to another | Move Term page |
| Create a new module (scaffolds the TTL) | New Module page |
| Regenerate all HTML after editing | Run Build page |

---

## Adding a tradition (step-by-step)

1. Open http://localhost:5050
2. Click **iroko-core**
3. Scroll to **Concepts**, click **+ Add Concept**
4. Fill in:
   - **Local ID**: `tradition-spiritual-baptists` (kebab-case, no spaces)
   - **Preferred Label**: `Spiritual Baptists`
   - **Definition**: one clear sentence
   - **Concept Scheme**: `TraditionScheme`
   - **Access Level**: Public — Unrestricted (for most traditions)
5. Click **Create Concept**
6. Go to **Run Build** and click **Run Build** to regenerate the HTML

---

## After editing TTL files

The manager saves directly to `vocab/*.ttl`. These are the source of truth.
Generated files (`vocab/*.html`, `vocab/*.jsonld`, etc.) are not updated
until you run the build:

- **In the manager:** Run Build page → Run Build button
- **From the terminal:** `python scripts/build_all.py`

---

## Adding a new module to the build pipeline

After using the New Module page to create the TTL scaffold, open
`scripts/iroko_config.py` and add entries in two places:

```python
# In MODULES list:
("My Module", "Domain", "MyTag", IROKO_NS, "iroko-mymodule"),

# In MODULE_CONFIG dict:
"iroko-mymodule": {
    "title":    "My Module — Description",
    "subtitle": "What this module covers",
    "tag_cls":  "tag-upcoming",   # or add a new tag color
    "tag_text": "MyTag",
    "prefix":   "iroko:",
    "dot_cls":  "dot-other",
    "layer":    "Domain",
},
```

Then run the build.

---

## Notes

- The manager runs on `localhost:5050` only — it is not accessible from other machines.
- All writes are atomic: a `.tmp` file is validated before replacing the live TTL.
- If a save produces invalid Turtle, the live file is untouched and the error surfaces in the flash message.
- The manager does not push to GitHub. Use `scripts/deploy.sh` or git manually when ready to publish.
