"""
Inference script — MCAT Classification
=======================================
Uses the fine-tuned Gemma-2 9B model (4-bit NF4 + LoRA) to predict
mcat_name + mcat_id from a free-text product name query.

Usage:
  python inference_mcat.py --query "siemens 1.5 kw three phase motor"
  python inference_mcat.py --file queries.txt   # one product name per line
"""

import argparse
import json
import re
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

MODEL_DIR      = "./mcat-gemma2-9b-finetuned"
BASE_MODEL_DIR = "/home3/indiamart/func_gemma/models/gemma-2-9b-it"
MAX_NEW_TOKENS = 64   # JSON output is short

INSTRUCTION_TEMPLATE = (
    "You are a product classification expert for an industrial marketplace. "
    "Given the product name below, identify the correct motor category (MCAT).\n\n"
    "Product Name: {product_name}\n\n"
    "Respond with a JSON object containing exactly two keys: 'mcat_name' and 'mcat_id'."
)


def load_model(model_dir: str):
    """Load fine-tuned model and tokenizer using transformers + 4-bit NF4."""
    print(f"Loading tokenizer from: {model_dir}")
    tokenizer = AutoTokenizer.from_pretrained(
        model_dir, trust_remote_code=True, use_fast=False
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading base model in 4-bit NF4 ...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_DIR,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    print(f"Loading LoRA adapter from: {model_dir}")
    model = PeftModel.from_pretrained(base_model, model_dir)
    model.eval()

    print("Model loaded.\n")
    return model, tokenizer


def predict(model, tokenizer, product_name: str) -> dict:
    """Return dict with mcat_name and mcat_id."""
    instruction = INSTRUCTION_TEMPLATE.format(product_name=product_name)
    prompt = (
        "<bos><start_of_turn>user\n"
        f"{instruction}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens     = MAX_NEW_TOKENS,
            do_sample          = False,
            repetition_penalty = 1.1,
            pad_token_id       = tokenizer.eos_token_id,
        )

    # Decode only the newly generated tokens
    generated = tokenizer.decode(
        output_ids[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True,
    ).strip()

    try:
        return json.loads(generated)
    except json.JSONDecodeError:
        match = re.search(r"\{.*?\}", generated, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        return {"raw_output": generated, "parse_error": True}


def main():
    parser = argparse.ArgumentParser(description="MCAT Inference")
    parser.add_argument("--query", type=str, help="Single product name query")
    parser.add_argument("--file",  type=str, help="Text file with one query per line")
    parser.add_argument("--model", type=str, default=MODEL_DIR,
                        help="Path to fine-tuned LoRA adapter directory")
    args = parser.parse_args()

    if not args.query and not args.file:
        parser.print_help()
        sys.exit(1)

    model, tokenizer = load_model(args.model)

    if args.query:
        result = predict(model, tokenizer, args.query)
        print(json.dumps({"query": args.query, **result}, indent=2, ensure_ascii=False))

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            queries = [line.strip() for line in f if line.strip()]

        print(f"Running {len(queries)} queries from {args.file} ...\n")
        results = []
        for q in queries:
            r = predict(model, tokenizer, q)
            entry = {"query": q, **r}
            results.append(entry)
            print(json.dumps(entry, ensure_ascii=False))

        out_path = args.file.replace(".txt", "_mcat_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(results)} results → {out_path}")


if __name__ == "__main__":
    main()
