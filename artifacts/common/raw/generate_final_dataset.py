import pandas as pd
import json

# Generate final training dataset
df = pd.read_csv("qmeans_results.csv")
training_data = []

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
            attrs[key.strip()] = value.strip().lower()
    
    if attrs:
        instruction = f"Extract key-value attributes from this query: {query}"
        output = json.dumps(attrs, ensure_ascii=False, sort_keys=True)
        
        training_data.append({
            "instruction": instruction,
            "output": output
        })

# Save as JSONL
output_df = pd.DataFrame(training_data)
output_df.to_json("gemma_final_training_dataset.jsonl", orient="records", lines=True, force_ascii=False)

print(f" Created final training dataset: gemma_final_training_dataset.jsonl")
print(f" Total examples: {len(training_data)}")
print(f" Format: JSONL (one JSON object per line)")
print(f"\n Sample entry:")
print(json.dumps(training_data[0], indent=2))
