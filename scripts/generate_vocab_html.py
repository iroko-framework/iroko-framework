#!/usr/bin/env python3
"""
Generate human-readable HTML documentation from Turtle vocabulary files.

Usage:
    python generate_vocab_html.py
    
Reads all .ttl files in vocab/ directory and generates companion .html files.
"""

from rdflib import Graph, Namespace, RDF, RDFS, OWL, SKOS
from rdflib.namespace import DCTERMS, XSD
from pathlib import Path
import sys
from datetime import datetime

# Namespaces
IROKO = Namespace("https://iroko-framework.github.io/iroko-framework/vocab/iroko-core#")
EWE = Namespace("https://iroko-framework.github.io/iroko-framework/vocab/iroko-ewe#")

def get_ontology_metadata(g):
    """Extract ontology-level metadata."""
    ontology_uri = None
    for s in g.subjects(RDF.type, OWL.Ontology):
        ontology_uri = s
        break
    
    if not ontology_uri:
        return None
    
    return {
        'uri': str(ontology_uri),
        'title': str(g.value(ontology_uri, DCTERMS.title) or "Vocabulary"),
        'description': str(g.value(ontology_uri, DCTERMS.description) or ""),
        'creator': str(g.value(ontology_uri, DCTERMS.creator) or ""),
        'created': str(g.value(ontology_uri, DCTERMS.created) or ""),
        'modified': str(g.value(ontology_uri, DCTERMS.modified) or ""),
        'version': str(g.value(ontology_uri, OWL.versionInfo) or ""),
        'license': str(g.value(ontology_uri, DCTERMS.license) or ""),
        'comment': str(g.value(ontology_uri, RDFS.comment) or "")
    }

def get_classes(g):
    """Extract all class definitions."""
    classes = []
    for cls in g.subjects(RDF.type, OWL.Class):
        cls_id = str(cls).split('#')[-1] if '#' in str(cls) else str(cls).split('/')[-1]
        
        # Get superclasses
        superclasses = []
        for super_cls in g.objects(cls, RDFS.subClassOf):
            superclasses.append(str(super_cls))
        
        classes.append({
            'uri': str(cls),
            'id': cls_id,
            'label': str(g.value(cls, RDFS.label) or cls_id),
            'comment': str(g.value(cls, RDFS.comment) or ""),
            'superclasses': superclasses,
            'defined_by': str(g.value(cls, RDFS.isDefinedBy) or "")
        })
    
    return sorted(classes, key=lambda x: x['label'])

def get_properties(g):
    """Extract all property definitions."""
    properties = []
    
    # Get both object and datatype properties
    prop_types = [OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty]
    
    for prop_type in prop_types:
        for prop in g.subjects(RDF.type, prop_type):
            prop_id = str(prop).split('#')[-1] if '#' in str(prop) else str(prop).split('/')[-1]
            
            prop_type_str = "Object Property"
            if prop_type == OWL.DatatypeProperty:
                prop_type_str = "Datatype Property"
            elif prop_type == OWL.AnnotationProperty:
                prop_type_str = "Annotation Property"
            
            # Get domain and range
            domain = str(g.value(prop, RDFS.domain) or "")
            range_val = str(g.value(prop, RDFS.range) or "")
            
            # Get minimum access level annotation
            min_access = str(g.value(prop, IROKO.minimumAccessLevel) or "")
            
            properties.append({
                'uri': str(prop),
                'id': prop_id,
                'label': str(g.value(prop, RDFS.label) or prop_id),
                'comment': str(g.value(prop, RDFS.comment) or ""),
                'type': prop_type_str,
                'domain': domain,
                'range': range_val,
                'min_access': min_access,
                'defined_by': str(g.value(prop, RDFS.isDefinedBy) or "")
            })
    
    return sorted(properties, key=lambda x: x['label'])

def get_concept_schemes(g):
    """Extract all concept schemes and their concepts."""
    schemes = []
    
    for scheme in g.subjects(RDF.type, SKOS.ConceptScheme):
        scheme_id = str(scheme).split('#')[-1] if '#' in str(scheme) else str(scheme).split('/')[-1]
        
        # Get all concepts in this scheme
        concepts = []
        for concept in g.subjects(SKOS.inScheme, scheme):
            concept_id = str(concept).split('#')[-1] if '#' in str(concept) else str(concept).split('/')[-1]
            
            # Get alternative labels
            alt_labels = [str(l) for l in g.objects(concept, SKOS.altLabel)]
            
            # Get notation (for access levels)
            notation = str(g.value(concept, SKOS.notation) or "")
            
            concepts.append({
                'uri': str(concept),
                'id': concept_id,
                'pref_label': str(g.value(concept, SKOS.prefLabel) or concept_id),
                'alt_labels': alt_labels,
                'definition': str(g.value(concept, SKOS.definition) or ""),
                'notation': notation
            })
        
        schemes.append({
            'uri': str(scheme),
            'id': scheme_id,
            'label': str(g.value(scheme, RDFS.label) or scheme_id),
            'description': str(g.value(scheme, DCTERMS.description) or ""),
            'concepts': sorted(concepts, key=lambda x: x['pref_label'])
        })
    
    return sorted(schemes, key=lambda x: x['label'])

