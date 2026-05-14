"""
V7 inference + evaluation against gold and qmeans on the 1000 business queries.

Outputs:
  /home3/indiamart/gemma_4/v7_priority_results.jsonl
      one row per query: {query, raw, parsed, flat}
  /home3/indiamart/gemma_4/v7_eval_summary.json
      precision/recall/F1 of v7 vs gold and qmeans vs gold (key-level and value-level).

flat = {canonical_key: value} extracted from the nested priority output by
taking key_priority1 of each attribute_priorityN as the canonical key.
"""
import os, sys, json, time, re

# scrub py3.9 site-packages so unsloth's importlib_version probes don't fail
sys.path = [p for p in sys.path if "python3.9" not in p]

# stub out vllm to dodge unsloth's import_fixes.fix_vllm_aimv2_issue probing
import importlib.metadata as _md
_real_version = _md.version
def _safe_version(name):
    try:
        return _real_version(name)
    except _md.PackageNotFoundError:
        if name in ("vllm",):
            return "0.0.0"
        raise
_md.version = _safe_version

import unsloth                                   # noqa: F401
from unsloth import FastModel
import torch

ADAPTER = "/home3/indiamart/gemma_4/isq-gemma4-e4b-v7-priority"
QUERIES_FILE = "/home3/indiamart/gemma_4/76cat_queries"
GOLD_FILE    = "/home3/indiamart/gemma_4/gold_1k_v2.jsonl"
QMEANS_FILE  = "/home3/indiamart/gemma_4/qmeans_v2_results.jsonl"

OUT_RESULTS  = "/home3/indiamart/gemma_4/v7_priority_results.jsonl"
OUT_SUMMARY  = "/home3/indiamart/gemma_4/v7_eval_summary.json"

MAX_LENGTH   = 768
MAX_NEW      = 320

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


