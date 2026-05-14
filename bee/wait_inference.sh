#!/bin/bash
# wait for v3 inference to complete (up to 60 min)
LOG=/home3/indiamart/gemma_4/agent/v3_inference.log
CSV=/home3/indiamart/gemma_4/agent/v3_results.csv
for i in $(seq 1 60); do
    n=$(wc -l "$CSV" 2>/dev/null | awk '{print $1}')
    [ -z "$n" ] && n=0
    if [ "$n" -ge 1001 ]; then echo INFER_DONE; break; fi
    if grep -q "DONE  ok" "$LOG" 2>/dev/null; then echo INFER_DONE_LOG; break; fi
    sleep 60
done
echo "---STATUS---"
tail -8 "$LOG"
echo
wc -l "$CSV"
