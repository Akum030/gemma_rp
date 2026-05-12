import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
import json

MODEL_PATH = "./isq-gemma2-9b-finetuned-v4-priority"
BASE_MODEL = "google/gemma-2-9b-it"

# 10 test queries
TEST_QUERIES = [
    "siemens 1.5 kw 415v three phase motor",
    "abb 3 hp single phase 230v motor",
    "crompton 2.2 kw bldc servo motor ip55",
    "5hp three phase 1440 rpm foot mounted motor",
    "stepper motor nema 23 1.8 degree",
    "baldor 10 hp 3 phase 460v 1800 rpm tefc motor",
    "2 hp single phase capacitor start motor 220v",
    "ge 7.5 kw squirrel cage induction motor ie3",
    "brushless dc motor 24v 3000 rpm encoder",
    "oriental motor gearhead 25w 200v reducer 1:10"
]

def load_model():
    print("Loading model...")
    
    bnb_config = BitsAndBytesConfig(
        load_in_8bit=True,
        bnb_8bit_compute_dtype=torch.float16
    )
    
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )
    
    model = PeftModel.from_pretrained(base_model, MODEL_PATH)
    
    print("✓ Model loaded\n")
    return model, tokenizer

def predict(model, tokenizer, query):
    instruction = f"""Extract product attributes from the search query and provide them in JSON format with multiple key alternatives and priorities.

Query: {query}

Output format:
{{"attributes": [{{"attribute_key": "key_name", "value": "extracted_value", "key_priority": 1-4, "attribute_priority": 1-N}}]}}"""

    messages = [{"role": "user", "content": instruction}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=768,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    return response.strip()

def main():
    model, tokenizer = load_model()
    
    print("=" * 90)
    print("🎯 GEMMA V4 - RAW JSON OUTPUT TEST (10 Queries)")
    print("=" * 90)
    print()
    
    results = []
    
    for idx, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'='*90}")
        print(f"Query #{idx}: {query}")
        print('='*90)
        
        raw_output = predict(model, tokenizer, query)
        
        print("\n📄 RAW MODEL OUTPUT:")
        print("-" * 90)
        print(raw_output)
        print("-" * 90)
        
        # Try to parse and pretty print
        try:
            # Try to extract JSON if there's extra text
            if '{' in raw_output and '}' in raw_output:
                json_start = raw_output.find('{')
                json_end = raw_output.rfind('}') + 1
                json_str = raw_output[json_start:json_end]
                parsed = json.loads(json_str)
                
                print("\n✅ PARSED JSON:")
                print(json.dumps(parsed, indent=2))
                
                # Count unique values and total keys
                unique_values = set()
                total_keys = 0
                for attr in parsed.get('attributes', []):
                    unique_values.add(attr.get('value', ''))
                    total_keys += 1
                
                print(f"\n📊 Stats: {len(unique_values)} unique values, {total_keys} total keys")
                
                results.append({
                    'query': query,
                    'success': True,
                    'unique_values': len(unique_values),
                    'total_keys': total_keys,
                    'raw_output': raw_output,
                    'parsed_json': parsed
                })
            else:
                print("\n❌ No JSON found in output")
                results.append({
                    'query': query,
                    'success': False,
                    'raw_output': raw_output
                })
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON Parse Error: {e}")
            results.append({
                'query': query,
                'success': False,
                'error': str(e),
                'raw_output': raw_output
            })
        
        print()
    
    # Summary
    print("\n" + "=" * 90)
    print("📊 SUMMARY")
    print("=" * 90)
    
    successful = [r for r in results if r.get('success', False)]
    print(f"✅ Successful extractions: {len(successful)}/{len(TEST_QUERIES)}")
    
    if successful:
        avg_values = sum(r['unique_values'] for r in successful) / len(successful)
        avg_keys = sum(r['total_keys'] for r in successful) / len(successful)
        print(f"📈 Avg unique values per query: {avg_values:.1f}")
        print(f"📈 Avg total keys per query: {avg_keys:.1f}")
    
    # Save full results
    output_file = "raw_output_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Full results saved to: {output_file}")
    print()

if __name__ == "__main__":
    main()
