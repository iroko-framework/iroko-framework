# Contributing to Iroko Framework

Thank you for your interest in contributing to the Iroko Framework vocabularies!

## Development Setup

### Prerequisites

- **Python 3.8+** (for HTML generation)
- **Rapper** (for TTL validation)
- **Git**

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/iroko-framework/iroko-framework.git
cd iroko-framework
```

#### 2. Install Dependencies

**Python dependencies:**
```bash
pip install -r requirements.txt
```

**Rapper (RDF validator):**

Ubuntu/Debian:
```bash
sudo apt-get install raptor2-utils
```

macOS:
```bash
brew install raptor
```

#### 3. Make Scripts Executable
```bash
chmod +x scripts/*.sh
chmod +x scripts/*.py
```

#### 4. Verify Installation
```bash
# Validate vocabularies
bash scripts/validate_ttl.sh

# Generate HTML documentation
python scripts/build_all.py

# Check generated pages, links, JavaScript, RDF, sitemap, and robots policy
python scripts/check_site.py
```

You should see:
```
SITE CHECK PASSED
```

## Workflow

### 1. Edit Vocabulary Files

Edit TTL files in `vocab/` directory:
- `vocab/iroko-core.ttl` - Core vocabulary
- `vocab/iroko-ewe.ttl` - Ewé module

### 2. Validate Changes
```bash
bash scripts/validate_ttl.sh
```

Fix any syntax errors before proceeding.

### 3. Generate HTML Documentation
```bash
python scripts/build_all.py
python scripts/check_site.py
```

This auto-generates:
- module browse pages in `vocab/`
- the full term list
- RDF serializations
- stable URI alias pages
- `sitemap.xml`

### 4. Review Changes
```bash
git status
git diff vocab/
```

### 5. Deploy

**Option A: Automated deployment script**
```bash
bash scripts/deploy.sh
```

This will:
1. Validate TTL files
2. Run the full build
3. Run the generated site checks
4. Ask before committing
5. Ask before pushing to GitHub

**Option B: Manual deployment**
```bash
python scripts/build_all.py
python scripts/check_site.py
git status --short
git add -A
git commit -m "Update vocabulary: [describe changes]"
git push origin main
```

Changes will be live at https://ontology.irokosociety.org/ within a few minutes.

## Adding New Terms

### Adding a Class
```turtle
iroko:NewClass
    a owl:Class ;
    rdfs:subClassOf iroko:SacredEntity ;
    rdfs:label "New Class"@en ;
    rdfs:comment "Description of the new class."@en ;
    rdfs:isDefinedBy <https://ontology.irokosociety.org/iroko-ewe> .
```

### Adding a Property
```turtle
iroko:newProperty
    a owl:ObjectProperty ;
    rdfs:label "new property"@en ;
    rdfs:comment "Description of the property."@en ;
    rdfs:domain iroko:Plant ;
    rdfs:range skos:Concept ;
    iroko:minimumAccessLevel iroko:access-community-only ;
    rdfs:isDefinedBy <https://ontology.irokosociety.org/iroko-ewe> .
```

### Adding a Concept
```turtle
iroko:ritual-new-use
    a skos:Concept ;
    skos:inScheme iroko:RitualUseScheme ;
    skos:prefLabel "New Ritual Use"@en ;
    skos:definition "Description of this ritual use."@en .
```

## Code Style

### Turtle Formatting

- **Indent with 4 spaces** (not tabs)
- **Use blank lines** to separate major sections
- **Comment sections** with `# ===== SECTION NAME =====`
- **Alphabetize concepts** within schemes

### Namespace Prefixes

Always declare at top of file:
```turtle
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix iroko: <https://ontology.irokosociety.org/iroko#> .
```

## Testing

### Validate RDF Syntax
```bash
bash scripts/validate_ttl.sh
```

### Test HTML Generation
```bash
python scripts/build_all.py
```

Then open `vocab/iroko-core.html` in a browser.

### Check Links

All internal links in HTML should work:
- Table of contents anchors
- Cross-references between terms

## Versioning

We use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes (incompatible with previous version)
- **MINOR:** New terms added (backward compatible)
- **PATCH:** Bug fixes, documentation improvements

Update `owl:versionInfo` in the ontology declaration:
```turtle
<https://ontology.irokosociety.org/iroko-core>
    a owl:Ontology ;
    owl:versionInfo "1.1.0" ;  # Update this
    dcterms:modified "2026-02-18"^^xsd:date ;  # Update this
```

## Pull Request Guidelines

1. **Create a branch** for your changes
2. **Write clear commit messages**
3. **Validate before submitting** (`bash scripts/validate_ttl.sh`)
4. **Update version info** if adding new terms
5. **Describe changes** in PR description

## Questions?

- **Issues:** [GitHub Issues](https://github.com/iroko-framework/iroko-framework/issues)
- **Email:** info@iroko.org

## License

By contributing, you agree to release your contributions under CC0 1.0 Universal (Public Domain).
