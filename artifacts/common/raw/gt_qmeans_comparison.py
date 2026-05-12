#!/usr/bin/env python3
"""
Ground Truth (Claude Opus) vs QMeans Comparison Analysis
Creates detailed comparison CSV showing matched keys, values, and priorities.
"""

import csv
import json
import os
from collections import defaultdict

def load_claude_results(filepath):
    """Load Claude (Ground Truth) results."""
    results = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = row['query']
            attrs = []
            if row['attributes_json']:
                try:
                    data = json.loads(row['attributes_json'])
                    attrs = data.get('attributes', [])
                except:
                    pass
            results[query] = {
                'success': row['success'] == 'True',
                'attributes': attrs,
                'unique_values': int(row['unique_value_count']) if row['unique_value_count'] else 0,
                'total_keys': int(row['total_key_count']) if row['total_key_count'] else 0
            }
    return results

def load_qmeans_results(filepath):
    """Load QMeans results from JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = {}
    for item in data:
        query = item['query']
        results[query] = {
            'success': item.get('success', False),
            'attributes': item.get('attributes', {}),
            'response_time': item.get('response_time', 0)
        }
    return results

def normalize_key(key):
    """Normalize key for comparison."""
    return key.lower().strip().replace('_', ' ').replace('-', ' ')

def normalize_value(value):
    """Normalize value for comparison."""
    if value is None:
        return ''
    return str(value).lower().strip()

def compare_query(gt_data, qmeans_data, query):
    """
    Compare Ground Truth (Claude) vs QMeans for a single query.
    Returns detailed comparison metrics.
    """
    result = {
        'query': query,
        'gt_success': gt_data.get('success', False) if gt_data else False,
        'qmeans_success': qmeans_data.get('success', False) if qmeans_data else False,
        'gt_total_keys': gt_data.get('total_keys', 0) if gt_data else 0,
        'gt_unique_values': gt_data.get('unique_values', 0) if gt_data else 0,
        'qmeans_total_keys': len(qmeans_data.get('attributes', {})) if qmeans_data else 0,
        'matched_keys': [],
        'matched_values': [],
        'gt_only_keys': [],
        'qmeans_only_keys': [],
        'key_match_details': [],
        'value_match_details': []
    }
    
    if not gt_data or not qmeans_data:
        return result
    
    gt_attrs = gt_data.get('attributes', [])
    qmeans_attrs = qmeans_data.get('attributes', {})
    
    # Create lookup structures for GT
    gt_keys_normalized = {}  # normalized_key -> list of {original_key, value, key_priority, attr_priority}
    gt_values_normalized = set()
    
    for attr in gt_attrs:
        key = attr.get('attribute_key', '')
        value = attr.get('value', '')
        key_priority = attr.get('key_priority', 0)
        attr_priority = attr.get('attribute_priority', 0)
        
        norm_key = normalize_key(key)
        norm_value = normalize_value(value)
        
        if norm_key not in gt_keys_normalized:
            gt_keys_normalized[norm_key] = []
        gt_keys_normalized[norm_key].append({
            'original_key': key,
            'value': value,
            'key_priority': key_priority,
            'attribute_priority': attr_priority
        })
        gt_values_normalized.add(norm_value)
    
    # Create lookup for QMeans
    qmeans_keys_normalized = {}  # normalized_key -> original_key, value
    qmeans_values_normalized = set()
    
    for key, value in qmeans_attrs.items():
        norm_key = normalize_key(key)
        norm_value = normalize_value(value)
        qmeans_keys_normalized[norm_key] = {'original_key': key, 'value': value}
        qmeans_values_normalized.add(norm_value)
    
    # Find matched keys
    matched_keys = set(gt_keys_normalized.keys()) & set(qmeans_keys_normalized.keys())
    gt_only = set(gt_keys_normalized.keys()) - set(qmeans_keys_normalized.keys())
    qmeans_only = set(qmeans_keys_normalized.keys()) - set(gt_keys_normalized.keys())
    
    # Find matched values
    matched_values = gt_values_normalized & qmeans_values_normalized
    
    result['matched_keys'] = list(matched_keys)
    result['matched_values'] = list(matched_values)
    result['gt_only_keys'] = list(gt_only)
    result['qmeans_only_keys'] = list(qmeans_only)
    
    # Detailed key match info with priorities
    key_match_details = []
    for norm_key in matched_keys:
        gt_info = gt_keys_normalized[norm_key][0]  # Take first match (best priority usually)
        qmeans_info = qmeans_keys_normalized[norm_key]
        
        # Check if values also match
        gt_val_norm = normalize_value(gt_info['value'])
        qmeans_val_norm = normalize_value(qmeans_info['value'])
        value_match = gt_val_norm == qmeans_val_norm
        
        key_match_details.append({
            'normalized_key': norm_key,
            'gt_key': gt_info['original_key'],
            'gt_value': gt_info['value'],
            'gt_key_priority': gt_info['key_priority'],
            'gt_attr_priority': gt_info['attribute_priority'],
            'qmeans_key': qmeans_info['original_key'],
            'qmeans_value': qmeans_info['value'],
            'value_also_matches': value_match
        })
    
    result['key_match_details'] = key_match_details
    
    # Value match details (values that match but might be under different keys)
    value_match_details = []
    for norm_val in matched_values:
        # Find GT keys with this value
        gt_keys_for_val = []
        for attr in gt_attrs:
            if normalize_value(attr.get('value', '')) == norm_val:
                gt_keys_for_val.append({
                    'key': attr.get('attribute_key', ''),
                    'key_priority': attr.get('key_priority', 0),
                    'attr_priority': attr.get('attribute_priority', 0)
                })
        
        # Find QMeans keys with this value
        qmeans_keys_for_val = []
        for key, value in qmeans_attrs.items():
            if normalize_value(value) == norm_val:
                qmeans_keys_for_val.append(key)
        
        value_match_details.append({
            'value': norm_val,
            'gt_keys': gt_keys_for_val,
            'qmeans_keys': qmeans_keys_for_val
        })
    
    result['value_match_details'] = value_match_details
    
    return result


def main():
    # Paths
    claude_path = 'claude_1000_results.csv'
    qmeans_path = 'qmeans_results.json'
    output_path = '../present/gt_vs_qmeans_detailed_comparison.csv'
    summary_path = '../present/gt_vs_qmeans_summary.csv'
    
    print("Loading Ground Truth (Claude Opus) results...")
    gt_results = load_claude_results(claude_path)
    print(f"  Loaded {len(gt_results)} queries")
    
    print("Loading QMeans results...")
    qmeans_results = load_qmeans_results(qmeans_path)
    print(f"  Loaded {len(qmeans_results)} queries")
    
    # Compare all queries
    print("\nComparing queries...")
    comparisons = []
    
    # Use GT queries as the base (since Claude processed all 1000)
    for query in gt_results.keys():
        gt_data = gt_results.get(query)
        qmeans_data = qmeans_results.get(query)
        
        comparison = compare_query(gt_data, qmeans_data, query)
        comparisons.append(comparison)
    
    # Write detailed CSV
    print(f"\nWriting detailed comparison to {output_path}...")
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'query',
            'gt_success',
            'qmeans_success',
            'gt_total_keys',
            'gt_unique_values',
            'qmeans_total_keys',
            'matched_key_count',
            'matched_value_count',
            'gt_only_key_count',
            'qmeans_only_key_count',
            'key_match_rate',
            'value_match_rate',
            'matched_keys',
            'gt_only_keys',
            'qmeans_only_keys',
            'matched_values',
            'key_match_details_json',
            'value_match_details_json'
        ])
        
        for comp in comparisons:
            # Calculate match rates
            gt_unique_keys = len(set(normalize_key(a.get('attribute_key', '')) for a in gt_results.get(comp['query'], {}).get('attributes', [])))
            key_match_rate = len(comp['matched_keys']) / gt_unique_keys if gt_unique_keys > 0 else 0
            
            gt_unique_vals = comp['gt_unique_values']
            value_match_rate = len(comp['matched_values']) / gt_unique_vals if gt_unique_vals > 0 else 0
            
            writer.writerow([
                comp['query'],
                comp['gt_success'],
                comp['qmeans_success'],
                comp['gt_total_keys'],
                comp['gt_unique_values'],
                comp['qmeans_total_keys'],
                len(comp['matched_keys']),
                len(comp['matched_values']),
                len(comp['gt_only_keys']),
                len(comp['qmeans_only_keys']),
                f"{key_match_rate:.2%}",
                f"{value_match_rate:.2%}",
                '; '.join(comp['matched_keys']),
                '; '.join(comp['gt_only_keys'][:10]),  # Limit to first 10
                '; '.join(comp['qmeans_only_keys']),
                '; '.join(comp['matched_values']),
                json.dumps(comp['key_match_details']),
                json.dumps(comp['value_match_details'])
            ])
    
    # Calculate summary statistics
    print(f"Writing summary to {summary_path}...")
    
    total_queries = len(comparisons)
    both_success = sum(1 for c in comparisons if c['gt_success'] and c['qmeans_success'])
    gt_only_success = sum(1 for c in comparisons if c['gt_success'] and not c['qmeans_success'])
    qmeans_only_success = sum(1 for c in comparisons if not c['gt_success'] and c['qmeans_success'])
    both_fail = sum(1 for c in comparisons if not c['gt_success'] and not c['qmeans_success'])
    
    total_gt_keys = sum(c['gt_total_keys'] for c in comparisons)
    total_qmeans_keys = sum(c['qmeans_total_keys'] for c in comparisons)
    total_matched_keys = sum(len(c['matched_keys']) for c in comparisons)
    total_matched_values = sum(len(c['matched_values']) for c in comparisons)
    
    queries_with_key_match = sum(1 for c in comparisons if len(c['matched_keys']) > 0)
    queries_with_value_match = sum(1 for c in comparisons if len(c['matched_values']) > 0)
    queries_with_perfect_key_match = sum(1 for c in comparisons 
                                         if c['qmeans_total_keys'] > 0 and 
                                         len(c['qmeans_only_keys']) == 0)
    
    # Key coverage analysis
    all_gt_keys = defaultdict(int)
    all_qmeans_keys = defaultdict(int)
    matched_key_freq = defaultdict(int)
    
    for comp in comparisons:
        gt_data = gt_results.get(comp['query'], {})
        for attr in gt_data.get('attributes', []):
            norm_key = normalize_key(attr.get('attribute_key', ''))
            all_gt_keys[norm_key] += 1
        
        qmeans_data = qmeans_results.get(comp['query'], {})
        for key in qmeans_data.get('attributes', {}).keys():
            norm_key = normalize_key(key)
            all_qmeans_keys[norm_key] += 1
        
        for key in comp['matched_keys']:
            matched_key_freq[key] += 1
    
    with open(summary_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        writer.writerow(['GROUND TRUTH (CLAUDE OPUS) VS QMEANS - COMPARISON SUMMARY'])
        writer.writerow([])
        
        writer.writerow(['=== OVERVIEW ==='])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Queries', total_queries])
        writer.writerow(['Both Successful', both_success])
        writer.writerow(['GT Only Success', gt_only_success])
        writer.writerow(['QMeans Only Success', qmeans_only_success])
        writer.writerow(['Both Failed', both_fail])
        writer.writerow([])
        
        writer.writerow(['=== KEY ANALYSIS ==='])
        writer.writerow(['Total GT Keys (with synonyms)', total_gt_keys])
        writer.writerow(['Total QMeans Keys', total_qmeans_keys])
        writer.writerow(['Total Matched Keys', total_matched_keys])
        writer.writerow(['Queries with at least 1 key match', queries_with_key_match])
        writer.writerow(['Queries with perfect key coverage', queries_with_perfect_key_match])
        writer.writerow([])
        
        writer.writerow(['=== VALUE ANALYSIS ==='])
        writer.writerow(['Total Matched Values', total_matched_values])
        writer.writerow(['Queries with at least 1 value match', queries_with_value_match])
        writer.writerow([])
        
        writer.writerow(['=== TOP 20 GROUND TRUTH KEYS (by frequency) ==='])
        writer.writerow(['Key', 'Count', 'Also in QMeans?'])
        for key, count in sorted(all_gt_keys.items(), key=lambda x: -x[1])[:20]:
            in_qmeans = 'Yes' if key in all_qmeans_keys else 'No'
            writer.writerow([key, count, in_qmeans])
        writer.writerow([])
        
        writer.writerow(['=== TOP 20 QMEANS KEYS (by frequency) ==='])
        writer.writerow(['Key', 'Count', 'Also in GT?'])
        for key, count in sorted(all_qmeans_keys.items(), key=lambda x: -x[1])[:20]:
            in_gt = 'Yes' if key in all_gt_keys else 'No'
            writer.writerow([key, count, in_gt])
        writer.writerow([])
        
        writer.writerow(['=== TOP MATCHED KEYS ==='])
        writer.writerow(['Key', 'Match Count'])
        for key, count in sorted(matched_key_freq.items(), key=lambda x: -x[1])[:20]:
            writer.writerow([key, count])
        writer.writerow([])
        
        writer.writerow(['=== KEY MATCH RATE DISTRIBUTION ==='])
        rate_buckets = {'0%': 0, '1-25%': 0, '26-50%': 0, '51-75%': 0, '76-99%': 0, '100%': 0}
        for comp in comparisons:
            gt_unique_keys = len(set(normalize_key(a.get('attribute_key', '')) 
                                    for a in gt_results.get(comp['query'], {}).get('attributes', [])))
            if gt_unique_keys == 0:
                continue
            rate = len(comp['matched_keys']) / gt_unique_keys
            if rate == 0:
                rate_buckets['0%'] += 1
            elif rate < 0.25:
                rate_buckets['1-25%'] += 1
            elif rate < 0.50:
                rate_buckets['26-50%'] += 1
            elif rate < 0.75:
                rate_buckets['51-75%'] += 1
            elif rate < 1.0:
                rate_buckets['76-99%'] += 1
            else:
                rate_buckets['100%'] += 1
        
        writer.writerow(['Match Rate', 'Query Count'])
        for bucket, count in rate_buckets.items():
            writer.writerow([bucket, count])
    
    # Print summary to console
    print("\n" + "="*70)
    print("GROUND TRUTH (CLAUDE OPUS) VS QMEANS - SUMMARY")
    print("="*70)
    print(f"\nTotal Queries: {total_queries}")
    print(f"Both Successful: {both_success} ({both_success/total_queries:.1%})")
    print(f"GT Only Success: {gt_only_success}")
    print(f"QMeans Only Success: {qmeans_only_success}")
    print(f"Both Failed: {both_fail}")
    print(f"\nKey Analysis:")
    print(f"  Total GT Keys: {total_gt_keys}")
    print(f"  Total QMeans Keys: {total_qmeans_keys}")
    print(f"  Total Matched Keys: {total_matched_keys}")
    print(f"  Queries with key match: {queries_with_key_match} ({queries_with_key_match/total_queries:.1%})")
    print(f"\nValue Analysis:")
    print(f"  Total Matched Values: {total_matched_values}")
    print(f"  Queries with value match: {queries_with_value_match} ({queries_with_value_match/total_queries:.1%})")
    print(f"\nOutput files:")
    print(f"  Detailed: {output_path}")
    print(f"  Summary: {summary_path}")


if __name__ == '__main__':
    main()
