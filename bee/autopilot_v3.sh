#!/bin/bash
# Auto-pilot: waits for v3 training to finish, then runs v3 inference, then exits.
# Designed to be launched once and left running with nohup.
set -e
LOG=/home3/indiamart/gemma_4/agent/training_v3.log
MERGED=/home3/indiamart/gemma_4/models/gemma4-v3-merged
ADAPTER=/home3/indiamart/gemma_4/models/gemma4-v3
OUT_CSV=/home3/indiamart/gemma_4/agent/v3_results.csv
OUT_JSONL=/home3/indiamart/gemma_4/agent/v3_results.jsonl

echo "[$(date)] auto-pilot waiting for training to finish ..."
# Wait until merged model exists OR adapter exists with 'Done!' line in log
while true; do
    if grep -q "^Done!" "$LOG" 2>/dev/null; then
        echo "[$(date)] training done"
        break
    fi
    sleep 60
done

# Pick model: prefer merged, else adapter
if [ -d "$MERGED" ] && [ -n "$(ls -A "$MERGED" 2>/dev/null)" ]; then
    MODEL_ARG="$MERGED"
elif [ -d "$ADAPTER" ] && [ -n "$(ls -A "$ADAPTER" 2>/dev/null)" ]; then
    MODEL_ARG="$ADAPTER"
else
    echo "[$(date)] ERROR: no v3 model found"; exit 1
fi
echo "[$(date)] running inference with model $MODEL_ARG"

export LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}
source /home3/indiamart/gemma_4/gemma4_env/bin/activate
source /home3/indiamart/gemma_4/set_env.sh
cd /home3/indiamart/gemma_4

CUDA_VISIBLE_DEVICES=1 python -u agent/gemma4_batch_inference_v3.py \
    --model "$MODEL_ARG" \
    --queries /home3/indiamart/gemma_4/76cat_queries \
    --out_csv "$OUT_CSV" \
    --out_jsonl "$OUT_JSONL" \
    --normalize_keys \
    --max_new_tokens 96

echo "[$(date)] v3 inference complete -> $OUT_CSV"
