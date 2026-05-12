"""
Gemini 3 Pro Preview - Batch Inference with Few-Shot Learning
Process 1000 queries using Gemini with multi-key priority output matching Gemma format

Budget: $10 (monitored with token counting)
Output: CSV with same format as Gemma results
"""

import requests
import json
import csv
import time
import argparse
from typing import Dict, List, Any

# API Configuration
API_KEY = "os.environ.get("API_KEY", "")"
API_BASE_URL = "https://imllm.intermesh.net/v1/chat/completions"
MODEL_NAME = "qwen/qwen3-32b"  # Format: openrouter/provider/model

# Cost tracking (approximate - Gemini pricing)
# Input: ~$0.50 per 1M tokens, Output: ~$1.50 per 1M tokens
INPUT_COST_PER_1K = 0.0005
OUTPUT_COST_PER_1K = 0.0015

# 10 Best Few-Shot Examples from Electric Motors domain
# Carefully selected to show: multiple keys, key priorities, attribute priorities
FEW_SHOT_EXAMPLES = [
    {
        "query": "siemens 1.5 kw 415v three phase motor",
        "attributes": [
            {"attribute_key": "brand", "value": "siemens", "key_priority": 1, "attribute_priority": 1},
            {"attribute_key": "manufacturer", "value": "siemens", "key_priority": 2, "attribute_priority": 1},
            {"attribute_key": "company", "value": "siemens", "key_priority": 3, "attribute_priority": 1},
            {"attribute_key": "power", "value": "1.5 kw", "key_priority": 1, "attribute_priority": 2},
            {"attribute_key": "wattage", "value": "1.5 kw", "key_priority": 2, "attribute_priority": 2},
            {"attribute_key": "kilowatt", "value": "1.5 kw", "key_priority": 3, "attribute_priority": 2},
            {"attribute_key": "voltage", "value": "415v", "key_priority": 1, "attribute_priority": 3},
            {"attribute_key": "volt", "value": "415v", "key_priority": 2, "attribute_priority": 3},
            {"attribute_key": "phase", "value": "three phase", "key_priority": 1, "attribute_priority": 4},
            {"attribute_key": "phase_type", "value": "three phase", "key_priority": 2, "attribute_priority": 4},
            {"attribute_key": "motor_type", "value": "motor", "key_priority": 1, "attribute_priority": 5}
        ]
    },
    {
        "query": "crompton 3 hp single phase 1440 rpm motor",
        "attributes": [
            {"attribute_key": "brand", "value": "crompton", "key_priority": 1, "attribute_priority": 1},
            {"attribute_key": "horsepower", "value": "3 hp", "key_priority": 1, "attribute_priority": 2},
            {"attribute_key": "power", "value": "3 hp", "key_priority": 2, "attribute_priority": 2},
            {"attribute_key": "hp", "value": "3 hp", "key_priority": 3, "attribute_priority": 2},
            {"attribute_key": "phase", "value": "single phase", "key_priority": 1, "attribute_priority": 3},
            {"attribute_key": "phase_type", "value": "single phase", "key_priority": 2, "attribute_priority": 3},
            {"attribute_key": "rpm", "value": "1440 rpm", "key_priority": 1, "attribute_priority": 4},
            {"attribute_key": "speed", "value": "1440 rpm", "key_priority": 2, "attribute_priority": 4},
            {"attribute_key": "rotation_speed", "value": "1440 rpm", "key_priority": 3, "attribute_priority": 4}
        ]
    },
    {
        "query": "abb 7.5 kw 960 rpm tefc motor ip55",
        "attributes": [
            {"attribute_key": "brand", "value": "abb", "key_priority": 1, "attribute_priority": 1},
            {"attribute_key": "power", "value": "7.5 kw", "key_priority": 1, "attribute_priority": 2},
            {"attribute_key": "wattage", "value": "7.5 kw", "key_priority": 2, "attribute_priority": 2},
            {"attribute_key": "rpm", "value": "960 rpm", "key_priority": 1, "attribute_priority": 3},
            {"attribute_key": "speed", "value": "960 rpm", "key_priority": 2, "attribute_priority": 3},
            {"attribute_key": "enclosure", "value": "tefc", "key_priority": 1, "attribute_priority": 4},
            {"attribute_key": "enclosure_type", "value": "tefc", "key_priority": 2, "attribute_priority": 4},
            {"attribute_key": "protection", "value": "ip55", "key_priority": 1, "attribute_priority": 5},
            {"attribute_key": "ip_rating", "value": "ip55", "key_priority": 2, "attribute_priority": 5}
        ]
    },
    {
        "query": "bldc motor 24v 3000 rpm with encoder",
        "attributes": [
            {"attribute_key": "motor_type", "value": "bldc", "key_priority": 1, "attribute_priority": 1},
            {"attribute_key": "brushless_dc", "value": "bldc", "key_priority": 2, "attribute_priority": 1},
            {"attribute_key": "voltage", "value": "24v", "key_priority": 1, "attribute_priority": 2},
            {"attribute_key": "volt", "value": "24v", "key_priority": 2, "attribute_priority": 2},
            {"attribute_key": "rpm", "value": "3000 rpm", "key_priority": 1, "attribute_priority": 3},
            {"attribute_key": "speed", "value": "3000 rpm", "key_priority": 2, "attribute_priority": 3},
            {"attribute_key": "feature", "value": "encoder", "key_priority": 1, "attribute_priority": 4},
            {"attribute_key": "accessory", "value": "encoder", "key_priority": 2, "attribute_priority": 4}
        ]
    },
    {
        "query": "stepper motor nema 23 1.8 degree bipolar",
        "attributes": [
            {"attribute_key": "motor_type", "value": "stepper motor", "key_priority": 1, "attribute_priority": 1},
            {"attribute_key": "stepper", "value": "stepper motor", "key_priority": 2, "attribute_priority": 1},
            {"attribute_key": "size", "value": "nema 23", "key_priority": 1, "attribute_priority": 2},
            {"attribute_key": "nema_size", "value": "nema 23", "key_priority": 2, "attribute_priority": 2},
            {"attribute_key": "step_angle", "value": "1.8 degree", "key_priority": 1, "attribute_priority": 3},
            {"attribute_key": "angle", "value": "1.8 degree", "key_priority": 2, "attribute_priority": 3},
            {"attribute_key": "winding", "value": "bipolar", "key_priority": 1, "attribute_priority": 4},
            {"attribute_key": "winding_type", "value": "bipolar", "key_priority": 2, "attribute_priority": 4}
        ]
    },
    {
        "query": "kirloskar 10 hp 3 phase 960 rpm flange mounted motor",
        "attributes": [
            {"attribute_key": "brand", "value": "kirloskar", "key_priority": 1, "attribute_priority": 1},
            {"attribute_key": "horsepower", "value": "10 hp", "key_priority": 1, "attribute_priority": 2},
            {"attribute_key": "power", "value": "10 hp", "key_priority": 2, "attribute_priority": 2},
            {"attribute_key": "phase", "value": "3 phase", "key_priority": 1, "attribute_priority": 3},
            {"attribute_key": "phase_type", "value": "3 phase", "key_priority": 2, "attribute_priority": 3},
            {"attribute_key": "rpm", "value": "960 rpm", "key_priority": 1, "attribute_priority": 4},
            {"attribute_key": "speed", "value": "960 rpm", "key_priority": 2, "attribute_priority": 4},
            {"attribute_key": "mounting", "value": "flange mounted", "key_priority": 1, "attribute_priority": 5},
            {"attribute_key": "mounting_type", "value": "flange mounted", "key_priority": 2, "attribute_priority": 5}
        ]
    },
    {
        "query": "servo motor 750w 3000 rpm 230v ac",
        "attributes": [
            {"attribute_key": "motor_type", "value": "servo motor", "key_priority": 1, "attribute_priority": 1},
            {"attribute_key": "servo", "value": "servo motor", "key_priority": 2, "attribute_priority": 1},
            {"attribute_key": "power", "value": "750w", "key_priority": 1, "attribute_priority": 2},
            {"attribute_key": "wattage", "value": "750w", "key_priority": 2, "attribute_priority": 2},
            {"attribute_key": "rpm", "value": "3000 rpm", "key_priority": 1, "attribute_priority": 3},
            {"attribute_key": "speed", "value": "3000 rpm", "key_priority": 2, "attribute_priority": 3},
            {"attribute_key": "voltage", "value": "230v", "key_priority": 1, "attribute_priority": 4},
            {"attribute_key": "volt", "value": "230v", "key_priority": 2, "attribute_priority": 4},
            {"attribute_key": "current_type", "value": "ac", "key_priority": 1, "attribute_priority": 5}
        ]
    },
    {
        "query": "havells 2 hp single phase cooler motor copper winding",
        "attributes": [
            {"attribute_key": "brand", "value": "havells", "key_priority": 1, "attribute_priority": 1},
            {"attribute_key": "horsepower", "value": "2 hp", "key_priority": 1, "attribute_priority": 2},
            {"attribute_key": "power", "value": "2 hp", "key_priority": 2, "attribute_priority": 2},
            {"attribute_key": "phase", "value": "single phase", "key_priority": 1, "attribute_priority": 3},
            {"attribute_key": "application", "value": "cooler motor", "key_priority": 1, "attribute_priority": 4},
            {"attribute_key": "use", "value": "cooler motor", "key_priority": 2, "attribute_priority": 4},
            {"attribute_key": "winding_material", "value": "copper", "key_priority": 1, "attribute_priority": 5},
            {"attribute_key": "material", "value": "copper", "key_priority": 2, "attribute_priority": 5}
        ]
    },
    {
        "query": "dc motor 12v 100 rpm high torque geared",
        "attributes": [
            {"attribute_key": "motor_type", "value": "dc motor", "key_priority": 1, "attribute_priority": 1},
            {"attribute_key": "dc", "value": "dc motor", "key_priority": 2, "attribute_priority": 1},
            {"attribute_key": "voltage", "value": "12v", "key_priority": 1, "attribute_priority": 2},
            {"attribute_key": "volt", "value": "12v", "key_priority": 2, "attribute_priority": 2},
            {"attribute_key": "rpm", "value": "100 rpm", "key_priority": 1, "attribute_priority": 3},
            {"attribute_key": "speed", "value": "100 rpm", "key_priority": 2, "attribute_priority": 3},
            {"attribute_key": "torque", "value": "high torque", "key_priority": 1, "attribute_priority": 4},
            {"attribute_key": "feature", "value": "geared", "key_priority": 1, "attribute_priority": 5},
            {"attribute_key": "gearbox", "value": "geared", "key_priority": 2, "attribute_priority": 5}
        ]
    },
    {
        "query": "panasonic ac servo motor 400w with brake",
        "attributes": [
            {"attribute_key": "brand", "value": "panasonic", "key_priority": 1, "attribute_priority": 1},
            {"attribute_key": "motor_type", "value": "ac servo motor", "key_priority": 1, "attribute_priority": 2},
            {"attribute_key": "servo", "value": "ac servo motor", "key_priority": 2, "attribute_priority": 2},
            {"attribute_key": "power", "value": "400w", "key_priority": 1, "attribute_priority": 3},
            {"attribute_key": "wattage", "value": "400w", "key_priority": 2, "attribute_priority": 3},
            {"attribute_key": "feature", "value": "brake", "key_priority": 1, "attribute_priority": 4},
            {"attribute_key": "brake", "value": "brake", "key_priority": 2, "attribute_priority": 4}
        ]
    }
]


