"""
Improved Gemma 4 batch inference (v3-ready):
  * Greedy decoding (deterministic - prevents part-number rewrites like 6dr5->6dr3)
  * No repetition_penalty / no_repeat_ngram (caused JSON syntax breakage)
  * EOS-aware generation, longer max_new_tokens for big attribute lists
  * Strict JSON extraction (handles trailing junk like </start_of_turn>)
  * Optional canonical-key normalization against the 69-key training vocabulary
  * Argparse: choose model path, output paths, key-normalize on/off

Usage:
  python gemma4_batch_inference_v3.py \
      --model /home3/indiamart/isq-gemma4-e4b-v2 \
      --queries /home3/indiamart/gemma_4/76cat_queries \
      --out_csv /home3/indiamart/gemma_4/agent/v2_clean_results.csv \
      --out_jsonl /home3/indiamart/gemma_4/agent/v2_clean_results.jsonl
"""
import argparse, csv, json, os, re, sys, time

sys.path = [p for p in sys.path if "python3.9" not in p]

import torch
from unsloth import FastModel
from transformers import StoppingCriteria, StoppingCriteriaList


class JsonBalancedStop(StoppingCriteria):
    """Stop generation as soon as the decoded text contains a balanced {...} JSON."""
    def __init__(self, tokenizer, prompt_len: int):
        self.tok = tokenizer
        self.prompt_len = prompt_len
        self.last_check = 0

    def __call__(self, input_ids, scores, **kwargs):
        gen = input_ids[0, self.prompt_len:]
        n = gen.shape[0]
        # check periodically (every 4 new tokens) for speed
        if n - self.last_check < 4:
            return False
        self.last_check = n
        text = self.tok.decode(gen, skip_special_tokens=False)
        depth = 0
        started = False
        for ch in text:
            if ch == "{":
                depth += 1; started = True
            elif ch == "}":
                depth -= 1
                if started and depth == 0:
                    return True
        return False


# ── 69-key canonical vocabulary derived from product_train_with_keys.jsonl ────
CANON_KEYS = {
    "frequency","die type","automation grade","power","motor power","weight","process",
    "location/city","usage","operation","place of origin","number of layers","storage material",
    "processing type","shape","country of origin","voltage","types of metal","series","brand",
    "suitable for","size","type of namkeen","name of extract","machine name","technology",
    "machine type","metal","driven type","purity","refining material","power source",
    "screw diameter","blower type","part type","product","botanical name","orientation",
    "power consumption","model name/number","rated speed","material","capacity","color",
    "phase","horsepower","speed","feature","grade","packaging size","model number",
    "voltage rating","current","insulation class","mounting type","frame size","rpm",
    "torque","efficiency","ip rating","duty cycle","cooling type","starter type",
    "shaft diameter","poles","temperature range","application","quantity","dimension",
    "warranty",
}

# common aliases observed in v2 outputs -> canonical key
KEY_ALIASES = {
    "brand/series": "brand",
    "brand/seller": "brand",
    "brand/make":   "brand",
    "Brand":        "brand",
    "Motor":        "part type",
    "motor":        "part type",
    "motor type":   "driven type",
    "fan":          "part type",
    "actuator":     "part type",
    "encoder":      "part type",
    "kit":          "part type",
    "control board":"part type",
    "Model":        "model name/number",
    "model":        "model name/number",
    "model_number": "model name/number",
    "model number": "model name/number",
    "part_number":  "model name/number",
    "part number":  "model name/number",
    "product_code": "model name/number",
    "code":         "model name/number",
    "hp":           "horsepower",
    "power_source": "power source",
    "country_of_origin": "country of origin",
    "place_of_origin":   "place of origin",
    "location":     "location/city",
    "voltage_rating":"voltage rating",
    "size/weight":  "size",
    "number":       "size",
    "key":          None,            # drop
    "key_attributes": None,
    "attribute":    None,
    "attributes":   None,
    "query":        None,
}

