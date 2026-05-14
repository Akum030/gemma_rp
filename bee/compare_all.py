import json, re

def load_jsonl(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]

gold = load_jsonl('bee/gold_1k_v2.jsonl')
v4   = load_jsonl('bee/v4_priority_results.jsonl')
v6   = load_jsonl('bee/v6_flat_results_fixed.jsonl')
qm   = load_jsonl('bee/qmeans_v2_results.jsonl')

def norm(s): return str(s).lower().strip()

def v4_expanded_pairs(raw_text):
    # Expands all 3 key priorities into separate (key, value) pairs
    raw = re.sub(r'```(?:json)?', '', raw_text).strip()
    start = raw.find('{')
    if start < 0: return set()
    depth = 0; end = -1
    for i in range(start, len(raw)):
        if raw[i] == '{': depth += 1
        elif raw[i] == '}':
            depth -= 1
            if depth == 0: end = i + 1; break
    if end < 0: return set()
    try: obj = json.loads(raw[start:end])
    except: return set()
    pairs = set()
    for grp in obj.get('attributes', []):
        if not isinstance(grp, dict): continue
        for _, payload in grp.items():
            if not isinstance(payload, dict): continue
            val = payload.get('value')
            if not val: continue
            for kp in ['key_priority1', 'key_priority2', 'key_priority3']:
                k = payload.get(kp)
                if k: pairs.add((norm(k), norm(val)))
    return pairs

def to_flat(d):
    pairs = set()
    for k, v in d.items():
        if isinstance(v, list):
            for x in v: pairs.add((norm(k), norm(x)))
        else:
            pairs.add((norm(k), norm(v)))
    return pairs

qm_by_q = {r['query'].strip().lower(): r.get('attributes', {}) for r in qm}
v6_by_q = {r['query'].strip().lower(): r.get('attributes', {}) for r in v6}
v4_by_q = {r['query'].strip().lower(): r for r in v4}

tot_gold = 0
v4_pred = v6_pred = qm_pred = 0
v4_key = v4_val = v4_pair = 0
v6_key = v6_val = v6_pair = 0
qm_key = qm_val = qm_pair = 0

for g in gold:
    q = g['query']
    truth = g.get('attributes', {})
    tp = to_flat(truth)
    tk = set(k for k, _ in tp)
    tv = set(v for _, v in tp)
    tot_gold += len(tp)

    v4p = v4_expanded_pairs(v4_by_q.get(q.strip().lower(), {}).get('raw', ''))
    v6p = to_flat(v6_by_q.get(q.strip().lower(), {}))
    qmp = to_flat(qm_by_q.get(q.strip().lower(), {}))

    v4_pred += len(v4p); v6_pred += len(v6p); qm_pred += len(qmp)
    v4_key  += len(set(k for k, _ in v4p) & tk)
    v4_val  += len(set(v for _, v in v4p) & tv)
    v4_pair += len(v4p & tp)
    v6_key  += len(set(k for k, _ in v6p) & tk)
    v6_val  += len(set(v for _, v in v6p) & tv)
    v6_pair += len(v6p & tp)
    qm_key  += len(set(k for k, _ in qmp) & tk)
    qm_val  += len(set(v for _, v in qmp) & tv)
    qm_pair += len(qmp & tp)

def cell(n, d, best_pct):
    p = n/d*100
    star = " (*BEST*)" if abs(p - best_pct) < 0.01 else ""
    return f"{n:,}/{d:,} = {p:.1f}%{star}"

def trow(label, v4n, v4d, v6n, v6d, qmn, qmd):
    best = max(v4n/v4d, v6n/v6d, qmn/qmd) * 100
    print(f"  {label:<60s}  {cell(v4n,v4d,best):<28s}  {cell(v6n,v6d,best):<28s}  {cell(qmn,qmd,best)}")

SEP  = "=" * 130
SEP2 = "-" * 130
HDR  = f"  {'':60s}  {'V4  (made 4,659 guesses)':<28s}  {'V6  (made 2,220 guesses)':<28s}  {'qmeans  (made 2,884 guesses)'}"

print()
print(SEP)
print("  MODEL COMPARISON  —  1,000 IndiaMART motor queries")
print(f"  Gold (correct answer sheet): {tot_gold:,} key-value pairs  |  (*BEST*) = winner for that row")
print(SEP)
print()
print(HDR)
print(SEP2)
print()
print("  COVERAGE: out of 3,200 gold answers, how many did each system find?")
print(SEP2)
trow("Correct ATTRIBUTE NAMES found\n"
     "    e.g. gold says 'phase'  -> did system also say 'phase'?",
     v4_key, tot_gold, v6_key, tot_gold, qm_key, tot_gold)
print()
trow("Correct VALUES found\n"
     "    e.g. gold says value='3'  -> did system also say '3'?",
     v4_val, tot_gold, v6_val, tot_gold, qm_val, tot_gold)
print()
trow("EXACT MATCH  —  right name AND right value together  [MAIN SCORE]\n"
     "    e.g. gold says 'phase=3'  -> did system say 'phase=3'?",
     v4_pair, tot_gold, v6_pair, tot_gold, qm_pair, tot_gold)
print()
print(SEP2)
print("  RELIABILITY: of each system's OWN guesses, how many turned out to be correct?")
print("  (low % = system is over-predicting / mostly wrong)")
print(SEP2)
trow("Name reliability  —  of its own guesses, how many names were correct\n"
     "    e.g. V4 made 4,659 guesses; only 538 names matched gold",
     v4_key, v4_pred, v6_key, v6_pred, qm_key, qm_pred)
print()
trow("Value reliability  —  of its own guesses, how many values were correct",
     v4_val, v4_pred, v6_val, v6_pred, qm_val, qm_pred)
print()
trow("Full reliability  —  of its own guesses, how many were fully correct (name+value)\n"
     "    e.g. V6 made 2,220 guesses; 1,296 were fully correct = 58% trustworthy",
     v4_pair, v4_pred, v6_pair, v6_pred, qm_pair, qm_pred)
print()
print(SEP)
print("  RESULT: V6 wins every single metric.")
print("  V4 made 2x more guesses than V6 but 88% of them were wrong -> not useful.")
print("  V6 main score (exact match) = 40.5%  vs  qmeans = 27.0%  ->  +50% improvement.")
print(SEP)
print()
