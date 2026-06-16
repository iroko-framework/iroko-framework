#!/bin/bash
# Run nightly to export public data to vocabulary repo

# Export minimal public data
python3 scripts/export_minimal_public_data.py

# Navigate to vocabulary repo
cd ../iroko-framework

# Commit and push
git add data/plants-public.ttl
git commit -m "Update public plant data - $(date +%Y-%m-%d)"
git push origin main

echo "✓ Public data exported and pushed to GitHub Pages"
```

---

## HTML Structure (Planned, Not Implemented Yet)

Each vocabulary file gets a companion HTML file:
```
vocab/iroko-core.ttl     →  vocab/iroko-core.html
vocab/iroko-ewe.ttl      →  vocab/iroko-ewe.html
