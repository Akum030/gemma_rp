"""
Generate Multi-Task Training Data for Gemma 2 9B
Tasks: ISQ Extraction + Query Correction + Translation

This creates a unified training dataset for all three capabilities
"""

import json
import random
import pandas as pd
from collections import defaultdict

# Configuration
ISQ_CSV = "unique_key_val_96_cat.csv"
OUTPUT_TRAIN = "multitask_train.jsonl"
OUTPUT_VAL = "multitask_val.jsonl"

# Task distribution (total 30k samples)
TASK_DISTRIBUTION = {
    "isq_extraction": 0.60,  # 18k samples - primary task
    "query_correction": 0.20,  # 6k samples
    "translation": 0.20  # 6k samples
}

TOTAL_SAMPLES = 30000
random.seed(42)

# ==================== ISQ EXTRACTION (same as before) ====================

PRODUCTS = [
    "twin screw extruder", "extruder machine", "blown film extrusion machine",
    "gold refining machine", "silver refining plant", "solvent extraction plant",
    "herbal extraction plant", "cable extruder", "plastic extruder",
    "oil extraction plant", "film extrusion machine", "pipe extrusion machine"
]

def load_isq_data(filepath):
    """Load and organize ISQ data"""
    df = pd.read_csv(filepath, header=None, names=['key', 'value'])
    
    # Normalize
    df['key'] = df['key'].str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')
    df['value'] = df['value'].astype(str).str.strip().str.lower()
    
    # Filter
    df = df[df['value'].notna() & (df['value'] != '') & (df['value'] != 'nan')]
    
    # Group by key
    attr_by_key = defaultdict(list)
    for _, row in df.iterrows():
        attr_by_key[row['key']].append(row['value'])
    
    # Deduplicate
    return {k: list(set(v)) for k, v in attr_by_key.items()}

def generate_isq_sample(attr_by_key):
    """Generate one ISQ extraction sample"""
    all_keys = list(attr_by_key.keys())
    num_attrs = random.randint(2, min(8, len(all_keys)))
    selected_keys = random.sample(all_keys, num_attrs)
    
    isqs = {}
    for key in selected_keys:
        if attr_by_key[key]:
            isqs[key] = random.choice(attr_by_key[key])
    
    product = random.choice(PRODUCTS)
    isqs = {"product": product, **isqs}
    
    # Generate query
    query_parts = [product]
    for k, v in list(isqs.items())[1:]:  # Skip product
        if random.random() > 0.3:
            query_parts.append(v)
    query = " ".join(query_parts)
    
    instruction = f"""Extract ISQs from the following product description.

Product description:
\"\"\"{query}\"\"\"

Return output in JSON format only."""
    
    output = json.dumps(isqs, ensure_ascii=False)
    
    return {
        "task": "isq_extraction",
        "instruction": instruction,
        "output": output
    }

# ==================== QUERY CORRECTION ====================

# Common typos and corrections
CORRECTION_PATTERNS = [
    # Spelling corrections
    ("extracter", "extractor"),
    ("machin", "machine"),
    ("indusrial", "industrial"),
    ("automatik", "automatic"),
    ("stainles", "stainless"),
    ("stil", "steel"),
    ("capasity", "capacity"),
    ("voltge", "voltage"),
    ("phas", "phase"),
    ("refinging", "refining"),
    ("extrusion", "extrusion"),
    ("machien", "machine"),
    ("trew", "screw"),
    ("plastik", "plastic"),
    ("electricl", "electrical"),
    
    # Common product typos
    ("twin skrew", "twin screw"),
    ("extuder", "extruder"),
    ("blow film", "blown film"),
    ("gold refing", "gold refining"),
    ("solvet extraction", "solvent extraction"),
    
    # Unit typos
    ("440 volt", "440 v"),
    ("3 fase", "3 phase"),
    ("50 kg/h", "50 kg/hr"),
    ("100 kilogram", "100 kg"),
    ("5 horsepower", "5 hp"),
]

def generate_query_correction_sample():
    """Generate query correction sample"""
    
    # Base correct query
    product = random.choice(PRODUCTS)
    attrs = random.sample([
        "440 v", "three phase", "automatic", "stainless steel",
        "50 kg/hr", "industrial", "made in india", "new only"
    ], k=random.randint(2, 4))
    
    correct_query = f"{product} {' '.join(attrs)}"
    
    # Introduce errors
    incorrect_query = correct_query
    num_errors = random.randint(1, 3)
    
    for _ in range(num_errors):
        wrong, right = random.choice(CORRECTION_PATTERNS)
        if right in incorrect_query:
            incorrect_query = incorrect_query.replace(right, wrong, 1)
    
    # Additional random errors
    if random.random() > 0.5:
        # Remove random spaces
        words = incorrect_query.split()
        if len(words) > 2:
            idx = random.randint(0, len(words)-2)
            words[idx] = words[idx] + words[idx+1]
            del words[idx+1]
            incorrect_query = " ".join(words)
    
    instruction = f"""Correct the following product query.

Query: {incorrect_query}

Return the corrected query only."""
    
    output = correct_query
    
    return {
        "task": "query_correction",
        "instruction": instruction,
        "output": output
    }

# ==================== TRANSLATION ====================

