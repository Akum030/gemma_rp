"""
V5 batch inference — flat JSON attribute extraction.

Reads v4_inputs.jsonl (1000 queries), runs Gemma-4 E4B V5-flat,
outputs v5_flat_results.jsonl in same format as qmeans:
  {"query": "...", "attributes": {"part type": "motor", ...}}

Usage:
  CUDA_VISIBLE_DEVICES=0 python inference_v5.py --part 1  # queries 0-499
  CUDA_VISIBLE_DEVICES=1 python inference_v5.py --part 2  # queries 500-999

If no --part flag: runs all 1000 on whatever GPU is visible.
"""

import os, sys, json, re, argparse
sys.path = [p for p in sys.path if "python3.9" not in p]

import torch
import unsloth  # noqa
from unsloth import FastModel

MODEL_PATH   = "/home3/indiamart/isq-gemma4-e4b-v5-flat"
INPUT_FILE   = "/home3/indiamart/gemma_4/v4_inputs.jsonl"
OUT_PART1    = "/home3/indiamart/gemma_4/v5_flat_results_part1.jsonl"
OUT_PART2    = "/home3/indiamart/gemma_4/v5_flat_results_part2.jsonl"
OUT_FULL     = "/home3/indiamart/gemma_4/v5_flat_results.jsonl"

MAX_NEW_TOKENS = 180
BATCH_SIZE     = 8   # flat JSON is shorter than nested → bigger batch OK

SYSTEM_PROMPT = (
    "You are a product attribute extractor for IndiaMART (B2B marketplace). "
    "Given a search query, extract all product attributes and return ONLY a "
    "compact JSON object. Use standard IndiaMART attribute keys such as: "
    "part type, brand, model name/number, power, voltage, phase, speed, usage, "
    "material, size, color, series, driven type, power source, rpm, frequency, "
    "capacity, mounting type, ip rating, insulation class, torque, automation grade, "
    "quantity, dimension, weight, country of origin, horsepower, rated speed, "
    "frame size, shape, orientation, certification, application. "
    "Only include attributes actually present in the query. "
    "Output ONLY the JSON — no explanation, no code fences."
)


def build_prompt(query: str) -> str:
    return (
        "<start_of_turn>user\n"
        f"{SYSTEM_PROMPT}\n\n"
        f"Query: {query}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )


_JSON_RE = re.compile(r'\{[^{}]*\}', re.DOTALL)

def parse_flat(text: str) -> dict:
    """Extract the first valid JSON dict from generated text."""
    # strip any code fences
    text = re.sub(r'```(?:json)?', '', text).strip()
    m = _JSON_RE.search(text)
    if m:
        try:
            d = json.loads(m.group())
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    # try entire stripped text
    try:
        d = json.loads(text.strip())
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", type=int, choices=[1, 2], default=None,
                        help="1=first 500, 2=second 500")
    args = parser.parse_args()

    # Load queries
    queries = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line)["query"])
    print(f"Total queries: {len(queries)}")

    if args.part == 1:
        subset = queries[:500]
        out_path = OUT_PART1
        print("Running PART 1 (queries 0-499)")
    elif args.part == 2:
        subset = queries[500:]
        out_path = OUT_PART2
        print("Running PART 2 (queries 500-999)")
    else:
        subset = queries
        out_path = OUT_FULL
        print("Running ALL queries")

    # Skip already-done
    done = set()
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["query"])
                except Exception:
                    pass
    print(f"Already done: {len(done)}, remaining: {len(subset) - len(done)}")

    # Load model
    print("Loading V5 model ...")
    model, tokenizer = FastModel.from_pretrained(
        model_name=MODEL_PATH,
        max_seq_length=512,
        load_in_4bit=True,
        full_finetuning=False,
    )
    FastModel.for_inference(model)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Get EOS token ids
    inner_tok = getattr(tokenizer, "tokenizer", tokenizer)
    end_of_turn_id = inner_tok.convert_tokens_to_ids("<end_of_turn>")
    eos_ids = list({inner_tok.eos_token_id, end_of_turn_id} - {None})
    print(f"eos_token_ids: {eos_ids}")

    remaining = [q for q in subset if q not in done]

    with open(out_path, "a", encoding="utf-8") as fout:
        for batch_start in range(0, len(remaining), BATCH_SIZE):
            batch = remaining[batch_start: batch_start + BATCH_SIZE]
            prompts = [build_prompt(q) for q in batch]

            enc = tokenizer(text=prompts, return_tensors="pt",
                            padding=True, truncation=True, max_length=512)
            enc = {k: v.cuda() for k, v in enc.items()}

            with torch.no_grad():
                out_ids = model.generate(
                    **enc,
                    max_new_tokens=MAX_NEW_TOKENS,
                    eos_token_id=eos_ids,
                    do_sample=False,
                    temperature=1.0,
                    repetition_penalty=1.1,
                )

            input_len = enc["input_ids"].shape[1]
            for i, q in enumerate(batch):
                new_ids = out_ids[i][input_len:]
                raw = tokenizer.decode(new_ids, skip_special_tokens=True).strip()
                attrs = parse_flat(raw)
                fout.write(json.dumps({"query": q, "attributes": attrs,
                                       "raw": raw}, ensure_ascii=False) + "\n")
                fout.flush()

            done_count = batch_start + len(batch)
            if done_count % 100 == 0 or done_count >= len(remaining):
                print(f"  [{done_count}/{len(remaining)}] last: {batch[-1][:60]!r}")

    print(f"\nDone → {out_path}")


if __name__ == "__main__":
    main()