def generate_html(ttl_file):
    """Generate HTML documentation from TTL file."""
    print(f"Processing {ttl_file}...")
    
    # Parse TTL
    g = Graph()
    try:
        g.parse(ttl_file, format='turtle')
    except Exception as e:
        print(f"ERROR parsing {ttl_file}: {e}")
        return False
    
    # Extract components
    metadata = get_ontology_metadata(g)
    if not metadata:
        print(f"WARNING: No ontology metadata found in {ttl_file}")
        metadata = {'title': 'Vocabulary', 'description': '', 'version': '', 'created': '', 'modified': ''}
    
    classes = get_classes(g)
    properties = get_properties(g)
    schemes = get_concept_schemes(g)
    
    # Generate HTML
    html_file = ttl_file.replace('.ttl', '.html')
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata['title']}</title>
    <link rel="stylesheet" href="../assets/vocab-style.css">
</head>
<body>
    <header>
        <h1>{metadata['title']}</h1>
        <p class="subtitle">{metadata['description']}</p>
    </header>
    
    <div class="metadata">
        <dl>
            <dt>Namespace URI:</dt>
            <dd><code>{metadata['uri']}</code></dd>
            
            <dt>Version:</dt>
            <dd>{metadata['version']}</dd>
            
            <dt>Date:</dt>
            <dd>{metadata['modified'] or metadata['created']}</dd>
            
            <dt>Creator:</dt>
            <dd>{metadata['creator']}</dd>
            
            <dt>License:</dt>
            <dd><a href="{metadata['license']}">{metadata['license'].split('/')[-2] if '/' in metadata['license'] else metadata['license']}</a></dd>
            
            <dt>Formats:</dt>
            <dd>
                <a href="{Path(ttl_file).name}">Turtle</a>
            </dd>
        </dl>
    </div>
""")
        
        # Table of Contents
        f.write("""
    <nav class="toc">
        <h2>Table of Contents</h2>
        <ul>
""")
        
        if classes:
            f.write("            <li><a href=\"#classes\">Classes</a>\n")
            f.write("                <ul>\n")
            for cls in classes:
                f.write(f"                    <li><a href=\"#{cls['id']}\">{cls['label']}</a></li>\n")
            f.write("                </ul>\n")
            f.write("            </li>\n")
        
        if properties:
            f.write("            <li><a href=\"#properties\">Properties</a>\n")
            f.write("                <ul>\n")
            for prop in properties:
                f.write(f"                    <li><a href=\"#{prop['id']}\">{prop['label']}</a></li>\n")
            f.write("                </ul>\n")
            f.write("            </li>\n")
        
        if schemes:
            f.write("            <li><a href=\"#concept-schemes\">Concept Schemes</a>\n")
            f.write("                <ul>\n")
            for scheme in schemes:
                f.write(f"                    <li><a href=\"#{scheme['id']}\">{scheme['label']}</a></li>\n")
            f.write("                </ul>\n")
            f.write("            </li>\n")
        
        f.write("""        </ul>
    </nav>
""")
        
        # Classes Section
        if classes:
            f.write("""
    <section id="classes">
        <h2>Classes</h2>
""")
            for cls in classes:
                f.write(f"""
        <div class="term" id="{cls['id']}">
            <h3>{cls['label']}</h3>
            <div class="term-uri">{cls['uri']}</div>
            <span class="term-type">CLASS</span>
            
            <div class="term-description">
                <p>{cls['comment']}</p>
            </div>
            
            <dl class="term-properties">
                <dt>Label:</dt>
                <dd>"{cls['label']}"@en</dd>
""")
                if cls['superclasses']:
                    f.write("                <dt>Subclass Of:</dt>\n")
                    for super_cls in cls['superclasses']:
                        super_label = super_cls.split('#')[-1] if '#' in super_cls else super_cls.split('/')[-1]
                        f.write(f"                <dd><code>{super_label}</code></dd>\n")
                
                f.write("""            </dl>
        </div>
