#!/bin/bash
cd /home3/indiamart/gemma_4
source ./set_env.sh
exec ./gemma4_env/bin/python finetune_gemma4_v4_priority.py
