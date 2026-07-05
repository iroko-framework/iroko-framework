#!/usr/bin/env bash
#
# Retired legacy helper.
#
# This script used to call export_minimal_public_data.py and commit data/*.ttl,
# but those files are no longer part of this repository's active workflow.

set -euo pipefail

cat <<'MSG'
nightly_export.sh is retired.

Use the active ontology site workflow instead:
  python scripts/build_all.py
  python scripts/check_site.py

For publishing, run:
  bash scripts/deploy.sh
MSG

exit 1
