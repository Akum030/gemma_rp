#!/bin/bash
set -euo pipefail

while pgrep -f finetune_gemma4_v9_priority.py >/dev/null 2>&1 || pgrep -f "eval_priority_adapter.py --adapter /home3/indiamart/gemma_4/isq-gemma4-e4b-v8-priority" >/dev/null 2>&1; do
  sleep 300
done

cd /home/indiamart/gemma_4
CUDA_VISIBLE_DEVICES=0 /home3/indiamart/gemma_4/gemma4_env/bin/python /home/indiamart/gemma_4/eval_priority_adapter.py \
  --adapter /home3/indiamart/gemma_4/isq-gemma4-e4b-v9-priority \
  --label v9 \
  --out-results /home3/indiamart/gemma_4/v9_priority_results.jsonl \
  --out-summary /home3/indiamart/gemma_4/v9_eval_summary.json