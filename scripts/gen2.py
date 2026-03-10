#!/usr/bin/env python3
"""
gen2.py  –  Generate all 16 Iroko Framework module browse pages.
Each page links to  ../assets/iroko-module-style.css  (no embedded CSS).
Run from any directory.  Output: /home/claude/pages2/iroko-{mod}.html
"""
import json, os
from pathlib import Path

DATA = Path("/home/claude/iroko_data2.json")
OUT  = Path("/home/claude/pages2")
OUT.mkdir(exist_ok=True)

with open(DATA) as f:
    d = json.load(f)

# ── Module metadata ────────────────────────────────────────────────────────
META = {
    "agency":        {"display": "Agency Module",        "layer": "Governance Layer"},
    "authority":     {"display": "Authority Module",     "layer": "Governance Layer"},
    "core":          {"display": "Core Vocabulary",      "layer": "Foundation Layer"},
    "ekpe":          {"display": "Ékpè Module",          "layer": "Domain Layer"},
    "epistemic":     {"display": "Epistemic Module",     "layer": "Governance Layer"},
    "ewe":           {"display": "Ewé Module",           "layer": "Domain Layer"},
    "ile":           {"display": "Ilé Module",           "layer": "Domain Layer"},
    "manifestation": {"display": "Manifestation Module", "layer": "Governance Layer"},
    "marca":         {"display": "Marca Module",         "layer": "Domain Layer"},
    "narrative":     {"display": "Narrative Module",     "layer": "Governance Layer"},
    "ngoma":         {"display": "Ngoma Module",         "layer": "Domain Layer"},
    "nkisi":         {"display": "Nkisi Module",         "layer": "Domain Layer"},
    "qal":           {"display": "Qal Module",           "layer": "Domain Layer"},
    "sankofa":       {"display": "Sankofa Module",       "layer": "Domain Layer"},
    "travay":        {"display": "Travay Module",        "layer": "Domain Layer"},
    "veve":          {"display": "Vèvè Module",          "layer": "Domain Layer"},
}

# Build global class→module lookup
class_to_mod = {}
for mod, data in d.items():
    for cls in data["classes"]:
        class_to_mod[cls["uri"]] = mod

def esc_js(s):
    """Escape a string for use inside a JS single-quoted string literal."""
    return str(s).replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ").replace("\r", "")

