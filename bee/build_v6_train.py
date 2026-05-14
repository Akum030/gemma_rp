"""
Build V6 training data from multiple sources.

Sources (stacked):
  1. product_train_with_keys.jsonl  — 10K rows, remap to canonical keys
  2. gold_1k_v2.jsonl               — 1000 GT examples (exact target format)
  3. qmeans_v2_results.jsonl        — 615 rich qmeans outputs, key-canonicalized

Strategy:
  1. Remap non-canonical keys to canonical using KEY_REMAP
  2. Drop keys that cannot be remapped (None mapping)
  3. Drop rows whose queries are clearly non-motor / food / refining domain
  4. Keep rows that have at least 1 canonical key after remapping
  5. Output: v6_train.jsonl (flat JSON format, same as V5 input)

Run: python bee/build_v6_train.py
"""

import json, re, random
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent

INPUT_PROD    = ROOT / "product_train_with_keys.jsonl"
INPUT_GT      = ROOT / "bee" / "gold_1k_v2.jsonl"
INPUT_QMEANS  = ROOT / "bee" / "qmeans_v2_results.jsonl"
OUTPUT_TRAIN  = ROOT / "v6_train.jsonl"
OUTPUT_VAL    = ROOT / "v6_val.jsonl"

# ──────────────────────────────────────────────────────────────
# Canonical key set — MUST match gold_1k_v2 keys exactly
# ──────────────────────────────────────────────────────────────
CANONICAL = {
    "part type", "brand", "driven type", "model name/number", "feature",
    "usage", "power source", "phase", "horsepower", "power", "series", "rpm",
    "starter type", "voltage", "size", "mounting type", "quantity",
    "location/city", "material", "current", "weight", "frame size",
    "efficiency", "stroke length", "orientation", "shape", "frequency",
    "grade", "torque", "force", "poles", "color", "displacement",
    "application", "shaft diameter", "insulation class", "ip rating",
    "cooling type", "duty cycle", "capacity",
}

# ──────────────────────────────────────────────────────────────
# Key remapping: non-canonical → canonical (None = drop key)
# ──────────────────────────────────────────────────────────────
KEY_REMAP = {
    # motor domain fixes
    "motor power":          "power",
    "motor type":           "driven type",
    "motor_type":           "driven type",
    "motortype":            "driven type",
    "machine type":         "part type",
    "machine name":         "model name/number",
    "model number":         "model name/number",
    "model no":             "model name/number",
    "model no.":            "model name/number",
    "model":                "model name/number",
    "rated speed":          "rpm",
    "speed":                "rpm",
    "ratedspeed":           "rpm",
    "output speed":         "rpm",
    "input speed":          "rpm",
    "power consumption":    "power",
    "output power":         "power",
    "rated power":          "power",
    "input power":          "power",
    "load type":            "driven type",
    "drive type":           "driven type",
    "driving type":         "driven type",
    "type of drive":        "driven type",
    "motor mounting":       "mounting type",
    "mount type":           "mounting type",
    "mounting":             "mounting type",
    "flange type":          "mounting type",
    "frame":                "frame size",
    "frame size/flange":    "frame size",
    "suitable for":         "usage",
    "application type":     "usage",
    "operating voltage":    "voltage",
    "supply voltage":       "voltage",
    "rated voltage":        "voltage",
    "current (amp)":        "current",
    "rated current":        "current",
    "input current":        "current",
    "output current":       "current",
    "no. of poles":         "poles",
    "number of poles":      "poles",
    "no of poles":          "poles",
    "hp":                   "horsepower",
    "kw":                   "power",
    "rated hp":             "horsepower",
    # material / quality
    "types of metal":       "material",
    "metal":                "material",
    "storage material":     "material",
    "melting material":     "material",
    "refining material":    "material",
    "purity":               "grade",
    "material type":        "material",
    # process → usage
    "process":              "usage",
    "operation":            "usage",
    "processing type":      "usage",
    "working":              "usage",
    # feature / tech
    "die type":             "feature",
    "screw type":           "feature",
    "number of layers":     "feature",
    "layers":               "feature",
    "technology":           "feature",
    # drop irrelevant keys
    "country of origin":    None,
    "place of origin":      None,
    "name of extract":      None,
    "type of namkeen":      None,
    "storage capacity":     None,
    "material to be extruded": None,
    "automation grade":     "feature",
    "power factor":         "feature",
    "insulation":           "insulation class",
    "insulation type":      "insulation class",
    "class":                "insulation class",
    "ip":                   "ip rating",
    "protection":           "ip rating",
    "protection degree":    "ip rating",
    "cooling":              "cooling type",
    "cooling method":       "cooling type",
    # packaging / generic → drop
    "packaging size":       None,
    "pack size":            None,
    "packaging type":       None,
    "packaging":            None,
    # ambiguous passthrough → canonical
    "speed":                "rpm",
    "type":                 "part type",
    "technology":           "feature",
    "automation grade":     "feature",
    "certification":        "feature",
    "temperature range":    "feature",
    "enclosure type":       "feature",
    "protection class":     "ip rating",
    # qmeans-specific keys
    "product":              "part type",
    "probable-product":     "part type",
    "motor type":           "driven type",
    "motor part type":      "part type",
    "actuator type":        "driven type",
    "no of phase":          "phase",
    "number of phase":      "phase",
    "rated power":          "power",
    # GT edge-case keys
    "weight capacity":      "capacity",
    "air flow capacity":    "capacity",
    "flow rate":            "capacity",
    "step angle":           "feature",
    "head":                 "feature",
    "length":               "size",
    "rated speed":          "rpm",
    "country of origin":    None,
}

