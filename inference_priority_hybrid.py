"""
Hybrid priority inference for user queries.

This serving path keeps V7's priority-schema extraction when available and
fills missing attributes from qmeans, then returns the final result in the
priority-ordered nested schema.

Offline benchmark on the 1k set using existing V7 outputs plus qmeans:
  - qmeans: key F1 0.4550, key+value F1 0.0600
  - V7:     key F1 0.2909, key+value F1 0.1552
  - hybrid: key F1 0.5438, key+value F1 0.1722

Usage:
  python inference_priority_hybrid.py
  python inference_priority_hybrid.py --query "45 hp 3 phase siemens motor"
  python inference_priority_hybrid.py --queries queries.jsonl
"""

import argparse
import importlib.metadata as _md
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path = [path for path in sys.path if "python3.9" not in path]

_real_version = _md.version


def _safe_version(name):
    try:
        return _real_version(name)
    except _md.PackageNotFoundError:
        if name in ("vllm",):
            return "0.0.0"
        raise


_md.version = _safe_version

ADAPTER_PATH = "/home3/indiamart/gemma_4/isq-gemma4-e4b-v7-priority"
BASE_MODEL = "/home3/indiamart/gemma_4/models/gemma-4-e4b-it"
DEFAULT_OUT = "/home3/indiamart/gemma_4/hybrid_priority_inference_results.jsonl"
DEFAULT_QMEANS_URL = "http://34.93.70.216:8009/attribute-search"
DEFAULT_QMEANS_SOURCE = "priority.hybrid"
MAX_LENGTH = 768

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
]

MODEL_RANK = {"q-means/2.0.1": 3, "attr-v2": 2, "probable-product": 1}

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

VOCAB = {
    "brand": ["brand", "manufacturer", "company", "make"],
    "part type": ["part_type", "product_type", "type", "product_category", "category"],
    "driven type": ["driven_type", "motor_type", "machine_type", "drive_type"],
    "power": ["power", "wattage", "kilowatt", "horsepower", "hp", "kw", "motor_power", "power_rating", "rated_power"],
    "horsepower": ["horsepower", "hp", "power", "motor_horsepower", "rated_power"],
    "model name/number": ["model_number", "part_number", "model", "model_name", "mpn"],
    "phase": ["phase", "phase_type", "no_of_phase", "number_of_phase"],
    "voltage": ["voltage", "rated_voltage", "operating_voltage", "voltage_rating"],
    "current": ["current", "rated_current", "amperage", "ampere"],
    "frequency": ["frequency", "frequency_hertz", "operating_frequency", "hz"],
    "rpm": ["rpm", "speed", "rotation_speed", "rated_speed", "revolutions_per_minute"],
    "poles": ["poles", "no_of_poles", "number_of_poles", "pole_count"],
    "size": ["size", "dimension", "frame_size", "physical_size"],
    "frame size": ["frame_size", "frame", "size", "frame_designation"],
    "weight": ["weight", "mass", "net_weight", "gross_weight"],
    "mounting type": ["mounting_type", "mounting", "fixing_type", "installation_type"],
    "orientation": ["orientation", "alignment", "mounting_orientation"],
    "shape": ["shape", "geometry", "form"],
    "shaft diameter": ["shaft_diameter", "shaft_size", "shaft"],
    "stroke length": ["stroke_length", "stroke", "stroke_size"],
    "displacement": ["displacement", "swept_volume", "volume_displacement"],
    "torque": ["torque", "rated_torque", "torque_rating", "nm_torque"],
    "capacity": ["capacity", "rated_capacity", "load_capacity", "tank_capacity"],
    "quantity": ["quantity", "qty", "count", "no_of_units"],
    "ip rating": ["ip_rating", "ingress_protection", "ip_class", "protection_rating"],
    "insulation class": ["insulation_class", "insulation", "insulation_grade", "class_of_insulation"],
    "cooling type": ["cooling_type", "cooling", "cooling_method"],
    "efficiency": ["efficiency", "efficiency_class", "ie_class", "energy_efficiency"],
    "grade": ["grade", "quality_grade", "class"],
    "material": ["material", "body_material", "construction_material", "casing_material"],
    "color": ["color", "colour", "shade"],
    "feature": ["feature", "specification", "characteristic", "attribute"],
    "usage": ["usage", "application", "suitable_for", "use_case", "purpose"],
    "application": ["application", "usage", "use_case", "suitable_for"],
    "starter type": ["starter_type", "starter", "starting_method"],
    "power source": ["power_source", "power_supply", "energy_source", "fuel_type"],
    "series": ["series", "product_series", "model_series"],
    "location/city": ["location", "city", "place", "region"],
}

