"""
Like inference_v4.py but for queries 1-500 (first half) only.
"""
import sys
sys.path.insert(0, "/home3/indiamart/gemma_4")
import inference_v4 as base
base.QUERIES_IN = "/home3/indiamart/gemma_4/v4_inputs_part1.jsonl"
base.OUT_PATH   = "/home3/indiamart/gemma_4/v4_priority_results_part1.jsonl"
if __name__ == "__main__":
    base.main()