# ──────────────────────────────────────────────────────────────
# Query-level domain filter: drop clearly non-motor queries
# ──────────────────────────────────────────────────────────────
REJECT_WORDS = {
    "namkeen", "extractor", "extrusion", "pellet", "pellets",
    "solvent", "desolventizer", "gold", "silver", "platinum",
    "refin", "food", "spice", "masala", "snack", "chips", "flour",
    "edible oil", "hexane", "vegetable oil", "soybean", "mustard oil",
    "groundnut oil", "sunflower oil", "cottonseed", "bimetallic screw",
    "injection molding", "blow molding", "blow moulding",
}

def is_rejected(query: str) -> bool:
    q = query.lower()
    return any(w in q for w in REJECT_WORDS)


def remap_attrs(raw_attrs: dict) -> dict:
    """Apply KEY_REMAP first (priority), then accept canonical keys as-is.
    Drops keys mapped to None or not in CANONICAL+KEY_REMAP."""
    out = {}
    for k, v in raw_attrs.items():
        k_lower = k.lower().strip()
        if k_lower in KEY_REMAP:
            new_k = KEY_REMAP[k_lower]
            if new_k is not None:
                out[new_k] = v
        elif k_lower in CANONICAL:
            out[k_lower] = v
        # else: unknown key → drop
    return out


def main():
    rows_read = rows_kept = rows_val = 0
    key_counter = Counter()
    train_rows = []

    # ── Source 1: product_train (remapped + filtered) ─────────────────────
    with open(INPUT_PROD, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                query = r.get("instruction", "").replace("Extract key-value attributes from this query:", "").strip()
                raw   = json.loads(r.get("output", "{}"))
            except Exception:
                continue

            rows_read += 1

            if is_rejected(query):
                continue

            attrs = remap_attrs(raw)
            if not attrs:
                continue

            # must have at least one key from motor-meaningful set
            MUST_HAVE_ONE = CANONICAL - {"feature", "grade", "color", "shape", "orientation"}
            if not any(k in MUST_HAVE_ONE for k in attrs):
                continue

            train_rows.append({"instruction": query,
                                "output": json.dumps(attrs, ensure_ascii=False)})
            rows_kept += 1

    print(f"Source 1 (product_train): read={rows_read}, kept={rows_kept}")

    # ── Source 2: ground truth gold_1k_v2.jsonl ───────────────────────────
    gt_count = 0
    if INPUT_GT.exists():
        with open(INPUT_GT, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    query = r.get("query", "").strip()
                    attrs = r.get("attributes", {})
                    if not query or not attrs:
                        continue
                    # Apply remap to catch any non-canonical GT keys
                    attrs = remap_attrs(attrs)
                    if not attrs:
                        continue
                    train_rows.append({"instruction": query,
                                       "output": json.dumps(attrs, ensure_ascii=False)})
                    gt_count += 1
                except Exception:
                    continue
        print(f"Source 2 (gold GT):       added={gt_count}")
    else:
        print(f"Source 2 (gold GT):       NOT FOUND at {INPUT_GT}")

    # ── Source 3: qmeans_v2_results.jsonl (key-canonicalized) ────────────
    qm_count = 0
    if INPUT_QMEANS.exists():
        with open(INPUT_QMEANS, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    query = r.get("query", "").strip()
                    raw   = r.get("attributes", {})
                    if not query or not raw:
                        continue
                    attrs = remap_attrs(raw)
                    # Only use high-quality qmeans rows (2+ canonical attrs)
                    if len(attrs) < 2:
                        continue
                    train_rows.append({"instruction": query,
                                       "output": json.dumps(attrs, ensure_ascii=False)})
                    qm_count += 1
                except Exception:
                    continue
        print(f"Source 3 (qmeans):        added={qm_count}")
    else:
        print(f"Source 3 (qmeans):        NOT FOUND at {INPUT_QMEANS}")

    print(f"\nTotal training rows before split: {len(train_rows)}")

    # ── Count keys across all sources ────────────────────────────────────
    for row in train_rows:
        for k in json.loads(row["output"]):
            key_counter[k] += 1

    # ── Shuffle and split 90/10 ───────────────────────────────────────────
    random.seed(42)
    random.shuffle(train_rows)
    split = int(len(train_rows) * 0.9)
    val_rows   = train_rows[split:]
    train_rows = train_rows[:split]

    with open(OUTPUT_TRAIN, "w", encoding="utf-8") as f:
        for r in train_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(OUTPUT_VAL, "w", encoding="utf-8") as f:
        for r in val_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Written: {len(train_rows)} train / {len(val_rows)} val")

    print(f"\nTop 30 keys in final training data:")
    for k, v in key_counter.most_common(30):
        canonical_mark = "✓" if k in CANONICAL else "?"
        print(f"  {canonical_mark} {k!r}: {v}")

    # Verify no non-canonical keys remain
    bad_keys = {k for k in key_counter if k not in CANONICAL}
    if bad_keys:
        print(f"\n⚠  NON-CANONICAL keys still present: {bad_keys}")
    else:
        print("\n✓ All keys are canonical!")


if __name__ == "__main__":
    main()
