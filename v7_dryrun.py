"""Dry-run: only build/inspect v7 datasets, do NOT load model."""
import json, sys, os, importlib.util

# Just import the real script's helpers without running main()
spec = importlib.util.spec_from_file_location("v7", "/home/indiamart/gemma_4/finetune_gemma4_v7_priority.py")
v7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v7)

ct = v7.load_nested_jsonl(v7.CAT74_NESTED_TRAIN)
cv = v7.load_nested_jsonl(v7.CAT74_NESTED_VAL)
v6t = v7.load_flat_v6_as_nested(v7.V6_FLAT_TRAIN)
v6v = v7.load_flat_v6_as_nested(v7.V6_FLAT_VAL)
print(f"cat74 nested  train={len(ct)} val={len(cv)}")
print(f"v6 flat->nest train={len(v6t)} val={len(v6v)}")
print(f"COMBINED      train={len(ct)+len(v6t)} val={len(cv)+len(v6v)}")
print()
print("SAMPLE v6 converted:")
print("  instr tail:", v6t[0]['instruction'][-120:])
print("  output    :", v6t[0]['output'])
print()
print("SAMPLE cat74 nested:")
print("  instr tail:", ct[0]['instruction'][-120:])
print("  output    :", ct[0]['output'][:300])
print()
# check a few v6 conversions to ensure priority structure is sane
for r in v6t[:5]:
    print(" >", r['output'][:200])
