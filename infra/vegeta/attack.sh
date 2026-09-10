#!/usr/bin/env bash
# Ataque de ejemplo: 5 req/s durante 30s contra el orquestador, con reporte.
set -e
RATE="${1:-5}"
DURATION="${2:-30s}"
echo "Atacando a $RATE req/s durante $DURATION..."
vegeta attack -targets=targets.txt -rate="$RATE" -duration="$DURATION" | vegeta report
