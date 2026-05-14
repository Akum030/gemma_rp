#!/bin/bash
PID=$1
CSV=${2:-/home3/indiamart/gemma_4/agent/v3_smoke.csv}
LOG=${3:-/home3/indiamart/gemma_4/agent/v3_smoke.log}
for i in 1 2 3 4 5 6; do
    if [ -f "$CSV" ]; then
        n=$(wc -l "$CSV" | awk '{print $1}')
        if [ "$n" -ge 11 ]; then echo SMOKE_DONE; break; fi
    fi
    if ! ps -p $PID > /dev/null 2>&1; then echo PROC_GONE; break; fi
    sleep 60
done
echo "--LOG--"
tail -25 "$LOG"
echo "--CSV--"
cat "$CSV" 2>/dev/null
