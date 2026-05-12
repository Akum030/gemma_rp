"""Check if model is actually on GPU and GPU specifications"""
import torch
print("=" * 80)
print("GPU DIAGNOSTIC")
print("=" * 80)

# Check CUDA availability
print(f"\nCUDA Available: {torch.cuda.is_available()}")
if not torch.cuda.is_available():
    print("❌ CRITICAL: CUDA not available! Model running on CPU!")
    exit(1)

# GPU count and details
print(f"GPU Count: {torch.cuda.device_count()}")
for i in range(torch.cuda.device_count()):
    print(f"\nGPU {i}: {torch.cuda.get_device_name(i)}")
    props = torch.cuda.get_device_properties(i)
    print(f"  Compute Capability: {props.major}.{props.minor}")
    print(f"  Total Memory: {props.total_memory / 1024**3:.2f} GB")
    print(f"  Multiprocessors: {props.multi_processor_count}")

# Current GPU memory usage
print(f"\nCurrent Device: {torch.cuda.current_device()}")
print(f"Memory Allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
print(f"Memory Reserved: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")

print("\n" + "=" * 80)
print("Loading model to check device placement...")
print("=" * 80)

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
import time

MODEL_PATH = "./isq-gemma2-9b-finetuned-v4-priority"
BASE_MODEL = "google/gemma-2-9b-it"

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

print(f"\n✓ Model loaded in {time.time() - t0:.1f}s")

# Check model device placement
print("\nModel Device Placement:")
param_count = 0
gpu_count = 0
cpu_count = 0

for name, param in model.named_parameters():
    param_count += 1
    if param.device.type == 'cuda':
        gpu_count += 1
    else:
        cpu_count += 1

print(f"  Total parameters: {param_count}")
print(f"  On GPU: {gpu_count} ({gpu_count*100/param_count:.1f}%)")
print(f"  On CPU: {cpu_count} ({cpu_count*100/param_count:.1f}%)")

if cpu_count > 0:
    print("  ⚠️  WARNING: Some parameters on CPU! This will slow inference.")

print(f"\nGPU Memory After Model Load:")
print(f"  Allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
print(f"  Reserved: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")

# Quick token generation speed test
print("\n" + "=" * 80)
print("TOKEN GENERATION SPEED TEST")
print("=" * 80)

test_query = "siemens 1.5 kw motor"
instruction = f"""Extract product attributes from this search query. Return ONLY valid JSON, no extra text.

Query: {test_query}

JSON format:
{{"attributes": [{{"attribute_key": "key", "value": "val", "key_priority": 1-3, "attribute_priority": 1-N}}]}}"""

messages = [{"role": "user", "content": instruction}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(model.device)

print(f"\nInput tokens: {inputs['input_ids'].shape[1]}")

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

output_tokens = len(outputs[0]) - inputs['input_ids'].shape[1]
tokens_per_sec = output_tokens / elapsed

print(f"Output tokens: {output_tokens}")
print(f"Time: {elapsed:.2f}s")
print(f"Speed: {tokens_per_sec:.1f} tokens/second")

print("\n" + "=" * 80)
print("PERFORMANCE ASSESSMENT")
print("=" * 80)

if tokens_per_sec < 5:
    print("❌ CRITICAL: <5 tok/s - GPU severely underperforming or model on CPU")
    print("   Expected: 10-50+ tok/s on decent GPU")
    print("   Action: Check GPU model, drivers, or consider different hardware")
elif tokens_per_sec < 10:
    print("⚠️  SLOW: 5-10 tok/s - Weak GPU or bottleneck")
    print("   This will take 10-20 hours for 1000 queries")
elif tokens_per_sec < 20:
    print("⚡ ACCEPTABLE: 10-20 tok/s - Budget GPU performance")
    print("   Expect 5-10 hours for 1000 queries")
else:
    print("✅ GOOD: 20+ tok/s - Decent GPU performance")
    print("   Expect 2-5 hours for 1000 queries")

print(f"\nEstimated time for 642 remaining queries:")
print(f"  ~{(642 * elapsed) / 3600:.1f} hours")

print("\n" + "=" * 80)
