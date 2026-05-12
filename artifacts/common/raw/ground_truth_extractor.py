import pandas as pd
import requests
import time
from urllib.parse import quote
import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration
INPUT_CSV = "exclusion_test_queries.csv"  # Your exclusion keyword list
GROUND_TRUTH_API = "http://34.93.70.216:8009/attribute-search"
DELAY_MS = 100
OUTPUT_CSV = "ground_truth_100_queries.csv"

def extract_attributes_from_ground_truth(response_json):
    """
    Extract ISQ attributes from ground truth API response
    Format: value:name:type
    """
    attributes = response_json.get('attributes', {})
    isq_list = []
    
    for attr_key, attr_data in attributes.items():
        attr_value = attr_data.get('attr_value', '')
        attr_name = attr_data.get('attr_name', '')
        attr_type = attr_data.get('attr_type', '')
        
        # Skip if attr_name is "-" (not a valid attribute)
        if attr_name == "-":
            continue
        
        # Format: value:name:type (ISQ format)
        isq = f"{attr_value}:{attr_name}:{attr_type}"
        isq_list.append(isq)
        
        # Also extract from 'others' if present
        others = attr_data.get('others', [])
        for other in others:
            other_value = other.get('attr_value', '')
            other_name = other.get('attr_name', '')
            other_type = other.get('attr_type', '')
            
            if other_name != "-":
                other_isq = f"{other_value}:{other_name}:{other_type}"
                if other_isq not in isq_list:
                    isq_list.append(other_isq)
    
    return isq_list

def call_ground_truth_api(query):
    """Call ground truth API and return formatted results"""
    try:
        # URL encode the query
        encoded_query = quote(query)
        url = f"{GROUND_TRUTH_API}?query={encoded_query}&source=test.run"
        
        # Make API call
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract ISQ attributes
            isq_attributes = extract_attributes_from_ground_truth(data)
            
            return {
                'success': True,
                'query': query,
                'ground_truth_attr_count': len(isq_attributes),
                'ground_truth_isq_list': str(isq_attributes),
                'ground_truth_isq_pipe': ' | '.join(isq_attributes),
                'api_version': data.get('api_version', '-'),
                'raw_response': str(data)
            }
        else:
            return {
                'success': False,
                'query': query,
                'ground_truth_attr_count': 0,
                'ground_truth_isq_list': '[]',
                'ground_truth_isq_pipe': '',
                'error': f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        return {
            'success': False,
            'query': query,
            'ground_truth_attr_count': 0,
            'ground_truth_isq_list': '[]',
            'ground_truth_isq_pipe': '',
            'error': str(e)
        }

def main():
    # Read input CSV
    print(f"Reading exclusion queries from: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    
    if 'query' not in df.columns:
        print("ERROR: 'query' column not found in CSV!")
        print(f"Available columns: {df.columns.tolist()}")
        return
    
    queries = df['query'].dropna().tolist()
    total_queries = len(queries)
    
    print(f"Found {total_queries} queries to process")
    print("=" * 80)
    
    # Process each query
    results = []
    for i, query in enumerate(queries, 1):
        print(f"[{i}/{total_queries}] Query: {query[:70]}...")
        
        # Call ground truth API
        result = call_ground_truth_api(str(query))
        
        if result['success']:
            print(f"  [OK] Attributes: {result['ground_truth_attr_count']}")
            if result['ground_truth_attr_count'] > 0:
                print(f"  --> {result['ground_truth_isq_pipe'][:120]}...")
        else:
            print(f"  [ERROR] {result.get('error', 'Unknown')}")
        
        results.append(result)
        
        # Delay between requests
        time.sleep(DELAY_MS / 100)
        print()
    
    # Create output DataFrame
    output_df = pd.DataFrame(results)
    
    # Save to CSV
    output_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    print("=" * 80)
    print(f"[DONE] PROCESSING COMPLETE!")
    print(f"[DONE] Results saved to: {OUTPUT_CSV}")
    print(f"[DONE] Total queries: {total_queries}")
    print(f"[DONE] Successful: {sum(1 for r in results if r.get('success', False))}")
    print(f"[DONE] Failed: {sum(1 for r in results if not r.get('success', False))}")
    
    # Summary stats
    total_attrs = sum(r.get('ground_truth_attr_count', 0) for r in results)
    avg_attrs = total_attrs / total_queries if total_queries > 0 else 0
    print(f"[DONE] Total attributes extracted: {total_attrs}")
    print(f"[DONE] Average attributes per query: {avg_attrs:.2f}")

if __name__ == "__main__":
    main()
