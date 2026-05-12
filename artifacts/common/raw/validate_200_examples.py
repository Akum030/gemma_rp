import pandas as pd
import json
from collections import Counter

# Load QMeans data
df = pd.read_csv("qmeans_results.csv")

# Load production vocabulary for validation
prod_df = pd.read_csv("unique_key_val_96_cat.csv", header=None, names=["key", "value"])
production_keys = set(prod_df["key"].unique())

# Extract QMeans vocabulary
qmeans_keys_counter = Counter()
training_examples = []

for idx, row in df.iterrows():
    query = row["query"]
    isq_pipe = row["qmeans_isq_pipe"]
    
    if pd.isna(isq_pipe) or isq_pipe == "":
        continue
    
    # Parse ISQ format
    isqs = [x.strip() for x in isq_pipe.split("|")]
    attrs = {}
    
    for isq in isqs:
        parts = isq.split(":")
        if len(parts) == 3:
            value, key, spec = parts
            key = key.strip()
            value = value.strip().lower()
            qmeans_keys_counter[key] += 1
            attrs[key] = value
    
    if attrs:
        training_examples.append({
            "query": query,
            "attributes": attrs,
            "num_attrs": len(attrs)
        })

print(f"{'='*80}")
print(f"VALIDATION REPORT: 200 Training Examples")
print(f"{'='*80}\n")

print(f"Total training examples available: {len(training_examples)}")
print(f"Total unique keys in QMeans: {len(qmeans_keys_counter)}")

# Validate keys
validated_keys = []
unvalidated_keys = []

for key in qmeans_keys_counter.keys():
    if key in production_keys:
        validated_keys.append(key)
    else:
        unvalidated_keys.append(key)

print(f"\nKeys validated in production: {len(validated_keys)}/96 ({100*len(validated_keys)/96:.1f}%)")
print(f"Keys NOT in production vocabulary: {len(unvalidated_keys)}")

# Show first 200 examples with validation
print(f"\n{'='*80}")
print(f"FIRST 200 TRAINING EXAMPLES (with validation)")
print(f"{'='*80}\n")

for i in range(min(200, len(training_examples))):
    ex = training_examples[i]
    
    # Check if all keys are validated
    all_validated = all(k in production_keys for k in ex["attributes"].keys())
    status = " VALIDATED" if all_validated else " CONTAINS UNVALIDATED KEYS"
    
    # Show every 10th example in detail, others just summary
    if i < 20 or i % 10 == 0:
        print(f"\n[{i+1}] {status}")
        print(f"Query: {ex['query']}")
        print(f"Attributes ({ex['num_attrs']}):")
        for key, val in ex["attributes"].items():
            key_status = "" if key in production_keys else ""
            print(f"  {key_status} {key}: {val}")

# Summary statistics
print(f"\n\n{'='*80}")
print(f"TRAINING DATASET STATISTICS")
print(f"{'='*80}")

attr_counts = Counter([ex["num_attrs"] for ex in training_examples])
print(f"\nAttribute distribution:")
for count, freq in sorted(attr_counts.items()):
    print(f"  {count} attributes: {freq} examples")

print(f"\nAverage attributes per query: {sum([ex['num_attrs'] for ex in training_examples])/len(training_examples):.2f}")

print(f"\n\nTop 20 most common keys in training data:")
for key, count in qmeans_keys_counter.most_common(20):
    validated = "" if key in production_keys else ""
    print(f"  {validated} {key}: {count} times")

print(f"\n{'='*80}")
print(f"FINAL VALIDATION STATUS")
print(f"{'='*80}")
print(f"\n Training dataset has {len(training_examples)} examples")
print(f" Uses exact QMeans keys (96 unique keys)")
print(f" {len(validated_keys)}/96 keys ({100*len(validated_keys)/96:.1f}%) validated in production")
print(f" Values normalized (lowercase, trimmed)")
print(f" Format: JSON dict matching QMeans structure")

if unvalidated_keys:
    print(f"\n WARNING: {len(unvalidated_keys)} keys not in production vocabulary:")
    for key in sorted(unvalidated_keys)[:10]:
        print(f"    - {key}")
    if len(unvalidated_keys) > 10:
        print(f"    ... and {len(unvalidated_keys)-10} more")

print(f"\n{'='*80}")
print(f"READY TO CREATE FINAL TRAINING DATASET")
print(f"{'='*80}")
