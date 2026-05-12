"""
Test Fine-tuned Gemma 2 9B V3 Model
Compare with QMeans ground truth and calculate key overlap metrics
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import pandas as pd
import json
from collections import defaultdict
import re

# Model paths
MODEL_PATH = "./isq-gemma2-9b-finetuned-v3"
TEST_FILE = "ground_truth_100_queries.csv"

print("=" * 60)
print("Loading Gemma 2 9B V3 Fine-tuned Model")
print("=" * 60)

print("\nLoading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
model.eval()

print("✓ Model loaded successfully!")

def extract_attributes_gemma(query):
    """Extract attributes using Gemma V3"""
    prompt = f"Extract key-value attributes from this query: {query}"
    
    formatted_prompt = (
        "<bos><start_of_turn>user\n"
        f"{prompt}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )
    
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract JSON from response
    try:
        # Find JSON in response
        match = re.search(r'\{[^}]+\}', response)
        if match:
            json_str = match.group(0)
            attributes = json.loads(json_str)
            return attributes
        return {}
    except:
        return {}

def parse_qmeans_isq(isq_pipe):
    """Parse Ground Truth ISQ format: value:key:specification"""
    attributes = {}
    if pd.isna(isq_pipe):
        return attributes
    
    items = isq_pipe.split('|')
    for item in items:
        parts = item.split(':')
        if len(parts) >= 2:
            value = parts[0].strip()
            key = parts[1].strip()
            if key and value:
                attributes[key] = value
    
    return attributes

def calculate_metrics(gemma_attrs, ground_truth_attrs):
    """Calculate key overlap and value match metrics"""
    gemma_keys = set(gemma_attrs.keys())
    gt_keys = set(ground_truth_attrs.keys())
    
    # Key metrics
    common_keys = gemma_keys & gt_keys
    key_overlap = len(common_keys) / len(gt_keys) * 100 if gt_keys else 0
    
    # Value match for common keys
    value_matches = 0
    for key in common_keys:
        if gemma_attrs[key].lower().strip() == ground_truth_attrs[key].lower().strip():
            value_matches += 1
    
    value_match_rate = value_matches / len(common_keys) * 100 if common_keys else 0
    
    # Extraction volume
    gemma_count = len(gemma_keys)
    gt_count = len(gt_keys)
    
    return {
        'key_overlap_pct': key_overlap,
        'value_match_pct': value_match_rate,
        'gemma_keys': gemma_count,
        'ground_truth_keys': gt_count,
        'common_keys': len(common_keys),
        'gemma_only_keys': len(gemma_keys - gt_keys),
        'ground_truth_only_keys': len(gt_keys - gemma_keys)
    }

# Load test data
print("\n" + "=" * 60)
print("Loading test data from ground_truth_100_queries.csv")
print("=" * 60)

df = pd.read_csv(TEST_FILE)
print(f"Total test queries: {len(df)}")

# Filter successful Ground Truth results
df_test = df[df['success'] == True]  # Use all successful queries
print(f"Testing on {len(df_test)} queries with Ground Truth")

# Run tests
print("\n" + "=" * 60)
print("Running Tests")
print("=" * 60)

results = []
all_gemma_keys = set()
all_gt_keys = set()

for idx, row in df_test.iterrows():
    query = row['query']
    gt_isq = row['ground_truth_isq_pipe']
    
    # Get predictions
    gemma_attrs = extract_attributes_gemma(query)
    gt_attrs = parse_qmeans_isq(gt_isq)
    
    # Track all keys
    all_gemma_keys.update(gemma_attrs.keys())
    all_gt_keys.update(gt_attrs.keys())
    
    # Calculate metrics
    metrics = calculate_metrics(gemma_attrs, gt_attrs)
    
    results.append({
        'query': query,
        'gemma_attrs': gemma_attrs,
        'ground_truth_attrs': gt_attrs,
        **metrics
    })
    
    if (idx + 1) % 10 == 0:
        print(f"  Processed {idx + 1}/{len(df_test)} queries...")

# Calculate overall metrics
print("\n" + "=" * 60)
print("OVERALL METRICS")
print("=" * 60)

avg_key_overlap = sum(r['key_overlap_pct'] for r in results) / len(results)
avg_value_match = sum(r['value_match_pct'] for r in results) / len(results)
avg_gemma_extraction = sum(r['gemma_keys'] for r in results) / len(results)
avg_gt_extraction = sum(r['ground_truth_keys'] for r in results) / len(results)

print(f"\n📊 Key Overlap Rate: {avg_key_overlap:.2f}%")
print(f"   (vs Ground Truth)")

print(f"\n✓ Value Match Rate: {avg_value_match:.2f}%")
print(f"   (Among matched keys)")

print(f"\n📈 Extraction Volume:")
print(f"   Gemma V3: {avg_gemma_extraction:.2f} attributes/query")
print(f"   Ground Truth: {avg_gt_extraction:.2f} attributes/query")

print(f"\n🔑 Key Coverage:")
print(f"   Gemma V3 uses {len(all_gemma_keys)} unique keys")
print(f"   Ground Truth uses {len(all_gt_keys)} unique keys")
print(f"   Common keys: {len(all_gemma_keys & all_gt_keys)}")

# Show sample results
print("\n" + "=" * 60)
print("SAMPLE RESULTS (First 5 queries)")
print("=" * 60)

for i in range(min(5, len(results))):
    r = results[i]
    print(f"\n[Query {i+1}]: {r['query'][:80]}...")
    print(f"  Gemma V3: {r['gemma_attrs']}")
    print(f"  Ground Truth: {r['ground_truth_attrs']}")
    print(f"  Key Overlap: {r['key_overlap_pct']:.1f}% | Value Match: {r['value_match_pct']:.1f}%")

# Save detailed results
results_df = pd.DataFrame(results)
output_file = "gemma_v3_test_results.csv"
results_df.to_csv(output_file, index=False)

print("\n" + "=" * 60)
print("✓ Testing Complete!")
print("=" * 60)
print(f"\nDetailed results saved to: {output_file}")

# Success check
if avg_key_overlap >= 70:
    print("\n🎉 SUCCESS! Key overlap >= 70% vs Ground Truth")
elif avg_key_overlap >= 50:
    print("\n✓ GOOD! Key overlap >= 50% vs Ground Truth")
else:
    print(f"\n⚠️ Key overlap {avg_key_overlap:.1f}% - Needs improvement")

print("\n" + "=" * 60)
