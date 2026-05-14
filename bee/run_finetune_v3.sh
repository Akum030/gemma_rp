#!/bin/bash
# Wrapper for v3 fine-tune
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}
source /home3/indiamart/gemma_4/gemma4_env/bin/activate
source /home3/indiamart/gemma_4/set_env.sh
cd /home3/indiamart/gemma_4
exec python -u agent/finetune_v3.py "$@"
