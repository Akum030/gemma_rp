import json, csv

# Load data
with open('bee/qmeans_v2_results.csv', encoding='utf-8') as f:
    qm_rows = {r['query']: json.loads(r['attributes_json']) for r in csv.DictReader(f)}

with open('bee/gold_1k_v2.jsonl', encoding='utf-8') as f:
    gold_data = [json.loads(l) for l in f if l.strip()]

with open('bee/v6_flat_results_fixed.jsonl', encoding='utf-8') as f:
    v6_data = {json.loads(l)['query']: json.loads(l).get('attributes', {}) for l in f if l.strip()}

def norm(s):
    return str(s).lower().strip()

def val_to_str(v):
    if v is None: return ''
    if isinstance(v, list): return '; '.join(str(x) for x in v)
    return str(v)

def val_matches(gold_val, pred_val):
    if pred_val is None: return False
    gold_set = set(p.strip().lower() for p in str(gold_val).split(';'))
    pred_set = set(norm(x) for x in pred_val) if isinstance(pred_val, list) else {norm(pred_val)}
    return bool(gold_set & pred_set)

# ── Find max attribute counts across all queries ─────────────────────────────
max_gold = max(len(g.get('attributes', {})) for g in gold_data)
max_qm   = max(len(qm_rows.get(g['query'], {})) for g in gold_data)
max_v6   = max(len(v6_data.get(g['query'], {})) for g in gold_data)

print(f'Max gold attrs: {max_gold}  |  Max qmeans attrs: {max_qm}  |  Max gemma attrs: {max_v6}')

# ── Build header ─────────────────────────────────────────────────────────────
header = ['query']
for i in range(1, max_gold + 1):
    header += [f'gt_key{i}', f'gt_val{i}']
header.append('')   # gap column
for i in range(1, max_qm + 1):
    header += [f'qmeans_key{i}', f'qmeans_val{i}']
header.append('')   # gap column
for i in range(1, max_v6 + 1):
    header += [f'gemma_key{i}', f'gemma_val{i}']
header.append('')   # gap column
header += [
    'qmeans_key_match',       # gold keys found in qmeans (regardless of value)
    'gemma_key_match',        # gold keys found in gemma
    'qmeans_kv_match',        # gold (key+value) pairs correct in qmeans
    'gemma_kv_match',         # gold (key+value) pairs correct in gemma
    'qmeans_val_any_match',   # gold values found anywhere in qmeans (ignoring key names)
    'gemma_val_any_match',    # gold values found anywhere in gemma (ignoring key names)
    'total_gold_attrs',       # total gold attrs for this query
]

# ── Build data rows ───────────────────────────────────────────────────────────
rows = []
# Accumulators for summary
tot_gold = tot_qm_key = tot_v6_key = tot_qm_kv = tot_v6_kv = tot_qm_val_any = tot_v6_val_any = 0

