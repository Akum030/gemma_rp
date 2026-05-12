import pandas as pd
import requests
import time
import json
import sys
import io
import os
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Configuration
GEMINI_API_KEY = "os.environ.get("API_KEY", "")"
GEMINI_API_URL = "https://imllm.intermesh.net/v1/chat/completions"
DELAY_MS = 50
SAVE_INTERVAL = 5

# ============================================================================
# ATTRIBUTE DATASET
# ============================================================================
ATTRIBUTE_DATASET = r"""
440 v:voltage:specification
380 v:voltage:specification
415 v:voltage:specification
240 v:voltage:specification
400 v:voltage:specification
220 v:voltage:specification
230 volts:voltage:specification
paint coated:surface finishing:specification
color coated:surface finishing:specification
painted:surface finishing:specification
powder coated:surface finishing:specification
polished:surface finishing:specification
automatic:automation grade:specification
semi-automatic:automation grade:specification
fully automatic:automation grade:specification
manual:automation grade:specification
three phase:phase:specification
3 phase:phase:specification
single phase:phase:specification
1 phase:phase:specification
stainless steel:body material:specification
mild steel:body material:specification
ms:body material:specification
ss:body material:specification
iron:body material:specification
pp:body material:specification
steel:body material:specification
100 kg/hr:capacity:specification
1000 liter:capacity:specification
10 tpd:capacity:specification
5 ton:capacity:specification
200 kg:capacity:specification
twin screw:design:specification
parallel:design:specification
conical:design:specification
co-rotating:design:specification
50 hz:frequency:specification
60 hz:frequency:specification
pharmaceutical:usage/application:specification
food processing:usage/application:specification
plastic processing:usage/application:specification
industrial:usage/application:specification
2 hp:power:specification
5.5 hp:power:specification
50 hp:power:specification
10 hp:power:specification
1 hp:power:specification
20 hp:power:specification
"""

def log_message(message, log_file):
    """Log message to file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(message)

def parse_attribute_dataset(raw_data):
    """Parse the attribute dataset"""
    lines = [line.strip() for line in raw_data.strip().split('\n') if line.strip()]
    attr_dict = {}
    for line in lines:
        parts = line.split(':')
        if len(parts) == 3:
            value, name, attr_type = parts
            if name not in attr_dict:
                attr_dict[name] = []
            if value not in attr_dict[name]:
                attr_dict[name].append(value)
    return attr_dict

def create_dataset_prompt(query, attr_dict):
    """Create prompt with attribute dataset"""
    attr_reference = "ATTRIBUTE EXTRACTION TRAINING DATA:\n\n"
    for attr_name, values in attr_dict.items():
        value_list = ' | '.join(values[:20])
        if len(values) > 20:
            value_list += f" ... (+{len(values)-20} more)"
        attr_reference += f"• {attr_name}: {value_list}\n"

    prompt = f"""{attr_reference}

TASK: Extract product attributes from the given query.

OUTPUT FORMAT (ISQ):
- attribute_value:attribute_name:attribute_type
- attribute_type is always "specification"
- Return as a Python list

EXTRACTION GUIDELINES:
1. Identify ALL product-related attributes in the query
2. Extract quantities with units (e.g., "500 gm", "1 kg", "750 ml")
3. Extract specifications (voltage, phase, power, capacity, etc.)
4. Extract materials, colors, sizes, and other descriptive attributes
5. If no clear attributes are found, return empty list []

EXAMPLES:

Query: "440V three phase automatic extruder"
Output: ['440 v:voltage:specification', 'three phase:phase:specification', 'automatic:automation grade:specification', 'extruder:product:specification']

Query: "stainless steel paint coated extraction plant"
Output: ['stainless steel:body material:specification', 'paint coated:surface finishing:specification', 'extraction plant:product:specification']

Now extract attributes:

