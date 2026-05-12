"""
Prepare Training Data for Gemma 2 9B - ISQ Extraction
Converts ISQ key-value pairs into training format with synthetic queries

Input: unique_key_val_96_cat.csv (11k ISQ pairs)
Output: 
  - product_train.jsonl (80% - ~9k samples)
  - product_val.jsonl (10% - ~1k samples)  
  - product_test.jsonl (10% - ~1k samples)
"""

import pandas as pd
import json
import random
from collections import defaultdict

# Configuration
INPUT_CSV = "unique_key_val_96_cat.csv"
OUTPUT_TRAIN = "product_train.jsonl"
OUTPUT_VAL = "product_val.jsonl"
OUTPUT_TEST = "product_test.jsonl"

# Split ratios
TRAIN_RATIO = 0.8
VAL_RATIO = 0.1
TEST_RATIO = 0.1

random.seed(42)

# Product templates for query generation
PRODUCTS = [
    "twin screw extruder", "extruder machine", "blown film extrusion machine",
    "gold refining machine", "silver refining plant", "solvent extraction plant",
    "herbal extraction plant", "cable extruder", "monolayer extruder",
    "centrifuge extractor", "bitumen extractor", "metal recovery plant",
    "rice bran extraction plant", "tube extrusion machine", "sheet extruder",
    "basket extruder", "conical twin screw extruder", "lab extruder",
    "aluminium extrusion plant", "gold refinery plant", "silver refinery machine",
    "co-rotating twin screw extruder", "plastic extruder", "pvc extruder",
    "ldpe blown film machine", "hdpe extruder", "curcumin extraction plant",
    "oleoresin extraction plant", "oil extraction plant", "film extrusion machine",
    "wire extruder", "polymer extruder", "foam extruder", "pipe extrusion machine"
]

def normalize_key(key):
    """Normalize ISQ key to lowercase with underscores"""
    return key.strip().lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "")

def normalize_value(value):
    """Clean and normalize ISQ value"""
    value = str(value).strip().lower()
    # Remove quotes and extra spaces
    value = value.replace('"', '').replace("'", "")
    return value

def load_isq_data(filepath):
    """Load ISQ data and group by attribute combinations"""
    print(f"Loading ISQ data from {filepath}...")
    
    df = pd.read_csv(filepath, header=None, names=['key', 'value'])
    
    # Clean data
    df['key'] = df['key'].apply(normalize_key)
    df['value'] = df['value'].apply(normalize_value)
    
    # Remove invalid entries
    df = df[df['value'].notna()]
    df = df[df['value'] != '']
    df = df[df['value'] != 'nan']
    
    # Group attributes by key
    attr_by_key = defaultdict(list)
    for _, row in df.iterrows():
        key = row['key']
        value = row['value']
        if len(value) > 1 and value not in ['abc', 'xxx', 'na']:
            attr_by_key[key].append(value)
    
    # Deduplicate
    attr_by_key = {k: list(set(v)) for k, v in attr_by_key.items()}
    
    print(f"Loaded {len(attr_by_key)} unique ISQ keys")
    print(f"Total attribute combinations: {sum(len(v) for v in attr_by_key.values())}")
    
    return attr_by_key

def generate_query_from_isqs(isqs, product_type=None):
    """Generate synthetic product query from ISQ dictionary"""
    
    if product_type is None:
        product_type = random.choice(PRODUCTS)
    
    query_parts = [product_type]
    
    # Query style variations
    style = random.choice(['natural', 'specification', 'detailed', 'brief'])
    
    if style == 'natural':
        # "looking for [product] with [attr1], [attr2]..."
        if len(isqs) > 0:
            attrs = [f"{k.replace('_', ' ')} {v}" for k, v in list(isqs.items())[:random.randint(2, min(4, len(isqs)))]]
            query_parts = [f"looking for {product_type} with " + ", ".join(attrs)]
    
    elif style == 'specification':
        # "[product], [attr1]: [val1], [attr2]: [val2]"
        attrs = [f"{k.replace('_', ' ')}: {v}" for k, v in list(isqs.items())[:random.randint(3, min(6, len(isqs)))]]
        query_parts = [product_type + ", " + ", ".join(attrs)]
    
    elif style == 'detailed':
        # "high quality [brand] [product] [attr1] type, [val2], [val3]..."
        prefix = random.choice(["high quality", "industrial", "reliable", "efficient", ""])
        brand = isqs.get('brand', None)
        if brand:
            query_parts = [f"{prefix} {brand} {product_type}".strip()]
        else:
            query_parts = [f"{prefix} {product_type}".strip()]
        
        other_attrs = [f"{v}" for k, v in isqs.items() if k != 'brand' and random.random() > 0.3][:random.randint(2, 5)]
        if other_attrs:
            query_parts.append(", ".join(other_attrs))
    
    else:  # brief
        # Just product + few key values
        key_attrs = [v for k, v in list(isqs.items())[:random.randint(1, 3)]]
        query_parts.extend(key_attrs)
    
    query = " ".join(query_parts)
    return query.strip()

