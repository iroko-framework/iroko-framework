# scripts/generate_vocab_html.py
"""
Generate human-readable HTML from Turtle vocabulary files.
Run after updating .ttl files to keep HTML in sync.
"""

from rdflib import Graph, Namespace, RDF, RDFS, OWL, SKOS
from rdflib.namespace import DCTERMS
import sys

IROKO = Namespace("https://iroko-framework.github.io/iroko-framework/vocab/iroko-core#")

def generate_html_from_ttl(ttl_file, output_html):
    g = Graph()
    g.parse(ttl_file, format='turtle')
    
    # Extract ontology metadata
    ontology_uri = None
    for s in g.subjects(RDF.type, OWL.Ontology):
        ontology_uri = s
        break
    
    title = str(g.value(ontology_uri, DCTERMS.title) or "Vocabulary")
    description = str(g.value(ontology_uri, DCTERMS.description) or "")
    
    # Extract all classes
    classes = []
    for cls in g.subjects(RDF.type, OWL.Class):
        label = str(g.value(cls, RDFS.label) or cls)
        comment = str(g.value(cls, RDFS.comment) or "")
        classes.append({
            'uri': str(cls),
            'id': str(cls).split('#')[-1],
            'label': label,
            'comment': comment
        })
    
    # Extract all properties
    properties = []
    for prop in set(g.subjects(RDF.type, OWL.ObjectProperty)) | set(g.subjects(RDF.type, OWL.DatatypeProperty)):
        label = str(g.value(prop, RDFS.label) or prop)
        comment = str(g.value(prop, RDFS.comment) or "")
        properties.append({
            'uri': str(prop),
            'id': str(prop).split('#')[-1],
            'label': label,
            'comment': comment
        })
    
    # Generate HTML (template above)
    # ... implementation details
    
    print(f"Generated {output_html}")

if __name__ == '__main__':
    generate_html_from_ttl('vocab/iroko-core.ttl', 'vocab/iroko-core.html')
    generate_html_from_ttl('vocab/iroko-ewe.ttl', 'vocab/iroko-ewe.html')
```

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
