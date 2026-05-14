#!/bin/bash
set -euo pipefail

HOST="${OLLAMA_HOST_URL:-http://localhost:3389}"
MODEL="${OLLAMA_MODEL:-gemma4:e4b}"

curl -s "${HOST}/api/generate" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"${MODEL}\",\"prompt\":\"Reply with just: OK\",\"stream\":false}" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print(r.get('response') or r.get('error') or r)"
