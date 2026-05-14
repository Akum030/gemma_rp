"""
Evaluate a priority-schema adapter against gold and qmeans on the 1000-query set.

This is a reusable version of eval_v7.py that accepts adapter and output paths
via CLI arguments so the same evaluator can be used for v7, v8, v9, ...
"""
import argparse
import json
import os
import re
import sys
import time

sys.path = [p for p in sys.path if "python3.9" not in p]

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

import unsloth  # noqa: F401
from unsloth import FastModel
import torch


QUERIES_FILE = "/home3/indiamart/gemma_4/76cat_queries"
GOLD_FILE = "/home3/indiamart/gemma_4/gold_1k_v2.jsonl"
QMEANS_FILE = "/home3/indiamart/gemma_4/qmeans_v2_results.jsonl"

MAX_LENGTH = 768
MAX_NEW = 320

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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out-results", required=True)
    parser.add_argument("--out-summary", required=True)
    return parser.parse_args()


def build_prompt(query):
    return (
        "<start_of_turn>user\n"
        f"{INSTRUCTION}\n\nQuery: {query}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )


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


def canon_key(key):
    key = scalar_text(key).lower().strip().replace("_", " ")
    if not key:
        return ""
    key_us = key.replace(" ", "_")
    if key in KEY_ALIASES:
        return KEY_ALIASES[key]
    if key_us in KEY_ALIASES:
        return KEY_ALIASES[key_us]
    return key


def norm_value(value):
    value = scalar_text(value).lower().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def iter_priority_bodies(node):
    if isinstance(node, list):
        for item in node:
            yield from iter_priority_bodies(item)
        return

    if not isinstance(node, dict):
        return

    has_value = "value" in node
    has_key = any(key.startswith("key_priority") for key in node)
    if has_value and has_key:
        yield node

    for key, value in node.items():
        if isinstance(value, dict):
            if key.startswith("attribute_priority") or "value" in value or any(k.startswith("key_priority") for k in value):
                yield from iter_priority_bodies(value)
        elif isinstance(value, list):
            yield from iter_priority_bodies(value)


def flatten_priority_output(parsed):
    flat = {}
    if not isinstance(parsed, dict):
        return flat
    attrs = parsed.get("attributes")
    if not isinstance(attrs, list):
        return flat
    for item in attrs:
        for body in iter_priority_bodies(item):
            key = canon_key(body.get("key_priority1") or body.get("key_priority_1") or "")
            value = norm_value(body.get("value", ""))
            if key and value and key not in flat:
                flat[key] = value
    return flat


def flatten_flat_dict(data):
    out = {}
    if not isinstance(data, dict):
        return out
    for key, value in data.items():
        canon = canon_key(key)
        if canon:
            out[canon] = norm_value(value)
    return out


def prf(pred, gold):
    pred_keys = set(pred.keys())
    gold_keys = set(gold.keys())
    tp_k = len(pred_keys & gold_keys)
    pred_kv = {(key, pred[key]) for key in pred_keys}
    gold_kv = {(key, gold[key]) for key in gold_keys}
    tp_kv = len(pred_kv & gold_kv)
    return {
        "tp_k": tp_k,
        "fp_k": len(pred_keys) - tp_k,
        "fn_k": len(gold_keys) - tp_k,
        "tp_kv": tp_kv,
        "fp_kv": len(pred_keys) - tp_kv,
        "fn_kv": len(gold_keys) - tp_kv,
    }


def aggregate(stats):
    def metric(prefix):
        tp = sum(item[f"tp_{prefix}"] for item in stats)
        fp = sum(item[f"fp_{prefix}"] for item in stats)
        fn = sum(item[f"fn_{prefix}"] for item in stats)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }

    return {"key_only": metric("k"), "key_value": metric("kv")}


