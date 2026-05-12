"""
Test Gemma 2 9B ISQ Model - Inference Script
Load trained model and test on sample queries
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import json

# Configuration
BASE_MODEL_PATH = "/home3/indiamart/func_gemma/models/gemma-2-9b-it"
FINETUNED_MODEL_PATH = "./isq-gemma2-9b-finetuned"

# Test queries
TEST_QUERIES = [
    "twin screw extruder 440v three phase automatic stainless steel body 50 kg/hr capacity",
    "looking for gold refining plant with 99% purity, 5 tpd capacity, made in india",
    "industrial solvent extraction plant, brand kabra, 415v, automatic grade, hdpe body",
    "blown film machine 380v 3 phase 10 hp power 60 micron thickness",
    "silver refinery machine with 100 kg capacity, single phase, mild steel construction"
]

def load_model():
    """Load fine-tuned model"""
    print("=" * 60)
    print("Loading Gemma 2 9B ISQ Model")
    print("=" * 60)
    
    print("\nLoading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        FINETUNED_MODEL_PATH,
        trust_remote_code=True
    )
    
    print("Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        load_in_8bit=True  # Match training config
    )
    
    print("Loading LoRA adapters...")
    model = PeftModel.from_pretrained(
        base_model,
        FINETUNED_MODEL_PATH,
        torch_dtype=torch.bfloat16
    )
    
    model.eval()
    print("✓ Model loaded successfully!\n")
    
    return model, tokenizer

def extract_isqs(model, tokenizer, query):
    """Extract ISQs from product query"""
    
    # Format prompt
    instruction = f"""Extract ISQs from the following product description.

Product description:
\"\"\"{query}\"\"\"

Return output in JSON format only."""
    
    prompt = (
        "<bos><start_of_turn>user\n"
        f"{instruction}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )
    
    # Tokenize
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512
    ).to(model.device)
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.1,  # Low temperature for deterministic output
            top_p=0.95,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    # Decode
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract JSON part
    if "<start_of_turn>model" in response:
        response = response.split("<start_of_turn>model")[-1].strip()
    
    return response

def validate_json(output):
    """Check if output is valid JSON"""
    try:
        parsed = json.loads(output)
        return True, parsed
    except:
        return False, None

def main():
    # Load model
    model, tokenizer = load_model()
    
    print("=" * 60)
    print("Testing ISQ Extraction")
    print("=" * 60)
    
    success_count = 0
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'─' * 60}")
        print(f"Test {i}/{len(TEST_QUERIES)}")
        print(f"{'─' * 60}")
        print(f"Query: {query}\n")
        
        # Extract ISQs
        output = extract_isqs(model, tokenizer, query)
        print(f"Output:\n{output}\n")
        
        # Validate
        is_valid, parsed = validate_json(output)
        if is_valid:
            print("✓ Valid JSON")
            print(f"Extracted {len(parsed)} attributes:")
            for key, value in parsed.items():
                print(f"  • {key}: {value}")
            success_count += 1
        else:
            print("✗ Invalid JSON - needs refinement")
    
    print(f"\n{'=' * 60}")
    print(f"Results: {success_count}/{len(TEST_QUERIES)} valid outputs ({success_count/len(TEST_QUERIES)*100:.1f}%)")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