def build_prompt(q):
    return (
        "<start_of_turn>user\n"
        f"{INSTRUCTION}\n\nQuery: {q}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )


# ---------- normalization helpers for fair eval ----------
KEY_ALIASES = {
    "model_number": "model name/number",
    "model name": "model name/number",
    "model": "model name/number",
    "part_number": "model name/number",
    "model_name": "model name/number",
    "mpn": "model name/number",
    "manufacturer": "brand",
    "company": "brand",
    "make": "brand",
    "product_type": "part type",
    "product": "part type",
    "type": "part type",
    "category": "part type",
    "motor_type": "driven type",
    "machine_type": "driven type",
    "drive_type": "driven type",
    "wattage": "power",
    "kilowatt": "power",
    "kw": "power",
    "motor_power": "power",
    "power_rating": "power",
    "rated_power": "power",
    "horsepower": "power",
    "hp": "power",
    "speed": "rpm",
    "rated_speed": "rpm",
    "rotation_speed": "rpm",
    "revolutions_per_minute": "rpm",
    "rated_voltage": "voltage",
    "operating_voltage": "voltage",
    "voltage_rating": "voltage",
    "rated_current": "current",
    "amperage": "current",
    "ampere": "current",
    "frequency_hertz": "frequency",
    "operating_frequency": "frequency",
    "hz": "frequency",
    "no_of_phase": "phase",
    "number_of_phase": "phase",
    "phase_type": "phase",
    "no_of_poles": "poles",
    "number_of_poles": "poles",
    "pole_count": "poles",
    "ip_class": "ip rating",
    "ingress_protection": "ip rating",
    "protection_rating": "ip rating",
    "insulation_grade": "insulation class",
    "class_of_insulation": "insulation class",
    "ie_class": "efficiency",
    "energy_efficiency": "efficiency",
    "efficiency_class": "efficiency",
    "frame": "frame size",
    "mounting": "mounting type",
    "fixing_type": "mounting type",
    "installation_type": "mounting type",
    "cooling": "cooling type",
    "cooling_method": "cooling type",
    "body_material": "material",
    "construction_material": "material",
    "casing_material": "material",
    "colour": "color",
    "shade": "color",
    "suitable_for": "usage",
    "use_case": "usage",
    "purpose": "usage",
    "application": "usage",
    "starter": "starter type",
    "starting_method": "starter type",
    "fuel_type": "power source",
    "energy_source": "power source",
    "power_supply": "power source",
    "qty": "quantity",
    "count": "quantity",
    "no_of_units": "quantity",
    "size": "size",
    "dimension": "size",
    "physical_size": "size",
    "frame_size": "frame size",
    "shaft_size": "shaft diameter",
    "shaft": "shaft diameter",
    "stroke": "stroke length",
    "stroke_size": "stroke length",
    "swept_volume": "displacement",
    "volume_displacement": "displacement",
    "rated_torque": "torque",
    "torque_rating": "torque",
    "nm_torque": "torque",
    "rated_capacity": "capacity",
    "load_capacity": "capacity",
    "tank_capacity": "capacity",
    "model_series": "series",
    "product_series": "series",
    "city": "location/city",
    "place": "location/city",
    "region": "location/city",
    "location": "location/city",
}


def scalar_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = [scalar_text(item).strip() for item in value]
        return " ".join(part for part in parts if part)
    if isinstance(value, dict):
        for key in ("key", "name", "label", "value", "text"):
            text = scalar_text(value.get(key)).strip()
            if text:
                return text
        for item in value.values():
            text = scalar_text(item).strip()
            if text:
                return text
        return ""
    return str(value)


def canon_key(k):
    k = scalar_text(k).lower().strip().replace("_", " ")
    if not k:
        return ""
    # also try underscored form
    k_us = k.replace(" ", "_")
    if k in KEY_ALIASES:
        return KEY_ALIASES[k]
    if k_us in KEY_ALIASES:
        return KEY_ALIASES[k_us]
    return k


def norm_value(v):
    v = scalar_text(v).lower().strip()
    v = re.sub(r"\s+", " ", v)
    return v


def flatten_priority_output(parsed):
    """Take v7 nested output -> {canon_key: value} dict."""
    flat = {}
    if not isinstance(parsed, dict):
        return flat
    attrs = parsed.get("attributes")
    if not isinstance(attrs, list):
        return flat
    for item in attrs:
        if not isinstance(item, dict) or not item:
            continue
        # expect single key "attribute_priorityN"
        for ap_key, body in item.items():
            if not isinstance(body, dict):
                continue
            value = body.get("value", "")
            kp1 = body.get("key_priority1") or body.get("key_priority_1") or ""
            key = canon_key(kp1)
            value = norm_value(value)
            if key and value:
                flat[key] = value
    return flat


def flatten_flat_dict(d):
    out = {}
    if not isinstance(d, dict):
        return out
    for k, v in d.items():
        out[canon_key(k)] = norm_value(v)
    return out


def prf(pred, gold):
    """key-only and key+value precision/recall/f1 over a single example."""
    pk = set(pred.keys())
    gk = set(gold.keys())
    tp_k = len(pk & gk)
    pkv = {(k, pred[k]) for k in pk}
    gkv = {(k, gold[k]) for k in gk}
    tp_kv = len(pkv & gkv)
    return {
        "tp_k": tp_k, "fp_k": len(pk) - tp_k, "fn_k": len(gk) - tp_k,
        "tp_kv": tp_kv, "fp_kv": len(pk) - tp_kv, "fn_kv": len(gk) - tp_kv,
    }


def aggregate(stats):
    def f(prefix):
        tp = sum(s[f"tp_{prefix}"] for s in stats)
        fp = sum(s[f"fp_{prefix}"] for s in stats)
        fn = sum(s[f"fn_{prefix}"] for s in stats)
        p = tp / (tp + fp) if (tp + fp) else 0.0
        r = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4),
                "tp": tp, "fp": fp, "fn": fn}
    return {"key_only": f("k"), "key_value": f("kv")}


