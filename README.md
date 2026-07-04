# Iroko Framework

> **Visit the full site:** [https://ontology.irokosociety.org/](https://ontology.irokosociety.org/)

Semantic vocabularies and access-governance mechanisms for documenting sacred knowledge in Afro-Atlantic traditions.

The Iroko Framework publishes RDF/OWL vocabularies for sacred plant knowledge, spiritual entities, ritual processes, lineages, authority, disclosure constraints, narrative transmission, and related archival description. The framework separates open vocabulary publication from protected community knowledge: the vocabulary is public, while sensitive data remains governed by the communities and systems that steward it.

## Canonical Namespace

All Iroko classes, properties, and SKOS concepts use one shared hash namespace:

```text
https://ontology.irokosociety.org/iroko#
```

Example term IRI:

```text
https://ontology.irokosociety.org/iroko#SacredEntity
```

The namespace document is published at [https://ontology.irokosociety.org/iroko](https://ontology.irokosociety.org/iroko).

## Quick Links

- **Browse vocabularies:** [https://ontology.irokosociety.org/vocab/](https://ontology.irokosociety.org/vocab/)
- **Full term index:** [vocab/iroko-termlist.html](vocab/iroko-termlist.html)
- **Technical architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Reuse guide:** [docs/REUSE.md](docs/REUSE.md)
- **Contributing guide:** [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)

## Download RDF

Each module is published as Turtle, JSON-LD, RDF/XML, and N-Triples.

- [iroko-core.ttl](vocab/iroko-core.ttl)
- [iroko-ewe.ttl](vocab/iroko-ewe.ttl)
- [iroko-nkisi.ttl](vocab/iroko-nkisi.ttl)
- [iroko-travay.ttl](vocab/iroko-travay.ttl)

## Using This Vocabulary

```turtle
@prefix iroko: <https://ontology.irokosociety.org/iroko#> .
@prefix dwc:   <http://rs.tdwg.org/dwc/terms/> .
@prefix skos:  <http://www.w3.org/2004/02/skos/core#> .

<http://your-archive.org/plants/001>
    a iroko:Plant ;
    dwc:scientificName "Newbouldia laevis" ;
    skos:prefLabel "Akoko"@yo ;
    iroko:ritualUse iroko:ritual-purification ;
    iroko:accessLevel iroko:access-public-unrestricted .
```

## Development

Install the root dependencies once:

```bash
pip install -r requirements.txt
```

Run the full static build:

```bash
python scripts/build_all.py
```

Launch the local ontology manager:

```bash
python scripts/manage/app.py
```

## Project Structure

```text
iroko-framework/
├── vocab/           # Turtle source vocabularies and generated RDF/HTML outputs
├── docs/            # Markdown documentation and generated HTML docs
├── whitepaper/      # Whitepaper source/export
├── scripts/         # Build, validation, conversion, and manager tools
├── assets/          # Shared CSS, images, and generated social cards
└── fonts-onto/      # Local font assets
```

## License

Vocabularies are released under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

## Citation

```text
Iroko Historical Society. (2026). Iroko Framework: Semantic Vocabularies
for Afro-Atlantic Sacred Knowledge Systems.
https://ontology.irokosociety.org/
```

## Contact

- **Website:** [irokosociety.org](https://irokosociety.org)
- **Ontology site:** [ontology.irokosociety.org](https://ontology.irokosociety.org)
- **Email:** irokosociety@gmail.com
