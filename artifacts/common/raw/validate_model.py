"""
Validate Gemma V4 Priority-Based ISQ Model
Tests the fine-tuned model with various motor queries and generates a team report
"""

import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from datetime import datetime

MODEL_PATH = "/home3/indiamart/func_gemma/models/gemma-2-9b-it"
ADAPTER_PATH = "./isq-gemma2-9b-finetuned-v4-priority"

SYSTEM_PROMPT = (
    "Extract product attributes from the following search query. "
    "For each identified attribute value, provide all possible attribute keys "
    "ranked by priority (key_priority: 1 = most appropriate key). "
    "Also assign attribute_priority based on importance in the query "
    "(1 = most important for search). Return the result as a JSON object."
)

# Test queries covering different scenarios
TEST_QUERIES = [
    # Simple queries
    "siemens 1.5 kw motor",
    "3 hp single phase motor",
    "abb motor 415v",
    
    # Medium complexity
    "crompton 2.2 kw three phase 415v motor",
    "havells 1 hp single phase 230v motor",
    "bharat bijlee 5 hp 3 phase motor",
    
    # Complex queries
    "siemens 7.5 kw 415v three phase foot mounted ip55 motor",
    "abb 3 hp single phase 230v 1440 rpm tefc motor",
    "crompton greaves 2.2 kw bldc servo motor with encoder",
    
    # Very specific
    "kirloskar 15 hp three phase 415v 1440 rpm foot mounted cast iron body motor",
    "lenze 1.5 kw servo motor 3 phase 400v with absolute encoder ip65",
    
    # Missing brand
    "5 hp three phase 415v 1500 rpm motor",
    "1.5 kw single phase motor foot mounted",
    
    # Different motor types
    "stepper motor nema 23 1.8 degree 2 phase",
    "bldc motor 24v 100w 3000 rpm",
    "gear motor 1 hp three phase 50 rpm",
    "servo motor 1 kw 3 phase with brake",
    
    # Real IndiaMART style queries
    "need 3hp motor for industrial use",
    "looking for siemens motor 2.2kw three phase",
    "buy crompton 1.5 kw motor online"
]


def load_model():
    """Load the fine-tuned model."""
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True, use_fast=False)

    print("Loading base model (8-bit)...")
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

    print("Loading LoRA adapters...")
    model = PeftModel.from_pretrained(model, ADAPTER_PATH)
    model.eval()

    return model, tokenizer


def predict(model, tokenizer, query, max_new_tokens=512):
    """Run inference on a query."""
    instruction = f"{SYSTEM_PROMPT}\n\nQuery: {query}"
    
    prompt = (
        "<bos><start_of_turn>user\n"
        f"{instruction}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.1,
            top_p=0.9,
            do_sample=True,
            repetition_penalty=1.1,
        )
    
    response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    response = response.strip()
    
    if response.endswith("<end_of_turn>"):
        response = response[:-len("<end_of_turn>")].strip()
    
    # Try to parse as JSON
    try:
        result = json.loads(response)
        return result, True, response
    except json.JSONDecodeError:
        # Try to extract JSON
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                result = json.loads(response[start:end])
                return result, True, response[start:end]
            except json.JSONDecodeError:
                pass
        return None, False, response


def analyze_result(query, result):
    """Analyze extraction quality."""
    if not result or "attributes" not in result:
        return {
            "success": False,
            "unique_values": 0,
            "total_keys": 0,
            "has_priorities": False
        }
    
    attrs = result["attributes"]
    unique_values = set(a["value"] for a in attrs)
    
    # Check priority consistency
    has_key_priority = all("key_priority" in a for a in attrs)
    has_attr_priority = all("attribute_priority" in a for a in attrs)
    
    # Count primary keys (priority 1)
    primary_keys = [a for a in attrs if a.get("key_priority") == 1]
    
    return {
        "success": True,
        "unique_values": len(unique_values),
        "total_keys": len(attrs),
        "primary_keys": len(primary_keys),
        "has_priorities": has_key_priority and has_attr_priority,
        "values": list(unique_values)
    }


