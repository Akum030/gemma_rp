import pandas as pd
import json

# Load QMeans results
df = pd.read_csv("qmeans_results.csv")

training_data = []

for idx, row in df.iterrows():
    query = row["query"]
    isq_pipe = row["qmeans_isq_pipe"]
    
    if pd.isna(isq_pipe) or isq_pipe == "":
        continue
    
    # Parse ISQ format: value:key:specification
    isqs = [x.strip() for x in isq_pipe.split("|")]
    attrs = {}
    
    for isq in isqs:
        parts = isq.split(":")
        if len(parts) == 3:
            value, key, spec = parts
            # Normalize: lowercase, trim
            attrs[key.strip()] = value.strip().lower()
    
    if attrs:
        instruction = f"Extract key-value attributes from this query: {query}"
        output = json.dumps(attrs, ensure_ascii=False)
        
        training_data.append({
            "instruction": instruction,
            "output": output
        })

# Save training dataset
output_df = pd.DataFrame(training_data)
output_df.to_json("gemma_training_dataset.jsonl", orient="records", lines=True, force_ascii=False)

print(f"Created training dataset with {len(training_data)} examples")
print(f"\nSample training examples:")
for i in range(min(5, len(training_data))):
    print(f"\n--- Example {i+1} ---")
    print(f"Instruction: {training_data[i]['instruction']}")
    print(f"Output: {training_data[i]['output']}")

print(f"\n\nKey Statistics:")
print(f"Total examples: {len(training_data)}")
print(f"Saved to: gemma_training_dataset.jsonl")
