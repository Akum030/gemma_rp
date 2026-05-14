"""Retry qmeans for queries that previously failed/empty."""
import json, os, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "bee", "qmeans_results.jsonl")
URL = "http://34.93.70.216:8009/attribute-search"

def qmeans(query):
    params = urllib.parse.urlencode({"query": query, "source": "test.run"})
    url = f"{URL}?{params}"
    last = None
    for _ in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "agent/1.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read().decode("utf-8"))
            attrs = {}
            for token, info in (data.get("attributes") or {}).items():
                name = (info.get("attr_name") or "").strip()
                val = (info.get("attr_value") or "").strip()
                atype = info.get("attr_type") or ""
                if not name or name == "-":
                    if atype == "product":
                        attrs.setdefault("product", val)
                    continue
                attrs.setdefault(name, val)
            return {"query": query, "attributes": attrs, "ok": True}
        except Exception as e:
            last = str(e); time.sleep(1.0)
    return {"query": query, "attributes": {}, "ok": False, "error": last}

def main():
    rows = [json.loads(l) for l in open(PATH, encoding="utf-8")]
    fail_idx = [i for i, r in enumerate(rows) if not r.get("ok")]
    print(f"Retrying {len(fail_idx)} failed queries...")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=10) as pool:
        futs = {pool.submit(qmeans, rows[i]["query"]): i for i in fail_idx}
        for fut in as_completed(futs):
            i = futs[fut]
            rows[i] = fut.result()
    with open(PATH, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    ok = sum(1 for r in rows if r.get("ok"))
    print(f"Done in {time.time()-t0:.1f}s; total ok now {ok}/{len(rows)}")

if __name__ == "__main__":
    main()
