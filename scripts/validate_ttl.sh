#!/bin/bash
#
# Validate all Turtle files in vocab/ directory
# Requires: rapper (part of raptor2-utils package)
#
# Install:
#   Ubuntu/Debian: sudo apt-get install raptor2-utils
#   macOS: brew install raptor

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VOCAB_DIR="$SCRIPT_DIR/../vocab"

echo "Validating Turtle files in $VOCAB_DIR"
echo "========================================"

# Check if rapper is installed
if ! command -v rapper &> /dev/null; then
    echo "ERROR: rapper not found. Please install raptor2-utils:"
    echo "  Ubuntu/Debian: sudo apt-get install raptor2-utils"
    echo "  macOS: brew install raptor"
    exit 1
fi

# Validate each TTL file
errors=0
for ttl_file in "$VOCAB_DIR"/*.ttl; do
    if [ -f "$ttl_file" ]; then
        filename=$(basename "$ttl_file")
        echo -n "Validating $filename... "
        
        if rapper -i turtle -o ntriples "$ttl_file" > /dev/null 2>&1; then
            echo "✓ VALID"
        else
            echo "✗ INVALID"
            echo "  Errors:"
            rapper -i turtle -o ntriples "$ttl_file" 2>&1 | grep -E "rapper: (Error|Warning)" | sed 's/^/    /'
            ((errors++))
        fi
    fi
done

echo "========================================"

if [ $errors -eq 0 ]; then
    echo "✓ All Turtle files are valid"
    exit 0
else
    echo "✗ $errors file(s) have validation errors"
    exit 1
fi