for g in gold_data:
    query      = g['query']
    gold_attrs = g.get('attributes', {})
    qm_attrs   = qm_rows.get(query, {})
    v6_attrs   = v6_data.get(query, {})

    row = [query]

    # Gold attributes (padded to max_gold)
    gold_items = list(gold_attrs.items())
    for i in range(max_gold):
        if i < len(gold_items):
            row += [gold_items[i][0], val_to_str(gold_items[i][1])]
        else:
            row += ['', '']
    row.append('')  # gap

    # qmeans attributes (padded to max_qm)
    qm_items = list(qm_attrs.items())
    for i in range(max_qm):
        if i < len(qm_items):
            row += [qm_items[i][0], val_to_str(qm_items[i][1])]
        else:
            row += ['', '']
    row.append('')  # gap

    # Gemma attributes (padded to max_v6)
    v6_items = list(v6_attrs.items())
    for i in range(max_v6):
        if i < len(v6_items):
            row += [v6_items[i][0], val_to_str(v6_items[i][1])]
        else:
            row += ['', '']
    row.append('')  # gap

    # ── Metrics ──────────────────────────────────────────────────────────────
    gold_keys = set(norm(k) for k in gold_attrs)
    qm_keys   = set(norm(k) for k in qm_attrs)
    v6_keys   = set(norm(k) for k in v6_attrs)

    qm_key_match = len(gold_keys & qm_keys)
    v6_key_match = len(gold_keys & v6_keys)

    qm_kv_match = sum(1 for k, v in gold_attrs.items() if val_matches(v, qm_attrs.get(norm(k))))
    v6_kv_match = sum(1 for k, v in gold_attrs.items() if val_matches(v, v6_attrs.get(norm(k))))

    # All gold values flattened (semicolons split)
    all_gold_vals = set()
    for v in gold_attrs.values():
        for p in str(v).split(';'):
            all_gold_vals.add(p.strip().lower())

    def flatten_vals(attrs):
        out = set()
        for v in attrs.values():
            if isinstance(v, list):
                for x in v: out.add(norm(x))
            else:
                out.add(norm(v))
        return out

    qm_val_any = len(all_gold_vals & flatten_vals(qm_attrs))
    v6_val_any = len(all_gold_vals & flatten_vals(v6_attrs))

    row += [qm_key_match, v6_key_match, qm_kv_match, v6_kv_match,
            qm_val_any, v6_val_any, len(gold_attrs)]

    rows.append(row)

    # Accumulate
    tot_gold     += len(gold_attrs)
    tot_qm_key   += qm_key_match
    tot_v6_key   += v6_key_match
    tot_qm_kv    += qm_kv_match
    tot_v6_kv    += v6_kv_match
    tot_qm_val_any += qm_val_any
    tot_v6_val_any += v6_val_any

# ── Write detail CSV ─────────────────────────────────────────────────────────
out_path = 'bee/wide_comparison.csv'
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows)

print(f'Detail CSV written: {out_path}  ({len(rows)} rows, {len(header)} columns)')

# ── Write summary CSV ────────────────────────────────────────────────────────
summary = [
    ['metric', 'qmeans', 'gemma_v6'],
    ['Total queries',                                   1000,    1000],
    ['Total gold attribute pairs',                      tot_gold, tot_gold],
    ['Key match (gold key found in prediction)',         tot_qm_key,   tot_v6_key],
    ['Key match %',                                     f'{tot_qm_key/tot_gold*100:.1f}%', f'{tot_v6_key/tot_gold*100:.1f}%'],
    ['Key+Value match (both correct)',                  tot_qm_kv,    tot_v6_kv],
    ['Key+Value match %',                               f'{tot_qm_kv/tot_gold*100:.1f}%',  f'{tot_v6_kv/tot_gold*100:.1f}%'],
    ['Value match ignoring key names',                  tot_qm_val_any, tot_v6_val_any],
    ['Value match % (ignoring keys)',                   f'{tot_qm_val_any/tot_gold*100:.1f}%', f'{tot_v6_val_any/tot_gold*100:.1f}%'],
    [''],
    ['--- qmeans notes ---', '', ''],
    ['Queries using synthetic product key (never in gold)',
     sum(1 for a in qm_rows.values() if 'product' in a), 'N/A'],
    ['Total predictions made',
     sum(len(a) for a in qm_rows.values()),
     sum(len(a) for a in v6_data.values())],
]

sum_path = 'bee/wide_summary.csv'
with open(sum_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerows(summary)

print(f'Summary CSV written: {sum_path}')
print()
print(f'Key match:   qmeans={tot_qm_key}/{tot_gold} ({tot_qm_key/tot_gold*100:.1f}%)  '
      f'gemma={tot_v6_key}/{tot_gold} ({tot_v6_key/tot_gold*100:.1f}%)')
print(f'KV match:    qmeans={tot_qm_kv}/{tot_gold} ({tot_qm_kv/tot_gold*100:.1f}%)  '
      f'gemma={tot_v6_kv}/{tot_gold} ({tot_v6_kv/tot_gold*100:.1f}%)')
print(f'Val any:     qmeans={tot_qm_val_any}/{tot_gold} ({tot_qm_val_any/tot_gold*100:.1f}%)  '
      f'gemma={tot_v6_val_any}/{tot_gold} ({tot_v6_val_any/tot_gold*100:.1f}%)')
