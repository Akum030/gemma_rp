import pandas as pd
import requests
import time
import json
from urllib.parse import quote
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
INPUT_CSV = "validation_queries.csv"
COLUMN_NAME = "query"
QMEANS_API = "http://34.93.70.216:8009/attribute-search-qmeans"
DELAY_MS = 30
OUTPUT_CSV = "qmeans_1000_validation.csv"

def extract_attributes_from_qmeans(response_json):
    """
    Extract attributes from QMeans response in ISQ format
    Format: value:name:type
    """
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
    """Call QMeans API and return formatted results"""
    try:
        encoded_query = quote(query)
        url = f"{QMEANS_API}?query={encoded_query}"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            isq_attributes = extract_attributes_from_qmeans(data)
            
            return {
                'success': True,
                'query': query,
                'qmeans_attr_count': len(isq_attributes),
                'qmeans_isq_list': str(isq_attributes),
                'qmeans_isq_pipe': ' | '.join(isq_attributes),
                'response_time': data.get('response_time', 0)
            }
        else:
            return {
                'success': False,
                'query': query,
                'qmeans_attr_count': 0,
                'qmeans_isq_list': '[]',
                'qmeans_isq_pipe': '',
                'error': f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        return {
            'success': False,
            'query': query,
            'qmeans_attr_count': 0,
            'qmeans_isq_list': '[]',
            'qmeans_isq_pipe': '',
            'error': str(e)
        }

def main():
    print(f"Reading CSV file: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    
    if COLUMN_NAME not in df.columns:
        print(f"ERROR: Column '{COLUMN_NAME}' not found in CSV!")
        print(f"Available columns: {df.columns.tolist()}")
        return
    
    queries = df[COLUMN_NAME].dropna().tolist()
    total_queries = len(queries)
    
    print(f"Found {total_queries} queries to process")
    print("=" * 80)
    
    results = []
    for i, query in enumerate(queries, 1):
        print(f"[{i}/{total_queries}] Query: {query[:70]}...")
        
        result = call_qmeans_api(str(query))
        
        if result['success']:
            print(f"  [OK] Attributes: {result['qmeans_attr_count']}")
            if result['qmeans_attr_count'] > 0:
                print(f"  --> {result['qmeans_isq_pipe'][:120]}...")
        else:
            print(f"  [ERROR] {result.get('error', 'Unknown')}")
        
        results.append(result)
        
        time.sleep(DELAY_MS / 1000)
        print()
    
    output_df = pd.DataFrame(results)
    output_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    print("=" * 80)
    print(f"[DONE] PROCESSING COMPLETE!")
    print(f"[DONE] Results saved to: {OUTPUT_CSV}")
    print(f"[DONE] Total queries: {total_queries}")
    print(f"[DONE] Successful: {sum(1 for r in results if r.get('success', False))}")
    print(f"[DONE] Failed: {sum(1 for r in results if not r.get('success', False))}")
    
    total_attrs = sum(r.get('qmeans_attr_count', 0) for r in results)
    avg_attrs = total_attrs / total_queries if total_queries > 0 else 0
    print(f"[DONE] Total attributes extracted: {total_attrs}")
    print(f"[DONE] Average attributes per query: {avg_attrs:.2f}")

if __name__ == "__main__":
    main()
