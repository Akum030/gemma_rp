import pandas as pd
import json
import random
from collections import defaultdict

# Load production data
prod_df = pd.read_csv('unique_key_val_96_cat.csv', header=None, names=['key', 'value'])
print(f"Loaded {len(prod_df)} production key-value pairs")
print(f"Unique keys in production: {prod_df['key'].nunique()}")

# Load QMeans results to extract the 96 keys QMeans actually uses
qmeans_df = pd.read_csv('qmeans_results.csv')
qmeans_keys = set()
for idx, row in qmeans_df.iterrows():
    isq_pipe = row['qmeans_isq_pipe']
    if pd.notna(isq_pipe) and isinstance(isq_pipe, str):
        isqs = [x.strip() for x in isq_pipe.split('|')]
        for isq in isqs:
            parts = isq.split(':')
            if len(parts) >= 2:
                key = parts[1].strip()
                qmeans_keys.add(key)

print(f"\nQMeans uses {len(qmeans_keys)} unique keys")
print(f"Sample QMeans keys: {list(qmeans_keys)[:20]}")

# Filter production data to only include QMeans keys
filtered_df = prod_df[prod_df['key'].isin(qmeans_keys)].copy()
print(f"\nFiltered to {len(filtered_df)} rows matching QMeans keys")
print(f"Coverage: {len(filtered_df)} rows from {filtered_df['key'].nunique()} unique keys")

# Group by key to see distribution
key_counts = filtered_df['key'].value_counts()
print(f"\nTop 10 keys by count:")
print(key_counts.head(10))

# Create training examples: synthetic queries with multiple attributes
training_examples = []

# Group values by key for easy lookup
key_to_values = defaultdict(list)
for _, row in filtered_df.iterrows():
    key_to_values[row['key']].append(row['value'])

# Strategy: Create synthetic product queries by combining 1-5 key-value pairs
available_keys = list(key_to_values.keys())
num_samples = 200

for i in range(num_samples):
    # Randomly select 1-5 keys for this example
    num_attrs = random.randint(1, 5)
    selected_keys = random.sample(available_keys, min(num_attrs, len(available_keys)))
    
    # For each key, pick a random value
    attributes = {}
    query_parts = []
    
    for key in selected_keys:
        value = random.choice(key_to_values[key])
        attributes[key] = value
        # Build query naturally incorporating the value
        query_parts.append(value)
    
    # Create a synthetic query
    query = " ".join(query_parts)
    
    # Create training example in the format: instruction + output
    example = {
        "instruction": f"Extract key-value attributes from this query: {query}",
        "output": json.dumps(attributes, ensure_ascii=False)
    }
    
    training_examples.append(example)

# Save first 200 examples for validation
output_file = 'sample_training_data_200.jsonl'
with open(output_file, 'w', encoding='utf-8') as f:
    for example in training_examples:
        f.write(json.dumps(example, ensure_ascii=False) + '\n')

print(f"\n✓ Created {len(training_examples)} sample training examples")
print(f"✓ Saved to {output_file}")

# Show some examples for validation
print(f"\n=== SAMPLE TRAINING EXAMPLES ===")
for i in range(min(10, len(training_examples))):
    print(f"\nExample {i+1}:")
    print(f"Instruction: {training_examples[i]['instruction']}")
    print(f"Output: {training_examples[i]['output']}")

# Statistics
print(f"\n=== STATISTICS ===")
total_attrs = sum(len(json.loads(ex['output'])) for ex in training_examples)
print(f"Total examples: {len(training_examples)}")
print(f"Average attributes per example: {total_attrs / len(training_examples):.2f}")
print(f"Keys used: {len(available_keys)}")

# Verify all keys match QMeans
all_keys_in_examples = set()
for ex in training_examples:
    output = json.loads(ex['output'])
    all_keys_in_examples.update(output.keys())

print(f"\nValidation:")
print(f"✓ All {len(all_keys_in_examples)} keys in examples are from QMeans vocabulary")
print(f"✓ Keys used: {sorted(all_keys_in_examples)[:20]}...")
