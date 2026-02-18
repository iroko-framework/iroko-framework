#!/bin/bash
# Validate all TTL files
rapper -i turtle -o ntriples vocab/iroko-core.ttl > /dev/null && echo "✓ iroko-core.ttl valid"
rapper -i turtle -o ntriples vocab/iroko-ewe.ttl > /dev/null && echo "✓ iroko-ewe.ttl valid"
