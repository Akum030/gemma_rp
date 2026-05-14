#!/bin/bash
# Smoke v3b: 10 queries, debug first 3 raw outputs
# run_inference.sh expects: <model> <queries> <out_csv> <out_jsonl> [extra]
cd /home3/indiamart/gemma_4
exec bash agent/run_inference.sh \
  /home3/indiamart/gemma_4/models/gemma-4-e4b-it \
  /home3/indiamart/gemma_4/76cat_queries \
  /home3/indiamart/gemma_4/agent/v3b_smoke.csv \
  /home3/indiamart/gemma_4/agent/v3b_smoke.jsonl \
  --base_model /home3/indiamart/gemma_4/models/gemma-4-e4b-it \
  --adapter /home3/indiamart/gemma_4/models/gemma4-v3b \
  --normalize_keys --debug_first 3 --limit 10
