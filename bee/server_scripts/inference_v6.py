"""
V6 batch inference — flat JSON attribute extraction.

Reads v4_inputs.jsonl (1000 queries), runs Gemma-4 E4B V6,
outputs v6_flat_results.jsonl in same format as qmeans:
  {"query": "...", "attributes": {"part type": "motor", ...}}

Usage:
  CUDA_VISIBLE_DEVICES=0 python inference_v6.py --part 1  # queries 0-499
  CUDA_VISIBLE_DEVICES=1 python inference_v6.py --part 2  # queries 500-999

If no --part flag: runs all 1000 on whatever GPU is visible.
"""

import os, sys, json, re, argparse
sys.path = [p for p in sys.path if "python3.9" not in p]

import torch
import unsloth  # noqa
from unsloth import FastModel

MODEL_PATH   = "/home3/indiamart/isq-gemma4-e4b-v6"
INPUT_FILE   = "/home3/indiamart/gemma_4/v4_inputs.jsonl"
OUT_PART1    = "/home3/indiamart/gemma_4/v6_flat_results_part1.jsonl"
OUT_PART2    = "/home3/indiamart/gemma_4/v6_flat_results_part2.jsonl"
OUT_FULL     = "/home3/indiamart/gemma_4/v6_flat_results.jsonl"

MAX_NEW_TOKENS = 200
BATCH_SIZE     = 8

CANONICAL_KEYS = (
    "part type, brand, driven type, model name/number, feature, usage, "
    "power source, phase, horsepower, power, series, rpm, starter type, "
    "voltage, size, mounting type, quantity, location/city, material, "
    "current, weight, frame size, efficiency, stroke length, orientation, "
    "shape, frequency, grade, torque, poles, color, displacement, "
    "application, shaft diameter, insulation class, ip rating, cooling type, "
    "capacity"
)

SYSTEM_PROMPT = (
    "You are a product attribute extractor for IndiaMART (B2B marketplace). "
    "Given a search query, extract all product attributes and return ONLY a "
    "compact JSON object.\n\n"
    "CRITICAL RULES:\n"
    "1. Use ONLY these exact key names (no synonyms, no variations):\n"
    f"   {CANONICAL_KEYS}\n"
    "2. Do NOT use: type, motor type, motor power, speed, automation grade, "
    "machine type, technology, country of origin, rated speed, or any key "
    "not in the list above.\n"
    "3. Only include attributes actually present in the query.\n"
    "4. Output ONLY the JSON — no explanation, no code fences.\n\n"
    "Examples of CORRECT keys: "
    "part type (not 'type'), driven type (not 'motor type'), "
    "rpm (not 'speed'), power (not 'motor power'), "
    "model name/number (not 'model number')"
)


def build_prompt(query: str, tokenizer) -> str:
    messages = [{"role": "user", "content": f"{SYSTEM_PROMPT}\n\nQuery: {query}"}]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )


_JSON_RE = re.compile(r'\{[^{}]*\}', re.DOTALL)

def parse_flat(text: str) -> dict:
    """Extract the first valid JSON dict from generated text."""
    text = re.sub(r'```(?:json)?', '', text).strip()
    m = _JSON_RE.search(text)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    # fallback: try the whole text
    try:
        return json.loads(text)
    except Exception:
        return {}


def run_inference(queries: list[str], out_path: str):
    print(f"\nLoading model from {MODEL_PATH} ...")
    model, tokenizer = FastModel.from_pretrained(
        model_name=MODEL_PATH,
        max_seq_length=512,
        load_in_4bit=True,
        load_in_8bit=False,
        full_finetuning=False,
    )
    FastModel.for_inference(model)

    prompts = [build_prompt(q, tokenizer) for q in queries]
    results = []

    print(f"Running inference on {len(prompts)} queries (batch={BATCH_SIZE}) ...")
    for i in range(0, len(prompts), BATCH_SIZE):
        batch_p  = prompts[i:i+BATCH_SIZE]
        batch_q  = queries[i:i+BATCH_SIZE]
        inputs   = tokenizer(text=batch_p, return_tensors="pt", padding=True,
                             truncation=True, max_length=512).to("cuda")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=0.1,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        for j, (q, out_ids) in enumerate(zip(batch_q, outputs)):
            in_len  = inputs["input_ids"].shape[1]
            new_ids = out_ids[in_len:]
            text    = tokenizer.decode(new_ids, skip_special_tokens=True).strip()
            attrs   = parse_flat(text)
            results.append({"query": q, "attributes": attrs, "raw": text})

        if (i // BATCH_SIZE) % 10 == 0:
            print(f"  {i+len(batch_p)}/{len(prompts)} done ...")

    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Saved {len(results)} results → {out_path}")


def merge_parts():
    rows = []
    for path in [OUT_PART1, OUT_PART2]:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
    with open(OUT_FULL, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Merged {len(rows)} rows → {OUT_FULL}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", type=int, choices=[1, 2], default=None,
                        help="1 = queries 0-499, 2 = queries 500-999, omit = all")
    parser.add_argument("--merge", action="store_true",
                        help="Merge part1+part2 into full results file")
    args = parser.parse_args()

    if args.merge:
        merge_parts()
        sys.exit(0)

    # Load queries
    all_queries = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                all_queries.append(r.get("query", r.get("instruction", "")).strip())

    if args.part == 1:
        queries  = all_queries[:500]
        out_path = OUT_PART1
    elif args.part == 2:
        queries  = all_queries[500:]
        out_path = OUT_PART2
    else:
        queries  = all_queries
        out_path = OUT_FULL

    run_inference(queries, out_path)
