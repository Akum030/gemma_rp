"""
Identical to inference_v4.py but reads queries 501-1000 and writes to a
separate output file. Used in parallel with the main process on GPU1.
The wrapper script sets CUDA_VISIBLE_DEVICES=1.
"""
from __future__ import annotations
import os, sys, json, time, re, torch
sys.path.insert(0, "/home3/indiamart/gemma_4")
import inference_v4 as base

# ------- override paths -------
base.QUERIES_IN = "/home3/indiamart/gemma_4/v4_inputs_part2.jsonl"
base.OUT_PATH   = "/home3/indiamart/gemma_4/v4_priority_results_part2.jsonl"

if __name__ == "__main__":
    base.main()
