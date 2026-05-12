import pandas as pd
import json
from collections import Counter

# Load production data
prod_df = pd.read_csv("unique_key_val_96_cat.csv", header=None, names=["key", "value"])

# Load QMeans to get correct key vocabulary
qmeans_df = pd.read_csv("qmeans_results.csv")

# Extract QMeans keys
qmeans_keys = set()
for idx, row in qmeans_df.iterrows():
    isq_pipe = row["qmeans_isq_pipe"]
    if pd.notna(isq_pipe) and isq_pipe != "":
        isqs = [x.strip() for x in isq_pipe.split("|")]
        for isq in isqs:
            parts = isq.split(":")
            if len(parts) == 3:
                value, key, spec = parts
                qmeans_keys.add(key.strip())

print("="*80)
print("KEY MAPPING: Production  QMeans")
print("="*80)

# Get production keys
prod_keys = prod_df["key"].unique()
print(f"\nProduction keys (unique_key_val_96_cat.csv): {len(prod_keys)}")
print(f"QMeans keys (qmeans_results.csv): {len(qmeans_keys)}")

# Create key mapping
key_mapping = {}

# Direct matches
for pkey in prod_keys:
    if pkey in qmeans_keys:
        key_mapping[pkey] = pkey
        
# Manual mappings for common mismatches
manual_mappings = {
    "usage/application": "usage",
    "automatic grade": "automation grade",
    "body material": "material",
    "production capacity": "capacity",
    "model name/number": "model name/number",
    "power consumption": "capacity",
    "machine power": "capacity",
    "screw speed": "screw type",
    "motor power": "capacity"
}

for pkey, qkey in manual_mappings.items():
    if pkey in prod_keys and qkey in qmeans_keys:
        key_mapping[pkey] = qkey

print(f"\n\nMapped keys: {len(key_mapping)}")
print(f"\nSample mappings:")
for i, (pk, qk) in enumerate(list(key_mapping.items())[:20]):
    match_indicator = "" if pk == qk else ""
    print(f"  {pk} {match_indicator} {qk}")

# Check unmapped production keys
unmapped = set(prod_keys) - set(key_mapping.keys())
print(f"\n\nUnmapped production keys: {len(unmapped)}")
print(f"Sample unmapped: {list(unmapped)[:10]}")

print("\n\n" + "="*80)
print("QUESTION: Should we:")
print("="*80)
print("\nOption A: Only use production keys that map to QMeans keys")
print(f"          Result: {len(key_mapping)} training keys")
print("\nOption B: Keep all production keys (ignore QMeans mapping)")
print(f"          Result: {len(prod_keys)} training keys")
print("\nOption C: Create comprehensive mapping for all keys")
print(f"          Result: {len(prod_keys)} training keys")
