#!/bin/bash
set -euo pipefail

while pgrep -f finetune_gemma4_v9_priority.py >/dev/null 2>&1; do
  sleep 300
done

cd /home/indiamart/gemma_4
CUDA_VISIBLE_DEVICES=1 nohup /home3/indiamart/gemma_4/gemma4_env/bin/python /home/indiamart/gemma_4/finetune_gemma4_v10_priority_clean.py > /home/indiamart/gemma_4/v10_train.log 2>&1 &
disown