# Iroko Framework

> **🌐 Visit the full site:** [https://iroko-framework.github.io/iroko-framework/](https://iroko-framework.github.io/iroko-framework/)


**Semantic vocabulary for governing access to Afro-Atlantic sacred knowledge systems**

The Iroko Framework provides controlled vocabularies and access governance mechanisms for documenting sacred plant knowledge, spiritual entities, ritual processes, and archival materials in Afro-Atlantic traditions.

## Vocabulary Modules

- **[Core Vocabulary](vocab/iroko-core.html)** - Cross-module infrastructure (access control, provenance, contested knowledge)
- **[Ewé Module](vocab/iroko-ewe.html)** - Sacred plant knowledge with field-level access governance

## Quick Links

- **Browse Vocabularies:** [https://iroko-framework.github.io/iroko-framework/](https://iroko-framework.github.io/iroko-framework/)
- **Download RDF:**
  - [iroko-core.ttl](vocab/iroko-core.ttl)
  - [iroko-ewe.ttl](vocab/iroko-ewe.ttl)
- **Public Data:** [plants-public.ttl](data/plants-public.ttl) (scientific names only)
- **Documentation:** [docs/](docs/)

## Using This Vocabulary
```turtle
@prefix ewe: <https://iroko-framework.github.io/iroko-framework/vocab/iroko-ewe#> .
@prefix iroko: <https://iroko-framework.github.io/iroko-framework/vocab/iroko-core#> .
@prefix dwc: <http://rs.tdwg.org/dwc/terms/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

<http://your-archive.org/plants/001>
    a ewe:Plant ;
    dwc:scientificName "Newbouldia laevis" ;
    skos:prefLabel "Akoko"@yo ;
    ewe:ritualUse ewe:ritual/purification ;
    iroko:accessLevel iroko:access/public-unrestricted .
```

See [docs/REUSE.md](docs/REUSE.md) for detailed examples.

## Access Philosophy

Other institutions can use the Iroko vocabulary with their own access policies:

- **Universities** may publish more data (from published ethnographies)
- **Temple archives** may publish less (active sacred practice)
- **Museums** may mix (public exhibits + restricted donations)

**Iroko Historical Society publishes:**
- ✅ Full vocabulary (all classes, properties, concepts)
- ✅ Minimal public data (scientific names, vernacular names only)
- ❌ Sacred knowledge details (kept private, API-accessed at [irokosociety.org](https://irokosociety.org))

## For Developers

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for:
- Setting up development environment
- Validating vocabularies
- Generating HTML documentation
- Deployment process

## Project Structure
```
iroko-framework/
├── vocab/           # Vocabulary definitions (TTL + HTML)
├── data/            # Minimal public data instances
├── examples/        # Usage examples
├── scripts/         # Build and validation scripts
├── docs/            # Documentation
└── assets/          # Shared CSS and images
```

## License

Vocabularies and public data released under [CC0 1.0 Universal (Public Domain)](LICENSE).

## Citation
```
Iroko Historical Society. (2026). Iroko Framework: Vocabularies for 
Afro-Atlantic Sacred Knowledge Systems. 
https://iroko-framework.github.io/iroko-framework/
```

## Contact

- **Website:** [irokosociety.org](https://irokosociety.org)
- **GitHub:** [github.com/iroko-framework](https://github.com/iroko-framework)
- **Email:** irokosociety@gmail.com

---

*Developed by [Iroko Historical Society](https://irokosociety.org)*
