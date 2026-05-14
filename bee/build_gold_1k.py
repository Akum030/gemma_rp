"""
Generate Claude Opus 4.7 ground truth for all queries.

Usage:
  set ANTHROPIC_API_KEY=sk-ant-...
  python bee/build_gold_1k.py --queries 76cat_queries --out bee/gold_1k.jsonl

Cost estimate (Apr 2026 pricing):
  Opus 4.7: ~$15/1M input, ~$75/1M output
  Per query ~ 500 in + 80 out = ~$0.014/query
  1000 queries ≈ $14
"""
import argparse, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from anthropic import Anthropic
except ImportError:
    print("pip install anthropic", file=sys.stderr); sys.exit(1)

CANON_KEYS = [
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
    "shaft diameter","poles","temperature range","application","quantity","dimension","warranty",
]

SYSTEM = f"""You are an expert at extracting structured product attributes from search queries on IndiaMART (B2B marketplace for industrial goods).

Given a free-text query, return ONLY a compact JSON object mapping attribute keys to their values found in the query.

STRICT RULES:
1. Output JSON ONLY (no preamble, no code fence, no explanation).
2. Use ONLY keys from this canonical vocabulary:
   {", ".join(CANON_KEYS)}
3. Always include "part type" when the query mentions a product type (e.g. "motor", "actuator", "valve", "pump", "fan", "compressor", "transformer", "encoder", "switch").
4. Preserve original casing/punctuation of the value as it appears in the query (e.g. "6dr5", "1FK2104-6AF01-1MB0").
5. Do NOT invent attributes not present in the query.
6. Use lowercase for the key, original case for the value.
7. If the query has nothing extractable, return {{}}.

Examples:
Query: "Siemens Sipart Ps2 Positioner Model 6dr5"
Output: {{"brand": "Siemens", "part type": "positioner", "model name/number": "6dr5"}}

Query: "3 phase 5 hp ABB induction motor"
Output: {{"brand": "ABB", "part type": "motor", "phase": "3", "horsepower": "5 hp", "driven type": "induction"}}

Query: "Cooler Motor"
Output: {{"part type": "motor", "usage": "cooler"}}
"""


def call_claude(client, model, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            r = client.messages.create(
                model=model,
                max_tokens=200,
                temperature=0,
                system=SYSTEM,
                messages=[{"role": "user", "content": f"Query: {query}"}],
            )
            txt = r.content[0].text.strip()
            # strip code fences if any
            if txt.startswith("```"):
                txt = txt.split("```")[1]
                if txt.startswith("json"): txt = txt[4:]
                txt = txt.strip()
            obj = json.loads(txt)
            if not isinstance(obj, dict):
                obj = {}
            return {"query": query, "attributes": obj, "ok": True}
        except json.JSONDecodeError as e:
            if attempt == max_retries - 1:
                return {"query": query, "attributes": {}, "ok": False, "error": f"JSON: {e} raw={txt[:200]}"}
        except Exception as e:
            if attempt == max_retries - 1:
                return {"query": query, "attributes": {}, "ok": False, "error": str(e)[:200]}
            time.sleep(1.5 * (attempt + 1))


def load_queries(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            q = line.strip()
            if not q: continue
            if i == 0 and q.lower() == "query": continue
            out.append(q)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="claude-opus-4-5-20250929")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume", action="store_true",
                    help="Skip queries already present in --out")
    args = ap.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY env var not set", file=sys.stderr)
        sys.exit(2)

    client = Anthropic()
    queries = load_queries(args.queries)
    if args.limit:
        queries = queries[:args.limit]

    done = set()
    if args.resume and os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as f:
            for line in f:
                try:
                    done.add(json.loads(line)["query"])
                except Exception:
                    pass
        print(f"Resume: {len(done)} already done.")

    todo = [q for q in queries if q not in done]
    print(f"To do: {len(todo)} / {len(queries)}  (model={args.model})")

    mode = "a" if args.resume else "w"
    out_f = open(args.out, mode, encoding="utf-8")
    t0 = time.time()
    n_ok = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(call_claude, client, args.model, q): q for q in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            res = fut.result()
            out_f.write(json.dumps(res, ensure_ascii=False) + "\n")
            out_f.flush()
            if res.get("ok"): n_ok += 1
            if i % 25 == 0:
                rate = i / (time.time() - t0)
                eta = (len(todo) - i) / max(rate, 1e-9) / 60
                print(f"[{i}/{len(todo)}] ok={n_ok}  rate={rate:.1f}/s  eta={eta:.1f}min")
    out_f.close()
    print(f"DONE  ok={n_ok}/{len(todo)}  total={(time.time()-t0)/60:.1f}min")
    print(f"  -> {args.out}")


if __name__ == "__main__":
    main()