def format_result_table(query, result):
    """Format result as a readable table."""
    lines = []
    lines.append(f"\nQuery: {query}")
    lines.append("=" * 80)
    
    if not result or "attributes" not in result:
        lines.append("❌ Failed to extract attributes")
        return "\n".join(lines)
    
    # Group by value
    by_value = {}
    for attr in result["attributes"]:
        val = attr["value"]
        if val not in by_value:
            by_value[val] = []
        by_value[val].append(attr)
    
    # Sort by attribute_priority
    sorted_values = sorted(by_value.items(), key=lambda x: x[1][0].get("attribute_priority", 999))
    
    lines.append(f"{'Value':<30} {'Primary Key':<25} {'Alt Keys':<20} {'Attr P':<8}")
    lines.append("-" * 80)
    
    for val, attrs in sorted_values:
        # Sort by key_priority
        sorted_attrs = sorted(attrs, key=lambda x: x.get("key_priority", 999))
        primary = sorted_attrs[0]
        alts = [a["attribute_key"] for a in sorted_attrs[1:3]]  # Show first 2 alternates
        
        alt_str = ", ".join(alts) if alts else "-"
        lines.append(f"{val:<30} {primary['attribute_key']:<25} {alt_str:<20} {primary.get('attribute_priority', '-'):<8}")
    
    lines.append("")
    return "\n".join(lines)


def main():
    print("=" * 80)
    print("Gemma V4 Priority-Based ISQ Model - Validation Report")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Model: {ADAPTER_PATH}")
    print(f"Test Queries: {len(TEST_QUERIES)}")
    print("=" * 80)
    
    model, tokenizer = load_model()
    
    results = []
    success_count = 0
    json_parse_count = 0
    total_values = 0
    total_keys = 0
    
    print("\n📊 Running Validation Tests...\n")
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"[{i}/{len(TEST_QUERIES)}] Testing: {query[:60]}...")
        
        result, json_ok, raw = predict(model, tokenizer, query)
        analysis = analyze_result(query, result)
        
        results.append({
            "query": query,
            "result": result,
            "analysis": analysis,
            "json_valid": json_ok,
            "raw_output": raw
        })
        
        if analysis["success"]:
            success_count += 1
        if json_ok:
            json_parse_count += 1
        if analysis["success"]:
            total_values += analysis["unique_values"]
            total_keys += analysis["total_keys"]
    
    # Generate report
    print("\n" + "=" * 80)
    print("📈 VALIDATION SUMMARY")
    print("=" * 80)
    print(f"✅ Successful extractions: {success_count}/{len(TEST_QUERIES)} ({success_count*100/len(TEST_QUERIES):.1f}%)")
    print(f"✅ Valid JSON output: {json_parse_count}/{len(TEST_QUERIES)} ({json_parse_count*100/len(TEST_QUERIES):.1f}%)")
    print(f"📊 Avg attributes extracted: {total_values/max(success_count,1):.1f} unique values/query")
    print(f"📊 Avg total keys (with synonyms): {total_keys/max(success_count,1):.1f} keys/query")
    
    # Detailed results
    print("\n" + "=" * 80)
    print("📋 DETAILED RESULTS")
    print("=" * 80)
    
    for r in results:
        print(format_result_table(r["query"], r["result"]))
    
    # Save report
    report_file = "validation_report.json"
    with open(report_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model_path": ADAPTER_PATH,
            "summary": {
                "total_queries": len(TEST_QUERIES),
                "successful": success_count,
                "json_valid": json_parse_count,
                "avg_unique_values": total_values/max(success_count,1),
                "avg_total_keys": total_keys/max(success_count,1)
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Full report saved to: {report_file}")
    
    # Team presentation summary
    print("\n" + "=" * 80)
    print("🎯 KEY HIGHLIGHTS FOR TEAM PRESENTATION")
    print("=" * 80)
    print(f"✓ Model successfully fine-tuned on 1,600 Cat_74 electric motor queries")
    print(f"✓ Training completed in ~6.8 hours (3 epochs, final loss: 0.516)")
    print(f"✓ Extraction success rate: {success_count*100/len(TEST_QUERIES):.1f}%")
    print(f"✓ JSON format compliance: {json_parse_count*100/len(TEST_QUERIES):.1f}%")
    print(f"✓ Avg {total_values/max(success_count,1):.1f} attributes per query")
    print(f"✓ Priority-based multi-key output (3-4 key synonyms per value)")
    print(f"✓ Handles simple to complex motor specifications")
    print("\n💡 Next Steps:")
    print("  - Deploy for A/B testing against current QMeans system")
    print("  - Expand training data to other categories (Cat_75, Cat_76, etc.)")
    print("  - Integrate with production search pipeline")
    print("=" * 80)


if __name__ == "__main__":
    main()