Query: "{query}"
Output: """
    return prompt

def call_api(query, attr_dict, model_name, max_retries=3):
    """Call API with retries"""
    for attempt in range(max_retries):
        try:
            prompt = create_dataset_prompt(query, attr_dict)
            
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 300
            }
            
            headers = {
                "Authorization": f"Bearer {GEMINI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=60)
            
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
                    'attr_count': len(valid_isqs),
                    'isq_list': str(valid_isqs),
                    'isq_pipe': ' | '.join(valid_isqs),
                    'raw_output': content
                }
            else:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return None
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return None
    return None

def retry_failed_queries(model_name, model_short_name, input_csv):
    """Retry failed queries and update the CSV"""
    
    log_file = f"compare/{model_short_name}_retry_log.txt"
    
    print(f"\n{'='*80}")
    print(f"RETRY FAILED QUERIES - {model_name}")
    print(f"{'='*80}\n")
    
    # Load existing results
    if not os.path.exists(input_csv):
        print(f"ERROR: File not found: {input_csv}")
        return
    
    df = pd.read_csv(input_csv)
    
    # Find failed queries
    failed_mask = df['success'] == False
    failed_df = df[failed_mask].copy()
    failed_count = len(failed_df)
    
    if failed_count == 0:
        print(f"✓ No failed queries found! All {len(df)} queries successful.")
        return
    
    print(f"Found {failed_count} failed queries to retry")
    log_message(f"Starting retry for {failed_count} failed queries", log_file)
    
    # Parse attributes
    attr_dict = parse_attribute_dataset(ATTRIBUTE_DATASET)
    
    # Retry failed queries
    success_count = 0
    still_failed = 0
    
    for idx, row in failed_df.iterrows():
        query = row['query']
        request_num = row.get('request_number', idx)
        
        print(f"[{success_count + still_failed + 1}/{failed_count}] Retrying: {str(query)[:60]}...", end=" ")
        
        result = call_api(query, attr_dict, model_name)
        
        if result and result['success']:
            # Update the original dataframe
            df.at[idx, 'success'] = True
            df.at[idx, 'attr_count'] = result['attr_count']
            df.at[idx, 'isq_list'] = result['isq_list']
            df.at[idx, 'isq_pipe'] = result['isq_pipe']
            df.at[idx, 'raw_output'] = result['raw_output']
            if 'error' in df.columns:
                df.at[idx, 'error'] = ''
            
            success_count += 1
            print(f"✓ SUCCESS ({result['attr_count']} attrs)")
        else:
            still_failed += 1
            print("✗ STILL FAILED")
        
        # Save progress every SAVE_INTERVAL
        if (success_count + still_failed) % SAVE_INTERVAL == 0:
            df.to_csv(input_csv, index=False, encoding='utf-8-sig')
            print(f"  [Progress saved: {success_count} recovered, {still_failed} still failed]")
        
        time.sleep(DELAY_MS / 1000)
    
    # Final save
    df.to_csv(input_csv, index=False, encoding='utf-8-sig')
    
    # Summary
    print(f"\n{'='*80}")
    print(f"RETRY SUMMARY - {model_name}")
    print(f"{'='*80}")
    print(f"Retry attempts: {failed_count}")
    print(f"Recovered: {success_count} ({(success_count/failed_count)*100:.1f}%)")
    print(f"Still failed: {still_failed} ({(still_failed/failed_count)*100:.1f}%)")
    print(f"\nUpdated file: {input_csv}")
    
    # Updated totals
    total_success = len(df[df['success'] == True])
    total_queries = len(df)
    print(f"\nFinal Stats:")
    print(f"Total queries: {total_queries}")
    print(f"Successful: {total_success} ({(total_success/total_queries)*100:.1f}%)")
    print(f"Failed: {total_queries - total_success} ({((total_queries - total_success)/total_queries)*100:.1f}%)")
    print(f"{'='*80}\n")
    
    log_message(f"Retry complete: {success_count} recovered, {still_failed} still failed", log_file)

def main():
    print("\n" + "="*80)
    print("FAILED QUERIES RETRY UTILITY")
    print("="*80)
    
    # Retry Claude Sonnet 4
    print("\n1. Processing Claude Sonnet 4 failures...")
    retry_failed_queries(
        "anthropic/claude-sonnet-4",
        "claude_sonnet_4",
        "compare/claude_sonnet_4_output.csv"
    )
    
    # Retry Qwen
    print("\n2. Processing Qwen 32B failures...")
    retry_failed_queries(
        "qwen/qwen3-32b",
        "qwen_32b",
        "compare/qwen_32b_output.csv"
    )
    
    print("\n" + "="*80)
    print("ALL RETRIES COMPLETED!")
    print("="*80)
    print("\nYou can now run Gemini 3 Pro separately.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
