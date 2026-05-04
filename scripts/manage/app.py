"""
app.py — Iroko Framework Management GUI

Run:
    python app.py
    Open http://localhost:5050

This tool edits the TTL files in vocab/ directly. It does NOT touch any
generated HTML. After editing, click "Run Build" to regenerate all HTML.
"""

import subprocess
import sys
from pathlib import Path
from flask import (Flask, render_template, redirect, url_for,
                   request, flash, Response, stream_with_context)

MANAGE_DIR  = Path(__file__).resolve().parent
SCRIPTS_DIR = MANAGE_DIR.parent
REPO_ROOT   = SCRIPTS_DIR.parent

sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(MANAGE_DIR))

import iroko_manager as mgr
from iroko_config import MODULE_CONFIG, ACCESS_MAP, MODULES

app = Flask(__name__)
app.secret_key = "iroko-manage-local-only"  # local tool only, not a public secret

# ---------------------------------------------------------------------------
# Context helpers
# ---------------------------------------------------------------------------

ACCESS_OPTIONS = [
    ("access-public-unrestricted",     "Public — Unrestricted"),
    ("access-public-no-amplification", "Public — No Amplification"),
    ("access-public-attributed",       "Public — Attributed"),
    ("access-community-only",          "Community Only"),
    ("access-initiated-only",          "Initiated Only"),
    ("access-initiated-elder",         "Initiated Elder"),
    ("access-no-access",               "No Access"),
]

PROP_TYPE_OPTIONS = ["ObjectProperty", "DatatypeProperty", "AnnotationProperty"]

LAYER_OPTIONS = ["Foundation", "Governance", "Domain", "Alignment"]

def module_stems():
    return [stem for *_, stem in MODULES if "Alignment" not in _]

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    modules = mgr.list_modules()
    return render_template("dashboard.html", modules=modules)

# ---------------------------------------------------------------------------
# Module view
# ---------------------------------------------------------------------------

@app.route("/module/<stem>")
def module_view(stem):
    if stem not in MODULE_CONFIG and not (REPO_ROOT / "vocab" / f"{stem}.ttl").exists():
        flash(f"Module '{stem}' not found.", "error")
        return redirect(url_for("dashboard"))
    try:
        g = mgr.load_module(stem)
    except Exception as e:
        flash(f"Could not load {stem}.ttl: {e}", "error")
        return redirect(url_for("dashboard"))

    cfg      = MODULE_CONFIG.get(stem, {"title": stem, "layer": "Unknown", "tag_cls": "tag-upcoming", "tag_text": stem})
    classes  = mgr.get_all_classes(g)
    props    = mgr.get_all_properties(g)
    concepts = mgr.get_all_concepts(g)
    schemes  = mgr.get_all_schemes(g)
    all_stems = [s for *_, s in MODULES]

    return render_template("module_view.html",
        stem=stem, cfg=cfg,
        classes=classes, props=props, concepts=concepts, schemes=schemes,
        all_stems=all_stems,
    )

# ---------------------------------------------------------------------------
# Concept routes
# ---------------------------------------------------------------------------

@app.route("/module/<stem>/concept/new", methods=["GET", "POST"])
def concept_new(stem):
    g = mgr.load_module(stem)
    schemes = mgr.get_scheme_options(g)

    if request.method == "POST":
        data = {
            "local_id":   request.form["local_id"].strip(),
            "label":      request.form.get("label", "").strip(),
            "definition": request.form.get("definition", "").strip(),
            "scope_note": request.form.get("scope_note", "").strip(),
            "scheme_id":  request.form.get("scheme_id", "").strip(),
            "broader":    request.form.get("broader", "").strip(),
            "access":     request.form.get("access", "access-public-unrestricted"),
        }
        if not data["local_id"]:
            flash("Local ID is required.", "error")
        else:
            mgr.upsert_concept(g, data)
            mgr.save_module(stem, g)
            flash(f"Concept iroko:{data['local_id']} saved.", "success")
            return redirect(url_for("module_view", stem=stem) + "#concepts")

    return render_template("term_edit.html",
        stem=stem, term_type="concept", mode="new",
        data={}, schemes=schemes,
        access_options=ACCESS_OPTIONS,
        class_options=[], prop_type_options=[],
    )

