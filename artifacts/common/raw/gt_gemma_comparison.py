#!/usr/bin/env python3
"""
Ground Truth (Claude Opus) vs Gemma V4 Comparison Analysis
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

def load_gemma_results(filepath):
    """Load Gemma V4 results."""
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

def normalize_key(key):
    """Normalize key for comparison."""
    return key.lower().strip().replace('_', ' ').replace('-', ' ')

def normalize_value(value):
    """Normalize value for comparison."""
    if value is None:
        return ''
    return str(value).lower().strip()

def compare_query(gt_data, gemma_data, query):
    """
    Compare Ground Truth (Claude) vs Gemma V4 for a single query.
    Returns detailed comparison metrics with priorities.
    """
    result = {
        'query': query,
        'gt_success': gt_data.get('success', False) if gt_data else False,
        'gemma_success': gemma_data.get('success', False) if gemma_data else False,
        'gt_total_keys': gt_data.get('total_keys', 0) if gt_data else 0,
        'gt_unique_values': gt_data.get('unique_values', 0) if gt_data else 0,
        'gemma_total_keys': gemma_data.get('total_keys', 0) if gemma_data else 0,
        'gemma_unique_values': gemma_data.get('unique_values', 0) if gemma_data else 0,
        'matched_keys': [],
        'matched_values': [],
        'gt_only_keys': [],
        'gemma_only_keys': [],
        'key_match_details': [],
        'value_match_details': [],
        'priority_alignment': []
    }
    
    if not gt_data or not gemma_data:
        return result
    
    gt_attrs = gt_data.get('attributes', [])
    gemma_attrs = gemma_data.get('attributes', [])
    
    # Create lookup structures for GT
    gt_keys_normalized = {}  # normalized_key -> list of {original_key, value, key_priority, attr_priority}
    gt_values_normalized = {}  # normalized_value -> list of {original_value, key, key_priority, attr_priority}
    
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
            'norm_value': norm_value,
            'key_priority': key_priority,
            'attribute_priority': attr_priority
        })
        
        if norm_value not in gt_values_normalized:
            gt_values_normalized[norm_value] = []
        gt_values_normalized[norm_value].append({
            'original_value': value,
            'key': key,
            'norm_key': norm_key,
            'key_priority': key_priority,
            'attribute_priority': attr_priority
        })
    
    # Create lookup for Gemma
    gemma_keys_normalized = {}  # normalized_key -> list of entries
    gemma_values_normalized = {}  # normalized_value -> list of entries
    
    for attr in gemma_attrs:
        key = attr.get('attribute_key', '')
        value = attr.get('value', '')
        key_priority = attr.get('key_priority', 0)
        attr_priority = attr.get('attribute_priority', 0)
        
        norm_key = normalize_key(key)
        norm_value = normalize_value(value)
        
        if norm_key not in gemma_keys_normalized:
            gemma_keys_normalized[norm_key] = []
        gemma_keys_normalized[norm_key].append({
            'original_key': key,
            'value': value,
            'norm_value': norm_value,
            'key_priority': key_priority,
            'attribute_priority': attr_priority
        })
        
        if norm_value not in gemma_values_normalized:
            gemma_values_normalized[norm_value] = []
        gemma_values_normalized[norm_value].append({
            'original_value': value,
            'key': key,
            'norm_key': norm_key,
            'key_priority': key_priority,
            'attribute_priority': attr_priority
        })
    
    # Find matched keys
    matched_keys = set(gt_keys_normalized.keys()) & set(gemma_keys_normalized.keys())
    gt_only = set(gt_keys_normalized.keys()) - set(gemma_keys_normalized.keys())
    gemma_only = set(gemma_keys_normalized.keys()) - set(gt_keys_normalized.keys())
    
    # Find matched values
    matched_values = set(gt_values_normalized.keys()) & set(gemma_values_normalized.keys())
    
    result['matched_keys'] = list(matched_keys)
    result['matched_values'] = list(matched_values)
    result['gt_only_keys'] = list(gt_only)
    result['gemma_only_keys'] = list(gemma_only)
    
    # Detailed key match info with priorities
    key_match_details = []
    for norm_key in matched_keys:
        gt_entries = gt_keys_normalized[norm_key]
        gemma_entries = gemma_keys_normalized[norm_key]
        
        # Find matches by value within this key
        for gt_entry in gt_entries:
            for gemma_entry in gemma_entries:
                value_match = gt_entry['norm_value'] == gemma_entry['norm_value']
                
                key_match_details.append({
                    'normalized_key': norm_key,
                    'gt_key': gt_entry['original_key'],
                    'gt_value': gt_entry['value'],
                    'gt_key_priority': gt_entry['key_priority'],
                    'gt_attr_priority': gt_entry['attribute_priority'],
                    'gemma_key': gemma_entry['original_key'],
                    'gemma_value': gemma_entry['value'],
                    'gemma_key_priority': gemma_entry['key_priority'],
                    'gemma_attr_priority': gemma_entry['attribute_priority'],
                    'value_also_matches': value_match,
                    'key_priority_match': gt_entry['key_priority'] == gemma_entry['key_priority'],
                    'attr_priority_match': gt_entry['attribute_priority'] == gemma_entry['attribute_priority']
                })
    
    result['key_match_details'] = key_match_details
    
    # Value match details (values that match)
    value_match_details = []
    for norm_val in matched_values:
        gt_entries = gt_values_normalized[norm_val]
        gemma_entries = gemma_values_normalized[norm_val]
        
        # Find if they're under the same key
        gt_keys = set(e['norm_key'] for e in gt_entries)
        gemma_keys = set(e['norm_key'] for e in gemma_entries)
        same_key = bool(gt_keys & gemma_keys)
        
        value_match_details.append({
            'value': norm_val,
            'gt_original': gt_entries[0]['original_value'] if gt_entries else '',
            'gemma_original': gemma_entries[0]['original_value'] if gemma_entries else '',
            'gt_keys': [{'key': e['key'], 'key_priority': e['key_priority'], 'attr_priority': e['attribute_priority']} for e in gt_entries],
            'gemma_keys': [{'key': e['key'], 'key_priority': e['key_priority'], 'attr_priority': e['attribute_priority']} for e in gemma_entries],
            'under_same_key': same_key
        })
    
    result['value_match_details'] = value_match_details
    
    # Analyze priority alignment
    # For matched key+value pairs, check if priorities align
    perfect_matches = []
    partial_matches = []
    
    for detail in key_match_details:
        if detail['value_also_matches']:
            if detail['key_priority_match'] and detail['attr_priority_match']:
                perfect_matches.append({
                    'key': detail['normalized_key'],
                    'value': detail['gt_value'],
                    'priorities': f"key_prio={detail['gt_key_priority']}, attr_prio={detail['gt_attr_priority']}"
                })
            else:
                partial_matches.append({
                    'key': detail['normalized_key'],
                    'value': detail['gt_value'],
                    'gt_priorities': f"key_prio={detail['gt_key_priority']}, attr_prio={detail['gt_attr_priority']}",
                    'gemma_priorities': f"key_prio={detail['gemma_key_priority']}, attr_prio={detail['gemma_attr_priority']}"
                })
    
    result['priority_alignment'] = {
        'perfect_matches': perfect_matches,
        'partial_matches': partial_matches
    }
    
    return result


def main():
    # Paths
    claude_path = 'claude_1000_results.csv'
    gemma_path = '../present/gemma_v4_1000_results.csv'
    output_path = '../present/gt_vs_gemma_detailed_comparison.csv'
    summary_path = '../present/gt_vs_gemma_summary.csv'
    
    print("Loading Ground Truth (Claude Opus) results...")
    gt_results = load_claude_results(claude_path)
    print(f"  Loaded {len(gt_results)} queries")
    
    print("Loading Gemma V4 results...")
    gemma_results = load_gemma_results(gemma_path)
    print(f"  Loaded {len(gemma_results)} queries")
    
    # Compare all queries
    print("\nComparing queries...")
    comparisons = []
    
    # Use GT queries as the base
    all_queries = set(gt_results.keys()) | set(gemma_results.keys())
    
    for query in sorted(all_queries):
        gt_data = gt_results.get(query)
        gemma_data = gemma_results.get(query)
        
        comparison = compare_query(gt_data, gemma_data, query)
        comparisons.append(comparison)
    
    # Write detailed CSV
    print(f"\nWriting detailed comparison to {output_path}...")
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'query',
            'gt_success',
            'gemma_success',
            'gt_total_keys',
            'gt_unique_values',
            'gemma_total_keys',
            'gemma_unique_values',
            'matched_key_count',
            'matched_value_count',
            'gt_only_key_count',
            'gemma_only_key_count',
            'key_match_rate',
            'value_match_rate',
            'perfect_match_count',
            'partial_match_count',
            'matched_keys',
            'gt_only_keys',
            'gemma_only_keys',
            'matched_values',
            'key_match_details_json',
            'value_match_details_json',
            'priority_alignment_json'
        ])
        
        for comp in comparisons:
            # Calculate match rates
            gt_unique_keys = len(set(normalize_key(a.get('attribute_key', '')) 
                                    for a in gt_results.get(comp['query'], {}).get('attributes', [])))
            gemma_unique_keys = len(set(normalize_key(a.get('attribute_key', '')) 
                                       for a in gemma_results.get(comp['query'], {}).get('attributes', [])))
            
            key_match_rate = 0
            if gt_unique_keys > 0:
                key_match_rate = len(comp['matched_keys']) / gt_unique_keys
            
            gt_unique_vals = comp['gt_unique_values']
            value_match_rate = 0
            if gt_unique_vals > 0:
                value_match_rate = len(comp['matched_values']) / gt_unique_vals
            
            perfect_count = len(comp['priority_alignment'].get('perfect_matches', []))
            partial_count = len(comp['priority_alignment'].get('partial_matches', []))
            
            writer.writerow([
                comp['query'],
                comp['gt_success'],
                comp['gemma_success'],
                comp['gt_total_keys'],
                comp['gt_unique_values'],
                comp['gemma_total_keys'],
                comp['gemma_unique_values'],
                len(comp['matched_keys']),
                len(comp['matched_values']),
                len(comp['gt_only_keys']),
                len(comp['gemma_only_keys']),
                f"{key_match_rate:.2%}",
                f"{value_match_rate:.2%}",
                perfect_count,
                partial_count,
                '; '.join(comp['matched_keys'][:20]),  # Limit for readability
                '; '.join(comp['gt_only_keys'][:20]),
                '; '.join(comp['gemma_only_keys'][:20]),
                '; '.join(comp['matched_values'][:20]),
                json.dumps(comp['key_match_details']),
                json.dumps(comp['value_match_details']),
                json.dumps(comp['priority_alignment'])
            ])
    
    # Calculate summary statistics
    print(f"Writing summary to {summary_path}...")
    
    total_queries = len(comparisons)
    both_success = sum(1 for c in comparisons if c['gt_success'] and c['gemma_success'])
    gt_only_success = sum(1 for c in comparisons if c['gt_success'] and not c['gemma_success'])
    gemma_only_success = sum(1 for c in comparisons if not c['gt_success'] and c['gemma_success'])
    both_fail = sum(1 for c in comparisons if not c['gt_success'] and not c['gemma_success'])
    
    total_gt_keys = sum(c['gt_total_keys'] for c in comparisons)
    total_gemma_keys = sum(c['gemma_total_keys'] for c in comparisons)
    total_matched_keys = sum(len(c['matched_keys']) for c in comparisons)
    total_matched_values = sum(len(c['matched_values']) for c in comparisons)
    
    queries_with_key_match = sum(1 for c in comparisons if len(c['matched_keys']) > 0)
    queries_with_value_match = sum(1 for c in comparisons if len(c['matched_values']) > 0)
    queries_with_perfect_key_match = sum(1 for c in comparisons 
                                         if c['gemma_total_keys'] > 0 and 
                                         len(c['gemma_only_keys']) == 0 and
                                         len(c['gt_only_keys']) == 0)
    
    # Priority alignment stats
    total_perfect_matches = sum(len(c['priority_alignment'].get('perfect_matches', [])) for c in comparisons)
    total_partial_matches = sum(len(c['priority_alignment'].get('partial_matches', [])) for c in comparisons)
    queries_with_perfect_match = sum(1 for c in comparisons if len(c['priority_alignment'].get('perfect_matches', [])) > 0)
    
    # Key coverage analysis
    all_gt_keys = defaultdict(int)
    all_gemma_keys = defaultdict(int)
    matched_key_freq = defaultdict(int)
    
    for comp in comparisons:
        gt_data = gt_results.get(comp['query'], {})
        for attr in gt_data.get('attributes', []):
            norm_key = normalize_key(attr.get('attribute_key', ''))
            all_gt_keys[norm_key] += 1
        
        gemma_data = gemma_results.get(comp['query'], {})
        for attr in gemma_data.get('attributes', []):
            norm_key = normalize_key(attr.get('attribute_key', ''))
            all_gemma_keys[norm_key] += 1
        
        for key in comp['matched_keys']:
            matched_key_freq[key] += 1
    
    with open(summary_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        writer.writerow(['GROUND TRUTH (CLAUDE OPUS) VS GEMMA V4 - COMPARISON SUMMARY'])
        writer.writerow([])
        
        writer.writerow(['=== OVERVIEW ==='])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Queries', total_queries])
        writer.writerow(['Both Successful', both_success, f'{both_success/total_queries:.1%}'])
        writer.writerow(['GT Only Success', gt_only_success])
        writer.writerow(['Gemma Only Success', gemma_only_success])
        writer.writerow(['Both Failed', both_fail])
        writer.writerow([])
        
        writer.writerow(['=== KEY MATCHING ANALYSIS ==='])
        writer.writerow(['Total GT Keys (with synonyms)', total_gt_keys])
        writer.writerow(['Total Gemma Keys (with synonyms)', total_gemma_keys])
        writer.writerow(['Total Matched Keys', total_matched_keys])
        writer.writerow(['Queries with at least 1 key match', queries_with_key_match, f'{queries_with_key_match/total_queries:.1%}'])
        writer.writerow(['Queries with perfect key coverage', queries_with_perfect_key_match])
        writer.writerow([])
        
        writer.writerow(['=== VALUE MATCHING ANALYSIS ==='])
        writer.writerow(['Total Matched Values', total_matched_values])
        writer.writerow(['Queries with at least 1 value match', queries_with_value_match, f'{queries_with_value_match/total_queries:.1%}'])
        writer.writerow([])
        
        writer.writerow(['=== PRIORITY ALIGNMENT ANALYSIS ==='])
        writer.writerow(['Total Perfect Matches (key + value + priorities)', total_perfect_matches])
        writer.writerow(['Total Partial Matches (key + value, different priorities)', total_partial_matches])
        writer.writerow(['Queries with at least 1 perfect match', queries_with_perfect_match, f'{queries_with_perfect_match/total_queries:.1%}'])
        writer.writerow([])
        
        writer.writerow(['=== TOP 30 GROUND TRUTH KEYS (by frequency) ==='])
        writer.writerow(['Key', 'Count', 'Also in Gemma?', 'Match Count'])
        for key, count in sorted(all_gt_keys.items(), key=lambda x: -x[1])[:30]:
            in_gemma = 'Yes' if key in all_gemma_keys else 'No'
            match_count = matched_key_freq.get(key, 0)
            writer.writerow([key, count, in_gemma, match_count])
        writer.writerow([])
        
        writer.writerow(['=== TOP 30 GEMMA KEYS (by frequency) ==='])
        writer.writerow(['Key', 'Count', 'Also in GT?', 'Match Count'])
        for key, count in sorted(all_gemma_keys.items(), key=lambda x: -x[1])[:30]:
            in_gt = 'Yes' if key in all_gt_keys else 'No'
            match_count = matched_key_freq.get(key, 0)
            writer.writerow([key, count, in_gt, match_count])
        writer.writerow([])
        
        writer.writerow(['=== TOP 30 MATCHED KEYS ==='])
        writer.writerow(['Key', 'Match Count', 'GT Frequency', 'Gemma Frequency'])
        for key, count in sorted(matched_key_freq.items(), key=lambda x: -x[1])[:30]:
            writer.writerow([key, count, all_gt_keys.get(key, 0), all_gemma_keys.get(key, 0)])
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
        
        writer.writerow(['Match Rate Range', 'Query Count', 'Percentage'])
        for bucket, count in rate_buckets.items():
            writer.writerow([bucket, count, f'{count/total_queries:.1%}'])
        writer.writerow([])
        
        writer.writerow(['=== VALUE MATCH RATE DISTRIBUTION ==='])
        value_rate_buckets = {'0%': 0, '1-25%': 0, '26-50%': 0, '51-75%': 0, '76-99%': 0, '100%': 0}
        for comp in comparisons:
            gt_unique_vals = comp['gt_unique_values']
            if gt_unique_vals == 0:
                continue
            rate = len(comp['matched_values']) / gt_unique_vals
            if rate == 0:
                value_rate_buckets['0%'] += 1
            elif rate < 0.25:
                value_rate_buckets['1-25%'] += 1
            elif rate < 0.50:
                value_rate_buckets['26-50%'] += 1
            elif rate < 0.75:
                value_rate_buckets['51-75%'] += 1
            elif rate < 1.0:
                value_rate_buckets['76-99%'] += 1
            else:
                value_rate_buckets['100%'] += 1
        
        writer.writerow(['Match Rate Range', 'Query Count', 'Percentage'])
        for bucket, count in value_rate_buckets.items():
            writer.writerow([bucket, count, f'{count/total_queries:.1%}'])
    
    # Print summary to console
    print("\n" + "="*70)
    print("GROUND TRUTH (CLAUDE OPUS) VS GEMMA V4 - SUMMARY")
    print("="*70)
    print(f"\nTotal Queries: {total_queries}")
    print(f"Both Successful: {both_success} ({both_success/total_queries:.1%})")
    print(f"GT Only Success: {gt_only_success}")
    print(f"Gemma Only Success: {gemma_only_success}")
    print(f"Both Failed: {both_fail}")
    print(f"\nKey Matching:")
    print(f"  Total GT Keys: {total_gt_keys}")
    print(f"  Total Gemma Keys: {total_gemma_keys}")
    print(f"  Total Matched Keys: {total_matched_keys}")
    print(f"  Queries with key match: {queries_with_key_match} ({queries_with_key_match/total_queries:.1%})")
    print(f"\nValue Matching:")
    print(f"  Total Matched Values: {total_matched_values}")
    print(f"  Queries with value match: {queries_with_value_match} ({queries_with_value_match/total_queries:.1%})")
    print(f"\nPriority Alignment:")
    print(f"  Perfect matches (key+value+priorities): {total_perfect_matches}")
    print(f"  Partial matches (key+value, diff priorities): {total_partial_matches}")
    print(f"  Queries with perfect match: {queries_with_perfect_match} ({queries_with_perfect_match/total_queries:.1%})")
    print(f"\nOutput files:")
    print(f"  Detailed: {output_path}")
    print(f"  Summary: {summary_path}")


if __name__ == '__main__':
    main()
