import pandas as pd
import requests
import time
import json
import sys
import io
import traceback

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ================= CONFIG =================
INPUT_CSV = "../validation_queries.csv"

GEMINI_API_KEY = "os.environ.get("API_KEY", "")"
GEMINI_API_URL = "https://imllm.intermesh.net/v1/chat/completions"

# TRY ANY MODEL FROM YOUR LIST
GEMINI_MODEL = "google/gemini-3-flash-preview"

OUTPUT_CSV = "debug_output.csv"
DELAY_MS = 100
BATCH_SIZE = 10
# ==========================================

ATTRIBUTE_DATASET = r"""
440 v:voltage:specification
380 v:voltage:specification
415 v:voltage:specification
"""

# ------------------------------------------------------------

def parse_attribute_dataset(raw_data):
    lines = [line.strip() for line in raw_data.strip().split('\n') if line.strip()]
    attr_dict = {}
    for line in lines:
        parts = line.split(':')
        if len(parts) == 3:
            value, name, _ = parts
            attr_dict.setdefault(name, []).append(value)
    return attr_dict


def create_prompt(query):
    return f"""
Extract product attributes from the query.

Return Python list in format:
value:attribute:specification

Query:
{query}

Output:
"""


def call_llm(query):
    payload = {
        "model": GEMINI_MODEL,
        "messages": [
            {"role": "user", "content": create_prompt(query)}
        ],
        "temperature": 0,
        "max_tokens": 300
    }

    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            GEMINI_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        # 🔴 DESCRIPTIVE ERROR BLOCK
        if response.status_code != 200:
            print("\n================ API ERROR ================")
            print("MODEL:", GEMINI_MODEL)
            print("QUERY:", query)
            print("HTTP STATUS:", response.status_code)
            print("RAW RESPONSE:")
            print(response.text)

            # Try JSON parsing if possible
            try:
                err_json = response.json()
                print("\nPARSED ERROR JSON:")
                print(json.dumps(err_json, indent=2))
            except:
                print("\nResponse is not JSON")

            print("===========================================\n")

            return {
                "success": False,
                "query": query,
                "error": response.text
            }

        # SUCCESS PATH
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        return {
            "success": True,
            "query": query,
            "output": content
        }

    except Exception as e:
        print("\n============= PYTHON EXCEPTION =============")
        print("QUERY:", query)
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR MESSAGE:", str(e))
        print("TRACEBACK:")
        traceback.print_exc()
        print("===========================================\n")

        return {
            "success": False,
            "query": query,
            "error": str(e)
        }


def main():
    print("Reading CSV:", INPUT_CSV)
    df = pd.read_csv(INPUT_CSV)

    if "query" not in df.columns:
        print("ERROR: CSV must have a 'query' column")
        return

    queries = df["query"].dropna().tolist()
    print("Total queries:", len(queries))
    print("Model:", GEMINI_MODEL)
    print("=" * 80)

    results = []

    for i, q in enumerate(queries, 1):
        print(f"[{i}] Processing:", q)
        res = call_llm(str(q))
        results.append(res)
        time.sleep(DELAY_MS / 1000)

        if i >= BATCH_SIZE:
            break

    pd.DataFrame(results).to_csv(OUTPUT_CSV, index=False)
    print("Saved results to:", OUTPUT_CSV)


if __name__ == "__main__":
    main()

