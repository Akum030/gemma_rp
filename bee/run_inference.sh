#!/bin/bash
# Wrapper to run gemma4 inference with the right env
# Usage: run_inference.sh <model_path> <queries_file> <out_csv> <out_jsonl> [extra args]
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}
MODEL=${1:-/home3/indiamart/isq-gemma4-e4b-v2}
QUERIES=${2:-/home3/indiamart/gemma_4/76cat_queries}
OUT_CSV=${3:-/home3/indiamart/gemma_4/agent/inference_results.csv}
OUT_JSONL=${4:-/home3/indiamart/gemma_4/agent/inference_results.jsonl}
shift 4 || true

source /home3/indiamart/gemma_4/gemma4_env/bin/activate
source /home3/indiamart/gemma_4/set_env.sh
cd /home3/indiamart/gemma_4

exec python -u agent/gemma4_batch_inference_v3.py \
    --model "$MODEL" \
    --queries "$QUERIES" \
    --out_csv "$OUT_CSV" \
    --out_jsonl "$OUT_JSONL" \
    "$@"