# Hindi translations for common industrial terms
TRANSLATIONS = {
    # Products
    "extruder machine": "एक्सट्रूडर मशीन",
    "twin screw extruder": "ट्विन स्क्रू एक्सट्रूडर",
    "gold refining machine": "सोना शुद्धिकरण मशीन",
    "silver refining plant": "चांदी शुद्धिकरण संयंत्र",
    "extraction plant": "निष्कर्षण संयंत्र",
    "plastic extruder": "प्लास्टिक एक्सट्रूडर",
    
    # Attributes
    "automatic": "स्वचालित",
    "semi-automatic": "अर्ध-स्वचालित",
    "manual": "मैनुअल",
    "stainless steel": "स्टेनलेस स्टील",
    "mild steel": "माइल्ड स्टील",
    "industrial": "औद्योगिक",
    "made in india": "भारत में निर्मित",
    "new": "नया",
    "used": "इस्तेमाल किया हुआ",
    
    # Specifications
    "voltage": "वोल्टेज",
    "phase": "फेज़",
    "capacity": "क्षमता",
    "power": "शक्ति",
    "material": "सामग्री",
    "brand": "ब्रांड",
}

def generate_translation_sample():
    """Generate English->Hindi or Hindi->English translation sample"""
    
    direction = random.choice(["en_to_hi", "hi_to_en"])
    
    # Build phrase
    num_terms = random.randint(2, 4)
    en_terms = random.sample(list(TRANSLATIONS.keys()), k=min(num_terms, len(TRANSLATIONS)))
    
    if direction == "en_to_hi":
        source = " ".join(en_terms)
        target = " ".join([TRANSLATIONS[term] for term in en_terms])
        
        instruction = f"""Translate the following product query from English to Hindi.

English: {source}

Return Hindi translation only."""
        output = target
        
    else:  # hi_to_en
        hi_terms = [TRANSLATIONS[term] for term in en_terms]
        source = " ".join(hi_terms)
        target = " ".join(en_terms)
        
        instruction = f"""Translate the following product query from Hindi to English.

Hindi: {source}

Return English translation only."""
        output = target
    
    return {
        "task": "translation",
        "instruction": instruction,
        "output": output
    }

# ==================== MAIN GENERATION ====================

def generate_multitask_dataset():
    """Generate complete multi-task dataset"""
    
    print("=" * 60)
    print("Multi-Task Training Data Generation")
    print("=" * 60)
    
    # Load ISQ data
    print("\nLoading ISQ data...")
    attr_by_key = load_isq_data(ISQ_CSV)
    print(f"✓ Loaded {len(attr_by_key)} attribute keys")
    
    # Calculate samples per task
    samples_per_task = {
        task: int(TOTAL_SAMPLES * ratio)
        for task, ratio in TASK_DISTRIBUTION.items()
    }
    
    print(f"\nGenerating {TOTAL_SAMPLES} samples:")
    for task, count in samples_per_task.items():
        print(f"  • {task}: {count} samples")
    
    # Generate samples
    all_samples = []
    
    # ISQ Extraction
    print("\nGenerating ISQ extraction samples...")
    for i in range(samples_per_task["isq_extraction"]):
        sample = generate_isq_sample(attr_by_key)
        all_samples.append(sample)
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1}/{samples_per_task['isq_extraction']}")
    
    # Query Correction
    print("\nGenerating query correction samples...")
    for i in range(samples_per_task["query_correction"]):
        sample = generate_query_correction_sample()
        all_samples.append(sample)
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1}/{samples_per_task['query_correction']}")
    
    # Translation
    print("\nGenerating translation samples...")
    for i in range(samples_per_task["translation"]):
        sample = generate_translation_sample()
        all_samples.append(sample)
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1}/{samples_per_task['translation']}")
    
    # Shuffle
    print("\nShuffling samples...")
    random.shuffle(all_samples)
    
    # Split train/val
    split_idx = int(len(all_samples) * 0.9)
    train_samples = all_samples[:split_idx]
    val_samples = all_samples[split_idx:]
    
    # Save
    print(f"\nSaving files...")
    with open(OUTPUT_TRAIN, 'w', encoding='utf-8') as f:
        for sample in train_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    print(f"✓ Saved {OUTPUT_TRAIN} ({len(train_samples)} samples)")
    
    with open(OUTPUT_VAL, 'w', encoding='utf-8') as f:
        for sample in val_samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    print(f"✓ Saved {OUTPUT_VAL} ({len(val_samples)} samples)")
    
    # Summary
    print("\n" + "=" * 60)
    print("✓ Multi-task dataset generation complete!")
    print("=" * 60)
    print(f"\nTask distribution in training set:")
    task_counts = defaultdict(int)
    for sample in train_samples:
        task_counts[sample['task']] += 1
    for task, count in sorted(task_counts.items()):
        print(f"  • {task}: {count} ({count/len(train_samples)*100:.1f}%)")
    
    print(f"\nFiles created:")
    print(f"  - {OUTPUT_TRAIN}")
    print(f"  - {OUTPUT_VAL}")
    print(f"\nTo train multi-task model:")
    print(f"  python finetune_gemma2_9b.py  (update TRAIN_FILE/VAL_FILE)")

if __name__ == "__main__":
    generate_multitask_dataset()
