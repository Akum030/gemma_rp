"""
V7 priority inference — load Gemma-4 E4B + V7 LoRA adapters and extract
priority-nested attributes from queries.

Usage:
  python inference_v7.py                       # runs built-in sample queries
  python inference_v7.py --queries q1.jsonl    # one query per line in JSONL
  python inference_v7.py --query "45 hp 3 phase siemens motor"
"""
import os, sys, json, argparse, time
sys.path = [p for p in sys.path if "python3.9" not in p]

import unsloth                                   # noqa: F401
from unsloth import FastModel
import torch

ADAPTER_PATH = "/home3/indiamart/gemma_4/isq-gemma4-e4b-v7-priority"
BASE_MODEL   = "/home3/indiamart/gemma_4/models/gemma-4-e4b-it"
MAX_LENGTH   = 768

INSTRUCTION = (
    "Extract product attributes from the search query. Return JSON with key "
    "\"attributes\" = list of objects. Each object has ONE field "
    "\"attribute_priorityN\" (N=1 most important to user intent, N=2 next, ...). "
    "That field is itself an object with \"value\" (extracted text) and "
    "\"key_priority1\", \"key_priority2\", \"key_priority3\", ... ranking "
    "synonym key names from most preferred to least.\n"
    "Rules: extract only what is in the query; lowercase values except "
    "model/part numbers; group every synonym for the same value under one "
    "attribute_priority object; rank attributes by user intent "
    "(brand > product type > primary spec > model > phase/voltage > speed > "
    "frequency > mounting/IP > insulation > others)."
)

SAMPLES = [
    "siemens 45 hp 3 phase 1440 rpm motor",
    "crompton greaves 5 kw single phase 50hz induction motor",
    "abb model m2qa132s4a 7.5 kw foot mounted ip55",
    "havells 1 hp 220v single phase water pump",
    "kirloskar 100 hp 3 phase 415v 1500 rpm",
    "stainless steel 304 centrifugal pump 5 hp",
    "1.5 hp ceiling fan crompton 1200mm white",
    "bonfiglioli helical gearbox 7.5 kw 100 rpm",
]

def build_prompt(query: str) -> str:
    return (
        "<start_of_turn>user\n"
        f"{INSTRUCTION}\n\nQuery: {query}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", type=str, default=None)
    ap.add_argument("--queries", type=str, default=None,
                    help="JSONL file: one {'query':...} per line, OR plain text one query per line")
    ap.add_argument("--out", type=str, default="/home3/indiamart/gemma_4/v7_inference_results.jsonl")
    ap.add_argument("--max_new_tokens", type=int, default=512)
    args = ap.parse_args()

    # collect queries
    queries = []
    if args.query:
        queries = [args.query]
    elif args.queries:
        with open(args.queries, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    q = obj.get("query") or obj.get("instruction") or obj.get("text")
                    if q: queries.append(q)
                except json.JSONDecodeError:
                    queries.append(line)
    else:
        queries = SAMPLES

    print(f"Loading base model + V7 LoRA adapter ...")
    model, tokenizer = FastModel.from_pretrained(
        model_name=ADAPTER_PATH if os.path.exists(os.path.join(ADAPTER_PATH, "adapter_config.json")) else BASE_MODEL,
        max_seq_length=MAX_LENGTH,
        load_in_4bit=True,
        full_finetuning=False,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    FastModel.for_inference(model)

    print(f"Running on {len(queries)} queries ...\n")
    out_f = open(args.out, "w", encoding="utf-8")
    for i, q in enumerate(queries, 1):
        prompt = build_prompt(q)
        inputs = tokenizer(text=prompt, return_tensors="pt").to(model.device)
        t0 = time.time()
        with torch.no_grad():
            out_ids = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                temperature=1.0,
                pad_token_id=tokenizer.pad_token_id,
            )
        dt = time.time() - t0
        gen = tokenizer.decode(out_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        # strip end-of-turn
        gen = gen.replace("<end_of_turn>", "").strip()
        # try parse json
        parsed = None
        try:
            parsed = json.loads(gen)
        except Exception:
            pass
        rec = {"query": q, "raw": gen, "parsed": parsed, "secs": round(dt, 2)}
        out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        out_f.flush()
        print(f"[{i}/{len(queries)}] ({dt:.1f}s) {q}")
        print(f"   -> {gen[:300]}")
        print()
    out_f.close()
    print(f"Done. Results -> {args.out}")

if __name__ == "__main__":
    main()
