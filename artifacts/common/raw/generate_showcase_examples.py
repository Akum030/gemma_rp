#!/usr/bin/env python3
"""
Generate showcase examples for presentation
- 5 best matching examples (all models align)
- 5 examples where Gemma/QMeans fail to match GT
"""

import csv
import json
from collections import defaultdict

def load_csv_results(filepath):
    results = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = row['query']
            attrs = []
            json_col = 'attributes_json' if 'attributes_json' in row else None
            if json_col and row.get(json_col):
                try:
                    data = json.loads(row[json_col])
                    attrs = data.get('attributes', [])
                except:
                    pass
            results[query] = {
                'success': row.get('success', 'True') == 'True',
                'attributes': attrs
            }
    return results

def load_qmeans_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = {}
    for item in data:
        query = item['query']
        attrs = []
        if item.get('attributes'):
            for i, (key, value) in enumerate(item['attributes'].items(), 1):
                attrs.append({
                    'attribute_key': key,
                    'value': value,
                    'key_priority': 1,
                    'attribute_priority': i
                })
        results[query] = {
            'success': item.get('success', False),
            'attributes': attrs
        }
    return results

def normalize_key(key):
    if key is None:
        return ''
    return ' '.join(str(key).lower().strip().replace('_', ' ').replace('-', ' ').split())

def normalize_value(value):
    if value is None:
        return ''
    return ' '.join(str(value).lower().strip().split())

def format_attrs_for_display(attrs):
    """Format attributes in readable way with priorities"""
    if not attrs:
        return []
    
    formatted = []
    for attr in sorted(attrs, key=lambda x: (x.get('attribute_priority', 1), x.get('key_priority', 1))):
        formatted.append({
            "value": attr.get('value', ''),
            "key": attr.get('attribute_key', ''),
            "key_priority": attr.get('key_priority', 1),
            "attribute_priority": attr.get('attribute_priority', 1)
        })
    return formatted

def get_unique_normalized_keys(attrs):
    return set(normalize_key(a.get('attribute_key', '')) for a in attrs if a.get('attribute_key'))

def get_unique_normalized_values(attrs):
    return set(normalize_value(a.get('value', '')) for a in attrs if a.get('value'))

def calculate_match(gt_attrs, model_attrs):
    """Calculate key and value match counts"""
    gt_keys = get_unique_normalized_keys(gt_attrs)
    model_keys = get_unique_normalized_keys(model_attrs)
    gt_values = get_unique_normalized_values(gt_attrs)
    model_values = get_unique_normalized_values(model_attrs)
    
    return {
        'key_match': len(gt_keys & model_keys),
        'value_match': len(gt_values & model_values),
        'gt_keys': len(gt_keys),
        'model_keys': len(model_keys),
        'gt_values': len(gt_values),
        'model_values': len(model_values),
        'matched_keys': sorted(gt_keys & model_keys),
        'matched_values': sorted(gt_values & model_values)
    }

