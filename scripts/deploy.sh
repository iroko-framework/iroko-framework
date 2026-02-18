#!/bin/bash
#
# Deploy vocabulary updates to GitHub Pages
# Validates TTL files, generates HTML, commits, and pushes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."

cd "$PROJECT_ROOT"

echo "Iroko Framework Deployment"
echo "=========================="
echo

# Step 1: Validate TTL files
echo "Step 1: Validating TTL files..."
if ! bash "$SCRIPT_DIR/validate_ttl.sh"; then
    echo "ERROR: TTL validation failed. Fix errors before deploying."
    exit 1
fi
echo

# Step 2: Generate HTML documentation
echo "Step 2: Generating HTML documentation..."
if ! python3 "$SCRIPT_DIR/generate_vocab_html.py"; then
    echo "ERROR: HTML generation failed."
    exit 1
fi
echo

# Step 3: Check for changes
echo "Step 3: Checking for changes..."
if git diff --quiet && git diff --cached --quiet; then
    echo "No changes to deploy."
    exit 0
fi

git status --short
echo

# Step 4: Commit changes
echo "Step 4: Committing changes..."
read -p "Enter commit message (or press Enter for default): " commit_msg

if [ -z "$commit_msg" ]; then
    commit_msg="Update vocabulary - $(date +%Y-%m-%d)"
fi

git add vocab/*.ttl vocab/*.html data/*.ttl
git commit -m "$commit_msg"
echo

# Step 5: Push to GitHub
echo "Step 5: Pushing to GitHub..."
read -p "Push to origin/main? (y/n): " confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    git push origin main
    echo
    echo "✓ Deployed successfully!"
    echo "Changes will be live at https://iroko-framework.github.io/iroko-framework/"
else
    echo "Deployment cancelled. Changes committed locally but not pushed."
fi
