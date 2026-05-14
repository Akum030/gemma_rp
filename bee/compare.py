"""
Three-way comparison:  Gemma model results  vs  qmeans production API  vs  optional gold (Claude) ground truth.

Inputs (defaults assume agent/ folder layout):
  --gemma   <path>.csv|.jsonl   (CSV with norm_attributes_json column, OR jsonl with norm_attributes)
  --qmeans  <path>.jsonl        (qmeans_results.jsonl produced by run_qmeans.py)
  --gold    <path>.jsonl        (optional ground-truth ideal_outputs.jsonl)
  --canon                       (use the 69-key canonical vocabulary for key-validity metric)
  --report  <path>.txt          (output report)

Metrics produced:
  * Parse rate (% queries that returned a valid JSON object)
  * Mean / median key count
  * Key-vocabulary distribution (top-N keys, # unique keys)
  * % of keys that are in the canonical 69-key vocab
  * Pairwise key-overlap rate (Jaccard) per query, averaged
  * Pairwise value-exact-match per shared key, averaged
  * Vs gold (if provided): key precision / recall / F1, value exact match, value substring match
"""
import argparse, csv, json, os, sys, statistics
from collections import Counter, defaultdict

# 69-key canonical vocab from product_train_with_keys.jsonl
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


def load_attrs(path):
    """Returns dict: query -> attributes_dict   (empty dict if not parseable)"""
    out = {}
    if path.endswith(".jsonl"):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                row = json.loads(line)
                q = row["query"]
                attrs = row.get("norm_attributes") or row.get("attributes") or {}
                out[q] = attrs if isinstance(attrs, dict) else {}
        return out
    # CSV path: prefer norm_attributes_json column; else attributes_json
    with open(path, encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            q = r["query"]
            j = (r.get("norm_attributes_json") or r.get("attributes_json") or "").strip()
            try:
                d = json.loads(j) if j else {}
                out[q] = d if isinstance(d, dict) else {}
            except Exception:
                out[q] = {}
    return out


def norm_val(v):
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x).strip().lower() for x in v)
    return str(v).strip().lower()


def parse_rate(d):
    return sum(1 for v in d.values() if v) / max(1, len(d))


def vocab_stats(d):
    keys = Counter()
    for v in d.values():
        for k in v.keys():
            keys[k] += 1
    return keys


def in_canon(d):
    """Fraction of keys (across all queries) that are in the canonical vocab."""
    total = 0; in_v = 0
    for v in d.values():
        for k in v.keys():
            total += 1
            if k.lower() in CANON_KEYS:
                in_v += 1
    return (in_v / max(1, total))


def pairwise_metrics(a, b):
    """For shared queries, compute Jaccard(keys) + value-exact-match per shared key."""
    shared = set(a) & set(b)
    jac, exact = [], []
    for q in shared:
        ka, kb = set(a[q]), set(b[q])
        if not ka and not kb:
            continue
        union = ka | kb
        inter = ka & kb
        jac.append(len(inter) / max(1, len(union)))
        if inter:
            n_eq = sum(1 for k in inter if norm_val(a[q][k]) == norm_val(b[q][k]))
            exact.append(n_eq / len(inter))
    return {
        "queries_compared": len(jac),
        "key_jaccard_mean": statistics.mean(jac) if jac else 0,
        "value_exact_mean": statistics.mean(exact) if exact else 0,
    }


