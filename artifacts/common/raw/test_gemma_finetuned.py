"""
Test Fine-tuned Gemma Model
Validates the model outputs correct keys matching QMeans
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import json

MODEL_DIR = "./gemma_qmeans_finetuned"

print("="*80)
print("TESTING FINE-TUNED GEMMA MODEL")
print("="*80)

# Load model
print("\nLoading fine-tuned model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR,
    torch_dtype=torch.float16,
    device_map="auto"
)
print(" Model loaded")

# Test queries
test_queries = [
    "Blown Film Extrusion Machine",
    "sheet extruder machine",
    "Gold Refinery Plant",
    "lab extruder",
    "fully automatic extruder machine",
    "plastic extrusion plant",
    "twin screw extruder",
    "manual silver refining plant",
    "hdpe blown film machine",
    "mono layer extruder"
]

print("\n" + "="*80)
print("TEST RESULTS")
print("="*80)

for query in test_queries:
    instruction = f"Extract key-value attributes from this query: {query}"
    prompt = f"{instruction}\n\nOutput:"
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            temperature=0.1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Extract output after "Output:"
    if "Output:" in response:
        output = response.split("Output:")[-1].strip()
    else:
        output = response
    
    print(f"\nQuery: {query}")
    print(f"Output: {output}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print("\nExpected: JSON dict with QMeans keys (type, usage, material, automation grade, etc.)")
print("Validate: Keys should match QMeans vocabulary (not \"runner\", \"triple_co_extrusion\", etc.)")