def normalize_keys(parsed: dict, *, drop_unknown: bool = False) -> dict:
    """Map aliases -> canonical key; optionally drop keys not in CANON_KEYS."""
    out: dict = {}
    for k, v in parsed.items():
        if not isinstance(k, str):
            continue
        kl = k.strip()
        # alias rewrite
        if kl in KEY_ALIASES:
            new = KEY_ALIASES[kl]
            if new is None:
                continue
            kl = new
        # case fold to lower for canonical match
        kl_lower = kl.lower()
        for ck in CANON_KEYS:
            if ck == kl_lower:
                kl = ck; break
        else:
            if drop_unknown and kl_lower not in CANON_KEYS:
                continue
        # value coercion: list -> "; ".join, otherwise str
        if isinstance(v, list):
            v = "; ".join(str(x) for x in v)
        elif not isinstance(v, str):
            v = str(v)
        v = v.strip()
        if not v:
            continue
        if kl not in out:           # keep first occurrence
            out[kl] = v
    return out


JSON_OBJ_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)

def extract_json(raw: str) -> dict | None:
    """Tolerant JSON extraction. Try strict parse, then balanced-brace scan,
    then a last-ditch repair (drop tokens without colon)."""
    # cut off chat-template echoes
    for stop in ("<start_of_turn>", "<end_of_turn>", "</start_of_turn>"):
        idx = raw.find(stop)
        if idx >= 0:
            raw = raw[:idx]
    raw = raw.strip()

    # try the first {...} block via brace balance
    start = raw.find("{")
    if start < 0:
        return None
    depth = 0
    end = -1
    for i, ch in enumerate(raw[start:], start):
        if ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    candidate = raw[start:end] if end > 0 else raw[start:] + "}"
    try:
        return json.loads(candidate)
    except Exception:
        pass

    # repair: keep only "key":"value" pairs
    pairs = re.findall(r'"([^"]+)"\s*:\s*("[^"]*"|\[[^\]]*\]|true|false|null|-?\d+(?:\.\d+)?)', candidate)
    if not pairs:
        # repair2: try BARE-KEY pattern  {key: "value", key2: "value2"}
        # also handles  {key: value} with bare values up to , or }
        pairs2 = re.findall(
            r'([A-Za-z_][\w \-/]*?)\s*:\s*(?:"([^"]*)"|([A-Za-z0-9_.\-/ ]+?))(?=[,}])',
            candidate,
        )
        if pairs2:
            out = {}
            for k, qv, bv in pairs2:
                k = k.strip().lstrip("{").strip()
                v = (qv if qv else bv).strip()
                if not k or not v:
                    continue
                out.setdefault(k, v)
            return out if out else None
        return None
    rebuilt = "{" + ",".join(f'"{k}":{v}' for k, v in pairs) + "}"
    try:
        return json.loads(rebuilt)
    except Exception:
        return None


