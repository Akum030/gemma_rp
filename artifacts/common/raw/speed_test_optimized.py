"""Quick 5-query speed test with optimized settings"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
import time

MODEL_PATH = "./isq-gemma2-9b-finetuned-v4-priority"
BASE_MODEL = "google/gemma-2-9b-it"

TEST_QUERIES = [
    "siemens 1.5 kw motor",
    "3 hp crompton motor",
    "dc motor 12v",
    "servo motor 750w",
    "stepper motor nema 17"
]

print("Loading model...")
t0 = time.time()

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
model.eval()

print(f"✓ Model loaded in {time.time() - t0:.1f}s\n")

print("=" * 80)
print("SPEED TEST: 5 queries with OPTIMIZED settings")
print("=" * 80)

times = []
for i, query in enumerate(TEST_QUERIES, 1):
    instruction = f"""Extract product attributes from this search query. Return ONLY valid JSON, no extra text.

Query: {query}

JSON format:
{{"attributes": [{{"attribute_key": "key", "value": "val", "key_priority": 1-3, "attribute_priority": 1-N}}]}}"""

    messages = [{"role": "user", "content": instruction}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(model.device)

    t_start = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=False,
            num_beams=1,
            use_cache=True,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    elapsed = time.time() - t_start
    times.append(elapsed)

    response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
    output_tokens = len(outputs[0]) - inputs['input_ids'].shape[1]

    print(f"[{i}/5] {query}")
    print(f"      Time: {elapsed:.2f}s | Output tokens: {output_tokens}")
    print(f"      Response: {response[:100]}...")
    print()

    del inputs, outputs
    torch.cuda.empty_cache()

print("=" * 80)
print(f"Average time: {sum(times)/len(times):.2f}s per query")
print(f"Min: {min(times):.2f}s | Max: {max(times):.2f}s")
print(f"Expected for 642 queries: {(sum(times)/len(times) * 642) / 60:.1f} minutes")
print("=" * 80)

if sum(times)/len(times) > 20:
    print("\n⚠️  WARNING: Avg time >20s indicates GPU performance issue!")
    print("   Check: GPU model, CUDA drivers, memory bandwidth")
elif sum(times)/len(times) > 10:
    print("\n⚡ Performance acceptable but could be better (10-20s)")
else:
    print("\n✅ EXCELLENT: Speed is optimal (<10s per query)")