def build_prompt(query: str) -> str:
    """
    Build token-efficient few-shot prompt with 10 examples.
    
    Format:
    - System instruction (concise)
    - 10 few-shot examples (compact JSON)
    - User query
    
    Token budget per query: ~2000 input + 500 output = 2500 total
    Cost per query: ~$0.0025 (2.5K tokens)
    """
    
    # Compact system instruction (token-efficient)
    system_prompt = """Extract product attributes with multiple key alternatives and priorities.
Output JSON: {"attributes": [{"attribute_key": "key", "value": "val", "key_priority": 1-3, "attribute_priority": 1-N}]}
Rules: 1) Multiple keys per value 2) key_priority: synonyms ranking 3) attribute_priority: attribute importance"""
    
    # Build few-shot examples (compact format)
    few_shot_text = "\n\n".join([
        f"Query: {ex['query']}\nOutput: {json.dumps({'attributes': ex['attributes']}, separators=(',', ':'))}"
        for ex in FEW_SHOT_EXAMPLES
    ])
    
    # Full prompt
    full_prompt = f"{system_prompt}\n\nExamples:\n{few_shot_text}\n\nQuery: {query}\nOutput:"
    
    return full_prompt


def call_gemini_api(query: str) -> Dict[str, Any]:
    """
    Call Gemini 3 Pro Preview via OpenRouter API.
    
    Returns:
        {
            'success': bool,
            'raw_output': str,
            'attributes': List[Dict],
            'input_tokens': int,
            'output_tokens': int,
            'cost': float
        }
    """
    
    prompt = build_prompt(query)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,  # Deterministic output
        "max_tokens": 3000,  # Maximum limit for most complex queries
        "top_p": 1.0
    }
    
    try:
        response = requests.post(API_BASE_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract response
        raw_output = data['choices'][0]['message']['content'].strip()
        
        # Token usage and cost
        usage = data.get('usage', {})
        input_tokens = usage.get('prompt_tokens', 0)
        output_tokens = usage.get('completion_tokens', 0)
        cost = (input_tokens * INPUT_COST_PER_1K / 1000) + (output_tokens * OUTPUT_COST_PER_1K / 1000)
        
        # Check if hitting token limit (potential truncation)
        max_output = 3000
        token_limit_warning = ""
        if output_tokens >= max_output * 0.95:  # 95% threshold
            token_limit_warning = f" [WARN: Hit {output_tokens}/{max_output} token limit - possible truncation]"
        
        # Parse JSON from output
        try:
            # Extract JSON if wrapped in markdown or extra text
            if '{' in raw_output and '}' in raw_output:
                json_start = raw_output.find('{')
                json_end = raw_output.rfind('}') + 1
                json_str = raw_output[json_start:json_end]
                parsed = json.loads(json_str)
                attributes = parsed.get('attributes', [])
                
                return {
                    'success': True,
                    'raw_output': raw_output,
                    'attributes': attributes,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'cost': cost,
                    'token_warning': token_limit_warning
                }
            else:
                return {
                    'success': False,
                    'raw_output': raw_output,
                    'attributes': [],
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'cost': cost,
                    'error': 'No JSON in output',
                    'token_warning': token_limit_warning
                }
                
        except json.JSONDecodeError as e:
            # If JSON parse fails and we hit token limit, it's likely truncation
            error_msg = f'JSON parse error: {e}'
            if output_tokens >= max_output * 0.95:
                error_msg += " [Likely caused by token limit truncation]"
            
            return {
                'success': False,
                'raw_output': raw_output,
                'attributes': [],
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost': cost,
                'error': error_msg,
                'token_warning': token_limit_warning
            }
            
    except requests.exceptions.RequestException as e:
        # Detailed error for debugging
        error_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = f"{e.response.status_code}: {error_data}"
            except:
                error_msg = f"{e.response.status_code}: {e.response.text[:200]}"
        
        return {
            'success': False,
            'raw_output': f'API Error: {error_msg}',
            'attributes': [],
            'input_tokens': 0,
            'output_tokens': 0,
            'cost': 0,
            'error': error_msg
        }


def read_queries(filepath: str) -> List[str]:
    """Read queries from file (same logic as Gemma script)."""
    queries = []
    
    # Try CSV first
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'query' in (reader.fieldnames or []):
                for row in reader:
                    q = row['query'].strip()
                    if q:
                        queries.append(q)
                return queries
    except:
        pass
    
    # Fall back to line-by-line
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if line and line.lower() != 'query':
            queries.append(line)
    
    return queries


def main():
    parser = argparse.ArgumentParser(description='Gemini 3 Pro batch inference with few-shot learning')
    parser.add_argument('--input', default='76cat_queries', help='Input queries file')
    parser.add_argument('--output', default='gemini_1000_results.csv', help='Output CSV file')
    parser.add_argument('--start', type=int, default=0, help='Start index (for resume)')
    parser.add_argument('--limit', type=int, default=0, help='Max queries (0=all, use to stay within budget)')
    parser.add_argument('--test', action='store_true', help='Test API with single query')
    args = parser.parse_args()
    
    # Test mode: single query with full error details
    if args.test:
        print("Testing API with single query...")
        print(f"API URL: {API_BASE_URL}")
        print(f"Model: {MODEL_NAME}")
        print("-" * 80)
        
        test_query = "siemens 1.5 kw motor"
        result = call_gemini_api(test_query)
        
        print(f"\nSuccess: {result['success']}")
        print(f"Input tokens: {result['input_tokens']}")
        print(f"Output tokens: {result['output_tokens']}")
        print(f"Cost: ${result['cost']:.6f}")
        
        if result['success']:
            print(f"\nAttributes found: {len(result['attributes'])}")
            print(f"\nRaw output:\n{result['raw_output']}")
        else:
            print(f"\nError: {result.get('error', 'Unknown')}")
            print(f"\nRaw output:\n{result['raw_output']}")
        
        return
    
    # Read queries
    queries = read_queries(args.input)
    print(f"Total queries loaded: {len(queries)}")
    
    if args.limit > 0:
        queries = queries[:args.limit]
        print(f"Limited to first {args.limit} queries")
    
    if args.start > 0:
        queries = queries[args.start:]
        print(f"Starting from index {args.start}, remaining: {len(queries)}")
    
    # Budget tracking
    total_cost = 0.0
    budget_limit = 10.0  # $10 budget
    
    # CSV output with UTF-8 encoding
    csv_mode = 'a' if args.start > 0 else 'w'
    csv_file = open(args.output, csv_mode, newline='', encoding='utf-8-sig')  # BOM for Excel compatibility
    writer = csv.writer(csv_file)
    
    if args.start == 0:
        writer.writerow(['query', 'success', 'unique_value_count', 'total_key_count', 
                        'raw_output', 'attributes_json', 'input_tokens', 'output_tokens', 'cost'])
    
    print(f"\n{'='*80}")
    print(f"Processing {len(queries)} queries with Gemini 3 Pro Preview")
    print(f"Budget limit: ${budget_limit:.2f}")
    print(f"{'='*80}\n")
    
    success_count = 0
    total_time = 0
    
    for idx, query in enumerate(queries):
        actual_idx = idx + args.start
        t0 = time.time()
        
        # Check budget before making API call
        if total_cost >= budget_limit:
            print(f"\nWARNING: Budget limit ${budget_limit:.2f} reached! Stopping at query {actual_idx}")
            print(f"Processed {actual_idx} queries successfully")
            break
        
        try:
            result = call_gemini_api(query)
            
            # Debug: Print error details for first few failures
            if not result['success'] and idx < 5:
                print(f"\n  DEBUG Error: {result.get('error', 'Unknown error')}")
                print(f"  Raw output: {result['raw_output'][:200]}\n")
            
            # Calculate stats
            unique_values = set()
            if result['success']:
                for attr in result['attributes']:
                    unique_values.add(str(attr.get('value', '')).strip().lower())
            
            unique_value_count = len(unique_values)
            total_key_count = len(result['attributes'])
            
            # Write to CSV
            row = [
                query,
                result['success'],
                unique_value_count,
                total_key_count,
                result['raw_output'],
                json.dumps({'attributes': result['attributes']}) if result['success'] else '',
                result['input_tokens'],
                result['output_tokens'],
                f"${result['cost']:.6f}"
            ]
            
            writer.writerow(row)
            csv_file.flush()
            
            # Update tracking
            elapsed = time.time() - t0
            total_time += elapsed
            total_cost += result['cost']
            
            if result['success']:
                success_count += 1
            
            # Progress display
            avg_time = total_time / (idx + 1)
            remaining = avg_time * (len(queries) - idx - 1)
            avg_cost = total_cost / (idx + 1)
            estimated_total_cost = avg_cost * len(queries)
            
            status = 'OK' if result['success'] else 'FAIL'
            token_warn = result.get('token_warning', '')
            
            print(f"[{actual_idx + 1}/{len(queries) + args.start}] {status} "
                  f"| {unique_value_count} vals, {total_key_count} keys "
                  f"| {result['input_tokens']}in/{result['output_tokens']}out tok "
                  f"| ${result['cost']:.4f} "
                  f"| {elapsed:.1f}s "
                  f"| Cost: ${total_cost:.2f}/${estimated_total_cost:.2f} "
                  f"| ETA: {remaining/60:.0f}min "
                  f"| {query[:50]}{token_warn}")
            
            # Rate limiting: ~1 request per second to avoid throttling
            time.sleep(1.0)
            
        except Exception as e:
            print(f"[{actual_idx + 1}] ERROR: {e} | {query[:50]}")
            writer.writerow([query, False, 0, 0, f"ERROR: {e}", '', 0, 0, '$0.00'])
            csv_file.flush()
    
    csv_file.close()
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"COMPLETION SUMMARY")
    print(f"{'='*80}")
    print(f"Queries processed: {min(len(queries), actual_idx + 1)}")
    print(f"Success rate: {success_count}/{min(len(queries), actual_idx + 1)}")
    print(f"Total cost: ${total_cost:.2f} / ${budget_limit:.2f} budget")
    print(f"Avg time per query: {total_time / max(1, len(queries)):.2f}s")
    print(f"Output saved: {args.output}")
    
    if total_cost < budget_limit:
        remaining_budget = budget_limit - total_cost
        est_more_queries = int(remaining_budget / (total_cost / max(1, len(queries))))
        print(f"Remaining budget: ${remaining_budget:.2f} (~{est_more_queries} more queries)")
    
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
