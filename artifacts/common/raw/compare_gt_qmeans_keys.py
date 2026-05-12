import pandas as pd
import json
from collections import Counter

# Load Ground Truth data
gt_df = pd.read_csv("synthetic_validation_dataset.csv")

# Extract all keys from Ground Truth (key-value pair columns)
gt_keys = Counter()
gt_examples = []

for idx, row in gt_df.iterrows():
    query = row["query"]
    attrs = {}
    
    # Extract key-value pairs from columns
    for i in range(1, 10):
        key_col = f"attr_key_{i}"
        val_col = f"attr_value_{i}"
        
        if pd.notna(row[key_col]) and pd.notna(row[val_col]):
            key = str(row[key_col]).strip()
            value = str(row[val_col]).strip()
            gt_keys[key] += 1
            attrs[key] = value
    
    if attrs:
        gt_examples.append({"query": query, "attributes": attrs})

print("GROUND TRUTH - Top 50 Keys:")
print("="*60)
for key, count in gt_keys.most_common(50):
    print(f"{key}: {count}")

print(f"\n\nGround Truth Stats:")
print(f"Total unique keys: {len(gt_keys)}")
print(f"Total examples: {len(gt_examples)}")

# Now load QMeans and compare
print("\n\n" + "="*60)
print("QMEANS - Top 50 Keys:")
print("="*60)

df = pd.read_csv("qmeans_results.csv")
qmeans_keys = Counter()

for idx, row in df.iterrows():
    isq_pipe = row["qmeans_isq_pipe"]
    
    if pd.isna(isq_pipe) or isq_pipe == "":
        continue
    
    isqs = [x.strip() for x in isq_pipe.split("|")]
    
    for isq in isqs:
        parts = isq.split(":")
        if len(parts) == 3:
            value, key, spec = parts
            qmeans_keys[key] += 1

for key, count in qmeans_keys.most_common(50):
    print(f"{key}: {count}")

print(f"\n\nQMeans Stats:")
print(f"Total unique keys: {len(qmeans_keys)}")

# Compare overlaps
print("\n\n" + "="*60)
print("KEY COMPARISON:")
print("="*60)

gt_key_set = set(gt_keys.keys())
qmeans_key_set = set(qmeans_keys.keys())

common_keys = gt_key_set & qmeans_key_set
gt_only = gt_key_set - qmeans_key_set
qmeans_only = qmeans_key_set - gt_key_set

print(f"\nCommon keys (in both): {len(common_keys)}")
print(f"Ground Truth only: {len(gt_only)}")
print(f"QMeans only: {len(qmeans_only)}")

print(f"\nCommon keys: {sorted(common_keys)}")
print(f"\nGround Truth ONLY keys: {sorted(gt_only)}")
print(f"\nQMeans ONLY keys: {sorted(qmeans_only)}")