@app.route("/module/<stem>/concept/<local_id>/edit", methods=["GET", "POST"])
def concept_edit(stem, local_id):
    g = mgr.load_module(stem)
    schemes = mgr.get_scheme_options(g)
    data = mgr.get_concept(g, local_id) or {}

    if request.method == "POST":
        data = {
            "local_id":   local_id,
            "label":      request.form.get("label", "").strip(),
            "definition": request.form.get("definition", "").strip(),
            "scope_note": request.form.get("scope_note", "").strip(),
            "scheme_id":  request.form.get("scheme_id", "").strip(),
            "broader":    request.form.get("broader", "").strip(),
            "access":     request.form.get("access", "access-public-unrestricted"),
        }
        mgr.upsert_concept(g, data)
        mgr.save_module(stem, g)
        flash(f"Concept iroko:{local_id} updated.", "success")
        return redirect(url_for("module_view", stem=stem) + "#concepts")

    return render_template("term_edit.html",
        stem=stem, term_type="concept", mode="edit",
        data=data, schemes=schemes,
        access_options=ACCESS_OPTIONS,
        class_options=[], prop_type_options=[],
    )

@app.route("/module/<stem>/concept/<local_id>/delete", methods=["POST"])
def concept_delete(stem, local_id):
    g = mgr.load_module(stem)
    removed = mgr.delete_term(g, local_id)
    if removed:
        mgr.save_module(stem, g)
        flash(f"Concept iroko:{local_id} deleted.", "success")
    else:
        flash(f"iroko:{local_id} not found.", "error")
    return redirect(url_for("module_view", stem=stem) + "#concepts")

# ---------------------------------------------------------------------------
# Class routes
# ---------------------------------------------------------------------------

@app.route("/module/<stem>/class/new", methods=["GET", "POST"])
def class_new(stem):
    g = mgr.load_module(stem)
    class_options = mgr.get_class_options(g)

    if request.method == "POST":
        superclasses = [s.strip() for s in request.form.get("superclasses", "").split(",") if s.strip()]
        data = {
            "local_id":    request.form["local_id"].strip(),
            "label":       request.form.get("label", "").strip(),
            "definition":  request.form.get("definition", "").strip(),
            "superclasses": superclasses,
            "access":      request.form.get("access", "access-public-unrestricted"),
        }
        if not data["local_id"]:
            flash("Local ID is required.", "error")
        else:
            mgr.upsert_class(g, data)
            mgr.save_module(stem, g)
            flash(f"Class iroko:{data['local_id']} saved.", "success")
            return redirect(url_for("module_view", stem=stem) + "#classes")

    return render_template("term_edit.html",
        stem=stem, term_type="class", mode="new",
        data={}, schemes=[], class_options=class_options,
        access_options=ACCESS_OPTIONS, prop_type_options=[],
    )

@app.route("/module/<stem>/class/<local_id>/edit", methods=["GET", "POST"])
def class_edit(stem, local_id):
    g = mgr.load_module(stem)
    class_options = mgr.get_class_options(g)
    data = mgr.get_class(g, local_id) or {}

    if request.method == "POST":
        superclasses = [s.strip() for s in request.form.get("superclasses", "").split(",") if s.strip()]
        data = {
            "local_id":    local_id,
            "label":       request.form.get("label", "").strip(),
            "definition":  request.form.get("definition", "").strip(),
            "superclasses": superclasses,
            "access":      request.form.get("access", "access-public-unrestricted"),
        }
        mgr.upsert_class(g, data)
        mgr.save_module(stem, g)
        flash(f"Class iroko:{local_id} updated.", "success")
        return redirect(url_for("module_view", stem=stem) + "#classes")

    return render_template("term_edit.html",
        stem=stem, term_type="class", mode="edit",
        data=data, schemes=[], class_options=class_options,
        access_options=ACCESS_OPTIONS, prop_type_options=[],
    )

