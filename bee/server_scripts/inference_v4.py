"""
V4 batch inference on bee/gold_1k_v2.jsonl queries.

Output:  bee/v4_priority_results.jsonl  (one row per query with the model's
         raw nested-JSON output and a parsed flat dict for comparator use).
"""
import os, sys, json, re, time
sys.path = [p for p in sys.path if "python3.9" not in p]

import unsloth                              # noqa: F401
import torch
from unsloth import FastModel
from transformers import TextStreamer

BASE_MODEL = "/home3/indiamart/gemma_4/models/gemma-4-e4b-it"
ADAPTER    = "/home3/indiamart/isq-gemma4-e4b-v4-priority"
QUERIES_IN = "/home3/indiamart/gemma_4/v4_inputs.jsonl"   # one {"query": ...} per line
OUT_PATH   = "/home3/indiamart/gemma_4/v4_priority_results.jsonl"

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

MAX_NEW_TOKENS = 220
BATCH_SIZE     = 4


def build_prompt(query: str, tokenizer) -> str:
    user = f"{INSTRUCTION}\n\nQuery: {query}"
    messages = [{"role": "user", "content": user}]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
    )


def parse_nested_to_flat(text: str) -> dict:
    """Extract first {...} JSON, return {key_priority1_value: value, ...} dict
    for comparator-friendly format. Returns empty {} on failure."""
    # find first balanced {...}
    start = text.find("{")
    if start < 0:
        return {}
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end < 0:
        return {}
    try:
        obj = json.loads(text[start:end])
    except Exception:
        return {}
    flat = {}
    for grp in obj.get("attributes", []):
        if not isinstance(grp, dict):
            continue
        for ap_key, payload in grp.items():
            if not isinstance(payload, dict):
                continue
            val = payload.get("value")
            kp1 = payload.get("key_priority1")
            if kp1 and val:
                flat[kp1] = val
    return flat


def main():
    # load queries
    queries = []
    with open(QUERIES_IN, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            queries.append(row["query"])
    print(f"queries: {len(queries)}")

    # model
    print("loading base + adapter ...")
    model, tokenizer = FastModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=1024,
        load_in_4bit=True,
        full_finetuning=False,
    )
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, ADAPTER)
    model.eval()
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"   # left pad for batched generation

    fout = open(OUT_PATH, "w", encoding="utf-8")
    t0 = time.time()
    # Stop tokens: end_of_turn (chat-style EOS) and the canonical eos.
    # Gemma4Processor wraps the real tokenizer at .tokenizer
    inner_tok = getattr(tokenizer, "tokenizer", tokenizer)
    end_of_turn_id = inner_tok.convert_tokens_to_ids("<end_of_turn>")
    eos_ids = list({inner_tok.eos_token_id, end_of_turn_id} - {None})
    print(f"eos token ids used for stopping: {eos_ids}")
    for batch_start in range(0, len(queries), BATCH_SIZE):
        batch = queries[batch_start: batch_start + BATCH_SIZE]
        prompts = [build_prompt(q, tokenizer) for q in batch]
        enc = tokenizer(text=prompts, return_tensors="pt",
                        padding=True, truncation=True,
                        max_length=512).to(model.device)
        with torch.no_grad():
            out = model.generate(
                **enc,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                temperature=1.0,
                use_cache=True,
                eos_token_id=eos_ids,
                pad_token_id=tokenizer.pad_token_id,
            )
        gens = tokenizer.batch_decode(out[:, enc.input_ids.shape[1]:],
                                      skip_special_tokens=True)
        for q, g in zip(batch, gens):
            flat = parse_nested_to_flat(g)
            fout.write(json.dumps({
                "query": q,
                "raw":   g.strip(),
                "flat":  flat,
            }, ensure_ascii=False) + "\n")
        fout.flush()
        done = batch_start + len(batch)
        elapsed = time.time() - t0
        rate = done / max(1.0, elapsed)
        eta  = (len(queries) - done) / max(0.001, rate)
        print(f"  [{done}/{len(queries)}]  {rate:.2f} q/s  ETA {eta/60:.1f} min")

    fout.close()
    print(f"DONE -> {OUT_PATH}")


if __name__ == "__main__":
    main()
