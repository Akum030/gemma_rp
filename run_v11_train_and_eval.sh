#!/usr/bin/env bash
set -euo pipefail

export CUDA_VISIBLE_DEVICES=0

PYTHON_BIN="/home3/indiamart/gemma_4/gemma4_env/bin/python"
WORK_DIR="/home/indiamart/gemma_4"
RESULT_DIR="/home3/indiamart/gemma_4"

TRAIN_SCRIPT="$WORK_DIR/finetune_gemma4_v11_priority_balanced.py"
TRAIN_LOG="$RESULT_DIR/v11_train.log"
EVAL_LOG="$RESULT_DIR/v11_eval.log"

cd "$WORK_DIR"

echo "=== V11 TRAIN START $(date) ===" | tee -a "$TRAIN_LOG"
"$PYTHON_BIN" "$TRAIN_SCRIPT" 2>&1 | tee -a "$TRAIN_LOG"

echo "=== V11 EVAL START $(date) ===" | tee -a "$EVAL_LOG"
"$PYTHON_BIN" "$WORK_DIR/eval_priority_adapter.py" \
  --adapter "$RESULT_DIR/isq-gemma4-e4b-v11-priority-balanced" \
  --label v11 \
  --out-results "$RESULT_DIR/v11_priority_results.jsonl" \
  --out-summary "$RESULT_DIR/v11_eval_summary.json" 2>&1 | tee -a "$EVAL_LOG"

echo "=== V11 PIPELINE DONE $(date) ===" | tee -a "$EVAL_LOG"