@app.route("/module/<stem>/class/<local_id>/delete", methods=["POST"])
def class_delete(stem, local_id):
    g = mgr.load_module(stem)
    removed = mgr.delete_term(g, local_id)
    if removed:
        mgr.save_module(stem, g)
        flash(f"Class iroko:{local_id} deleted.", "success")
    else:
        flash(f"iroko:{local_id} not found.", "error")
    return redirect(url_for("module_view", stem=stem) + "#classes")

# ---------------------------------------------------------------------------
# Property routes
# ---------------------------------------------------------------------------

@app.route("/module/<stem>/property/new", methods=["GET", "POST"])
def property_new(stem):
    g = mgr.load_module(stem)
    class_options = mgr.get_class_options(g)

    if request.method == "POST":
        data = {
            "local_id":   request.form["local_id"].strip(),
            "label":      request.form.get("label", "").strip(),
            "definition": request.form.get("definition", "").strip(),
            "prop_type":  request.form.get("prop_type", "ObjectProperty"),
            "domain":     request.form.get("domain", "").strip(),
            "range":      request.form.get("range", "").strip(),
            "access":     request.form.get("access", "access-public-unrestricted"),
        }
        if not data["local_id"]:
            flash("Local ID is required.", "error")
        else:
            mgr.upsert_property(g, data)
            mgr.save_module(stem, g)
            flash(f"Property iroko:{data['local_id']} saved.", "success")
            return redirect(url_for("module_view", stem=stem) + "#properties")

    return render_template("term_edit.html",
        stem=stem, term_type="property", mode="new",
        data={}, schemes=[], class_options=class_options,
        access_options=ACCESS_OPTIONS, prop_type_options=PROP_TYPE_OPTIONS,
    )

@app.route("/module/<stem>/property/<local_id>/edit", methods=["GET", "POST"])
def property_edit(stem, local_id):
    g = mgr.load_module(stem)
    class_options = mgr.get_class_options(g)
    data = mgr.get_property(g, local_id) or {}

    if request.method == "POST":
        data = {
            "local_id":   local_id,
            "label":      request.form.get("label", "").strip(),
            "definition": request.form.get("definition", "").strip(),
            "prop_type":  request.form.get("prop_type", "ObjectProperty"),
            "domain":     request.form.get("domain", "").strip(),
            "range":      request.form.get("range", "").strip(),
            "access":     request.form.get("access", "access-public-unrestricted"),
        }
        mgr.upsert_property(g, data)
        mgr.save_module(stem, g)
        flash(f"Property iroko:{local_id} updated.", "success")
        return redirect(url_for("module_view", stem=stem) + "#properties")

    return render_template("term_edit.html",
        stem=stem, term_type="property", mode="edit",
        data=data, schemes=[], class_options=class_options,
        access_options=ACCESS_OPTIONS, prop_type_options=PROP_TYPE_OPTIONS,
    )

@app.route("/module/<stem>/property/<local_id>/delete", methods=["POST"])
def property_delete(stem, local_id):
    g = mgr.load_module(stem)
    removed = mgr.delete_term(g, local_id)
    if removed:
        mgr.save_module(stem, g)
        flash(f"Property iroko:{local_id} deleted.", "success")
    else:
        flash(f"iroko:{local_id} not found.", "error")
    return redirect(url_for("module_view", stem=stem) + "#properties")

# ---------------------------------------------------------------------------
# Move term
# ---------------------------------------------------------------------------

