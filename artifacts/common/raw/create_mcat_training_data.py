"""
Create Training Dataset for MCAT Classification
================================================
Reads: 50k_dataset_mcat_product.csv (pc_item_name, glcat_mcat_id, glcat_mcat_name)
Output: mcat_train.jsonl, mcat_val.jsonl  (Gemma-2 chat format)

Task: Given a product name, return the best matching MCAT (motor category)
        as JSON: {"mcat_name": "...", "mcat_id": ...}
"""

import csv
import json
import random
from collections import Counter

# ── CONFIG ─────────────────────────────────────────────────────────────────────
INPUT_CSV     = "50k_dataset_mcat_product.csv"
TRAIN_FILE    = "mcat_train.jsonl"
VAL_FILE      = "mcat_val.jsonl"
VAL_SPLIT     = 0.10          # 10 % validation
RANDOM_SEED   = 42
MAX_ROWS      = 20000         # take first N valid rows (no deduplication)
# ───────────────────────────────────────────────────────────────────────────────

random.seed(RANDOM_SEED)

# ── Varied instruction templates (avoids the model over-fitting one phrasing) ──
INSTRUCTION_TEMPLATES = [
    (
        "You are a product classification expert for an industrial marketplace. "
        "Given the product name below, identify the correct motor category (MCAT).\n\n"
        "Product Name: {product_name}\n\n"
        "Respond with a JSON object containing exactly two keys: 'mcat_name' and 'mcat_id'."
    ),
    (
        "Classify the following product into its most relevant motor category.\n\n"
        "Product: {product_name}\n\n"
        "Return your answer as JSON with keys 'mcat_name' (string) and 'mcat_id' (integer)."
    ),
    (
        "You are an expert catalog classifier. "
        "Map the product name to the correct MCAT (Motor Category).\n\n"
        "Product Name: {product_name}\n\n"
        "Output format (strict JSON):\n"
        "{{\"mcat_name\": \"<category name>\", \"mcat_id\": <integer id>}}"
    ),
    (
        "Task: Product to MCAT Classification\n\n"
        "Given: {product_name}\n\n"
        "Determine the most appropriate motor category and return:\n"
        "{{\"mcat_name\": \"...\", \"mcat_id\": ...}}"
    ),
    (
        "A customer is searching for: \"{product_name}\"\n\n"
        "What is the best matching motor category (MCAT) for this product?\n"
        "Respond strictly in JSON: {{\"mcat_name\": \"...\", \"mcat_id\": ...}}"
    ),
]


def build_output(mcat_name: str, mcat_id: int) -> str:
    return json.dumps({"mcat_name": mcat_name, "mcat_id": mcat_id}, ensure_ascii=False)


def main():
    # ── Load CSV ───────────────────────────────────────────────────────────────
    print(f"Reading {INPUT_CSV} ...")
    records = []
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if len(records) >= MAX_ROWS:
                break
            name  = row["pc_item_name"].strip()
            mid   = row["glcat_mcat_id"].strip()
            mname = row["glcat_mcat_name"].strip()
            # Only include rows where all three columns have values
            if name and mid and mname:
                try:
                    records.append((name, int(mid), mname))
                except ValueError:
                    pass  # skip rows where mcat_id is not numeric

    dedup = records  # no deduplication — keep all valid rows
    print(f"  Rows loaded (top {MAX_ROWS:,}, all 3 cols non-empty): {len(dedup):,}")

    # ── Show top mcats ─────────────────────────────────────────────────────────
    mcat_counts = Counter(r[1] for r in dedup)
    print(f"\n  Unique MCATs    : {len(mcat_counts):,}")
    print("  Top 15 MCATs by frequency:")
    for mid, cnt in mcat_counts.most_common(15):
        mname = next(r[2] for r in dedup if r[1] == mid)
        print(f"    [{mid:>7}]  {mname:<45}  {cnt:>5} examples")

    # ── Train / Val split – stratified by mcat_id ─────────────────────────────
    from collections import defaultdict
    by_mcat = defaultdict(list)
    for rec in dedup:
        by_mcat[rec[1]].append(rec)

    train_recs, val_recs = [], []
    for mid, recs in by_mcat.items():
        random.shuffle(recs)
        n_val = max(1, round(len(recs) * VAL_SPLIT)) if len(recs) > 1 else 0
        val_recs.extend(recs[:n_val])
        train_recs.extend(recs[n_val:])

    random.shuffle(train_recs)
    random.shuffle(val_recs)

    print(f"\n  Train samples   : {len(train_recs):,}")
    print(f"  Val   samples   : {len(val_recs):,}")

    # ── Write JSONL ────────────────────────────────────────────────────────────
    def write_jsonl(path, recs, desc):
        with open(path, "w", encoding="utf-8") as f:
            for i, (pname, mid, mname) in enumerate(recs):
                # rotate through instruction templates for variety
                tmpl = INSTRUCTION_TEMPLATES[i % len(INSTRUCTION_TEMPLATES)]
                instruction = tmpl.format(product_name=pname)
                output      = build_output(mname, mid)
                f.write(json.dumps({"instruction": instruction, "output": output}, ensure_ascii=False) + "\n")
        print(f"  Wrote {len(recs):>6,} {desc} examples → {path}")

    print()
    write_jsonl(TRAIN_FILE, train_recs, "train")
    write_jsonl(VAL_FILE,   val_recs,   "val  ")

    # ── Sample preview ─────────────────────────────────────────────────────────
    print("\n── Sample training record ──────────────────────────────────────────")
    sample = json.loads(open(TRAIN_FILE, encoding="utf-8").readline())
    print("INSTRUCTION:\n", sample["instruction"])
    print("OUTPUT:\n", sample["output"])

    print("\n✓ Training dataset creation complete!")
    print(f"  Files: {TRAIN_FILE}, {VAL_FILE}")


if __name__ == "__main__":
    main()
