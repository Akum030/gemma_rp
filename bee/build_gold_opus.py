"""
Rebuild gold ground-truth using Claude claude-opus-4-5 (or latest available Opus).

Reads bee/v4_inputs.jsonl (1000 queries) and annotates each with structured
product attributes using the SAME IndiaMART key vocabulary as the training data
and evaluation gold. Saves to bee/gold_opus_v3.jsonl.

Usage:
  set ANTHROPIC_API_KEY=sk-ant-...
  python bee/build_gold_opus.py [--resume] [--workers 8]

Cost estimate (Apr 2026):
  ~$0.01-0.02 per query × 1000 = ~$10-20 total
"""

import argparse, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from anthropic import Anthropic
except ImportError:
    print("pip install anthropic", file=sys.stderr); sys.exit(1)

ROOT     = os.path.dirname(os.path.abspath(__file__))
QUERIES  = os.path.join(ROOT, "v4_inputs.jsonl")
OUTPUT   = os.path.join(ROOT, "gold_opus_v3.jsonl")

# Try these model IDs in order (newest first)
MODEL_CANDIDATES = [
    "claude-opus-4-5",
    "claude-opus-4",
    "claude-3-opus-20240229",
]

SYSTEM = """\
You are an expert at extracting structured product attributes from search queries on IndiaMART (B2B marketplace for industrial goods in India).

Given a free-text query, extract all product attributes and return ONLY a compact JSON object mapping attribute keys to their values.

STRICT RULES:
1. Output JSON ONLY — no preamble, no code fences, no explanation.
2. Use ONLY keys from this canonical vocabulary:
   part type, brand, model name/number, power, voltage, phase, speed, usage,
   material, size, color, series, driven type, power source, rpm, frequency,
   capacity, mounting type, ip rating, insulation class, torque, automation grade,
   quantity, dimension, weight, country of origin, horsepower, rated speed,
   frame size, shape, orientation, certification, application, product,
   motor power, motor type, feature, efficiency, duty cycle, cooling type,
   starter type, shaft diameter, poles, temperature range, packaging size,
   purity, technology, machine type, machine name, process, operation,
   automation grade, location/city, place of origin
3. Always include "part type" when the query clearly names a product
   (e.g. "motor", "actuator", "valve", "pump", "fan", "compressor",
    "transformer", "encoder", "switch", "positioner", "sensor", "controller").
4. Preserve original casing for model/part numbers. Lowercase other values.
5. Do NOT invent attributes not present in the query.
6. If nothing is extractable, return {}.

Examples:
Query: "Siemens Sipart Ps2 Positioner Model 6dr5"
Output: {"brand": "Siemens", "part type": "positioner", "series": "Sipart Ps2", "model name/number": "6dr5"}

Query: "3 phase 5 hp ABB induction motor"
Output: {"brand": "ABB", "part type": "motor", "phase": "3", "horsepower": "5 hp", "driven type": "induction"}

Query: "Cooler Motor"
Output: {"part type": "motor", "usage": "cooler"}

Query: "SIEMENS SIMOTICS S-1FK2 SERVO MOTOR 1FK2104-6AF01-1MB0 1 kW"
Output: {"brand": "Siemens", "part type": "motor", "series": "SIMOTICS S-1FK2", "driven type": "servo", "model name/number": "1FK2104-6AF01-1MB0", "power": "1 kW"}
"""


def pick_model(client: Anthropic) -> str:
    for m in MODEL_CANDIDATES:
        try:
            client.messages.create(
                model=m,
                max_tokens=5,
                messages=[{"role": "user", "content": "hi"}],
            )
            print(f"Using model: {m}")
            return m
        except Exception as e:
            print(f"  Model {m} not available ({e}), trying next ...")
    raise RuntimeError("No Opus model available. Check your API key and tier.")


def annotate(client: Anthropic, model: str, query: str, retries: int = 3) -> dict:
    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=256,
                system=SYSTEM,
                messages=[{"role": "user", "content": f"Query: {query}"}],
            )
            text = resp.content[0].text.strip()
            # strip code fences if model disobeys
            text = text.replace("```json", "").replace("```", "").strip()
            d = json.loads(text)
            if isinstance(d, dict):
                return d
        except json.JSONDecodeError:
            pass
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  WARN: failed for {query!r}: {e}")
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8, help="parallel workers")
    parser.add_argument("--resume", action="store_true", help="skip already-done queries")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set.", file=sys.stderr)
        print("  Set it: $env:ANTHROPIC_API_KEY='sk-ant-...'", file=sys.stderr)
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    model  = pick_model(client)

    # Load queries
    queries = []
    with open(QUERIES, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line)["query"])
    print(f"Total queries: {len(queries)}")

    # Resume: skip already done
    done = {}
    if args.resume and os.path.exists(OUTPUT):
        with open(OUTPUT, encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                    done[row["query"]] = row["attributes"]
                except Exception:
                    pass
        print(f"Resuming — already done: {len(done)}")

    remaining = [q for q in queries if q not in done]
    print(f"Remaining: {len(remaining)}")

    results = dict(done)  # query → attrs

    def worker(q):
        return q, annotate(client, model, q)

    with open(OUTPUT, "w" if not args.resume else "a", encoding="utf-8") as fout:
        # Write already-done if starting fresh (not resume)
        if not args.resume:
            pass  # will write as we go

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(worker, q): q for q in remaining}
            done_count = 0
            for fut in as_completed(futures):
                q, attrs = fut.result()
                row = {"query": q, "attributes": attrs}
                fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                fout.flush()
                results[q] = attrs
                done_count += 1
                if done_count % 50 == 0:
                    print(f"  Progress: {done_count}/{len(remaining)} — last: {q[:60]!r}")

    print(f"\nDone! Wrote {len(results)} annotations to {OUTPUT}")

    # Quick sanity: count non-empty
    non_empty = sum(1 for a in results.values() if a)
    print(f"Non-empty: {non_empty}/{len(results)} ({100*non_empty/max(1,len(results)):.1f}%)")


if __name__ == "__main__":
    main()