RANK = {
    "brand": 1,
    "part type": 2,
    "driven type": 2,
    "power": 3,
    "horsepower": 3,
    "model name/number": 4,
    "phase": 5,
    "voltage": 5,
    "current": 5,
    "rpm": 6,
    "poles": 6,
    "power source": 6,
    "frequency": 7,
    "torque": 7,
    "capacity": 7,
    "size": 8,
    "frame size": 8,
    "mounting type": 8,
    "ip rating": 8,
    "weight": 9,
    "orientation": 9,
    "shape": 9,
    "shaft diameter": 9,
    "stroke length": 9,
    "displacement": 9,
    "insulation class": 9,
    "cooling type": 9,
    "efficiency": 9,
    "starter type": 9,
    "quantity": 10,
    "grade": 10,
    "material": 10,
    "color": 10,
    "feature": 10,
    "usage": 10,
    "application": 10,
    "series": 10,
    "location/city": 10,
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


def clean_value(value, normalize=False):
    text = scalar_text(value).strip()
    text = re.sub(r"\s+", " ", text)
    if normalize:
        text = text.lower()
    return text


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


def flatten_flat_dict(data, normalize_values=False):
    flat = {}
    if not isinstance(data, dict):
        return flat
    for key, value in data.items():
        canon = canon_key(key)
        clean = clean_value(value, normalize=normalize_values)
        if canon and clean and canon not in flat:
            flat[canon] = clean
    return flat


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
            if key.startswith("attribute_priority") or "value" in value or any(item.startswith("key_priority") for item in value):
                yield from iter_priority_bodies(value)
        elif isinstance(value, list):
            yield from iter_priority_bodies(value)


def flatten_priority_output(parsed, normalize_values=False):
    flat = {}
    if not isinstance(parsed, dict):
        return flat
    attrs = parsed.get("attributes")
    if not isinstance(attrs, list):
        return flat
    for item in attrs:
        for body in iter_priority_bodies(item):
            key = canon_key(body.get("key_priority1") or body.get("key_priority_1") or "")
            value = clean_value(body.get("value", ""), normalize=normalize_values)
            if key and value and key not in flat:
                flat[key] = value
    return flat


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


def flat_to_nested(flat):
    items = []
    for key, value in flat.items():
        canonical = canon_key(key)
        if not canonical:
            continue
        display_value = clean_value(value)
        if not display_value:
            continue
        rank = RANK.get(canonical, 99)
        synonyms = VOCAB.get(canonical, [canonical.replace(" ", "_")])
        items.append((rank, canonical, display_value, synonyms))
    items.sort(key=lambda item: item[0])
    nested = []
    for index, (_rank, _canonical, value, synonyms) in enumerate(items, start=1):
        body = {"value": value}
        for synonym_index, synonym in enumerate(synonyms, start=1):
            body[f"key_priority{synonym_index}"] = synonym
        nested.append({f"attribute_priority{index}": body})
    return {"attributes": nested}


def merge_priority_outputs(v7_flat, qmeans_flat):
    merged = dict(v7_flat)
    for key, value in qmeans_flat.items():
        if key not in merged:
            merged[key] = value
    return merged


def extract_qmeans_attributes(payload):
    attrs = {}
    products = []
    for _token, info in (payload.get("attributes") or {}).items():
        candidates = [info] + list(info.get("others") or [])
        best = None
        for candidate in candidates:
            name = clean_value(candidate.get("attr_name"), normalize=True)
            value = clean_value(candidate.get("attr_value"))
            if not name or name == "-" or not value:
                continue
            score = MODEL_RANK.get(candidate.get("model", ""), 0)
            if best is None or score > best[0]:
                best = (score, name, value)
        if best:
            _, name, value = best
            if name not in attrs or len(value) > len(attrs[name]):
                attrs[name] = value
        for candidate in candidates:
            if clean_value(candidate.get("attr_name"), normalize=True) == "-" and candidate.get("attr_type") == "product":
                value = clean_value(candidate.get("attr_value"))
                if value:
                    products.append(value)
    if products:
        attrs["product"] = max(products, key=len)
    return flatten_flat_dict(attrs)


def query_qmeans(query, url, source, retries=3, timeout=20):
    params = urllib.parse.urlencode({"query": query, "source": source})
    request_url = f"{url}?{params}"
    last_error = None
    started = time.time()
    for _ in range(retries):
        try:
            request = urllib.request.Request(request_url, headers={"User-Agent": "priority-hybrid/1.0"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return {
                "ok": True,
                "attrs": extract_qmeans_attributes(payload),
                "secs": round(time.time() - started, 2),
            }
        except Exception as exc:
            last_error = str(exc)
            time.sleep(0.5)
    return {
        "ok": False,
        "attrs": {},
        "secs": round(time.time() - started, 2),
        "error": last_error,
    }


def build_prompt(query):
    return (
        "<start_of_turn>user\n"
        f"{INSTRUCTION}\n\nQuery: {query}<end_of_turn>\n"
        "<start_of_turn>model\n"
    )


def collect_queries(args):
    if args.query:
        return [args.query]
    if args.queries:
        queries = []
        with open(args.queries, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    query = row.get("query") or row.get("instruction") or row.get("text")
                    if query:
                        queries.append(query)
                except json.JSONDecodeError:
                    queries.append(line)
        return queries
    return list(SAMPLES)


def load_model():
    import unsloth  # noqa: F401
    from unsloth import FastModel
    import torch

    model_name = ADAPTER_PATH if os.path.exists(os.path.join(ADAPTER_PATH, "adapter_config.json")) else BASE_MODEL
    model, tokenizer = FastModel.from_pretrained(
        model_name=model_name,
        max_seq_length=MAX_LENGTH,
        load_in_4bit=True,
        full_finetuning=False,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    FastModel.for_inference(model)
    return model, tokenizer, torch


def run_v7(model, tokenizer, torch_module, query, max_new_tokens):
    prompt = build_prompt(query)
    inputs = tokenizer(text=prompt, return_tensors="pt").to(model.device)
    started = time.time()
    with torch_module.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0,
            pad_token_id=tokenizer.pad_token_id,
        )
    raw = tokenizer.decode(output_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    raw = raw.replace("<end_of_turn>", "").strip()
    parsed = parse_json_loose(raw)
    flat = flatten_priority_output(parsed)
    return {
        "raw": raw,
        "parsed": parsed,
        "flat": flat,
        "secs": round(time.time() - started, 2),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--queries", type=str, default=None, help="JSONL with one {'query': ...} per line, or plain text one query per line")
    parser.add_argument("--out", type=str, default=DEFAULT_OUT)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    parser.add_argument("--qmeans-url", type=str, default=DEFAULT_QMEANS_URL)
    parser.add_argument("--qmeans-source", type=str, default=DEFAULT_QMEANS_SOURCE)
    return parser.parse_args()


def main():
    args = parse_args()
    queries = collect_queries(args)

    print("Loading base model + V7 LoRA adapter ...")
    model, tokenizer, torch_module = load_model()

    print(f"Running hybrid priority inference on {len(queries)} queries ...\n")
    with open(args.out, "w", encoding="utf-8") as out_handle:
        for index, query in enumerate(queries, start=1):
            v7_result = run_v7(model, tokenizer, torch_module, query, args.max_new_tokens)
            qmeans_result = query_qmeans(query, args.qmeans_url, args.qmeans_source)
            hybrid_flat = merge_priority_outputs(v7_result["flat"], qmeans_result["attrs"])
            hybrid_priority = flat_to_nested(hybrid_flat)

            record = {
                "query": query,
                "result": hybrid_priority,
                "hybrid_flat": hybrid_flat,
                "v7_flat": v7_result["flat"],
                "qmeans_flat": qmeans_result["attrs"],
                "v7_raw": v7_result["raw"],
                "v7_parsed": v7_result["parsed"],
                "v7_secs": v7_result["secs"],
                "qmeans_secs": qmeans_result["secs"],
                "qmeans_ok": qmeans_result["ok"],
            }
            if not qmeans_result["ok"]:
                record["qmeans_error"] = qmeans_result.get("error")

            out_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            out_handle.flush()

            print(f"[{index}/{len(queries)}] {query}")
            print(json.dumps(hybrid_priority, ensure_ascii=False, indent=2))
            if not qmeans_result["ok"]:
                print(f"qmeans fallback unavailable: {qmeans_result.get('error')}")
            print()

    print(f"Done. Results -> {args.out}")


if __name__ == "__main__":
    main()