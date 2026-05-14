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
    if isinstance(v, list):
        return '; '.join(str(x) for x in v)
    return str(v)

def is_match(gold_val, pred_val):
    if pred_val is None:
        return False
    # Gold may have semicolons as multi-value
    gold_set = set(p.strip().lower() for p in str(gold_val).split(';'))
    # Pred may be a list
    if isinstance(pred_val, list):
        pred_set = set(norm(x) for x in pred_val)
    else:
        pred_set = {norm(pred_val)}
    return bool(gold_set & pred_set)

# ── DETAIL CSV ──────────────────────────────────────────────────────────────
detail_rows = []
qm_correct = qm_total = v6_correct = v6_total = 0

for g in gold_data:
    query = g['query']
    gold_attrs = g.get('attributes', {})
    qm_attrs   = qm_rows.get(query, {})
    v6_attrs   = v6_data.get(query, {})

    for key, gold_val in gold_attrs.items():
        qm_pred  = qm_attrs.get(norm(key))
        v6_pred  = v6_attrs.get(norm(key))
        qm_hit   = is_match(gold_val, qm_pred)
        v6_hit   = is_match(gold_val, v6_pred)

        detail_rows.append({
            'query':         query,
            'gold_key':      key,
            'gold_value':    val_to_str(gold_val),
            'qmeans_value':  val_to_str(qm_pred) if qm_pred is not None else '',
            'v6_value':      val_to_str(v6_pred)  if v6_pred  is not None else '',
            'qmeans_match':  'TRUE' if qm_hit else 'FALSE',
            'v6_match':      'TRUE' if v6_hit  else 'FALSE',
        })

        qm_total += 1; qm_correct += int(qm_hit)
        v6_total += 1; v6_correct += int(v6_hit)

detail_path = 'bee/comparison_detail.csv'
with open(detail_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['query','gold_key','gold_value','qmeans_value','v6_value','qmeans_match','v6_match'])
    w.writeheader()
    w.writerows(detail_rows)

print(f'Detail CSV written: {detail_path}  ({len(detail_rows)} rows)')

# ── SUMMARY CSV ─────────────────────────────────────────────────────────────
# Per-query stats
qm_q_correct = {}
v6_q_correct = {}
for row in detail_rows:
    q = row['query']
    qm_q_correct.setdefault(q, []).append(row['qmeans_match'] == 'TRUE')
    v6_q_correct.setdefault(q,  []).append(row['v6_match']  == 'TRUE')

qm_perfect = sum(1 for v in qm_q_correct.values() if all(v))
v6_perfect  = sum(1 for v in v6_q_correct.values()  if all(v))
qm_zero     = sum(1 for v in qm_q_correct.values() if not any(v))
v6_zero     = sum(1 for v in v6_q_correct.values()  if not any(v))

summary_rows = [
    {'metric': 'Total queries evaluated',          'qmeans': 1000,                        'gemma_v6': 1000},
    {'metric': 'Total gold attribute pairs',        'qmeans': qm_total,                    'gemma_v6': v6_total},
    {'metric': 'Correct matches (key + value)',     'qmeans': qm_correct,                  'gemma_v6': v6_correct},
    {'metric': 'Match rate %',                      'qmeans': f'{qm_correct/qm_total*100:.1f}%', 'gemma_v6': f'{v6_correct/v6_total*100:.1f}%'},
    {'metric': 'Queries with ALL attributes correct','qmeans': qm_perfect,                  'gemma_v6': v6_perfect},
    {'metric': 'Queries with ZERO correct',         'qmeans': qm_zero,                     'gemma_v6': v6_zero},
    {'metric': '',                                  'qmeans': '',                          'gemma_v6': ''},
    {'metric': '--- qmeans only stats ---',         'qmeans': '',                          'gemma_v6': ''},
    {'metric': 'Queries using synthetic product key','qmeans': sum(1 for a in qm_rows.values() if 'product' in a), 'gemma_v6': 'N/A'},
    {'metric': 'Total qmeans predictions made',     'qmeans': sum(len(a) for a in qm_rows.values()), 'gemma_v6': sum(len(a) for a in v6_data.values())},
]

summary_path = 'bee/comparison_summary.csv'
with open(summary_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['metric','qmeans','gemma_v6'])
    w.writeheader()
    w.writerows(summary_rows)

print(f'Summary CSV written: {summary_path}')
print()
print(f'qmeans: {qm_correct}/{qm_total} = {qm_correct/qm_total*100:.1f}%')
print(f'V6:     {v6_correct}/{v6_total} = {v6_correct/v6_total*100:.1f}%')
