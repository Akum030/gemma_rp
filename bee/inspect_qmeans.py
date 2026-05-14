import json
from collections import Counter
lines = open('bee/qmeans_results.jsonl', encoding='utf-8').readlines()
print('total:', len(lines))
for i in range(3):
    print(lines[i].strip())
ks = Counter(); empty = 0; only_p = 0; ok = 0
for l in lines:
    r = json.loads(l)
    if r.get('ok'): ok += 1
    a = r.get('attributes') or {}
    ks.update(a.keys())
    if not a: empty += 1
    if set(a.keys()) == {'product'}: only_p += 1
print('ok:', ok, 'empty:', empty, 'only_product:', only_p)
print('top keys:', ks.most_common(25))
