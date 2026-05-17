#!/usr/bin/env bash
# Usage: ./ralph.sh [iterations]
# Default: runs until <REDAGENT_COMPLETE> is output or no open issues remain (max 50 iterations)

ITERATIONS=${1:-50}

for ((i=1; i<=ITERATIONS; i++)); do
  echo "=== Ralph iteration $i / $ITERATIONS ==="

  OUTPUT=$(claude --print "$(cat PROMPT.md)")
  echo "$OUTPUT"

  if echo "$OUTPUT" | grep -q "REDAGENT_COMPLETE"; then
    echo "=== Pipeline complete. Exiting. ==="
    exit 0
  fi

  if echo "$OUTPUT" | grep -q "NO_ISSUES_REMAINING"; then
    echo "=== No open issues remain. Exiting. ==="
    exit 0
  fi
done

echo "=== Reached iteration cap ($ITERATIONS). Review progress and re-run if needed. ==="
