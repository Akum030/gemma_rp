import pandas as pd
import json

# Load both datasets - find matching queries
gt_df = pd.read_csv("synthetic_validation_dataset.csv")
qmeans_df = pd.read_csv("qmeans_results.csv")

# Merge on query
merged = pd.merge(gt_df, qmeans_df, on="query", how="inner")

print(f"Found {len(merged)} matching queries between GT and QMeans\n")
print("="*80)
print("VALIDATION: Comparing 100 cases - Ground Truth vs QMeans")
print("="*80)

mismatches = []
matches = []

for idx in range(min(100, len(merged))):
    row = merged.iloc[idx]
    query = row["query"]
    
    # Extract Ground Truth attributes
    gt_attrs = {}
    for i in range(1, 10):
        key_col = f"attr_key_{i}"
        val_col = f"attr_value_{i}"
        if pd.notna(row[key_col]) and pd.notna(row[val_col]):
            gt_attrs[str(row[key_col]).strip()] = str(row[val_col]).strip().lower()
    
    # Extract QMeans attributes
    qmeans_attrs = {}
    isq_pipe = row["qmeans_isq_pipe"]
    if pd.notna(isq_pipe) and isq_pipe != "":
        isqs = [x.strip() for x in isq_pipe.split("|")]
        for isq in isqs:
            parts = isq.split(":")
            if len(parts) == 3:
                value, key, spec = parts
                qmeans_attrs[key.strip()] = value.strip().lower()
    
    # Compare keys
    gt_keys = set(gt_attrs.keys())
    qm_keys = set(qmeans_attrs.keys())
    
    common = gt_keys & qm_keys
    gt_only = gt_keys - qm_keys
    qm_only = qm_keys - gt_keys
    
    if gt_only or qm_only:
        mismatches.append({
            "query": query,
            "gt_attrs": gt_attrs,
            "qm_attrs": qmeans_attrs,
            "common_keys": common,
            "gt_only_keys": gt_only,
            "qm_only_keys": qm_only
        })
    else:
        matches.append(query)

print(f"\n\nSUMMARY:")
print(f"Perfect key matches: {len(matches)}/100")
print(f"Key mismatches: {len(mismatches)}/100")

print(f"\n\n{'='*80}")
print("DETAILED ANALYSIS - First 20 Mismatches:")
print(f"{'='*80}\n")

for i, mm in enumerate(mismatches[:20]):
    print(f"\n--- Case {i+1}: {mm['query']} ---")
    print(f"\nGround Truth: {json.dumps(mm['gt_attrs'], indent=2)}")
    print(f"\nQMeans:       {json.dumps(mm['qm_attrs'], indent=2)}")
    print(f"\nCommon keys: {mm['common_keys']}")
    print(f"GT only: {mm['gt_only_keys']}")
    print(f"QM only: {mm['qm_only_keys']}")
    print("-"*80)
