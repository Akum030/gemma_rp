#!/bin/bash
TARGET=${1:-/home3/indiamart/gemma_4/agent/v3b_smoke.csv}
LOG=${2:-/home3/indiamart/gemma_4/agent/v3b_smoke.log}
NEED=${3:-11}
MAX=${4:-30}
for i in $(seq 1 $MAX); do
  sleep 10
  n=$(wc -l < "$TARGET" 2>/dev/null || echo 0)
  s=$(wc -c < "$LOG" 2>/dev/null || echo 0)
  echo "t=${i}0s csv=$n log_bytes=$s"
  if [ "$n" -ge "$NEED" ]; then break; fi
done
echo "--LOG--"
tail -80 "$LOG"
echo "--CSV--"
cat "$TARGET" 2>/dev/null
