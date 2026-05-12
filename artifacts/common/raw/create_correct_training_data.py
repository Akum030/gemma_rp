import pandas as pd
import json
import random
from collections import defaultdict

# Read the production ISQ key-value data
print("Reading unique_key_val_96_cat.csv...")
df = pd.read_csv('unique_key_val_96_cat.csv', header=None, names=['key', 'value'])

print(f"Total rows: {len(df)}")
print(f"Unique keys: {df['key'].nunique()}")

# Group values by key
key_values = defaultdict(list)
for _, row in df.iterrows():
    key = str(row['key']).strip()
    value = str(row['value']).strip()
    if key and value and key != 'nan' and value != 'nan':
        key_values[key].append(value)

print(f"\nKeys with their value counts:")
for key in sorted(key_values.keys())[:20]:
    print(f"  {key}: {len(key_values[key])} values")

# Create training examples
# Strategy: Create synthetic queries by combining 3-7 random key-value pairs
# and format output as ISQ JSON matching QMeans structure

training_data = []
num_examples = 2000  # Create 2000 training examples

print(f"\nGenerating {num_examples} training examples...")

for i in range(num_examples):
    # Select 3-7 random keys
    num_attrs = random.randint(3, 7)
    selected_keys = random.sample(list(key_values.keys()), num_attrs)
    
    # For each key, select a random value
    query_parts = []
    isq_output = {}
    
    for key in selected_keys:
        value = random.choice(key_values[key])
        query_parts.append(value)
        isq_output[key] = value
    
    # Create query by joining values
    query = " ".join(query_parts)
    
    # Format training example
    training_example = {
        "instruction": f"Extract key-value attributes from this query: {query}",
        "output": json.dumps(isq_output, ensure_ascii=False)
    }
    
    training_data.append(training_example)
    
    if (i + 1) % 500 == 0:
        print(f"  Generated {i + 1} examples...")

# Save training data
output_file = 'gemma_correct_training_dataset.jsonl'
print(f"\nSaving to {output_file}...")

with open(output_file, 'w', encoding='utf-8') as f:
    for example in training_data:
        f.write(json.dumps(example, ensure_ascii=False) + '\n')

print(f"✓ Saved {len(training_data)} training examples")

# Show sample
print("\n=== Sample Training Examples ===")
for i in range(3):
    print(f"\nExample {i+1}:")
    print(f"Instruction: {training_data[i]['instruction'][:100]}...")
    print(f"Output: {training_data[i]['output'][:150]}...")

print("\n=== Key Statistics ===")
print(f"Total training examples: {len(training_data)}")
print(f"Unique keys in vocabulary: {len(key_values)}")
print(f"Total key-value pairs: {sum(len(vals) for vals in key_values.values())}")
