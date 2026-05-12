import pandas as pd
import requests
import time
import json
import sys
import io

# Fix Windows encoding issue
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration
INPUT_CSV = "exclusion_test_queries.csv"
GEMINI_API_KEY = "os.environ.get("API_KEY", "")"
GEMINI_API_URL = "https://imllm.intermesh.net/v1/chat/completions"
GEMINI_MODEL = "google/gemini-2.0-flash"
DELAY_MS = 100
OUTPUT_CSV = "gemini_zero_shot_exclusion_100_cases.csv"
BATCH_SIZE = 100

def create_zero_shot_prompt(query):
    prompt = f"""Extract product attributes from e-commerce search queries in ISQ format.

ISQ Format: attribute_value:attribute_name:attribute_type

Examples:

Query: "Blown Film Extrusion Machine"
Output: ['film:usage:specification']

Query: "sheet extruder machine"
Output: ['extruder:type:specification']

Query: "centrufuge Extractor For Textile Mills"
Output: ['extractor:product:specification', 'textile mills:usage:specification']

Query: "Gold Refinery Plant"
Output: ['gold:usage:specification', 'refinery:type:specification']

Query: "Extruder Machine"
Output: ['extruder:type:specification']

Query: "Solvent Extraction Plant"
Output: ['solvent extraction:usage:specification']

Query: "lab extruder"
Output: ['extruder:type:specification', 'lab:usage:specification']

Query: "plastic sheet plant near ahmedabad"
Output: ['plastic:material:specification']

Query: "Aluminium Extrusion Plant Consultant"
Output: ['aluminium:material:specification', 'extrusion:machine type:specification']

Query: "sheet extruder"
Output: ['extruder:type:specification']

Now extract attributes for this query:

Query: "{query}"
Output: """
    
    return prompt

def call_gemini_api(query):
    try:
        prompt = create_zero_shot_prompt(query)
        
        payload = {
            "model": GEMINI_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0,
            "max_tokens": 200
        }
        
        headers = {
            "Authorization": f"Bearer {GEMINI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            GEMINI_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content'].strip()
            
            content = content.replace("'", '"')
            
            try:
                if content.startswith('[') and content.endswith(']'):
                    isq_list = json.loads(content)
                else:
                    isq_list = [item.strip() for item in content.replace('\n', ',').split(',') if item.strip()]
            except:
                isq_list = [content] if content else []
            
            valid_isqs = [isq for isq in isq_list if isq.count(':') == 2]
            
            return {
                'success': True,
                'query': query,
                'gemini_attr_count': len(valid_isqs),
                'gemini_isq_list': str(valid_isqs),
                'gemini_isq_pipe': ' | '.join(valid_isqs),
                'gemini_raw_output': content
            }
        else:
            return {
                'success': False,
                'query': query,
                'gemini_attr_count': 0,
                'gemini_isq_list': '[]',
                'gemini_isq_pipe': '',
                'error': f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        return {
            'success': False,
            'query': query,
            'gemini_attr_count': 0,
            'gemini_isq_list': '[]',
            'gemini_isq_pipe': '',
            'error': str(e)
        }

def main():
    if GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        print("ERROR: Please set your GEMINI_API_KEY in the script!")
        return
    
    print(f"Reading QMeans results from: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    
    if 'query' not in df.columns:
        print("ERROR: 'query' column not found in CSV!")
        return
    
    queries = df['query'].dropna().tolist()
    total_queries = len(queries)
    
    print(f"Processing {total_queries} queries with Gemini (zero-shot)")
    print(f"Progress updates every {BATCH_SIZE} queries")
    print("=" * 80)
    
    results = []
    success_count = 0
    fail_count = 0
    
    for i, query in enumerate(queries, 1):
        print(f"[{i}/{total_queries}] {query[:60]}...", end=" ")
        
        result = call_gemini_api(str(query))
        
        if result['success']:
            success_count += 1
            print(f"OK ({result['gemini_attr_count']} attrs)")
        else:
            fail_count += 1
            print(f"ERROR")
        
        results.append(result)
        
        if i % BATCH_SIZE == 0:
            print()
            print("=" * 80)
            print(f"BATCH SUMMARY [{i}/{total_queries}]")
            print(f"  Completed: {i} queries")
            print(f"  Success: {success_count}")
            print(f"  Failed: {fail_count}")
            print(f"  Progress: {(i/total_queries)*100:.1f}%")
            print(f"  Estimated time remaining: {((total_queries-i)*0.1/60):.1f} minutes")
            print("=" * 80)
            print()
        
        time.sleep(DELAY_MS / 1000)
    
    output_df = pd.DataFrame(results)
    output_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"[DONE] Results saved to: {OUTPUT_CSV}")
    print(f"[DONE] Total queries: {total_queries}")
    print(f"[DONE] Successful: {success_count} ({(success_count/total_queries)*100:.1f}%)")
    print(f"[DONE] Failed: {fail_count} ({(fail_count/total_queries)*100:.1f}%)")
    
    total_attrs = sum(r.get('gemini_attr_count', 0) for r in results)
    avg_attrs = total_attrs / total_queries if total_queries > 0 else 0
    print(f"[DONE] Total attributes extracted: {total_attrs}")
    print(f"[DONE] Average attributes per query: {avg_attrs:.2f}")
    print("=" * 80)

if __name__ == "__main__":
    main()