def vs_gold(pred, gold):
    """Per-query precision / recall over keys, plus value exact / substring match on shared keys."""
    qs = [q for q in gold if q in pred]
    P, R, F1, V_exact, V_sub = [], [], [], [], []
    for q in qs:
        p, g = pred[q], gold[q]
        kp, kg = set(p), set(g)
        tp = len(kp & kg)
        prec = tp / max(1, len(kp))
        rec  = tp / max(1, len(kg))
        f1 = 2 * prec * rec / max(1e-9, prec + rec)
        P.append(prec); R.append(rec); F1.append(f1)
        if kp & kg:
            ve = sum(1 for k in (kp & kg) if norm_val(p[k]) == norm_val(g[k])) / len(kp & kg)
            vs = sum(1 for k in (kp & kg) if norm_val(g[k]) in norm_val(p[k]) or norm_val(p[k]) in norm_val(g[k])) / len(kp & kg)
            V_exact.append(ve); V_sub.append(vs)
    return {
        "queries_compared": len(qs),
        "key_precision": statistics.mean(P) if P else 0,
        "key_recall":    statistics.mean(R) if R else 0,
        "key_f1":        statistics.mean(F1) if F1 else 0,
        "value_exact":   statistics.mean(V_exact) if V_exact else 0,
        "value_substring": statistics.mean(V_sub) if V_sub else 0,
    }


def report_block(name, d, lines):
    keys = vocab_stats(d)
    counts = [len(v) for v in d.values()]
    lines.append(f"### {name}")
    lines.append(f"  queries:                    {len(d)}")
    lines.append(f"  parse rate (non-empty):     {parse_rate(d)*100:.1f}%")
    lines.append(f"  mean keys/query:            {statistics.mean(counts) if counts else 0:.2f}")
    lines.append(f"  median keys/query:          {statistics.median(counts) if counts else 0}")
    lines.append(f"  unique keys total:          {len(keys)}")
    lines.append(f"  keys in canonical vocab:    {in_canon(d)*100:.1f}%")
    lines.append(f"  top 15 keys: {keys.most_common(15)}")
    lines.append("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gemma", required=True)
    ap.add_argument("--qmeans", required=True)
    ap.add_argument("--gold", default=None)
    ap.add_argument("--report", required=True)
    ap.add_argument("--qmeans-alias", action="store_true",
                    help="Alias qmeans 'product' key -> 'part type' for fair comparison.")
    args = ap.parse_args()

    gemma  = load_attrs(args.gemma)
    qmeans = load_attrs(args.qmeans)
    gold   = load_attrs(args.gold) if args.gold else {}

    # Fairness alias: qmeans uses 'product' for the probable-product token,
    # while gold/gemma use 'part type'. Map only when 'part type' missing.
    if args.qmeans_alias:
        for q, a in qmeans.items():
            if "product" in a and "part type" not in a:
                a["part type"] = a.pop("product")
            elif "product" in a:
                a.pop("product", None)

    lines = []
    lines.append(f"# Comparison report")
    lines.append(f"  gemma:  {args.gemma}  ({len(gemma)} queries)")
    lines.append(f"  qmeans: {args.qmeans} ({len(qmeans)} queries)")
    if gold:
        lines.append(f"  gold:   {args.gold}   ({len(gold)} queries)")
    lines.append("")

    report_block("Gemma (fine-tuned model)", gemma, lines)
    report_block("Qmeans (production API)",  qmeans, lines)
    if gold:
        report_block("Gold (Claude ground-truth)", gold, lines)

    lines.append("## Pairwise (gemma  vs  qmeans)")
    pm = pairwise_metrics(gemma, qmeans)
    for k, v in pm.items():
        lines.append(f"  {k:25s} {v:.3f}" if isinstance(v, float) else f"  {k:25s} {v}")
    lines.append("")

    if gold:
        lines.append("## Vs Gold (Claude)")
        gg = vs_gold(gemma, gold)
        gq = vs_gold(qmeans, gold)
        lines.append(f"{'metric':25s} {'gemma':>10s} {'qmeans':>10s}")
        for k in gg:
            v1 = gg[k]; v2 = gq[k]
            if isinstance(v1, float):
                lines.append(f"{k:25s} {v1*100:>9.1f}% {v2*100:>9.1f}%")
            else:
                lines.append(f"{k:25s} {v1:>10} {v2:>10}")
        lines.append("")

    out = "\n".join(lines)
    print(out)
    os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"\nWritten -> {args.report}")


if __name__ == "__main__":
    main()
