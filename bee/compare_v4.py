"""
Dual-dimension comparator for V4 (Gemma-4 nested-priority) vs qmeans_v2.

Dimension A (apples-to-apples):
    Flat token-level F1 on (key, value) extraction vs gold_1k_v2.
    Both systems are reduced to a flat dict of attribute -> value.

Dimension B (priority — V4-only, qmeans cannot do this):
    priority@1 — does V4's `attribute_priority1.value` match the gold's
    PRIMARY attribute value (the part_type / product_type when present,
    otherwise the first attribute)?

Inputs (workspace paths):
    bee/gold_1k_v2.jsonl
    bee/qmeans_v2_results.jsonl
    bee/v4_priority_results.jsonl   (produced by inference_v4.py)
"""
from __future__ import annotations
import json, re, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOLD     = ROOT / "gold_1k_v2.jsonl"
QMEANS   = ROOT / "qmeans_v2_results.jsonl"
V4       = ROOT / "v4_priority_results.jsonl"

# ---------- normalisation ----------
_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]")

def norm(s) -> str:
    if s is None:
        return ""
    s = str(s).lower().strip()
    s = _PUNCT.sub(" ", s)
    s = _WS.sub(" ", s).strip()
    return s

PRIMARY_KEYS = {"part type", "product_type", "product type", "product", "part_type"}

# ---------- loading ----------
def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

# ---------- flat F1 ----------
def kv_set(d: dict) -> set:
    """Return set of normalised "key=value" pairs."""
    out = set()
    for k, v in (d or {}).items():
        nk = norm(k)
        nv = norm(v)
        if nk and nv:
            out.add(f"{nk}={nv}")
    return out

def value_set(d: dict) -> set:
    """Just the set of values (key-agnostic, for fairer comparison vs qmeans
       which only ever produces 'product')."""
    return {norm(v) for v in (d or {}).values() if norm(v)}

def f1(pred: set, gold: set):
    if not pred and not gold: return 1.0, 1.0, 1.0
    if not pred or not gold:  return 0.0, 0.0, 0.0
    tp = len(pred & gold)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gold) if gold else 0.0
    f = 2*p*r/(p+r) if (p+r) else 0.0
    return p, r, f

# ---------- value-token F1 (for fair comparison: ignore key names) ----------
def tok_set(d: dict) -> set:
    out = set()
    for v in (d or {}).values():
        for t in norm(v).split():
            if t:
                out.add(t)
    return out

# ---------- priority@1 ----------
def gold_primary(attrs: dict) -> str:
    if not attrs: return ""
    for k in attrs:
        if norm(k) in {norm(x) for x in PRIMARY_KEYS}:
            return norm(attrs[k])
    # fallback: first
    first_k = next(iter(attrs))
    return norm(attrs[first_k])

def v4_primary(flat: dict) -> str:
    if not flat: return ""
    # inference_v4 puts attribute_priority1.value first. Check known keys.
    for cand in ("product_type", "part_type", "part type", "product"):
        if cand in flat:
            return norm(flat[cand])
    first_k = next(iter(flat))
    return norm(flat[first_k])

# ---------- main ----------
def index_by_query(items):
    return {row["query"]: row for row in items}

