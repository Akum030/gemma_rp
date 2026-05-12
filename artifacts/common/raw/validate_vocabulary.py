import pandas as pd
from collections import Counter

# Load production vocabulary
prod_df = pd.read_csv("unique_key_val_96_cat.csv", header=None, names=["key", "value"])
production_keys = set(prod_df["key"].unique())

print(f"Production vocabulary: {len(production_keys)} unique keys")

# Load QMeans keys
qmeans_df = pd.read_csv("qmeans_results.csv")
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

print(f"QMeans vocabulary: {len(qmeans_keys)} unique keys")

# Check overlap
common = qmeans_keys & production_keys
qmeans_not_in_prod = qmeans_keys - production_keys
prod_not_in_qmeans = production_keys - qmeans_keys

print(f"\n{'='*80}")
print("VALIDATION RESULT:")
print(f"{'='*80}")
print(f"QMeans keys in production: {len(common)}/{len(qmeans_keys)} ({100*len(common)/len(qmeans_keys):.1f}%)")
print(f"QMeans keys NOT in production: {len(qmeans_not_in_prod)}")

if qmeans_not_in_prod:
    print(f"\nQMeans keys NOT found in production vocabulary:")
    for key in sorted(qmeans_not_in_prod):
        print(f"  - {key}")

print(f"\n{'='*80}")
print("DECISION: Which vocabulary should we use for training?")
print(f"{'='*80}")
print(f"\nOption 1: QMeans 96 keys (what QMeans API currently returns)")
print(f"          Pros: Matches current API behavior exactly")
print(f"          Cons: Limited to 96 keys")
print(f"\nOption 2: Production 1,738 keys (full historical vocabulary)")
print(f"          Pros: Covers all possible attributes")
print(f"          Cons: May extract attributes QMeans doesn't return")
print(f"\n{'='*80}")
print("RECOMMENDATION: Use QMeans 96 keys")
print("  - Gemma will match QMeans API exactly")
print("  - {0} of QMeans keys are validated in production".format(len(common)))
print("  - Focus is to replicate QMeans, not expand beyond it")
print(f"{'='*80}")
