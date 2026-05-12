"""
Batch MCAT Inference — Unsloth Model
======================================
Reads : 76cat_queries  (header: query)
Output: unsloth_mcat_results.csv  (keyword, mcat_name, mcat_id)

Run:
  python batch_inference_unsloth.py
"""

import csv
import json
import re
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# ── CONFIG ─────────────────────────────────────────────────────────────────────
QUERIES_FILE   = "76cat_queries"
OUTPUT_CSV     = "unsloth_mcat_results.csv"
# Model is in the same directory as this script
MODEL_DIR      = str(Path(__file__).resolve().parent / "mcat-gemma2-9b-unsloth")
BASE_MODEL_DIR = "/home3/indiamart/func_gemma/models/gemma-2-9b-it"
MAX_NEW_TOKENS = 64
# ───────────────────────────────────────────────────────────────────────────────

INSTRUCTION_TEMPLATE = (
    "You are a product classification expert for an industrial marketplace. "
    "Given the product name below, identify the correct motor category (MCAT).\n\n"
    "Product Name: {product_name}\n\n"
    "Respond with a JSON object containing exactly two keys: 'mcat_name' and 'mcat_id'."
)


def load_model():
    print("Loading tokenizer...")
    print(f"  MODEL_DIR  = {MODEL_DIR}")
    print(f"  BASE_MODEL = {BASE_MODEL_DIR}")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_DIR, trust_remote_code=True, use_fast=False, local_files_only=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Loading base model in 4-bit NF4...")
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
        local_files_only=True,
    )

    print("Loading LoRA adapter (Unsloth-trained)...")
    model = PeftModel.from_pretrained(base_model, MODEL_DIR, local_files_only=True)
    model.eval()
    print("Model ready.\n")
    return model, tokenizer


def predict(model, tokenizer, product_name: str) -> dict:
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
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )
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
    return {"mcat_name": "", "mcat_id": "", "parse_error": generated}


def main():
    # Load queries (skip header)
    queries_path = Path(QUERIES_FILE)
    with open(queries_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        queries = [row["query"].strip() for row in reader if row["query"].strip()]
    print(f"Loaded {len(queries)} queries from {QUERIES_FILE}")

    model, tokenizer = load_model()

    results = []
    for i, q in enumerate(queries, 1):
        result = predict(model, tokenizer, q)
        row = {
            "keyword":   q,
            "mcat_name": result.get("mcat_name", ""),
            "mcat_id":   result.get("mcat_id", ""),
        }
        results.append(row)
        print(f"[{i:>4}/{len(queries)}] {q[:60]:<60}  →  {row['mcat_name']} ({row['mcat_id']})")

    # Write CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["keyword", "mcat_name", "mcat_id"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSaved {len(results)} rows → {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
