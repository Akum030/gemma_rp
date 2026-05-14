#!/bin/bash
set -e
cd /home3/indiamart/gemma_4
source ./set_env.sh
# Use first 5 queries only as smoke test
head -5 v4_inputs.jsonl > /tmp/v4_inputs_smoke.jsonl
# patch inference path on the fly via env override
QUERIES_OVERRIDE=/tmp/v4_inputs_smoke.jsonl OUT_OVERRIDE=/tmp/v4_smoke_out.jsonl \
    ./gemma4_env/bin/python -c "
import os
os.environ.setdefault('QUERIES_OVERRIDE','/tmp/v4_inputs_smoke.jsonl')
os.environ.setdefault('OUT_OVERRIDE','/tmp/v4_smoke_out.jsonl')
import inference_v4
inference_v4.QUERIES_IN = os.environ['QUERIES_OVERRIDE']
inference_v4.OUT_PATH   = os.environ['OUT_OVERRIDE']
inference_v4.BATCH_SIZE = 5
inference_v4.main()
"
echo '--- SMOKE RESULTS ---'
cat /tmp/v4_smoke_out.jsonl
