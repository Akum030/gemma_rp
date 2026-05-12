"""
Batch API inference for MCAT classification.
Calls the production API for each query in 76cat_queries and saves results to api_mcat_results.csv.
"""

import csv
import json
import time
import os
import urllib.request
import urllib.parse
import urllib.error

# ── Config ─────────────────────────────────────────────────────────────────────
QUERIES_FILE = "76cat_queries"
OUTPUT_FILE  = "api_mcat_results.csv"
API_BASE     = "http://34.93.37.76:8984/tools/related_info"
DELAY_SEC    = 0.1   # polite delay between requests
TIMEOUT_SEC  = 15    # per-request timeout
# ───────────────────────────────────────────────────────────────────────────────


def call_api(query: str):
    """Call the API and return (mcat_name, mcat_id, mcat_accuracy_level) or ('', '', '') on failure."""
    params = urllib.parse.urlencode({"q": query, "source": "dir.search"})
    url = f"{API_BASE}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        live_mcats = data.get("guess", {}).get("live_mcats", [])
        if not live_mcats:
            return "", "", ""
        top = live_mcats[0]
        return (
            top.get("name", ""),
            top.get("id", ""),
            top.get("mcat_accuracy_level", ""),
        )
    except urllib.error.URLError as e:
        print(f"  [URLError] {query!r}: {e}")
        return "", "", ""
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"  [ParseError] {query!r}: {e}")
        return "", "", ""
    except Exception as e:
        print(f"  [Error] {query!r}: {e}")
        return "", "", ""


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    queries_path = os.path.join(script_dir, QUERIES_FILE)
    output_path  = os.path.join(script_dir, OUTPUT_FILE)

    # Read all queries
    queries = []
    with open(queries_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = row.get("query", "").strip()
            if q:
                queries.append(q)

    print(f"Loaded {len(queries)} queries from {queries_path}")
    print(f"Output → {output_path}\n")

    # Resume support: find how many rows already written (excluding header)
    already_done = 0
    if os.path.exists(output_path):
        with open(output_path, newline="", encoding="utf-8") as chk:
            already_done = sum(1 for _ in chk) - 1  # subtract header
        already_done = max(already_done, 0)

    if already_done >= len(queries):
        print("All queries already processed. Nothing to do.")
        return

    if already_done > 0:
        print(f"Resuming from query {already_done + 1}/{len(queries)} (skipping first {already_done})\n")

    write_mode = "a" if already_done > 0 else "w"
    with open(output_path, write_mode, newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=["keyword", "mcat_name", "mcat_id", "mcat_accuracy_level"])
        if already_done == 0:
            writer.writeheader()

        for i, query in enumerate(queries[already_done:], already_done + 1):
            mcat_name, mcat_id, accuracy = call_api(query)
            writer.writerow({
                "keyword": query,
                "mcat_name": mcat_name,
                "mcat_id": mcat_id,
                "mcat_accuracy_level": accuracy,
            })
            # flush every 50 rows so partial results are saved on interrupt
            if i % 50 == 0:
                out_f.flush()
                print(f"  [{i}/{len(queries)}] {query!r} → {mcat_name} ({accuracy})")

            time.sleep(DELAY_SEC)

    print(f"\nDone! Results saved to {output_path}")


if __name__ == "__main__":
    main()