def parse_json_loose(txt):
    """try to parse model output as JSON, with light cleanup."""
    txt = txt.strip()
    # strip trailing incomplete tokens
    if txt.startswith("```"):
        txt = re.sub(r"^```(?:json)?\s*", "", txt)
        txt = re.sub(r"\s*```$", "", txt)
    try:
        return json.loads(txt)
    except Exception:
        pass
    # try to clip to outermost {...}
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def load_existing_results(path, gold, qmeans):
    processed = []
    v7_stats = []
    qm_stats = []
    if not os.path.exists(path):
        return processed, v7_stats, qm_stats

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue

            query = row.get("query")
            if not query:
                continue

            gold_flat = gold.get(query, flatten_flat_dict(row.get("gold", {})))
            qm_flat = qmeans.get(query, flatten_flat_dict(row.get("qmeans", {})))
            v7_flat = flatten_flat_dict(row.get("flat", {}))

            processed.append(query)
            v7_stats.append(prf(v7_flat, gold_flat))
            qm_stats.append(prf(qm_flat, gold_flat))

    return processed, v7_stats, qm_stats


def main():
    # read queries (skip header line)
    queries = []
    with open(QUERIES_FILE, encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            if i == 0 and line.lower() == "query":
                continue
            queries.append(line)
    print(f"queries: {len(queries)}")

    # gold + qmeans
    gold = {}
    with open(GOLD_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            r = json.loads(line)
            gold[r["query"]] = flatten_flat_dict(r.get("attributes", {}))

    qmeans = {}
    with open(QMEANS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            r = json.loads(line)
            qmeans[r["query"]] = flatten_flat_dict(r.get("attributes", {}))

    print(f"gold: {len(gold)}   qmeans: {len(qmeans)}")

    # load model
    print("loading v7 adapter ...")
    model, tokenizer = FastModel.from_pretrained(
        model_name=ADAPTER,
        max_seq_length=MAX_LENGTH,
        load_in_4bit=True,
        full_finetuning=False,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    FastModel.for_inference(model)

    processed_queries, v7_stats, qm_stats = load_existing_results(OUT_RESULTS, gold, qmeans)
    processed_set = set(processed_queries)
    remaining_queries = [q for q in queries if q not in processed_set]
    if processed_queries:
        print(f"resuming from {len(processed_queries)} existing rows")

    out_f = open(OUT_RESULTS, "a" if processed_queries else "w", encoding="utf-8")
    t0_all = time.time()

    for i, q in enumerate(remaining_queries, 1):
        prompt = build_prompt(q)
        inputs = tokenizer(text=prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out_ids = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW,
                do_sample=False,
                temperature=1.0,
                pad_token_id=tokenizer.pad_token_id,
            )
        gen = tokenizer.decode(out_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        gen = gen.replace("<end_of_turn>", "").strip()
        parsed = parse_json_loose(gen)
        v7_flat = flatten_priority_output(parsed) if parsed else {}

        gold_flat = gold.get(q, {})
        qm_flat   = qmeans.get(q, {})

        v7_stats.append(prf(v7_flat, gold_flat))
        qm_stats.append(prf(qm_flat, gold_flat))

        out_f.write(json.dumps({
            "query": q,
            "raw": gen,
            "parsed": parsed,
            "flat": v7_flat,
            "gold": gold_flat,
            "qmeans": qm_flat,
        }, ensure_ascii=False) + "\n")
        out_f.flush()

        done = len(processed_queries) + i
        if done % 25 == 0 or done == 1:
            dt = time.time() - t0_all
            rate = i / dt
            eta = (len(remaining_queries) - i) / rate / 60 if rate else 0.0
            print(f"[{done}/{len(queries)}] {dt/60:.1f}min  rate={rate:.2f}/s  eta={eta:.1f}min")

    out_f.close()

    summary = {
        "n": len(v7_stats),
        "v7_vs_gold":     aggregate(v7_stats),
        "qmeans_vs_gold": aggregate(qm_stats),
    }
    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print()
    print("=" * 60)
    print(json.dumps(summary, indent=2))
    print("=" * 60)


if __name__ == "__main__":
    main()