def build_prompt(query: str) -> str:
    return (
        "<start_of_turn>user\n"
        f"Extract key-value attributes from this query: {query}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )


def load_queries(path: str) -> list[str]:
    out = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            q = line.strip()
            if not q: continue
            if i == 0 and q.lower() == "query":
                continue
            out.append(q)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--queries", required=True)
    ap.add_argument("--out_csv", required=True)
    ap.add_argument("--out_jsonl", required=True)
    ap.add_argument("--max_new_tokens", type=int, default=96)
    ap.add_argument("--max_seq_length", type=int, default=384)
    ap.add_argument("--normalize_keys", action="store_true",
                    help="Map aliases to canonical 69-key vocab (post-process)")
    ap.add_argument("--drop_unknown_keys", action="store_true",
                    help="Drop keys not in CANON_KEYS (after alias rewrite)")
    ap.add_argument("--debug_first", type=int, default=0,
                    help="Print raw decoded output (with special tokens) for the first N queries")
    ap.add_argument("--no_endturn_eos", action="store_true",
                    help="Do NOT include <end_of_turn> in EOS tokens (lets generation continue past it)")
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--adapter", default=None, help="Optional LoRA adapter dir (loaded on top of base model)")
    ap.add_argument("--base_model", default=None, help="Base model dir (used when --adapter is set)")
    args = ap.parse_args()

    if args.adapter:
        base = args.base_model or args.model
        print(f"Loading base model {base} (4-bit) + adapter {args.adapter} ...")
        t0 = time.time()
        model, tokenizer = FastModel.from_pretrained(
            model_name=base,
            max_seq_length=args.max_seq_length,
            load_in_4bit=True,
        )
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter)
        FastModel.for_inference(model)
        print(f"Base+adapter loaded in {time.time()-t0:.1f}s")
    else:
        print(f"Loading model from {args.model} ...")
        t0 = time.time()
        model, tokenizer = FastModel.from_pretrained(
            model_name=args.model,
            max_seq_length=args.max_seq_length,
            load_in_4bit=True,
        )
        FastModel.for_inference(model)
        print(f"Model loaded in {time.time()-t0:.1f}s")

    queries = load_queries(args.queries)
    if args.limit:
        queries = queries[: args.limit]
    print(f"Inference on {len(queries)} queries")

    os.makedirs(os.path.dirname(args.out_csv), exist_ok=True)
    csv_f = open(args.out_csv, "w", newline="", encoding="utf-8")
    jsonl_f = open(args.out_jsonl, "w", encoding="utf-8")
    writer = csv.writer(csv_f)
    writer.writerow(["query", "ok", "key_count", "raw_output", "attributes_json", "norm_attributes_json"])

    # Gemma4 returns a Processor that wraps the real text tokenizer
    text_tok = getattr(tokenizer, "tokenizer", tokenizer)
    eos_ids = set()
    for tid in (getattr(text_tok, "eos_token_id", None),
                getattr(tokenizer, "eos_token_id", None)):
        if tid is not None:
            eos_ids.add(tid)
    try:
        end_turn = text_tok.convert_tokens_to_ids("<end_of_turn>")
        if isinstance(end_turn, int) and end_turn >= 0 and end_turn != getattr(text_tok, "unk_token_id", -1):
            if not args.no_endturn_eos:
                eos_ids.add(end_turn)
    except Exception:
        pass
    eos_list = sorted(eos_ids) if eos_ids else None
    pad_id = getattr(text_tok, "eos_token_id", None) or getattr(tokenizer, "eos_token_id", None)

    n_ok = 0
    total = 0.0
    for i, q in enumerate(queries):
        prompt = build_prompt(q)
        enc = tokenizer(text=prompt, return_tensors="pt").to("cuda")
        in_len = enc["input_ids"].shape[1]
        stop = StoppingCriteriaList([JsonBalancedStop(text_tok, in_len)])
        t0 = time.time()
        with torch.no_grad():
            out = model.generate(
                **enc,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,                # GREEDY - deterministic
                temperature=1.0,                # ignored when do_sample=False
                pad_token_id=pad_id,
                eos_token_id=eos_list,
                stopping_criteria=stop,
            )
        dt = time.time() - t0
        total += dt
        raw = text_tok.decode(out[0][in_len:], skip_special_tokens=False)
        if i < args.debug_first:
            print(f"DEBUG[{i}] q={q!r}")
            print(f"  full_raw={raw!r}")
            print(f"  gen_token_ids={out[0][in_len:].tolist()[:30]}")
        # strip trailing <end_of_turn> / pad
        raw_clean = raw.split("<end_of_turn>")[0].split("<eos>")[0].strip()
        parsed = extract_json(raw_clean)
        ok = parsed is not None
        if ok: n_ok += 1
        norm = normalize_keys(parsed or {},
                              drop_unknown=args.drop_unknown_keys) if args.normalize_keys else (parsed or {})
        writer.writerow([
            q, ok, len(parsed or {}),
            raw_clean.replace("\n", " ")[:300],
            json.dumps(parsed or {}, ensure_ascii=False),
            json.dumps(norm, ensure_ascii=False),
        ])
        csv_f.flush()
        jsonl_f.write(json.dumps({
            "query": q, "ok": ok, "raw": raw_clean,
            "attributes": parsed or {}, "norm_attributes": norm,
        }, ensure_ascii=False) + "\n")
        jsonl_f.flush()
        if (i + 1) % 25 == 0:
            avg = total / (i + 1)
            eta = avg * (len(queries) - i - 1) / 60
            print(f"[{i+1}/{len(queries)}] ok={n_ok} avg={avg:.2f}s eta={eta:.1f}min  q={q[:50]}")
        del enc, out
        if (i + 1) % 50 == 0:
            torch.cuda.empty_cache()

    csv_f.close(); jsonl_f.close()
    print(f"\nDONE  ok={n_ok}/{len(queries)} ({n_ok*100/max(1,len(queries)):.1f}%)  total={total/60:.1f}min")
    print(f"  -> {args.out_csv}")
    print(f"  -> {args.out_jsonl}")

if __name__ == "__main__":
    main()
