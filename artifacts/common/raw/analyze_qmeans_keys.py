import pandas as pd
import json
from collections import Counter

df = pd.read_csv("qmeans_results.csv")
all_keys = Counter()
examples = []

for idx, row in df.iterrows():
    query = row["query"]
    isq_pipe = row["qmeans_isq_pipe"]
    
    if pd.isna(isq_pipe) or isq_pipe == "":
        continue
    
    isqs = [x.strip() for x in isq_pipe.split("|")]
    attrs = {}
    
    for isq in isqs:
        parts = isq.split(":")
        if len(parts) == 3:
            value, key, spec = parts
            all_keys[key] += 1
            attrs[key] = value
    
    if attrs:
        examples.append({"query": query, "attributes": attrs})

print("Top 50 QMeans Keys:")
for key, count in all_keys.most_common(50):
    print(f"{key}: {count}")

print(f"\n\nTotal unique keys: {len(all_keys)}")
print(f"Total training examples: {len(examples)}")
print(f"\nSample training data (first 5):")
for i, ex in enumerate(examples[:5]):
    print(f"\n{i+1}. Query: {ex['query']}")
    print(f"   Attributes: {json.dumps(ex['attributes'], indent=2)}")