""")
            f.write("    </section>\n")
        
        # Properties Section
        if properties:
            f.write("""
    <section id="properties">
        <h2>Properties</h2>
""")
            for prop in properties:
                f.write(f"""
        <div class="term" id="{prop['id']}">
            <h3>{prop['label']}</h3>
            <div class="term-uri">{prop['uri']}</div>
            <span class="term-type">{prop['type'].upper()}</span>
            
            <div class="term-description">
                <p>{prop['comment']}</p>
            </div>
            
            <dl class="term-properties">
                <dt>Label:</dt>
                <dd>"{prop['label']}"@en</dd>
                
                <dt>Type:</dt>
                <dd><code>{prop['type']}</code></dd>
""")
                if prop['domain']:
                    domain_label = prop['domain'].split('#')[-1] if '#' in prop['domain'] else prop['domain'].split('/')[-1]
                    f.write(f"""                <dt>Domain:</dt>
                <dd><code>{domain_label}</code></dd>
""")
                
                if prop['range']:
                    range_label = prop['range'].split('#')[-1] if '#' in prop['range'] else prop['range'].split('/')[-1]
                    f.write(f"""                <dt>Range:</dt>
                <dd><code>{range_label}</code></dd>
""")
                
                if prop['min_access']:
                    f.write(f"""                <dt>Minimum Access Level:</dt>
                <dd>{prop['min_access']}</dd>
""")
                
                f.write("""            </dl>
        </div>
""")
            f.write("    </section>\n")
        
        # Concept Schemes Section
        if schemes:
            f.write("""
    <section id="concept-schemes">
        <h2>Concept Schemes</h2>
""")
            for scheme in schemes:
                f.write(f"""
        <div class="term" id="{scheme['id']}">
            <h3>{scheme['label']}</h3>
            <div class="term-uri">{scheme['uri']}</div>
            
            <p>{scheme['description']}</p>
            
            <div class="concept-list">
""")
                for concept in scheme['concepts']:
                    f.write(f"""                <div class="concept-item">
                    <strong>{concept['pref_label']}</strong>
""")
                    if concept['notation']:
                        f.write(f"                    <small>Rank: {concept['notation']}</small><br>\n")
                    if concept['definition']:
                        f.write(f"                    <small>{concept['definition']}</small>\n")
                    if concept['alt_labels']:
                        f.write(f"                    <small>Also: {', '.join(concept['alt_labels'])}</small>\n")
                    f.write("                </div>\n")
                
                f.write("""            </div>
        </div>
""")
            f.write("    </section>\n")
        
        # Footer
        f.write(f"""
    <footer>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>
            <a href="https://iroko.org">Iroko Historical Society</a> | 
            <a href="https://github.com/iroko-framework/iroko-framework">GitHub</a>
        </p>
    </footer>
</body>
</html>
""")
    
    print(f"✓ Generated {html_file}")
    return True

def main():
    """Generate HTML for all TTL files in vocab/ directory."""
    vocab_dir = Path(__file__).parent.parent / 'vocab'
    
    if not vocab_dir.exists():
        print(f"ERROR: vocab/ directory not found at {vocab_dir}")
        sys.exit(1)
    
    ttl_files = list(vocab_dir.glob('*.ttl'))
    
    if not ttl_files:
        print("No .ttl files found in vocab/ directory")
        sys.exit(1)
    
    print(f"Found {len(ttl_files)} TTL files")
    
    success_count = 0
    for ttl_file in ttl_files:
        if generate_html(str(ttl_file)):
            success_count += 1
    
    print(f"\n✓ Successfully generated HTML for {success_count}/{len(ttl_files)} files")

if __name__ == '__main__':
    main()

---

## Updated Repository Structure
```
iroko-framework/
├── vocab/
│   ├── iroko-core.ttl          ← Machine-readable (updated - no instances)
│   ├── iroko-core.html         ← Human-readable (NEW)
│   ├── iroko-ewe.ttl           ← Machine-readable (updated - no instances)
│   └── iroko-ewe.html          ← Human-readable (NEW)
│
├── data/
│   ├── plants-public.ttl       ← Minimal public data (names only)
│   └── README.md
│
├── examples/
│   ├── plant-minimal.ttl       ← Example: public plant (fictional)
│   ├── plant-full.ttl          ← Example: full plant (fictional, for docs)
│   └── how-to-use.md
│
├── scripts/
│   ├── export_minimal_public_data.py
│   └── generate_vocab_html.py  ← NEW: Auto-generate HTML from TTL
│
└── README.md
