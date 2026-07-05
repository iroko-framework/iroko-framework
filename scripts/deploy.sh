#!/usr/bin/env bash
#
# Canonical publish helper for the Iroko ontology site.
# Runs validation, the full static build, and site QA before offering to commit/push.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -n "${PYTHON:-}" ] && command -v "$PYTHON" >/dev/null 2>&1; then
    PYTHON_BIN="$PYTHON"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "ERROR: Python was not found. Install Python, then run: pip install -r requirements.txt"
    exit 1
fi

cd "$PROJECT_ROOT"

echo "Iroko Framework deployment"
echo "=========================="
echo "Python: $PYTHON_BIN"
echo

echo "Step 1: Validating Turtle files"
bash "$SCRIPT_DIR/validate_ttl.sh"
echo

echo "Step 2: Running full site build"
"$PYTHON_BIN" "$SCRIPT_DIR/build_all.py"
echo

echo "Step 3: Running generated site checks"
"$PYTHON_BIN" "$SCRIPT_DIR/check_site.py"
echo

echo "Step 4: Reviewing changed files"
if [ -z "$(git status --porcelain)" ]; then
    echo "No changes to deploy."
    exit 0
fi

git status --short
echo

read -r -p "Commit all listed changes? [y/N] " commit_confirm
case "$commit_confirm" in
    y|Y|yes|YES)
        ;;
    *)
        echo "Build and checks passed. No commit made."
        exit 0
        ;;
esac

default_msg="Update ontology site - $(date +%Y-%m-%d)"
read -r -p "Commit message [$default_msg]: " commit_msg
commit_msg="${commit_msg:-$default_msg}"

git add -A
git commit -m "$commit_msg"
echo

read -r -p "Push to origin/main? [y/N] " push_confirm
case "$push_confirm" in
    y|Y|yes|YES)
        git push origin main
        echo
        echo "Deployed. GitHub Pages will update https://ontology.irokosociety.org/ shortly."
        ;;
    *)
        echo "Commit created locally. Push later with: git push origin main"
        ;;
esac
