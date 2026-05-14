#!/bin/bash
# Block until training reaches step $1, ignoring already-existing eval_loss.
TARGET_STEP=${1:-300}
LOG=/home3/indiamart/gemma_4/agent/training_v3.log
INFLOG=/home3/indiamart/gemma_4/agent/v2_clean.log
while true; do
    step=$(grep -oE '[0-9]+/939' "$LOG" 2>/dev/null | tail -1 | cut -d/ -f1)
    [ -z "$step" ] && step=0
    if [ "$step" -ge "$TARGET_STEP" ]; then break; fi
    if grep -q "^Done!" "$LOG" 2>/dev/null; then break; fi
    sleep 90
done
echo "=== INFER ==="
tail -5 "$INFLOG"
echo "=== TRAIN ==="
grep -E "loss|epoch|eval_loss" "$LOG" | tail -25
echo "=== STEP ==="
grep -oE '[0-9]+/939' "$LOG" | tail -1
