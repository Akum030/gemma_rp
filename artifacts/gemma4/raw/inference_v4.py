"""
Inference script for Gemma 2 9B fine-tuned V4 (Priority-Based ISQ)
Tests the model with a query and outputs JSON with key_priority + attribute_priority
"""

import argparse
import json
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


def load_model():
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

    # Clean up response
    response = response.strip()
    if response.endswith("<end_of_turn>"):
        response = response[:-len("<end_of_turn>")].strip()

    # Try to parse as JSON
    try:
        result = json.loads(response)
        return result, response
    except json.JSONDecodeError:
        # Try to extract JSON from response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                result = json.loads(response[start:end])
                return result, response[start:end]
            except json.JSONDecodeError:
                pass
        return None, response


def main():
    parser = argparse.ArgumentParser(description="Test ISQ extraction with priority")
    parser.add_argument("--query", type=str, default="siemens 1.5 kw 415v three phase motor",
                        help="Search query to extract attributes from")
    args = parser.parse_args()

    model, tokenizer = load_model()

    print(f"\n{'='*60}")
    print(f"Query: {args.query}")
    print(f"{'='*60}")

    result, raw = predict(model, tokenizer, args.query)

    if result:
        print("\n✓ Parsed JSON output:")
        print(json.dumps(result, indent=2))

        # Summary table
        if "attributes" in result:
            print(f"\n{'='*60}")
            print(f"{'Value':<25} {'Key (P1)':<20} {'Key P':<6} {'Attr P':<6}")
            print(f"{'-'*60}")
            seen_values = set()
            for attr in result["attributes"]:
                val = attr.get("value", "")
                if val not in seen_values:
                    seen_values.add(val)
                    # Find all key synonyms for this value
                    keys_for_val = [a for a in result["attributes"] if a["value"] == val]
                    primary = keys_for_val[0]
                    print(f"{val:<25} {primary['attribute_key']:<20} {primary['key_priority']:<6} {primary['attribute_priority']:<6}")
                    for alt in keys_for_val[1:]:
                        print(f"{'':25} {alt['attribute_key']:<20} {alt['key_priority']:<6}")
    else:
        print("\n⚠ Could not parse JSON. Raw output:")
        print(raw)

    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