def parse_json_loose(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None
    return None


def load_existing_results(path, gold, qmeans):
    processed = []
    model_stats = []
    qmeans_stats = []
    if not os.path.exists(path):
        return processed, model_stats, qmeans_stats

    with open(path, encoding="utf-8") as handle:
        for line in handle:
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
            qmeans_flat = qmeans.get(query, flatten_flat_dict(row.get("qmeans", {})))
            parsed = row.get("parsed")
            if isinstance(parsed, dict):
                model_flat = flatten_priority_output(parsed)
            else:
                model_flat = flatten_flat_dict(row.get("flat", {}))

            processed.append(query)
            model_stats.append(prf(model_flat, gold_flat))
            qmeans_stats.append(prf(qmeans_flat, gold_flat))

    return processed, model_stats, qmeans_stats


def main():
    args = parse_args()

    queries = []
    with open(QUERIES_FILE, encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            line = line.strip()
            if not line:
                continue
            if index == 0 and line.lower() == "query":
                continue
            queries.append(line)
    print(f"queries: {len(queries)}")

    gold = {}
    with open(GOLD_FILE, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            gold[row["query"]] = flatten_flat_dict(row.get("attributes", {}))

    qmeans = {}
    with open(QMEANS_FILE, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            qmeans[row["query"]] = flatten_flat_dict(row.get("attributes", {}))

    processed_queries, model_stats, qmeans_stats = load_existing_results(args.out_results, gold, qmeans)
    processed_set = set(processed_queries)
    remaining_queries = [query for query in queries if query not in processed_set]
    if processed_queries:
        print(f"resuming from {len(processed_queries)} existing rows")

    if remaining_queries:
        print(f"loading adapter: {args.adapter}")

        model, tokenizer = FastModel.from_pretrained(
            model_name=args.adapter,
            max_seq_length=MAX_LENGTH,
            load_in_4bit=True,
            full_finetuning=False,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        FastModel.for_inference(model)

        out_handle = open(args.out_results, "a" if processed_queries else "w", encoding="utf-8")
        start_time = time.time()

        for index, query in enumerate(remaining_queries, 1):
            prompt = build_prompt(query)
            inputs = tokenizer(text=prompt, return_tensors="pt").to(model.device)
            with torch.no_grad():
                out_ids = model.generate(
                    **inputs,
                    max_new_tokens=MAX_NEW,
                    do_sample=False,
                    temperature=1.0,
                    pad_token_id=tokenizer.pad_token_id,
                )

            generated = tokenizer.decode(out_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
            generated = generated.replace("<end_of_turn>", "").strip()
            parsed = parse_json_loose(generated)
            model_flat = flatten_priority_output(parsed) if parsed else {}

            gold_flat = gold.get(query, {})
            qmeans_flat = qmeans.get(query, {})

            model_stats.append(prf(model_flat, gold_flat))
            qmeans_stats.append(prf(qmeans_flat, gold_flat))

            out_handle.write(json.dumps({
                "query": query,
                "raw": generated,
                "parsed": parsed,
                "flat": model_flat,
                "gold": gold_flat,
                "qmeans": qmeans_flat,
            }, ensure_ascii=False) + "\n")
            out_handle.flush()

            done = len(processed_queries) + index
            if done % 25 == 0 or done == 1:
                elapsed = time.time() - start_time
                rate = index / elapsed if elapsed else 0.0
                eta = (len(remaining_queries) - index) / rate / 60 if rate else 0.0
                print(f"[{done}/{len(queries)}] {elapsed/60:.1f}min  rate={rate:.2f}/s  eta={eta:.1f}min")

        out_handle.close()

    print(f"gold: {len(gold)}   qmeans: {len(qmeans)}")

    summary = {
        "label": args.label,
        "adapter": args.adapter,
        "n": len(model_stats),
        f"{args.label}_vs_gold": aggregate(model_stats),
        "qmeans_vs_gold": aggregate(qmeans_stats),
    }
    with open(args.out_summary, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()