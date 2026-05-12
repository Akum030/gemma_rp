"""
Generate 1000 unbiased test queries for MCAT evaluation.

Strategy:
  1. Parse training JSONL + source 50k CSV to get all unique mcat categories
  2. Collect product names per mcat from the full 50k CSV
  3. Select 1000 product names NOT in the training set, spread proportionally across categories
  4. Output: unbiased_1000_queries.csv  (header: query)
"""

import csv
import json
import random
from pathlib import Path
from collections import defaultdict, Counter

random.seed(42)

HERE       = Path(__file__).resolve().parent
DATA_DIR   = HERE.parent / "product_mcat"
TRAIN_JSONL = DATA_DIR / "mcat_train.jsonl"
VAL_JSONL   = DATA_DIR / "mcat_val.jsonl"
SOURCE_CSV  = DATA_DIR / "50k_dataset_mcat_product.csv"
OUTPUT_CSV  = HERE / "unbiased_1000_queries.csv"
TARGET      = 1000


def extract_product_from_instruction(instr: str) -> str:
    """Pull the product name from any of the 5 instruction templates."""
    import re
    # Template 1 & 2: "Product Name: XXX"
    m = re.search(r"Product Name:\s*(.+?)(?:\n|$)", instr)
    if m:
        return m.group(1).strip()
    # Template 3: "Product: XXX"
    m = re.search(r"Product:\s*(.+?)(?:\n|$)", instr)
    if m:
        return m.group(1).strip()
    # Template 4: 'Given: XXX'
    m = re.search(r"Given:\s*(.+?)(?:\n|$)", instr)
    if m:
        return m.group(1).strip()
    # Template 5: 'searching for: "XXX"'
    m = re.search(r'searching for:\s*"(.+?)"', instr)
    if m:
        return m.group(1).strip()
    return ""


def load_train_val_products():
    """Return set of all product names used in training & validation."""
    products = set()
    for fpath in [TRAIN_JSONL, VAL_JSONL]:
        if not fpath.exists():
            continue
        with open(fpath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                p = extract_product_from_instruction(rec.get("instruction", ""))
                if p:
                    products.add(p.lower().strip())
    return products


def load_source_csv():
    """Return list of (product_name, mcat_id, mcat_name) from full 50k CSV."""
    rows = []
    with open(SOURCE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("pc_item_name", "").strip()
            mid  = row.get("glcat_mcat_id", "").strip()
            mname = row.get("glcat_mcat_name", "").strip()
            if name and mid and mname:
                rows.append((name, mid, mname))
    return rows


def main():
    print("Loading training + validation products (to exclude)...")
    train_products = load_train_val_products()
    print(f"  Excluded product names: {len(train_products)}")

    print("Loading full 50k source CSV...")
    all_rows = load_source_csv()
    print(f"  Total source rows: {len(all_rows)}")

    # Group unseen products by mcat_id
    unseen_by_mcat = defaultdict(list)
    seen_names = set()
    for name, mid, mname in all_rows:
        nkey = name.lower().strip()
        if nkey in train_products:
            continue
        if nkey in seen_names:
            continue  # dedup within unseen pool
        seen_names.add(nkey)
        unseen_by_mcat[mid].append((name, mid, mname))

    total_unseen = sum(len(v) for v in unseen_by_mcat.values())
    print(f"  Unseen (not in train/val) unique products: {total_unseen}")
    print(f"  Spread across {len(unseen_by_mcat)} mcat categories")

    # Count training distribution to allocate proportionally
    train_mcat_count = Counter()
    for name, mid, mname in all_rows:
        if name.lower().strip() in train_products:
            train_mcat_count[mid] += 1

    # Proportional allocation: each mcat gets share based on training freq
    total_train = sum(train_mcat_count.values())
    allocation = {}
    for mid in unseen_by_mcat:
        freq = train_mcat_count.get(mid, 1)
        allocation[mid] = max(1, round(TARGET * freq / total_train))

    # If total allocation exceeds TARGET, scale down; if under, scale up
    total_alloc = sum(allocation.values())
    scale = TARGET / total_alloc if total_alloc > 0 else 1
    for mid in allocation:
        allocation[mid] = max(1, round(allocation[mid] * scale))

    # Sample
    selected = []
    for mid, pool in unseen_by_mcat.items():
        n = min(allocation.get(mid, 1), len(pool))
        chosen = random.sample(pool, n)
        selected.extend(chosen)

    # If over TARGET, trim; if under, top up from remaining
    random.shuffle(selected)
    if len(selected) > TARGET:
        selected = selected[:TARGET]
    elif len(selected) < TARGET:
        # top up from unused unseen products
        used = {s[0].lower().strip() for s in selected}
        remaining = []
        for mid, pool in unseen_by_mcat.items():
            for item in pool:
                if item[0].lower().strip() not in used:
                    remaining.append(item)
        random.shuffle(remaining)
        needed = TARGET - len(selected)
        selected.extend(remaining[:needed])

    random.shuffle(selected)
    selected = selected[:TARGET]

    # Write
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["query"])
        writer.writeheader()
        for name, mid, mname in selected:
            writer.writerow({"query": name})

    # Stats
    mcat_dist = Counter(mname for _, _, mname in selected)
    print(f"\nGenerated {len(selected)} queries → {OUTPUT_CSV}")
    print(f"Covering {len(mcat_dist)} distinct mcat categories")
    print("\nTop 20 categories in generated queries:")
    for mname, cnt in mcat_dist.most_common(20):
        print(f"  {cnt:>4}  {mname}")


if __name__ == "__main__":
    main()
