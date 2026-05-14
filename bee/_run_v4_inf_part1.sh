#!/usr/bin/env bash
cd /home3/indiamart/gemma_4
source ./set_env.sh
export CUDA_VISIBLE_DEVICES=0
exec ./gemma4_env/bin/python inference_v4_part1.py
