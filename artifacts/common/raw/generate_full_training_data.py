"""
Generate Full Training Dataset for Gemma 2 9B ISQ Extraction
Uses QMeans-compatible keys from unique_key_val_96_cat.csv
"""

import pandas as pd
import json
import random
from collections import defaultdict

# Load QMeans vocabulary
print("Loading QMeans vocabulary from qmeans_results.csv...")
qmeans_df = pd.read_csv('qmeans_results.csv')

# Extract all unique keys from QMeans ISQ outputs
qmeans_keys = set()
for _, row in qmeans_df.iterrows():
    if pd.notna(row['qmeans_isq_pipe']):
        items = row['qmeans_isq_pipe'].split('|')
        for item in items:
            parts = item.split(':')
            if len(parts) >= 2:
                key = parts[1].strip()
                if key:
                    qmeans_keys.add(key)

print(f"QMeans uses {len(qmeans_keys)} unique keys")

# Load production data
print("\nLoading production key-value pairs from unique_key_val_96_cat.csv...")
prod_df = pd.read_csv('unique_key_val_96_cat.csv', header=None, names=['key', 'value'])
print(f"Loaded {len(prod_df)} production key-value pairs")

# Filter to only QMeans-compatible keys
print("\nFiltering to QMeans-compatible keys...")
filtered_df = prod_df[prod_df['key'].isin(qmeans_keys)].copy()
print(f"Filtered to {len(filtered_df)} rows matching QMeans keys")

# Group values by key
key_to_values = defaultdict(list)
for _, row in filtered_df.iterrows():
    key_to_values[row['key']].append(row['value'])

available_keys = list(key_to_values.keys())
print(f"Coverage: {len(filtered_df)} rows from {len(available_keys)} unique keys")

# Generate training examples
print("\n" + "="*60)
print("Generating training examples...")
print("="*60)

train_examples = []
val_examples = []

# Generate diverse examples with 1-5 attributes
num_train = 10000  # Large training set
num_val = 1000     # Validation set

random.seed(42)

def create_example():
    """Create one training example with 1-5 attributes"""
    num_attrs = random.randint(1, 5)
    selected_keys = random.sample(available_keys, min(num_attrs, len(available_keys)))
    
    attributes = {}
    query_parts = []
    
    for key in selected_keys:
        value = random.choice(key_to_values[key])
        # Convert value to string to handle any numeric values
        value_str = str(value)
        attributes[key] = value_str
        query_parts.append(value_str)
    
    # Shuffle query parts to create natural variation
    random.shuffle(query_parts)
    query = " ".join(query_parts)
    
    return {
        "instruction": f"Extract key-value attributes from this query: {query}",
        "output": json.dumps(attributes, ensure_ascii=False)
    }

# Generate training examples
print(f"\nGenerating {num_train} training examples...")
for i in range(num_train):
    train_examples.append(create_example())
    if (i + 1) % 1000 == 0:
        print(f"  Generated {i + 1}/{num_train} training examples...")

# Generate validation examples
print(f"\nGenerating {num_val} validation examples...")
for i in range(num_val):
    val_examples.append(create_example())
    if (i + 1) % 200 == 0:
        print(f"  Generated {i + 1}/{num_val} validation examples...")

# Save to JSONL files
train_file = "product_train_with_keys.jsonl"
val_file = "product_val_with_keys.jsonl"

print(f"\nSaving training data to {train_file}...")
with open(train_file, 'w', encoding='utf-8') as f:
    for example in train_examples:
        f.write(json.dumps(example, ensure_ascii=False) + '\n')

print(f"Saving validation data to {val_file}...")
with open(val_file, 'w', encoding='utf-8') as f:
    for example in val_examples:
        f.write(json.dumps(example, ensure_ascii=False) + '\n')

# Statistics
train_attr_counts = [len(json.loads(ex['output'])) for ex in train_examples]
val_attr_counts = [len(json.loads(ex['output'])) for ex in val_examples]

print("\n" + "="*60)
print("✓ Dataset Generation Complete!")
print("="*60)
print(f"\nTraining examples: {len(train_examples)}")
print(f"  Average attributes per example: {sum(train_attr_counts) / len(train_attr_counts):.2f}")
print(f"  Min attributes: {min(train_attr_counts)}")
print(f"  Max attributes: {max(train_attr_counts)}")

print(f"\nValidation examples: {len(val_examples)}")
print(f"  Average attributes per example: {sum(val_attr_counts) / len(val_attr_counts):.2f}")
print(f"  Min attributes: {min(val_attr_counts)}")
print(f"  Max attributes: {max(val_attr_counts)}")

print(f"\n✓ Training file: {train_file}")
print(f"✓ Validation file: {val_file}")
print(f"\nAll {len(available_keys)} QMeans-compatible keys used in dataset")
print("\nReady for training! 🚀")