def generate_training_samples(attr_by_key, num_samples=10000):
    """Generate training samples from ISQ data"""
    
    print(f"Generating {num_samples} training samples...")
    
    samples = []
    all_keys = list(attr_by_key.keys())
    
    for i in range(num_samples):
        # Randomly select 2-8 attributes
        num_attrs = random.randint(2, min(8, len(all_keys)))
        selected_keys = random.sample(all_keys, num_attrs)
        
        # Build ISQ dictionary
        isqs = {}
        for key in selected_keys:
            if attr_by_key[key]:  # Check if values exist
                value = random.choice(attr_by_key[key])
                isqs[key] = value
        
        # Always include product type
        product = random.choice(PRODUCTS)
        isqs = {"product": product, **isqs}
        
        # Generate query
        query = generate_query_from_isqs(isqs, product)
        
        # Format as training sample
        instruction = f"""Extract ISQs from the following product description.

Product description:
\"\"\"{query}\"\"\"

Return output in JSON format only."""
        
        output = json.dumps(isqs, ensure_ascii=False)
        
        sample = {
            "instruction": instruction,
            "output": output
        }
        
        samples.append(sample)
        
        if (i + 1) % 1000 == 0:
            print(f"Generated {i + 1}/{num_samples} samples...")
    
    print(f"✓ Generated {len(samples)} training samples")
    return samples

def split_and_save(samples, train_file, val_file, test_file):
    """Split data and save to JSONL files"""
    
    print("Splitting data...")
    random.shuffle(samples)
    
    total = len(samples)
    train_size = int(total * TRAIN_RATIO)
    val_size = int(total * VAL_RATIO)
    
    train_samples = samples[:train_size]
    val_samples = samples[train_size:train_size + val_size]
    test_samples = samples[train_size + val_size:]
    
    print(f"Train: {len(train_samples)}, Val: {len(val_samples)}, Test: {len(test_samples)}")
    
    # Save train
    with open(train_file, 'w', encoding='utf-8') as f:
        for sample in train_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    print(f"✓ Saved {train_file}")
    
    # Save validation
    with open(val_file, 'w', encoding='utf-8') as f:
        for sample in val_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    print(f"✓ Saved {val_file}")
    
    # Save test
    with open(test_file, 'w', encoding='utf-8') as f:
        for sample in test_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    print(f"✓ Saved {test_file}")

def main():
    print("=" * 60)
    print("Gemma 2 9B Training Data Preparation")
    print("=" * 60)
    
    # Load ISQ data
    attr_by_key = load_isq_data(INPUT_CSV)
    
    # Generate samples (scale up for 9B model)
    num_samples = 20000  # 20k samples for better coverage
    samples = generate_training_samples(attr_by_key, num_samples)
    
    # Split and save
    split_and_save(samples, OUTPUT_TRAIN, OUTPUT_VAL, OUTPUT_TEST)
    
    print("\n" + "=" * 60)
    print("✓ Data preparation complete!")
    print("=" * 60)
    print(f"\nFiles created:")
    print(f"  - {OUTPUT_TRAIN} (training)")
    print(f"  - {OUTPUT_VAL} (validation)")
    print(f"  - {OUTPUT_TEST} (test)")
    print(f"\nNext steps:")
    print(f"  1. Download Gemma 2 9B model")
    print(f"  2. Run training script")

if __name__ == "__main__":
    main()
