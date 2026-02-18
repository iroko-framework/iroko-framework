# Iroko Framework Architecture

## Overview

The Iroko Framework consists of three separate but interconnected components:
```
┌─────────────────────────────────────────────────────────┐
│  iroko-framework (GitHub Pages)                         │
│  - Vocabulary definitions (TTL)                         │
│  - HTML documentation                                   │
│  - Minimal public data                                  │
│  https://iroko-framework.github.io/iroko-framework/     │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │ (nightly export)
                          │
┌─────────────────────────────────────────────────────────┐
│  iroko-archive (Private operational archive)            │
│  - PostgreSQL database with field-level access          │
│  - Next.js API with NextAuth                            │
│  - Web interface at https://iroko.org                   │
└─────────────────────────────────────────────────────────┘
```

## Vocabulary Repository (iroko-framework)

### Purpose

Publish the **vocabulary definitions** (ontology) and **minimal public data**.

### What's Published

**Vocabulary (Always Public):**
- Class definitions (`ewe:Plant`, `iroko:SacredEntity`)
- Property definitions (`ewe:ritualUse`, `iroko:accessLevel`)
- Concept schemes (traditions, access levels, ritual uses)

**Data (Conservative):**
- Scientific names only
- Vernacular names only
- NO ritual uses, NO preparation methods

### Repository Structure
```
iroko-framework/
├── vocab/                      # Vocabulary definitions
│   ├── iroko-core.ttl          # Core vocabulary (definitions)
│   ├── iroko-core.html         # Human-readable docs
│   ├── iroko-ewe.ttl           # Ewé module (definitions)
│   └── iroko-ewe.html          # Human-readable docs
│
├── data/                       # Public data instances
│   ├── plants-public.ttl       # Minimal plant data (names only)
│   └── README.md
│
├── examples/                   # Usage examples
│   ├── plant-minimal.ttl       # Example: public plant
│   └── plant-full.ttl          # Example: full plant (fictional)
│
├── scripts/                    # Build scripts
│   ├── generate_vocab_html.py  # TTL → HTML
│   ├── validate_ttl.sh         # Validate syntax
│   └── deploy.sh               # Full deployment
│
├── docs/                       # Documentation
│   ├── CONTRIBUTING.md         # Development setup
│   ├── REUSE.md                # How to use vocabulary
│   └── ARCHITECTURE.md         # This file
│
├── assets/
│   └── vocab-style.css         # Shared stylesheet
│
└── README.md
```

### Deployment

**GitHub Pages serves:**
- `https://iroko-framework.github.io/iroko-framework/vocab/iroko-core.ttl`
- `https://iroko-framework.github.io/iroko-framework/vocab/iroko-core.html`
- `https://iroko-framework.github.io/iroko-framework/data/plants-public.ttl`

## Operational Archive (iroko-archive)

### Purpose

Operational database with **full data** and **field-level access control**.

### Architecture

**Database: PostgreSQL on Railway**
```sql
archive.plants (base record)
archive.plant_details (field-level details with access levels)
```

**Backend: Next.js + NextAuth**
- API routes: `/api/plants/{id}`
- Access filtering based on user session
- Field-level permissions

**Frontend: React/Next.js**
- Web interface at https://iroko.org
- Tiered detail display based on user access
- Authentication required for community+ access

### Data Flow
```
User Request
    ↓
NextAuth Session Check
    ↓
API: /api/plants/akoko-001
    ↓
Database Query (with access filter)
    ↓
Return ONLY fields user can access
    ↓
Frontend displays tiered data
```

### Nightly Export

**Cron job at 2 AM:**
```bash
0 2 * * * /path/to/nightly_export.sh
```

**Workflow:**
1. Query database for `record_access_level = 'public-unrestricted'`
2. Export ONLY scientific names + vernacular names
3. Generate `plants-public.ttl`
4. Copy to `../iroko-framework/data/`
5. Commit and push to GitHub
6. GitHub Pages updates automatically

## Access Control Matrix

| Data Type | Public TTL | Database | API Response (Public) | API Response (Initiated) |
|-----------|-----------|----------|----------------------|-------------------------|
| Scientific name | ✅ | ✅ | ✅ | ✅ |
| Vernacular names | ✅ | ✅ | ✅ | ✅ |
| Ritual uses | ❌ | ✅ | ❌ | ✅ |
| Harvest protocols | ❌ | ✅ | ❌ | ✅ |
| Preparation methods | ❌ | ✅ | ❌ | ✅ |
| Invocation texts | ❌ | ✅ | ❌ | ❌ |

## Technology Stack

### Vocabulary Repository
- **Static Site:** GitHub Pages
- **Validation:** Rapper (raptor2-utils)
- **HTML Generation:** Python + rdflib
- **CI/CD:** GitHub Actions

### Operational Archive
- **Database:** PostgreSQL 15+ (Railway, $15/month)
- **Auth:** NextAuth.js (self-hosted)
- **Backend:** Next.js API Routes
- **Frontend:** React/Next.js + Tailwind
- **Hosting:** Vercel (free tier)
- **Media:** Backblaze B2 ($0.60/month)

**Total cost:** ~$16/month

## URI Strategy

### Vocabulary URIs (Permanent)
```
https://iroko-framework.github.io/iroko-framework/vocab/iroko-core#Plant
https://iroko-framework.github.io/iroko-framework/vocab/iroko-ewe#ritualUse
```

**Never change these.** Cool URIs don't change.

### Data Instance URIs
```
https://iroko.org/plants/akoko-001
```

Points to web interface with authentication.

### Public RDF Export
```
https://iroko-framework.github.io/iroko-framework/data/plants-public.ttl
```

Contains minimal public data only.

## Development Workflow

### Update Vocabulary

1. Edit `vocab/iroko-ewe.ttl`
2. Run `bash scripts/validate_ttl.sh`
3. Run `python3 scripts/generate_vocab_html.py`
4. Run `bash scripts/deploy.sh`
5. Changes live in ~2 minutes

### Update Public Data

1. Add plants to operational database
2. Set `record_access_level = 'public-unrestricted'`
3. Wait for nightly cron (or run manually)
4. Data exported to vocabulary repo automatically

## Future Modules

Planned vocabulary modules:
- **iroko-nkisi.ttl** - Spiritual entities (òrìṣà, lwa, mpungu)
- **iroko-travay.ttl** - Ritual processes
- **iroko-marca.ttl** - Divination systems
- **iroko-house.ttl** - Houses and lineages
- **iroko-sankofa.ttl** - Reclaimed/reconstructed practices

Same pattern: vocabulary public, data access-controlled.

## Questions?

See [CONTRIBUTING.md](CONTRIBUTING.md) or contact info@iroko.org
