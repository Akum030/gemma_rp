"""Run qmeans production API on all queries -> save normalized JSONL + CSV."""
import csv, json, sys, os, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUERIES_FILE = os.path.join(ROOT, "76cat_queries")
OUT_JSONL = os.path.join(ROOT, "bee", "qmeans_results.jsonl")
OUT_CSV   = os.path.join(ROOT, "bee", "qmeans_results.csv")
URL = "http://34.93.70.216:8009/attribute-search"

def load_queries():
    out = []
    with open(QUERIES_FILE, encoding="utf-8") as f:
        for i, line in enumerate(f):
            q = line.strip()
            if not q:
                continue
            if i == 0 and q.lower() == "query":  # skip header
                continue
            out.append(q)
    return out

def qmeans(query, retries=3):
    params = urllib.parse.urlencode({"query": query, "source": "test.run"})
    url = f"{URL}?{params}"
    last = None
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "agent/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8"))
            attrs = {}
            for token, info in (data.get("attributes") or {}).items():
                name = (info.get("attr_name") or "").strip()
                val = (info.get("attr_value") or "").strip()
                atype = info.get("attr_type") or ""
                if not name or name == "-":
                    # treat probable-product entries: use "product" key
                    if atype == "product":
                        attrs.setdefault("product", val)
                    continue
                # do not overwrite existing key with later same-name token
                attrs.setdefault(name, val)
            return {"query": query, "attributes": attrs, "ok": True}
        except Exception as e:
            last = str(e); time.sleep(0.5)
    return {"query": query, "attributes": {}, "ok": False, "error": last}

def main():
    queries = load_queries()
    print(f"Loaded {len(queries)} queries")
    results = [None] * len(queries)
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=20) as pool:
        futs = {pool.submit(qmeans, q): i for i, q in enumerate(queries)}
        done = 0
        for fut in as_completed(futs):
            i = futs[fut]
            results[i] = fut.result()
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(queries)}  elapsed={time.time()-t0:.1f}s")
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["query", "ok", "key_count", "attributes_json"])
        for r in results:
            w.writerow([r["query"], r["ok"], len(r["attributes"]), json.dumps(r["attributes"], ensure_ascii=False)])
    ok = sum(1 for r in results if r["ok"])
    print(f"DONE {ok}/{len(results)} ok in {time.time()-t0:.1f}s")
    print(f"  -> {OUT_JSONL}")
    print(f"  -> {OUT_CSV}")

if __name__ == "__main__":
    main()