@app.route("/term/move", methods=["GET", "POST"])
def term_move():
    all_stems = [s for *_, s in MODULES]

    if request.method == "POST":
        local_id  = request.form["local_id"].strip()
        from_stem = request.form["from_stem"].strip()
        to_stem   = request.form["to_stem"].strip()

        if not all([local_id, from_stem, to_stem]):
            flash("All fields required.", "error")
        elif from_stem == to_stem:
            flash("Source and destination must differ.", "error")
        else:
            ok, msg = mgr.move_term(local_id, from_stem, to_stem)
            flash(msg, "success" if ok else "error")
            if ok:
                return redirect(url_for("module_view", stem=to_stem))

    return render_template("move_term.html", all_stems=all_stems,
                           prefill=request.args.to_dict())

# ---------------------------------------------------------------------------
# New module
# ---------------------------------------------------------------------------

@app.route("/module/new", methods=["GET", "POST"])
def module_new():
    if request.method == "POST":
        stem        = request.form["stem"].strip().lower().replace(" ", "-")
        title       = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        layer       = request.form.get("layer", "Domain")
        prefix      = request.form.get("prefix", "iroko:").strip()
        tag_text    = request.form.get("tag_text", "").strip() or title

        if not stem:
            flash("Stem is required.", "error")
        elif not stem.startswith("iroko-"):
            flash("Stem must start with 'iroko-' (e.g., iroko-mymodule).", "error")
        else:
            ok, msg = mgr.create_module(stem, title, description, layer, prefix, tag_text)
            flash(msg, "success" if ok else "error")
            if ok:
                flash("Add this module to iroko_config.py MODULE_CONFIG and MODULES to include it in builds.", "info")
                return redirect(url_for("module_view", stem=stem))

    return render_template("module_new.html", layer_options=LAYER_OPTIONS)

# ---------------------------------------------------------------------------
# Tradition aliases
# ---------------------------------------------------------------------------

@app.route("/traditions")
def traditions():
    g = mgr.load_module("iroko-core")
    concepts = mgr.get_tradition_concepts(g)
    return render_template("traditions.html", concepts=concepts)

@app.route("/traditions/<local_id>/aliases", methods=["GET", "POST"])
def tradition_aliases(local_id):
    g = mgr.load_module("iroko-core")
    concept = mgr.get_concept(g, local_id)
    if concept is None:
        flash(f"Tradition concept '{local_id}' not found in iroko-core.", "error")
        return redirect(url_for("traditions"))

    if request.method == "POST":
        raw = request.form.get("alt_labels", "")
        new_alts = [a.strip() for a in raw.split("\n") if a.strip()]
        mgr.set_alt_labels(g, local_id, new_alts)
        mgr.save_module("iroko-core", g)
        flash(f"Aliases for {concept['label']} updated ({len(new_alts)} alias(es)).", "success")
        return redirect(url_for("traditions"))

    return render_template("tradition_aliases.html", concept=concept)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

@app.route("/build")
def build_page():
    return render_template("build.html")

@app.route("/build/run", methods=["POST"])
def build_run():
    """Stream build_all.py output as Server-Sent Events."""
    build_script = SCRIPTS_DIR / "build_all.py"

    def generate():
        yield "data: Starting build...\n\n"
        try:
            proc = subprocess.Popen(
                [sys.executable, str(build_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(REPO_ROOT),
            )
            for line in proc.stdout:
                yield f"data: {line.rstrip()}\n\n"
            proc.wait()
            status = "Build complete." if proc.returncode == 0 else f"Build finished with errors (exit {proc.returncode})."
            yield f"data: \n\n"
            yield f"data: {status}\n\n"
            yield "data: __DONE__\n\n"
        except Exception as e:
            yield f"data: ERROR: {e}\n\n"
            yield "data: __DONE__\n\n"

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Iroko Framework Manager")
    print(f"  Vocab dir:  {mgr.VOCAB_DIR}")
    print(f"  Repo root:  {REPO_ROOT}")
    print(f"  Open:       http://localhost:5050")
    print()
    app.run(host="127.0.0.1", port=5050, debug=False)
