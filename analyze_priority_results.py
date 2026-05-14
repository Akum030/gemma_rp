"""
Analyze priority-evaluation JSONL outputs for schema obedience and common errors.

Intended inputs are result files produced by eval_priority_adapter.py or eval_v7.py.
"""
import argparse
import json
import re
from collections import Counter


PLACEHOLDER_PATTERNS = (
    re.compile(r"^attribute\s*priority\d+$"),
    re.compile(r"^attribute\s*priorityn$"),
    re.compile(r"^attribute_priority\d+$"),
    re.compile(r"^attribute_priorityn$"),
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-jsonl", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out-json", required=True)
    return parser.parse_args()


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


def normalize_key(key):
    return scalar_text(key).strip().lower().replace("_", " ")


def is_placeholder_key(key):
    key = normalize_key(key)
    return any(pattern.match(key) for pattern in PLACEHOLDER_PATTERNS)


def iter_priority_bodies(node, depth=0):
    if isinstance(node, list):
        for item in node:
            yield from iter_priority_bodies(item, depth)
        return

    if not isinstance(node, dict):
        return

    has_value = "value" in node
    has_key = any(key.startswith("key_priority") for key in node)
    if has_value and has_key:
        yield {"body": node, "depth": depth}

    for key, value in node.items():
        if isinstance(value, dict):
            if key.startswith("attribute_priority") or "value" in value or any(k.startswith("key_priority") for k in value):
                yield from iter_priority_bodies(value, depth + 1)
        elif isinstance(value, list):
            yield from iter_priority_bodies(value, depth + 1)


def recompute_flat(parsed):
    flat = {}
    meta = {
        "body_count": 0,
        "deep_body_count": 0,
        "placeholder_keys": 0,
        "bodies": [],
    }
    if not isinstance(parsed, dict):
        return flat, meta
    attrs = parsed.get("attributes")
    if not isinstance(attrs, list):
        return flat, meta
    for item in attrs:
        for entry in iter_priority_bodies(item):
            body = entry["body"]
            depth = entry["depth"]
            meta["body_count"] += 1
            if depth > 1:
                meta["deep_body_count"] += 1
            key = normalize_key(body.get("key_priority1") or body.get("key_priority_1") or "")
            value = scalar_text(body.get("value", "")).strip().lower()
            if is_placeholder_key(key):
                meta["placeholder_keys"] += 1
            if key and value and key not in flat:
                flat[key] = value
            meta["bodies"].append({
                "key_priority1": key,
                "value": value,
                "depth": depth,
            })
    return flat, meta


def summarize_examples(examples):
    out = []
    for example in examples[:10]:
        out.append(example)
    return out


def main():
    args = parse_args()

    total = 0
    parsed_rows = 0
    attr_list_rows = 0
    empty_flat_rows = 0
    changed_flat_rows = 0
    deep_wrapper_rows = 0
    placeholder_rows = 0
    total_bodies = 0
    key_counter = Counter()
    stored_key_counter = Counter()

    wrapped_examples = []
    placeholder_examples = []
    changed_examples = []
    empty_examples = []

    with open(args.results_jsonl, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            total += 1

            parsed = row.get("parsed")
            if isinstance(parsed, dict):
                parsed_rows += 1
            if isinstance(parsed, dict) and isinstance(parsed.get("attributes"), list):
                attr_list_rows += 1

            recomputed_flat, meta = recompute_flat(parsed)
            stored_flat = {normalize_key(k): scalar_text(v).strip().lower() for k, v in (row.get("flat") or {}).items()}

            total_bodies += meta["body_count"]
            key_counter.update(recomputed_flat.keys())
            stored_key_counter.update(stored_flat.keys())

            if meta["deep_body_count"] > 0:
                deep_wrapper_rows += 1
                wrapped_examples.append({
                    "query": row.get("query"),
                    "body_count": meta["body_count"],
                    "deep_body_count": meta["deep_body_count"],
                    "raw": (row.get("raw") or "")[:300],
                })

            if meta["placeholder_keys"] > 0:
                placeholder_rows += 1
                placeholder_examples.append({
                    "query": row.get("query"),
                    "placeholder_keys": meta["placeholder_keys"],
                    "bodies": meta["bodies"][:5],
                })

            if not recomputed_flat:
                empty_flat_rows += 1
                empty_examples.append({
                    "query": row.get("query"),
                    "raw": (row.get("raw") or "")[:300],
                })

            if recomputed_flat != stored_flat:
                changed_flat_rows += 1
                changed_examples.append({
                    "query": row.get("query"),
                    "stored_flat": stored_flat,
                    "recomputed_flat": recomputed_flat,
                })

    summary = {
        "label": args.label,
        "rows": total,
        "parsed_rows": parsed_rows,
        "parsed_rate": round(parsed_rows / total, 4) if total else 0.0,
        "attributes_list_rows": attr_list_rows,
        "attributes_list_rate": round(attr_list_rows / total, 4) if total else 0.0,
        "avg_priority_bodies_per_row": round(total_bodies / total, 4) if total else 0.0,
        "empty_flat_rows": empty_flat_rows,
        "empty_flat_rate": round(empty_flat_rows / total, 4) if total else 0.0,
        "changed_flat_rows": changed_flat_rows,
        "changed_flat_rate": round(changed_flat_rows / total, 4) if total else 0.0,
        "deep_wrapper_rows": deep_wrapper_rows,
        "deep_wrapper_rate": round(deep_wrapper_rows / total, 4) if total else 0.0,
        "placeholder_rows": placeholder_rows,
        "placeholder_rate": round(placeholder_rows / total, 4) if total else 0.0,
        "top_recomputed_keys": key_counter.most_common(20),
        "top_stored_keys": stored_key_counter.most_common(20),
        "examples": {
            "wrapped": summarize_examples(wrapped_examples),
            "placeholder": summarize_examples(placeholder_examples),
            "changed_flat": summarize_examples(changed_examples),
            "empty": summarize_examples(empty_examples),
        },
    }

    with open(args.out_json, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()