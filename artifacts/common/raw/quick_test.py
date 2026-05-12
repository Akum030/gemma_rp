"""
Quick test script - Run inference on a few queries for immediate demo
"""

import json
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

MODEL_PATH = "/home3/indiamart/func_gemma/models/gemma-2-9b-it"
ADAPTER_PATH = "./isq-gemma2-9b-finetuned-v4-priority"

SYSTEM_PROMPT = (
    "Extract product attributes from the following search query. "
    "For each identified attribute value, provide all possible attribute keys "
    "ranked by priority (key_priority: 1 = most appropriate key). "
    "Also assign attribute_priority based on importance in the query "
    "(1 = most important for search). Return the result as a JSON object."
)

# Quick demo queries
DEMO_QUERIES = [
    "siemens 1.5 kw 415v three phase motor",
    "abb 3 hp single phase 230v motor",
    "crompton 2.2 kw bldc servo motor ip55",
    "5hp three phase 1440 rpm foot mounted motor",
    "stepper motor nema 23 1.8 degree"
]


def load_model():
    print("Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True, use_fast=False)
    
    bnb_config = BitsAndBytesConfig(
        load_in_8bit=True,
        bnb_8bit_compute_dtype=torch.float16,
        bnb_8bit_use_double_quant=True,
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    
    model = PeftModel.from_pretrained(model, ADAPTER_PATH)
    model.eval()
    
    return model, tokenizer


def predict(model, tokenizer, query):
    instruction = f"{SYSTEM_PROMPT}\n\nQuery: {query}"
    prompt = f"<bos><start_of_turn>user\n{instruction}<end_of_turn>\n<start_of_turn>model\n"
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.1,
            top_p=0.9,
            do_sample=True,
            repetition_penalty=1.1,
        )
    
    response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    if response.endswith("<end_of_turn>"):
        response = response[:-len("<end_of_turn>")].strip()
    
    try:
        return json.loads(response), True
    except:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(response[start:end]), True
            except:
                pass
        return response, False


def display_result(query, result, is_json):
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    if not is_json:
        print("❌ Invalid JSON output")
        print(result[:500])
        return
    
    if "attributes" not in result:
        print("❌ No attributes found")
        return
    
    # Group by value
    by_value = {}
    for attr in result["attributes"]:
        val = attr["value"]
        if val not in by_value:
            by_value[val] = []
        by_value[val].append(attr)
    
    # Sort by attribute_priority
    sorted_values = sorted(by_value.items(), key=lambda x: x[1][0].get("attribute_priority", 999))
    
    print(f"\n{'Value':<25} {'Key (Priority 1)':<25} {'Alt Keys':<30} {'Attr P'}")
    print("-" * 80)
    
    for val, attrs in sorted_values:
        sorted_attrs = sorted(attrs, key=lambda x: x.get("key_priority", 999))
        primary = sorted_attrs[0]
        alts = ", ".join([a["attribute_key"] for a in sorted_attrs[1:3]])
        
        print(f"{val:<25} {primary['attribute_key']:<25} {alts:<30} {primary.get('attribute_priority', '-')}")
    
    print(f"\n✓ Extracted {len(sorted_values)} unique attributes")


def main():
    if len(sys.argv) > 1:
        # Single query from command line
        query = " ".join(sys.argv[1:])
        queries = [query]
    else:
        # Demo queries
        queries = DEMO_QUERIES
    
    print("=" * 80)
    print("🚀 Gemma V4 Priority-Based ISQ - Quick Test")
    print("=" * 80)
    
    model, tokenizer = load_model()
    print("✓ Model loaded\n")
    
    for query in queries:
        result, is_json = predict(model, tokenizer, query)
        display_result(query, result, is_json)
    
    print("\n" + "=" * 80)
    print("💡 Usage:")
    print("  Single query:  python quick_test.py siemens 1.5kw motor")
    print("  Demo queries:  python quick_test.py")
    print("=" * 80)


if __name__ == "__main__":
    main()