def evaluate(name: str, by_q: dict, gold_rows: list, do_priority: bool, pred_field: str = "attributes"):
    macro_p = macro_r = macro_f = 0.0
    macro_vp = macro_vr = macro_vf = 0.0
    macro_tp = macro_tr = macro_tf = 0.0
    pri_hits = pri_total = 0
    n_with_pred = 0
    for g in gold_rows:
        q = g["query"]
        gold_attrs = g.get("attributes", {}) or {}
        pred_row = by_q.get(q)
        pred = (pred_row or {}).get(pred_field, {}) or {}
        if pred_row is not None: n_with_pred += 1

        p, r, ff = f1(kv_set(pred), kv_set(gold_attrs))
        macro_p += p; macro_r += r; macro_f += ff

        vp, vr, vf = f1(value_set(pred), value_set(gold_attrs))
        macro_vp += vp; macro_vr += vr; macro_vf += vf

        tp, tr, tf = f1(tok_set(pred), tok_set(gold_attrs))
        macro_tp += tp; macro_tr += tr; macro_tf += tf

        if do_priority:
            gp = gold_primary(gold_attrs)
            vp_ = v4_primary(pred)
            if gp:
                pri_total += 1
                # accept either exact, or one contains the other
                if gp and vp_ and (gp == vp_ or gp in vp_ or vp_ in gp):
                    pri_hits += 1

    n = len(gold_rows) or 1
    res = {
        "system": name,
        "n_gold": len(gold_rows),
        "n_predictions_present": n_with_pred,
        "kv_strict_F1":   round(100*macro_f/n,  2),
        "kv_strict_P":    round(100*macro_p/n,  2),
        "kv_strict_R":    round(100*macro_r/n,  2),
        "value_only_F1":  round(100*macro_vf/n, 2),
        "token_F1":       round(100*macro_tf/n, 2),
        "token_P":        round(100*macro_tp/n, 2),
        "token_R":        round(100*macro_tr/n, 2),
    }
    if do_priority:
        res["priority_at_1"] = round(100*pri_hits/pri_total, 2) if pri_total else 0.0
        res["priority_n"]    = pri_total
    return res

def fmt(d):
    return "  " + "\n  ".join(f"{k:25s}: {v}" for k, v in d.items())

def main():
    if not V4.exists():
        print(f"!! {V4} not found. Run inference_v4.py first.", file=sys.stderr)
        sys.exit(2)
    gold = load_jsonl(GOLD)
    qm   = index_by_query(load_jsonl(QMEANS))
    v4   = index_by_query(load_jsonl(V4))

    print("=" * 60)
    print(f"Gold: {len(gold)} queries  ({GOLD.name})")
    print("=" * 60)

    qm_res = evaluate("qmeans_v2", qm, gold, do_priority=False, pred_field="attributes")
    v4_res = evaluate("V4_gemma4_priority", v4, gold, do_priority=True, pred_field="flat")

    print("\n--- qmeans_v2 ---")
    print(fmt(qm_res))
    print("\n--- V4 (gemma-4 e4b nested priority) ---")
    print(fmt(v4_res))

    print("\n" + "=" * 60)
    print("HEAD-TO-HEAD (apples-to-apples on the key/value extraction task)")
    print("=" * 60)
    keys = ["kv_strict_F1", "value_only_F1", "token_F1", "token_P", "token_R"]
    print(f"  {'metric':20s}  {'qmeans':>10s}  {'V4':>10s}  {'delta':>10s}")
    for k in keys:
        delta = v4_res[k] - qm_res[k]
        sign = "+" if delta >= 0 else ""
        print(f"  {k:20s}  {qm_res[k]:>10.2f}  {v4_res[k]:>10.2f}  {sign}{delta:>9.2f}")

    print("\n  V4-only metric (qmeans has no concept of priority):")
    print(f"  priority_at_1       : {v4_res['priority_at_1']:.2f}%  "
          f"(over {v4_res['priority_n']} gold queries with a primary attribute)")

    # Examples — first 6 disagreements where V4 wins on token_F1
    print("\n" + "=" * 60)
    print("SAMPLE: queries where V4 beats qmeans (token_F1)")
    print("=" * 60)
    shown = 0
    for g in gold:
        if shown >= 8: break
        q = g["query"]
        ga = g.get("attributes", {})
        qa = (qm.get(q) or {}).get("attributes", {})
        va = (v4.get(q) or {}).get("flat", {})
        _,_,fq = f1(tok_set(qa), tok_set(ga))
        _,_,fv = f1(tok_set(va), tok_set(ga))
        if fv > fq + 0.05:
            print(f"\n  Q: {q}")
            print(f"   gold  : {ga}")
            print(f"   qmeans: {qa}")
            print(f"   V4    : {va}")
            shown += 1

if __name__ == "__main__":
    main()
