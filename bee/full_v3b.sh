#!/bin/bash
# Full v3b inference: 1000 queries
cd /home3/indiamart/gemma_4
exec bash agent/run_inference.sh \
  /home3/indiamart/gemma_4/models/gemma-4-e4b-it \
  /home3/indiamart/gemma_4/76cat_queries \
  /home3/indiamart/gemma_4/agent/v3b_results.csv \
  /home3/indiamart/gemma_4/agent/v3b_results.jsonl \
  --base_model /home3/indiamart/gemma_4/models/gemma-4-e4b-it \
  --adapter /home3/indiamart/gemma_4/models/gemma4-v3b \
  --normalize_keys