def esc_html(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

# ── Build JS data blob ─────────────────────────────────────────────────────

def build_classes_js(classes, mod):
    parts = []
    for cls in classes:
        cid = cls["id"]

        # cross-module connections keyed by other module slug
        cross = {}
        for p in cls.get("outgoing", []):
            rng = p.get("range", "")
            other = class_to_mod.get(rng)
            if other and other != mod:
                cross.setdefault(other, {"via": [], "direction": "references"})
                cross[other]["via"].append(p["uri"])
        for p in cls.get("incoming", []):
            dom = p.get("domain", "")
            other = class_to_mod.get(dom)
            if other and other != mod:
                cross.setdefault(other, {"via": [], "direction": "referenced by"})
                cross[other]["via"].append(p["uri"])

        cross_items = []
        for om, info in cross.items():
            via = ", ".join(info["via"][:2])
            cross_items.append(
                "{name:'" + esc_js(META[om]["display"]) + "',slug:'" + om +
                "',dotClass:'dot-" + om +
                "',props:'via " + esc_js(via) +
                "',direction:'" + info["direction"] + "'}"
            )

        def make_prop_obj(p, dir_):
            end_key = "range" if dir_ == "out" else "domain"
            end_val = p.get("range" if dir_ == "out" else "domain", "")
            cm = class_to_mod.get(end_val, "")
            return (
                "{uri:'" + esc_js(p["uri"]) +
                "',label:'" + esc_js(p.get("label", "")) +
                "',definition:'" + esc_js(p.get("definition", "")) +
                "'," + end_key + ":'" + esc_js(end_val) +
                "',crossModule:'" + esc_js(cm) + "'}"
            )

        out_items = [make_prop_obj(p, "out") for p in cls.get("outgoing", [])]
        in_items  = [make_prop_obj(p, "in")  for p in cls.get("incoming", [])]

        parts.append(
            "  " + cid + ":{"
            "uri:'" + esc_js(cls["uri"]) + "',"
            "label:'" + esc_js(cls["label"]) + "',"
            "definition:'" + esc_js(cls.get("definition", "")) + "',"
            "outgoing:[" + ",".join(out_items) + "],"
            "incoming:[" + ",".join(in_items) + "],"
            "crossModuleConnections:[" + ",".join(cross_items) + "]}"
        )
    return "const CLASSES={\n" + ",\n".join(parts) + "\n};"


def build_module_connections_js(mod, classes):
    connected = {}
    for cls in classes:
        for p in cls.get("outgoing", []) + cls.get("incoming", []):
            other_uri = p.get("range", "") or p.get("domain", "")
            other = class_to_mod.get(other_uri)
            if other and other != mod:
                connected[other] = connected.get(other, 0) + 1
    items = []
    for om, cnt in connected.items():
        label = "property" if cnt == 1 else "properties"
        items.append(
            "{name:'" + esc_js(META[om]["display"]) + "',slug:'" + om +
            "',dotClass:'dot-" + om +
            "',props:'" + str(cnt) + " shared " + label + "'}"
        )
    return "const MODULE_CONNECTIONS=[\n" + ",\n".join(items) + "\n];"


# ── HTML fragments ──────────────────────────────────────────────────────────

def class_cards_html(classes):
    rows = []
    for cls in classes:
        rows.append(
            '<div class="class-card" id="card-' + cls["id"] + '" '
            'onclick="activateClass(\'' + cls["id"] + '\')">'
            '<span class="card-uri">iroko:' + esc_html(cls["id"]) + '</span>'
            '<span class="card-label">' + esc_html(cls["label"] or cls["id"]) + '</span>'
            '</div>'
        )
    return "\n        ".join(rows)


def scheme_blocks_html(schemes):
    if not schemes:
        return ('<p style="font-family:\'Cormorant Garamond\',serif;color:var(--border-mid);'
                'font-style:italic;font-size:0.9rem;padding:0.75rem 0;">'
                'No concept schemes defined in this module.</p>')
    blocks = []
    for s in schemes:
        defn = ('<div class="csb-description">' + esc_html(s["definition"]) + '</div>'
                if s.get("definition") else "")
        cards = "".join(
            '<div class="concept-card">'
            '<span class="cc-label">' + esc_html(c["label"] or c["id"]) + '</span>'
            '<span class="cc-id">' + esc_html(c["uri"]) + '</span>'
            '</div>'
            for c in s.get("concepts", [])
        )
        cnt = len(s.get("concepts", []))
        word = "concept" if cnt == 1 else "concepts"
        blocks.append(
            '<div class="concept-scheme-block">'
            '<div class="csb-header">'
            '<span class="csb-uri">' + esc_html(s["uri"]) + '</span>'
            '<span class="csb-count">' + str(cnt) + " " + word + '</span>'
            '</div>'
            '<div class="csb-scheme-label">' + esc_html(s["label"] or s["id"]) + '</div>'
            + defn +
            '<div class="concept-grid">' + cards + '</div>'
            '</div>'
        )
    return "\n      ".join(blocks)


# ── JS runtime ─────────────────────────────────────────────────────────────

JS_RUNTIME = """
let activeClass = null;

function activateClass(classId) {
  if (activeClass === classId) { deactivateClass(); return; }
  if (activeClass) document.getElementById('card-' + activeClass)?.classList.remove('is-active');
  activeClass = classId;
  document.getElementById('card-' + classId)?.classList.add('is-active');
  const data = CLASSES[classId];
  if (!data) return;
  document.getElementById('panel-uri').textContent   = data.uri;
  document.getElementById('panel-label').textContent = data.label;
  document.getElementById('panel-definition').textContent = data.definition || '';
  const cite = data.uri + '. Iroko Framework Ontology v1.2.0. Iroko Historical Society. https://ontology.irokosociety.org/iroko#' + classId;
  document.getElementById('panel-cite-text').innerHTML = '<em>' + cite + '</em>';
  document.getElementById('panel-cite-btn').dataset.cite = cite;
  renderProps('incoming-props', data.incoming, 'in');
  renderProps('outgoing-props', data.outgoing, 'out');
  document.getElementById('zone2-empty').classList.add('hidden');
  document.getElementById('zone2-hint').textContent = 'Click class again to close';
  const panel = document.getElementById('property-panel');
  panel.classList.add('visible');
  setTimeout(() => panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);
  renderClassSidebar(data, classId);
  history.replaceState(null, '', '#' + classId);
}

function deactivateClass() {
  if (activeClass) document.getElementById('card-' + activeClass)?.classList.remove('is-active');
  activeClass = null;
  document.getElementById('property-panel').classList.remove('visible');
  document.getElementById('zone2-empty').classList.remove('hidden');
  document.getElementById('zone2-hint').textContent = 'Select a class above to explore its properties';
  renderModuleSidebar();
  history.replaceState(null, '', window.location.pathname);
}

function renderProps(containerId, props, dir) {
  const el = document.getElementById(containerId);
  if (!props || props.length === 0) {
    el.innerHTML = '<div class="no-props">None documented in this module.</div>';
    return;
  }
  el.innerHTML = props.map((p, i) => {
    const id = 'prop-' + dir + '-' + i;
    const endLabel = dir === 'out' ? 'Range' : 'Domain';
    const endVal   = dir === 'out' ? (p.range || '') : (p.domain || '');
    const crossTag = (p.crossModule && p.crossModule !== MOD_SLUG)
      ? '<span class="cross-tag">[' + p.crossModule + ']</span>' : '';
    return '<div class="prop-item" id="' + id + '" onclick="toggleProp(\'' + id + '\')">'
      + '<div class="prop-item-top">'
      + '<span class="prop-item-uri">' + p.uri + '</span>'
      + '<svg class="prop-item-chevron" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="5,3 11,8 5,13"/></svg>'
      + '</div>'
      + '<span class="prop-item-label">' + (p.label || '') + '</span>'
      + '<div class="prop-detail" id="' + id + '-detail">'
      + '<div class="prop-detail-row"><span class="pd-label">' + endLabel + '</span>'
      + '<span class="pd-value">' + endVal + crossTag + '</span></div>'
      + '<div class="prop-detail-row"><span class="pd-label">Definition</span>'
      + '<span class="pd-value">' + (p.definition || '') + '</span></div>'
      + '</div></div>';
  }).join('');
}

function toggleProp(propId) {
  const item   = document.getElementById(propId);
  const detail = document.getElementById(propId + '-detail');
  if (!item || !detail) return;
  const isOpen = item.classList.contains('is-expanded');
  document.querySelectorAll('.prop-item.is-expanded').forEach(el => {
    el.classList.remove('is-expanded');
    el.querySelector('.prop-detail')?.classList.remove('visible');
  });
  if (!isOpen) { item.classList.add('is-expanded'); detail.classList.add('visible'); }
}

function renderClassSidebar(data, classId) {
  const el = document.getElementById('sb-connections');
  el.classList.add('fading');
  setTimeout(() => {
    document.getElementById('sb-title').textContent = 'iroko:' + classId + ' — connections';
    const conns = data.crossModuleConnections || [];
    el.innerHTML = '<div class="active-class-card">'
      + '<span class="acc-uri">' + data.uri + '</span>'
      + '<span class="acc-label">' + data.label + '</span></div>'
      + (conns.length === 0
        ? '<p class="no-connections">No cross-module connections.</p>'
        : conns.map(c =>
            '<a class="connection-card" href="../' + c.slug + '/index.html">'
            + '<div class="cc-top"><span class="cc-dot ' + c.dotClass + '"></span>'
            + '<span class="cc-module-name">' + c.name + '</span></div>'
            + '<span class="cc-props">' + c.props + '</span>'
            + '<span class="cc-via">' + c.direction + '</span></a>'
          ).join('')
      );
    el.classList.remove('fading');
  }, 130);
}

function renderModuleSidebar() {
  const el = document.getElementById('sb-connections');
  el.classList.add('fading');
  setTimeout(() => {
    document.getElementById('sb-title').textContent = 'Connected modules';
    el.innerHTML = MODULE_CONNECTIONS.length === 0
      ? '<p class="no-connections">No cross-module connections documented.</p>'
      : MODULE_CONNECTIONS.map(c =>
          '<a class="connection-card" href="../' + c.slug + '/index.html">'
          + '<div class="cc-top"><span class="cc-dot ' + c.dotClass + '"></span>'
          + '<span class="cc-module-name">' + c.name + '</span></div>'
          + '<span class="cc-props">' + c.props + '</span></a>'
        ).join('');
    el.classList.remove('fading');
  }, 130);
}

function copyPanelCitation(btn) {
  navigator.clipboard.writeText(btn.dataset.cite).then(() => {
    const orig = btn.innerHTML;
    btn.textContent = '✓ Copied'; btn.classList.add('copied');
    setTimeout(() => { btn.innerHTML = orig; btn.classList.remove('copied'); }, 2000);
  });
}
function copyModuleCitation(btn) {
  navigator.clipboard.writeText(MOD_CITE).then(() => {
    const orig = btn.innerHTML;
    btn.textContent = '✓ Copied'; btn.classList.add('copied');
    setTimeout(() => { btn.innerHTML = orig; btn.classList.remove('copied'); }, 2000);
  });
}
function copyPageLink(btn) {
  navigator.clipboard.writeText(window.location.href).then(() => {
    const orig = btn.innerHTML;
    btn.textContent = '✓'; btn.classList.add('copied-state');
    setTimeout(() => { btn.innerHTML = orig; btn.classList.remove('copied-state'); }, 2000);
  });
}
function shareEmail(e) {
  e.preventDefault();
  window.location.href = 'mailto:?subject=' + encodeURIComponent('Iroko Framework — ' + MOD_DISPLAY)
    + '&body=' + encodeURIComponent(window.location.href);
}

window.addEventListener('DOMContentLoaded', () => {
  renderModuleSidebar();
  const hash = window.location.hash.slice(1);
  if (hash && CLASSES[hash]) setTimeout(() => activateClass(hash), 100);
});
"""

# ── Page template ───────────────────────────────────────────────────────────

def page_html(mod, data):
    meta    = META[mod]
    title   = meta["display"]
    layer   = meta["layer"]
    stats   = data["stats"]
    desc    = data.get("description") or ""
    short   = (desc.split(".")[0] + ".") if desc else ""
    cite    = '"' + title + '." Iroko Framework Ontology v1.2.0. Iroko Historical Society. https://ontology.irokosociety.org/' + mod
    classes_js  = build_classes_js(data["classes"], mod)
    modconn_js  = build_module_connections_js(mod, data["classes"])
    cards_html  = class_cards_html(data["classes"])
    schemes_html = scheme_blocks_html(data["schemes"])

    return """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Iroko Framework Ontology</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=Source+Code+Pro:wght@300;400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../assets/iroko-module-style.css" />
</head>
<body>

  <!-- ── Site nav ─────────────────────────────────────────── -->
  <nav class="site-nav">
    <a href="../index.html">
      <img class="nav-logo" src="../assets/IHS-Logo.jpg" alt="Iroko Historical Society" />
    </a>
    <a class="nav-wordmark" href="../index.html">Iroko Framework Ontology</a>
    <ul class="nav-links">
      <li><a href="../vocab/">Modules</a></li>
      <li><a href="../vocab/iroko-termlist.html">Classes</a></li>
      <li><a href="../vocab/iroko-termlist.html">Properties</a></li>
      <li><a href="../vocab/iroko-termlist.html">Concepts</a></li>
    </ul>
  </nav>

  <!-- ── Page header ──────────────────────────────────────── -->
  <header class="page-header">
    <div class="header-inner">
      <div class="breadcrumb">
        <a href="../index.html">Iroko Framework</a>
        <span>›</span>
        <a href="../vocab/">Modules</a>
        <span>›</span>
        {title}
      </div>
      <h1>{title} <span class="module-tag">{layer}</span></h1>
      <div class="module-desc">{short}</div>
      <div class="module-stats">
        <div class="stat"><span class="number">{n_classes}</span><span class="label">Classes</span></div>
        <div class="stat"><span class="number">{n_props}</span><span class="label">Properties</span></div>
        <div class="stat"><span class="number">{n_schemes}</span><span class="label">Concept Schemes</span></div>
        <div class="stat"><span class="number">{n_concepts}</span><span class="label">Concepts</span></div>
      </div>
    </div>
  </header>

  <!-- ── Content layout ───────────────────────────────────── -->
  <div class="layout">
    <main class="main-content">

      <!-- Zone 1: Classes -->
      <div class="zone-label">
        Classes
        <span class="zone-hint">Select a class to explore its properties</span>
      </div>
      <div class="class-grid">
        {cards}
      </div>

      <!-- Zone 2: Properties -->
      <div class="zone-label">
        Properties
        <span class="zone-hint" id="zone2-hint">Select a class above to explore its properties</span>
      </div>
      <div class="zone2-empty" id="zone2-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
          <circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/>
        </svg>
        No class selected. Click any class card above to see its incoming and outgoing properties.
      </div>
      <div class="property-panel" id="property-panel">
        <div class="panel-header">
          <div>
            <div class="ph-uri" id="panel-uri"></div>
            <div class="ph-label" id="panel-label"></div>
          </div>
          <button class="panel-close" onclick="deactivateClass()">✕</button>
        </div>
        <div class="panel-definition" id="panel-definition"></div>
        <div class="panel-body">
          <div class="prop-col">
            <div class="prop-col-label">
              <span class="direction-arrow">←</span> Incoming
              <span class="col-sublabel">(this class as range)</span>
            </div>
            <div id="incoming-props"></div>
          </div>
          <div class="prop-col">
            <div class="prop-col-label">
              <span class="direction-arrow">→</span> Outgoing
              <span class="col-sublabel">(this class as domain)</span>
            </div>
            <div id="outgoing-props"></div>
          </div>
        </div>
        <div class="panel-citation">
          <div class="cite-text" id="panel-cite-text"></div>
          <button class="btn-copy" id="panel-cite-btn" onclick="copyPanelCitation(this)">
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="4" y="4" width="9" height="10" rx="1"/>
              <path d="M3 3H2a1 1 0 00-1 1v9a1 1 0 001 1h9a1 1 0 001-1v-1"/>
            </svg>
            Copy citation
          </button>
        </div>
      </div>

      <!-- Zone 3: Controlled vocabulary -->
      <div class="zone-label">Controlled Vocabulary</div>
      {schemes}

    </main>

    <!-- ── Sidebar ─────────────────────────────────────────── -->
    <aside class="sidebar">
      <div class="sidebar-panel">
        <div class="sidebar-panel-title" id="sb-title">Connected modules</div>
        <div class="sidebar-dynamic" id="sb-connections"></div>
      </div>
      <div class="sidebar-panel">
        <div class="sidebar-panel-title">Share</div>
        <div class="share-buttons">
          <a class="share-btn" href="#" onclick="shareEmail(event)">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="2" y="4" width="16" height="12" rx="1.5"/>
              <polyline points="2,4 10,12 18,4"/>
            </svg>
            Email
          </a>
          <a class="share-btn" href="#" onclick="window.print();return false;">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="5" y="2" width="10" height="6"/>
              <rect x="2" y="8" width="16" height="8" rx="1"/>
              <rect x="5" y="12" width="10" height="5"/>
              <circle cx="15" cy="11" r="1" fill="currentColor" stroke="none"/>
            </svg>
            Print
          </a>
          <button class="share-btn" onclick="copyPageLink(this)">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M8 12a4 4 0 005.66 0l2-2A4 4 0 009.9 4.24l-1 1"/>
              <path d="M12 8a4 4 0 00-5.66 0l-2 2A4 4 0 006.1 15.76l1-1"/>
            </svg>
            Link
          </button>
        </div>
      </div>
      <div class="sidebar-panel">
        <div class="sidebar-panel-title">Cite the {title}</div>
        <div class="sidebar-citation">
          <div class="cite-text">"{title}." Iroko Framework Ontology v1.2.0. Iroko Historical Society. <em>ontology.irokosociety.org/{mod}</em></div>
          <button class="btn-copy-sm" onclick="copyModuleCitation(this)">
            <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="4" y="4" width="9" height="10" rx="1"/>
              <path d="M3 3H2a1 1 0 00-1 1v9a1 1 0 001 1h9a1 1 0 001-1v-1"/>
            </svg>
            Copy citation
          </button>
        </div>
      </div>
      <div class="sidebar-panel">
        <div class="sidebar-panel-title">Other formats</div>
        <div class="format-links">
          <a class="format-link" href="../vocab/iroko-{mod}.ttl">RDF/Turtle <span class="format-arrow">↗</span></a>
          <a class="format-link" href="../vocab/iroko-{mod}.jsonld">JSON-LD <span class="format-arrow">↗</span></a>
          <a class="format-link" href="../vocab/iroko-{mod}.rdf">RDF/XML <span class="format-arrow">↗</span></a>
          <a class="format-link" href="../vocab/iroko-{mod}.nt">N-Triples <span class="format-arrow">↗</span></a>
        </div>
      </div>
    </aside>
  </div>

  <!-- ── Footer ────────────────────────────────────────────── -->
  <footer>
    <div class="footer-logo">Iroko Historical Society</div>
    <div class="footer-links">
      <a href="https://ontology.irokosociety.org">ontology.irokosociety.org</a>
      <a href="https://irokosociety.org">irokosociety.org</a>
      <a href="https://github.com/iroko-framework/iroko-framework">GitHub</a>
    </div>
    <div class="footer-cc">CC0 1.0 Universal · Public Domain</div>
    <span class="version-badge">v1.2.0</span>
  </footer>

<script>
const MOD_SLUG    = '{mod}';
const MOD_DISPLAY = '{title}';
const MOD_CITE    = '{cite}';
{classes_js}
{modconn_js}
{js_runtime}
</script>
</body>
</html>""".format(
        title=title, layer=layer, short=short, mod=mod, cite=esc_js(cite),
        n_classes=stats["classes"], n_props=stats["properties"],
        n_schemes=stats["schemes"], n_concepts=stats["concepts"],
        cards=cards_html, schemes=schemes_html,
        classes_js=classes_js, modconn_js=modconn_js,
        js_runtime=JS_RUNTIME,
    )


# ── Generate ────────────────────────────────────────────────────────────────
for mod, data in d.items():
    html = page_html(mod, data)
    out  = OUT / ("iroko-" + mod + ".html")
    out.write_text(html, encoding="utf-8")
    stats = data["stats"]
    print(f"  ✓  {mod:<16}  {stats['classes']} cls  {stats['properties']} prop  {stats['schemes']} sch  {stats['concepts']} concepts")

print(f"\nAll {len(d)} pages written to {OUT}")
