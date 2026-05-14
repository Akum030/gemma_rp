"""
V5 comparator — compares V5 (flat JSON) vs qmeans vs gold.

Works identically to compare_v4.py but reads v5_flat_results.jsonl
(which has {"query": ..., "attributes": {...}}) — same format as qmeans.

Usage: python bee/compare_v5.py [--gold bee/gold_opus_v3.jsonl]
"""
from __future__ import annotations
import json, re, os, sys, argparse
from pathlib import Path

ROOT   = Path(__file__).resolve().parent
QMEANS = ROOT / "qmeans_v2_results.jsonl"

_WS    = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")

# ---- key normalization (synonym → canonical) ----
# Maps qmeans keys, V5 keys, and any synonym → ground truth canonical key
KEY_CANON = {
    # product / part type synonyms  (qmeans mostly uses "product", GT uses "part type")
    "product_type": "part type", "product type": "part type", "type": "part type",
    "part_type": "part type", "device_type": "part type",
    "item_type": "part type", "component": "part type", "product": "part type",
    "motor part type": "part type",   # qmeans uses this key
    # brand synonyms
    "manufacturer": "brand", "company": "brand", "make": "brand", "maker": "brand",
    # model synonyms
    "model": "model name/number", "model_number": "model name/number",
    "model number": "model name/number", "part_number": "model name/number",
    "part number": "model name/number", "model/type": "model name/number",
    "product number": "model name/number",
    # power synonyms
    "motor_power": "power", "wattage": "power", "power_rating": "power",
    "rated power": "power", "output power": "power", "motor power": "power",
    "hp": "horsepower", "horse power": "horsepower", "motor hp": "horsepower",
    "motor horsepower": "horsepower",
    # RPM / speed — ground truth uses "rpm" (74 occurrences) as canonical
    # qmeans uses "speed" for RPM values like "1450 rpm"
    "speed": "rpm", "rated_speed": "rpm", "rotation_speed": "rpm",
    "full load rpm": "rpm", "rated speed": "rpm",
    # driven type — qmeans uses "motor type", GT uses "driven type"
    "motor_type": "driven type", "motor type": "driven type", "driven_type": "driven type",
    # phase — qmeans uses "no of phase"
    "no of phase": "phase",
    # power source synonyms
    "power_source": "power source",
    # mounting synonyms
    "mounting_type": "mounting type", "mounting": "mounting type",
    # ip rating synonyms
    "ip_rating": "ip rating", "ip protection": "ip rating",
    # insulation synonyms
    "insulation_class": "insulation class", "insulation": "insulation class",
    # frame size synonyms
    "frame_size": "frame size",
    # color synonyms
    "colour": "color",
    # frequency synonyms
    "frequency_hertz": "frequency", "operating_frequency": "frequency",
    # size/dimension synonyms
    "dimension": "size", "dimensions": "size",
    # capacity synonyms
    "max_capacity": "capacity", "load_capacity": "capacity",
    # torque synonyms
    "output_torque": "torque", "rated_torque": "torque",
    # country synonyms
    "country_of_origin": "country of origin",
    # automation synonyms
    "automation_grade": "automation grade", "operation_mode": "automation grade",
    # voltage synonyms
    "input voltage": "voltage", "voltage rating": "voltage",
    # starter type synonyms
    "starter_type": "starter type",
    # usage/application synonyms
    "application": "usage",
    # feature synonyms
    "features": "feature",
}

# ---- value normalization for specific keys ----
# Normalize phase values: qmeans returns "3 phase", GT has "3"
_PHASE_NORM = {
    "single phase": "1", "1 phase": "1", "one phase": "1",
    "two phase": "2", "2 phase": "2",
    "three phase": "3", "3 phase": "3", "3phase": "3", "three-phase": "3",
}

def normalize_value(key: str, val: str) -> str:
    """Normalize value for specific keys to match ground truth conventions."""
    v = val.lower().strip()
    if key == "phase":
        return _PHASE_NORM.get(v, v)
    return val


def normalize_key(k: str) -> str:
    k = k.strip().lower()
    return KEY_CANON.get(k, k)


def norm(s) -> str:
    if s is None:
        return ""
    s = str(s).lower().strip()
    s = _PUNCT.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    return s


# ---- loading ----
def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


# ---- metrics ----
def kv_set(d: dict) -> set:
    out = set()
    for k, v in (d or {}).items():
        nk = normalize_key(k)
        nv = norm(normalize_value(nk, str(v)))
        if nk and nv:
            out.add(f"{nk}={nv}")
    return out


def value_set(d: dict) -> set:
    return {norm(v) for v in (d or {}).values() if norm(v)}


def tok_set(d: dict) -> set:
    out = set()
    for v in (d or {}).values():
        for t in norm(v).split():
            if t:
                out.add(t)
    return out


