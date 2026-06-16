# Using the Iroko Framework Vocabulary

The Iroko Framework vocabulary is designed for **reuse** by other projects documenting Afro-Atlantic sacred knowledge.

## Our Approach (Conservative)

Iroko Historical Society publishes:
- ✅ **Full vocabulary** (all classes, properties, concepts)
- ✅ **Minimal public data** (scientific names, vernacular names only)
- ❌ **Detailed knowledge** (kept private, accessed via authenticated API)

## Your Approach (Your Choice)

You can use the Iroko vocabulary with different access policies:

### Option 1: More Liberal (University Archive)
```turtle
# Example: University digitizing published ethnographies
<http://university.edu/plants/basil-001>
    a ewe:Plant ;
    dwc:scientificName "Ocimum basilicum" ;
    ewe:ritualUse ewe:ritual/purification ;  ← YOU publish this
    ewe:medicinalUse ewe:medicinal/digestive-support ;  ← We keep private
    dcterms:source <http://university.edu/sources/cabrera-1954> .
```

**Rationale:** Published ethnographies are already public. University making them findable.

---

### Option 2: More Conservative (Temple Archive)
```turtle
# Example: Temple documenting internal lineage knowledge
<http://temple.org/plants/secret-leaf-001>
    a ewe:Plant ;
    # Only publish existence, NO details
    iroko:accessLevel iroko:access/no-access ;
    rdfs:comment "Detailed information restricted to initiated members only." .
```

**Rationale:** Active practice, living tradition, maximum protection.

---

### Option 3: Hybrid (Museum Collection)
```turtle
# Example: Museum with both public and restricted items
<http://museum.org/plants/exhibit-001>
    a ewe:Plant ;
    dwc:scientificName "Newbouldia laevis" ;
    ewe:ritualUse ewe:ritual/purification ;  ← From published sources
    iroko:custodialRelationship iroko:custodial/community-held ;
    dcterms:provenance "Donated by Ilé Obatalá with access conditions" ;
    # Detailed preparation methods: private, per donor agreement
    rdfs:seeAlso <http://museum.org/access-request> .
```

**Rationale:** Respect donor wishes, show what you can, protect what you must.

---

## Benefits of Shared Vocabulary

### 1. Semantic Interoperability
Different archives can link to same concepts:
```turtle
# IHS says:
<https://iroko.org/plants/akoko-001> ewe:ritualUse ewe:ritual/purification .

# University says:
<http://university.edu/plants/akoko-002> ewe:ritualUse ewe:ritual/purification .

# Same concept URI: ewe:ritual/purification
# Now machines can find all plants for purification across archives
```

### 2. Respect Different Access Policies
```turtle
# IHS: keeps private
<https://iroko.org/plants/akoko-001>
    ewe:ritualUse ewe:ritual/purification ;
    # preparation method: not published

# University: publishes from Verger book (already public)
<http://university.edu/plants/akoko-002>
    ewe:ritualUse ewe:ritual/purification ;
    ewe:preparationMethod ewe:preparation/bath ;  ← They publish this
    dcterms:source <http://worldcat.org/verger-1995> .

# Both valid uses of same vocabulary
```

### 3. Community Choice
Each community decides:
- What to publish publicly
- What to keep private
- What requires authentication
- What requires initiation

**The vocabulary supports all these choices.**

---

## How to Adopt

### Step 1: Import Vocabulary
```turtle
@prefix ewe: <https://iroko-framework.github.io/iroko-framework/vocab/iroko-ewe#> .
@prefix iroko: <https://iroko-framework.github.io/iroko-framework/vocab/iroko-core#> .
```

### Step 2: Classify Your Data
```turtle
<http://your-archive.org/plants/001>
    a ewe:Plant ;
    # Use properties from vocab
    ewe:ritualUse ewe:ritual/purification ;
    # Use access levels from vocab
    iroko:accessLevel iroko:access/community-only .
```

### Step 3: Make Your Access Decisions
- Publish what your community approves
- Keep private what your community requests
- Use access level vocabulary to document policies

---

## Questions?

- Technical: https://github.com/iroko-framework/iroko-framework/issues
- Community: info@iroko.org
