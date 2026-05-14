#!/bin/bash
# Block until training reaches step $1 OR has eval_loss OR inference completes.
TARGET_STEP=${1:-300}
LOG=/home3/indiamart/gemma_4/agent/training_v3.log
INFLOG=/home3/indiamart/gemma_4/agent/v2_clean.log
while true; do
    step=$(grep -oE '[0-9]+/939' "$LOG" 2>/dev/null | tail -1 | cut -d/ -f1)
    inf=$(grep -oE '\[[0-9]+/1000\]' "$INFLOG" 2>/dev/null | tail -1 | tr -d '[]' | cut -d/ -f1)
    [ -z "$step" ] && step=0
    [ -z "$inf" ] && inf=0
    if [ "$step" -ge "$TARGET_STEP" ]; then break; fi
    if grep -q eval_loss "$LOG" 2>/dev/null; then break; fi
    if [ "$inf" -ge 1000 ]; then break; fi
    if grep -q "^Done!" "$LOG" 2>/dev/null; then break; fi
    sleep 60
done
echo "=== INFER ==="
tail -4 "$INFLOG"
echo "=== TRAIN ==="
grep -E "loss|epoch|eval_loss" "$LOG" | tail -20
echo "=== STEP ==="
grep -oE '[0-9]+/939' "$LOG" | tail -1
