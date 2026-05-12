import pandas as pd
import requests
import time
import json
from urllib.parse import quote
import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration
EXCLUSION_CSV = "exclusion_queries.csv"
QMEANS_API = "http://34.93.70.216:8009/attribute-search-qmeans"
GEMINI_API_KEY = "os.environ.get("API_KEY", "")"
GEMINI_API_URL = "https://imllm.intermesh.net/v1/chat/completions"
GEMINI_MODEL = "google/gemini-2.0-flash-lite"
DELAY_MS = 100
OUTPUT_CSV = "exclusion_comparison_results.csv"

def extract_qmeans_attributes(response_json):
    """Extract ISQ attributes from QMeans response"""
    attributes = response_json.get('attributes', {})
    isq_list = []
    
    for attr_key, attr_data in attributes.items():
        attr_value = attr_data.get('attr_value', '')
        attr_name = attr_data.get('attr_name', '')
        attr_type = attr_data.get('attr_type', '')
        isq = f"{attr_value}:{attr_name}:{attr_type}"
        isq_list.append(isq)
    
    return isq_list

def call_qmeans_api(query):
    """Call QMeans API"""
    try:
        encoded_query = quote(query)
        url = f"{QMEANS_API}?query={encoded_query}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            isq_attributes = extract_qmeans_attributes(data)
            
            return {
                'success': True,
                'attr_count': len(isq_attributes),
                'isq_list': isq_attributes,
                'isq_pipe': ' | '.join(isq_attributes)
            }
        else:
            return {
                'success': False,
                'attr_count': 0,
                'isq_list': [],
                'isq_pipe': ''
            }
    except Exception as e:
        return {
            'success': False,
            'attr_count': 0,
            'isq_list': [],
            'isq_pipe': '',
            'error': str(e)
        }

def create_zero_shot_prompt(query):
    """Create Gemini prompt with examples"""
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
    """Call Gemini API"""
    try:
        prompt = create_zero_shot_prompt(query)
        
        payload = {
            "model": GEMINI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 200
        }
        
        headers = {
            "Authorization": f"Bearer {GEMINI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=30)
        
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
                'attr_count': len(valid_isqs),
                'isq_list': valid_isqs,
                'isq_pipe': ' | '.join(valid_isqs)
            }
        else:
            return {
                'success': False,
                'attr_count': 0,
                'isq_list': [],
                'isq_pipe': ''
            }
    except Exception as e:
        return {
            'success': False,
            'attr_count': 0,
            'isq_list': [],
            'isq_pipe': '',
            'error': str(e)
        }

def main():
    if GEMINI_API_KEY == "YOUR_API_KEY_HERE":
        print("ERROR: Please set your GEMINI_API_KEY!")
        return
    
    # Read exclusion queries
    print(f"Reading exclusion queries from: {EXCLUSION_CSV}")
    df = pd.read_csv(EXCLUSION_CSV)
    
    queries = df['query'].tolist()
    expected_behaviors = df['expected_behavior'].tolist()
    notes = df['notes'].tolist()
    total = len(queries)
    
    print(f"Testing {total} exclusion queries")
    print("=" * 80)
    
    results = []
    
    for i, (query, expected, note) in enumerate(zip(queries, expected_behaviors, notes), 1):
        print(f"[{i}/{total}] {query[:50]}...")
        
        # Call QMeans
        print("  QMeans...", end=" ")
        qmeans_result = call_qmeans_api(query)
        print(f"OK ({qmeans_result['attr_count']} attrs)")
        
        time.sleep(DELAY_MS / 1000)
        
        # Call Gemini
        print("  Gemini...", end=" ")
        gemini_result = call_gemini_api(query)
        print(f"OK ({gemini_result['attr_count']} attrs)")
        
        # Combine results
        results.append({
            'query': query,
            'expected_behavior': expected,
            'notes': note,
            'qmeans_attr_count': qmeans_result['attr_count'],
            'qmeans_isq_pipe': qmeans_result['isq_pipe'],
            'gemini_attr_count': gemini_result['attr_count'],
            'gemini_isq_pipe': gemini_result['isq_pipe'],
            'match': qmeans_result['isq_pipe'] == gemini_result['isq_pipe']
        })
        
        time.sleep(DELAY_MS / 1000)
        print()
    
    # Save results
    output_df = pd.DataFrame(results)
    output_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    print("=" * 80)
    print("EXCLUSION TEST SUMMARY")
    print("=" * 80)
    print(f"[DONE] Results saved to: {OUTPUT_CSV}")
    print(f"[DONE] Total queries tested: {total}")
    
    # Analysis
    should_identify = output_df[output_df['expected_behavior'] == 'should_identify']
    should_not = output_df[output_df['expected_behavior'] == 'should_not_identify_brand']
    
    print(f"\n--- SHOULD IDENTIFY (normal cases) ---")
    print(f"QMeans identified: {sum(should_identify['qmeans_attr_count'] > 0)}/{len(should_identify)}")
    print(f"Gemini identified: {sum(should_identify['gemini_attr_count'] > 0)}/{len(should_identify)}")
    
    print(f"\n--- SHOULD NOT IDENTIFY (false positives) ---")
    print(f"QMeans wrongly identified: {sum(should_not['qmeans_attr_count'] > 0)}/{len(should_not)}")
    print(f"Gemini wrongly identified: {sum(should_not['gemini_attr_count'] > 0)}/{len(should_not)}")
    
    print("\n--- FALSE POSITIVE CASES (Gemini vs QMeans) ---")
    for _, row in should_not.iterrows():
        print(f"\nQuery: {row['query']}")
        print(f"  QMeans: {row['qmeans_isq_pipe'] if row['qmeans_isq_pipe'] else 'No attrs (CORRECT!)'}")
        print(f"  Gemini: {row['gemini_isq_pipe'] if row['gemini_isq_pipe'] else 'No attrs (CORRECT!)'}")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
