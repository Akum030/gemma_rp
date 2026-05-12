import pandas as pd
import json
from collections import Counter

# Load Ground Truth data
gt_df = pd.read_csv("synthetic_validation_dataset.csv")

# Extract all keys from Ground Truth
gt_keys = Counter()
gt_examples = []

for idx, row in gt_df.iterrows():
    query = row["query"]
    gt_isq = row["ground_truth_isq"]
    
    if pd.isna(gt_isq) or gt_isq == "":
        continue
    
    # Parse ISQ format
    isqs = [x.strip() for x in gt_isq.split("|")]
    attrs = {}
    
    for isq in isqs:
        parts = isq.split(":")
        if len(parts) == 3:
            value, key, spec = parts
            gt_keys[key] += 1
            attrs[key] = value
    
    if attrs:
        gt_examples.append({"query": query, "attributes": attrs})

print("Ground Truth - Top 50 Keys:")
for key, count in gt_keys.most_common(50):
    print(f"{key}: {count}")

print(f"\n\nGround Truth Stats:")
print(f"Total unique keys: {len(gt_keys)}")
print(f"Total examples: {len(gt_examples)}")