def main():
    print("Loading data...")
    gt_results = load_csv_results('claude_1000_results.csv')
    gemma_results = load_csv_results('../present/gemma_v4_1000_results.csv')
    gemini_results = load_csv_results('gemini_final_results.csv')
    qmeans_results = load_qmeans_json('qmeans_results.json')
    
    # Find queries that exist in all 4 sources
    common_queries = set(gt_results.keys()) & set(gemma_results.keys()) & set(gemini_results.keys()) & set(qmeans_results.keys())
    print(f"Common queries across all 4 sources: {len(common_queries)}")
    
    # Analyze each query
    query_scores = []
    for query in common_queries:
        gt_attrs = gt_results[query].get('attributes', [])
        gemma_attrs = gemma_results[query].get('attributes', [])
        gemini_attrs = gemini_results[query].get('attributes', [])
        qmeans_attrs = qmeans_results[query].get('attributes', [])
        
        if not gt_attrs:
            continue
        
        gemma_match = calculate_match(gt_attrs, gemma_attrs)
        gemini_match = calculate_match(gt_attrs, gemini_attrs)
        qmeans_match = calculate_match(gt_attrs, qmeans_attrs)
        
        # Score: higher is better match
        total_score = (
            gemma_match['key_match'] + gemma_match['value_match'] +
            gemini_match['key_match'] + gemini_match['value_match'] +
            qmeans_match['key_match'] + qmeans_match['value_match']
        )
        
        # Mismatch score: Gemma and QMeans fail but Gemini succeeds
        mismatch_score = (
            gemini_match['key_match'] * 2 - 
            gemma_match['key_match'] - 
            qmeans_match['key_match']
        )
        
        query_scores.append({
            'query': query,
            'total_score': total_score,
            'mismatch_score': mismatch_score,
            'gt_attrs': gt_attrs,
            'gemma_attrs': gemma_attrs,
            'gemini_attrs': gemini_attrs,
            'qmeans_attrs': qmeans_attrs,
            'gemma_match': gemma_match,
            'gemini_match': gemini_match,
            'qmeans_match': qmeans_match
        })
    
    # Sort by total score for best matches
    best_matches = sorted(query_scores, key=lambda x: -x['total_score'])[:20]
    
    # Filter to get diverse, meaningful examples (at least 3 GT attributes)
    best_examples = []
    for q in best_matches:
        if len(q['gt_attrs']) >= 3 and q['gemma_match']['key_match'] >= 2 and q['qmeans_match']['key_match'] >= 1:
            best_examples.append(q)
            if len(best_examples) >= 5:
                break
    
    # Sort by mismatch score for worst matches (Gemma/QMeans fail)
    worst_matches = sorted(query_scores, key=lambda x: -x['mismatch_score'])
    
    # Filter for meaningful mismatch examples
    mismatch_examples = []
    for q in worst_matches:
        if (len(q['gt_attrs']) >= 3 and 
            q['gemini_match']['key_match'] >= 3 and 
            q['gemma_match']['key_match'] <= 1 and 
            q['qmeans_match']['key_match'] <= 1):
            mismatch_examples.append(q)
            if len(mismatch_examples) >= 5:
                break
    
    # If not enough, try different criteria
    if len(mismatch_examples) < 5:
        for q in worst_matches:
            if q in mismatch_examples:
                continue
            if (len(q['gt_attrs']) >= 2 and 
                q['gemini_match']['key_match'] >= 2 and 
                (q['gemma_match']['key_match'] <= 1 or q['qmeans_match']['key_match'] <= 1)):
                mismatch_examples.append(q)
                if len(mismatch_examples) >= 5:
                    break
    
    # Create JSON output
    output = {
        "report_title": "Attribute Extraction Model Comparison - Showcase Examples",
        "date": "February 2026",
        "best_matching_examples": [],
        "mismatch_examples": []
    }
    
    print("\n" + "="*80)
    print("5 BEST MATCHING EXAMPLES (All models align well)")
    print("="*80)
    
    for i, ex in enumerate(best_examples[:5], 1):
        example = {
            "example_number": i,
            "query": ex['query'],
            "summary": {
                "gemini_key_match": f"{ex['gemini_match']['key_match']}/{ex['gemini_match']['gt_keys']}",
                "gemma_key_match": f"{ex['gemma_match']['key_match']}/{ex['gemma_match']['gt_keys']}",
                "qmeans_key_match": f"{ex['qmeans_match']['key_match']}/{ex['qmeans_match']['gt_keys']}",
                "matched_keys": ex['gemini_match']['matched_keys']
            },
            "ground_truth": {
                "source": "Claude Opus",
                "attributes": format_attrs_for_display(ex['gt_attrs'])
            },
            "gemini": {
                "source": "Gemini Zero-shot",
                "key_match": ex['gemini_match']['key_match'],
                "value_match": ex['gemini_match']['value_match'],
                "attributes": format_attrs_for_display(ex['gemini_attrs'])
            },
            "gemma_v4": {
                "source": "Gemma 2 9B Fine-tuned",
                "key_match": ex['gemma_match']['key_match'],
                "value_match": ex['gemma_match']['value_match'],
                "attributes": format_attrs_for_display(ex['gemma_attrs'])
            },
            "qmeans": {
                "source": "QMeans Production",
                "key_match": ex['qmeans_match']['key_match'],
                "value_match": ex['qmeans_match']['value_match'],
                "attributes": format_attrs_for_display(ex['qmeans_attrs'])
            }
        }
        output["best_matching_examples"].append(example)
        
        print(f"\n--- Example {i}: {ex['query']} ---")
        print(f"Key Matches: Gemini={ex['gemini_match']['key_match']}, Gemma={ex['gemma_match']['key_match']}, QMeans={ex['qmeans_match']['key_match']}")
    
    print("\n" + "="*80)
    print("5 MISMATCH EXAMPLES (Gemma/QMeans fail to match GT)")
    print("="*80)
    
    for i, ex in enumerate(mismatch_examples[:5], 1):
        example = {
            "example_number": i,
            "query": ex['query'],
            "issue": "Gemma and QMeans have low key match compared to Gemini",
            "summary": {
                "gemini_key_match": f"{ex['gemini_match']['key_match']}/{ex['gemini_match']['gt_keys']} (Good)",
                "gemma_key_match": f"{ex['gemma_match']['key_match']}/{ex['gemma_match']['gt_keys']} (Poor)",
                "qmeans_key_match": f"{ex['qmeans_match']['key_match']}/{ex['qmeans_match']['gt_keys']} (Poor)",
                "gemini_matched_keys": ex['gemini_match']['matched_keys'],
                "gemma_matched_keys": ex['gemma_match']['matched_keys'],
                "qmeans_matched_keys": ex['qmeans_match']['matched_keys']
            },
            "ground_truth": {
                "source": "Claude Opus",
                "attributes": format_attrs_for_display(ex['gt_attrs'])
            },
            "gemini": {
                "source": "Gemini Zero-shot",
                "key_match": ex['gemini_match']['key_match'],
                "value_match": ex['gemini_match']['value_match'],
                "status": "GOOD MATCH",
                "attributes": format_attrs_for_display(ex['gemini_attrs'])
            },
            "gemma_v4": {
                "source": "Gemma 2 9B Fine-tuned",
                "key_match": ex['gemma_match']['key_match'],
                "value_match": ex['gemma_match']['value_match'],
                "status": "POOR MATCH",
                "attributes": format_attrs_for_display(ex['gemma_attrs'])
            },
            "qmeans": {
                "source": "QMeans Production",
                "key_match": ex['qmeans_match']['key_match'],
                "value_match": ex['qmeans_match']['value_match'],
                "status": "POOR MATCH",
                "attributes": format_attrs_for_display(ex['qmeans_attrs'])
            }
        }
        output["mismatch_examples"].append(example)
        
        print(f"\n--- Example {i}: {ex['query']} ---")
        print(f"Key Matches: Gemini={ex['gemini_match']['key_match']} (Good), Gemma={ex['gemma_match']['key_match']} (Poor), QMeans={ex['qmeans_match']['key_match']} (Poor)")
    
    # Save JSON output
    with open('../present/showcase_examples.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("Output saved to: ../present/showcase_examples.json")
    print("="*80)

if __name__ == '__main__':
    main()