def f1(pred: set, gold: set):
    if not pred and not gold:
        return 1.0, 1.0, 1.0
    if not pred or not gold:
        return 0.0, 0.0, 0.0
    tp = len(pred & gold)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gold) if gold else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def evaluate(name: str, by_q: dict, gold_rows: list, pred_field: str = "attributes"):
    mp = mr = mf = 0.0
    mvp = mvr = mvf = 0.0
    mtp = mtr = mtf = 0.0
    n_with_pred = 0
    for g in gold_rows:
        q = g["query"]
        gold_attrs = g.get("attributes", {}) or {}
        pred_row = by_q.get(q)
        pred = (pred_row or {}).get(pred_field, {}) or {}
        if pred_row is not None:
            n_with_pred += 1

        p, r, ff = f1(kv_set(pred), kv_set(gold_attrs))
        mp += p; mr += r; mf += ff

        vp, vr, vf = f1(value_set(pred), value_set(gold_attrs))
        mvp += vp; mvr += vr; mvf += vf

        tp, tr, tf = f1(tok_set(pred), tok_set(gold_attrs))
        mtp += tp; mtr += tr; mtf += tf

    n = len(gold_rows) or 1
    return {
        "system": name,
        "n_gold": len(gold_rows),
        "n_predictions": n_with_pred,
        "kv_strict_F1":  round(100 * mf  / n, 2),
        "kv_strict_P":   round(100 * mp  / n, 2),
        "kv_strict_R":   round(100 * mr  / n, 2),
        "value_only_F1": round(100 * mvf / n, 2),
        "token_F1":      round(100 * mtf / n, 2),
        "token_P":       round(100 * mtp / n, 2),
        "token_R":       round(100 * mtr / n, 2),
    }


def index_by_query(items):
    return {row["query"]: row for row in items}


def print_result(res: dict):
    print(f"\n{'='*60}")
    print(f"  System : {res['system']}")
    print(f"  Gold   : {res['n_gold']}  Predictions: {res['n_predictions']}")
    print(f"  kv_strict_F1  : {res['kv_strict_F1']:6.2f}%  "
          f"(P={res['kv_strict_P']:.2f}  R={res['kv_strict_R']:.2f})")
    print(f"  value_only_F1 : {res['value_only_F1']:6.2f}%")
    print(f"  token_F1      : {res['token_F1']:6.2f}%  "
          f"(P={res['token_P']:.2f}  R={res['token_R']:.2f})")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", default=str(ROOT / "gold_1k_v2.jsonl"),
                        help="Path to gold file (default: gold_1k_v2.jsonl)")
    parser.add_argument("--v5", default=str(ROOT / "v5_flat_results.jsonl"),
                        help="Path to V5 results (default: v5_flat_results.jsonl)")
    args = parser.parse_args()

    gold_path = args.gold
    v5_path   = args.v5

    if not os.path.exists(gold_path):
        print(f"Gold not found: {gold_path}", file=sys.stderr); sys.exit(1)
    if not os.path.exists(QMEANS):
        print(f"qmeans not found: {QMEANS}", file=sys.stderr); sys.exit(1)

    gold_rows  = load_jsonl(gold_path)
    qmeans_rows = load_jsonl(QMEANS)
    qmeans_by_q = index_by_query(qmeans_rows)

    print(f"Gold   : {len(gold_rows)} queries  ({gold_path})")
    print(f"qmeans : {len(qmeans_rows)} predictions")

    # Evaluate qmeans
    res_qmeans = evaluate("qmeans_v2", qmeans_by_q, gold_rows, pred_field="attributes")
    print_result(res_qmeans)

    # Evaluate V5 if available
    if os.path.exists(v5_path):
        v5_rows  = load_jsonl(v5_path)
        v5_by_q  = index_by_query(v5_rows)
        print(f"V5     : {len(v5_rows)} predictions  ({v5_path})")
        res_v5 = evaluate("V5_flat", v5_by_q, gold_rows, pred_field="attributes")
        print_result(res_v5)

        # Final verdict
        print("\n" + "=" * 60)
        v5_f1 = res_v5["kv_strict_F1"]
        qm_f1 = res_qmeans["kv_strict_F1"]
        if v5_f1 > qm_f1:
            print(f"  ✅ V5 BEATS qmeans!  V5={v5_f1:.2f}% vs qmeans={qm_f1:.2f}%")
        else:
            gap = qm_f1 - v5_f1
            print(f"  ❌ V5 still behind.  V5={v5_f1:.2f}% vs qmeans={qm_f1:.2f}%  (gap={gap:.2f}%)")
        print("=" * 60)

        # Save comparison
        out_path = ROOT / "compare_v5_results.txt"
        with open(out_path, "w") as f:
            for res in [res_qmeans, res_v5]:
                f.write(json.dumps(res, indent=2) + "\n\n")
        print(f"\nSaved to {out_path}")
    else:
        print(f"\nV5 results not found yet: {v5_path}")
        print("Run inference_v5.py first.")


if __name__ == "__main__":
    main()
