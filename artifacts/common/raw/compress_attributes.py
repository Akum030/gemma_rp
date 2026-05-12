import pandas as pd
from collections import Counter

# Configuration
INPUT_CSV = "unique_key_val_96_cat.csv"
OUTPUT_ISQ = "compressed_attributes_isq.txt"
TOP_N_KEYS = 500  # Keep top 500 most frequent attribute keys
MAX_VALUES_PER_KEY = 15  # Max 15 values per attribute key

def compress_attributes():
    """Compress 11k attributes to top 500 most frequent"""
    
    print(f"Reading attributes from: {INPUT_CSV}")
    
    # Read CSV - first two columns
    df = pd.read_csv(INPUT_CSV, header=None)
    
    print(f"Total rows: {len(df)}")
    
    # Get columns
    attr_keys = df.iloc[:, 0].dropna()  # Column A: attribute names
    attr_values = df.iloc[:, 1].dropna()  # Column B: attribute values
    
    # Count frequency of each attribute key
    key_counter = Counter(attr_keys)
    
    print(f"\nTotal unique attribute keys: {len(key_counter)}")
    print(f"Total attribute pairs: {len(df)}")
    
    # Get top N most frequent keys
    top_keys = [key for key, count in key_counter.most_common(TOP_N_KEYS)]
    
    print(f"\nKeeping top {TOP_N_KEYS} most frequent attribute keys")
    print(f"\nTop 20 most frequent attributes:")
    for i, (key, count) in enumerate(key_counter.most_common(20), 1):
        print(f"  {i}. {key}: {count} occurrences")
    
    # Build compressed attribute dictionary
    compressed_attrs = {}
    
    for attr_key, attr_value in zip(df.iloc[:, 0], df.iloc[:, 1]):
        if pd.isna(attr_key) or pd.isna(attr_value):
            continue
        
        attr_key = str(attr_key).strip()
        attr_value = str(attr_value).strip()
        
        # Only keep if in top keys
        if attr_key in top_keys:
            if attr_key not in compressed_attrs:
                compressed_attrs[attr_key] = []
            
            # Add unique values only, up to max limit
            if attr_value not in compressed_attrs[attr_key] and len(compressed_attrs[attr_key]) < MAX_VALUES_PER_KEY:
                compressed_attrs[attr_key].append(attr_value)
    
    # Convert to ISQ format
    isq_list = []
    for attr_key, values in compressed_attrs.items():
        for value in values:
            isq = f"{value}:{attr_key}:specification"
            isq_list.append(isq)
    
    print(f"\nCompression Results:")
    print(f"  Original: {len(df)} attribute pairs")
    print(f"  Compressed: {len(isq_list)} attribute pairs")
    print(f"  Reduction: {((len(df) - len(isq_list)) / len(df) * 100):.1f}%")
    print(f"  Unique keys: {len(compressed_attrs)}")
    
    # Save to file
    with open(OUTPUT_ISQ, 'w', encoding='utf-8') as f:
        for isq in isq_list:
            f.write(isq + '\n')
    
    print(f"\n[DONE] Compressed ISQ format saved to: {OUTPUT_ISQ}")
    print(f"\n[NEXT STEPS]")
    print(f"1. Open {OUTPUT_ISQ}")
    print(f"2. Copy ALL lines")
    print(f"3. Paste into gemini_with_dataset_fixed.py in ATTRIBUTE_DATASET section")
    print(f"4. Run: python gemini_with_dataset_fixed.py")
    
    # Show sample
    print(f"\nFirst 10 compressed ISQs:")
    for isq in isq_list[:10]:
        print(f"  {isq}")
    
    print(f"\nEstimated tokens per prompt: ~{len(isq_list) * 8} tokens")
    print(f"Should work within 30K TPM limit! ✓")

if __name__ == "__main__":
    compress_attributes()
