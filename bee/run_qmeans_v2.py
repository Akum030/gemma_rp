"""Fixed qmeans collector: reads attr_name AND others[] from each token.
Preference: q-means/2.0.1 > attr-v2 > probable-product."""
import csv, json, os, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLD_FILE = os.path.join(ROOT, "bee", "gold_1k.jsonl")
OUT_JSONL = os.path.join(ROOT, "bee", "qmeans_v2_results.jsonl")
OUT_CSV   = os.path.join(ROOT, "bee", "qmeans_v2_results.csv")
URL = "http://34.93.70.216:8009/attribute-search"

MODEL_RANK = {"q-means/2.0.1": 3, "attr-v2": 2, "probable-product": 1}

def load_queries():
    out = []
    with open(GOLD_FILE, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line)["query"])
            except Exception:
                pass
    return out

def extract(data):
    """Walk attributes; emit {attr_name: attr_value}.
    For each token entry, consider top-level + others[]; pick best by MODEL_RANK.
    Skip entries with attr_name in {"", "-"} (they have no usable key).
    Probable-product entries (attr_name == "-", attr_type == "product") are
    stored under synthetic key "product"; keep the longest value."""
    attrs = {}
    products = []
    for token, info in (data.get("attributes") or {}).items():
        candidates = [info] + list(info.get("others") or [])
        # pick best named candidate
        best = None
        for c in candidates:
            name = (c.get("attr_name") or "").strip().lower()
            val = (c.get("attr_value") or "").strip()
            if not name or name == "-" or not val:
                continue
            score = MODEL_RANK.get(c.get("model", ""), 0)
            if best is None or score > best[0]:
                best = (score, name, val)
        if best:
            _, name, val = best
            # keep first occurrence; if same key seen, keep longer value
            if name not in attrs or len(val) > len(attrs[name]):
                attrs[name] = val
        # also collect probable-product values (attr_name "-" + type product)
        for c in candidates:
            if (c.get("attr_name") or "").strip() == "-" and c.get("attr_type") == "product":
                v = (c.get("attr_value") or "").strip()
                if v:
                    products.append(v)
    if products:
        # longest probable-product token (most specific)
        attrs["product"] = max(products, key=len)
    return attrs

def qmeans(query, retries=3):
    params = urllib.parse.urlencode({"query": query, "source": "test.run"})
    url = f"{URL}?{params}"
    last = None
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "agent/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8"))
            return {"query": query, "attributes": extract(data), "ok": True}
        except Exception as e:
            last = str(e); time.sleep(0.5)
    return {"query": query, "attributes": {}, "ok": False, "error": last}

def main():
    queries = load_queries()
    print(f"Loaded {len(queries)} queries")
    results = [None] * len(queries)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(qmeans, q): i for i, q in enumerate(queries)}
        done = 0
        for fut in as_completed(futs):
            i = futs[fut]
            results[i] = fut.result()
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(queries)}  elapsed={time.time()-t0:.1f}s")
    ok = sum(1 for r in results if r["ok"])
    print(f"Done: {ok}/{len(results)} ok in {time.time()-t0:.1f}s")
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["query", "ok", "key_count", "attributes_json"])
        for r in results:
            w.writerow([r["query"], r["ok"], len(r["attributes"]), json.dumps(r["attributes"], ensure_ascii=False)])

if __name__ == "__main__":
    main()
