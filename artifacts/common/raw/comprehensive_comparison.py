#!/usr/bin/env python3
"""
Comprehensive GT Comparison Tool - Clean, Readable Output
Compares Ground Truth (Claude) with Gemma, Gemini, and QMeans
Proper normalization: trim spaces, lowercase conversion
"""

import csv
import json
import os
from collections import defaultdict, OrderedDict

def normalize_key(key):
    """Normalize key: lowercase, trim spaces, replace underscores/hyphens with spaces."""
    if key is None:
        return ''
    return ' '.join(str(key).lower().strip().replace('_', ' ').replace('-', ' ').split())

def normalize_value(value):
    """Normalize value: lowercase, trim spaces."""
    if value is None:
        return ''
    return ' '.join(str(value).lower().strip().split())

def load_csv_results(filepath, has_json=True):
    """Load results from CSV file."""
    results = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = row['query']
            attrs = []
            json_col = 'attributes_json' if 'attributes_json' in row else None
            if json_col and row[json_col]:
                try:
                    data = json.loads(row[json_col])
                    attrs = data.get('attributes', [])
                except:
                    pass
            results[query] = {
                'success': row.get('success', 'True') == 'True',
                'attributes': attrs,
                'unique_values': int(row.get('unique_value_count', 0) or 0),
                'total_keys': int(row.get('total_key_count', 0) or 0)
            }
    return results

def load_qmeans_json(filepath):
    """Load QMeans results from JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = {}
    for item in data:
        query = item['query']
        # Convert QMeans format to standard format
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
            'attributes': attrs,
            'unique_values': len(set(str(v).lower().strip() for v in item.get('attributes', {}).values())),
            'total_keys': len(item.get('attributes', {}))
        }
    return results

def group_attrs_by_value_priority(attrs):
    """Group attributes by attribute_priority (value groups), then by key_priority within."""
    # Group by attribute_priority (each attr_priority = one value with multiple key synonyms)
    value_groups = defaultdict(list)
    for attr in attrs:
        attr_prio = attr.get('attribute_priority', 1)
        value_groups[attr_prio].append(attr)
    
    # Sort each group by key_priority
    result = OrderedDict()
    for attr_prio in sorted(value_groups.keys()):
        group = sorted(value_groups[attr_prio], key=lambda x: x.get('key_priority', 1))
        if group:
            # Get the value (should be same for all in group)
            value = group[0].get('value', '')
            keys = [a.get('attribute_key', '') for a in group]
            result[attr_prio] = {'value': value, 'keys': keys, 'attrs': group}
    
    return result

def format_value_keys(attrs):
    """Format as 'value - key1 | key2 |||| value2 - key3 | key4'"""
    grouped = group_attrs_by_value_priority(attrs)
    parts = []
    for attr_prio, data in grouped.items():
        value = data['value']
        keys = data['keys']
        keys_str = ' | '.join(keys)
        parts.append(f"{value} - {keys_str}")
    return ' |||| '.join(parts)

def compare_query(gt_data, model_data, query):
    """Compare GT with model data for a single query."""
    result = {
        'query': query,
        'gt_success': gt_data.get('success', False) if gt_data else False,
        'model_success': model_data.get('success', False) if model_data else False,
    }
    
    if not gt_data or not model_data:
        result.update({
            'key_match_count': 0,
            'value_match_count': 0,
            'key_priority_match_count': 0,
            'attr_priority_match_count': 0,
            'gt_formatted': format_value_keys(gt_data.get('attributes', [])) if gt_data else '',
            'model_formatted': format_value_keys(model_data.get('attributes', [])) if model_data else '',
            'matched_keys': [],
            'matched_values': [],
            'gt_only_keys': [],
            'model_only_keys': [],
            'match_details': [],
            'gt_unique_keys': 0,
            'model_unique_keys': 0,
            'gt_unique_values': 0,
            'model_unique_values': 0
        })
        return result
    
    gt_attrs = gt_data.get('attributes', [])
    model_attrs = model_data.get('attributes', [])
    
    # Build normalized lookup structures
    # GT: normalized_key -> list of (value, key_prio, attr_prio, original_key)
    gt_keys = defaultdict(list)
    gt_values = defaultdict(list)
    gt_key_value_pairs = set()
    
    for attr in gt_attrs:
        key = attr.get('attribute_key', '')
        value = attr.get('value', '')
        key_prio = attr.get('key_priority', 0)
        attr_prio = attr.get('attribute_priority', 0)
        
        norm_key = normalize_key(key)
        norm_value = normalize_value(value)
        
        gt_keys[norm_key].append({
            'value': value, 'norm_value': norm_value,
            'key_priority': key_prio, 'attribute_priority': attr_prio,
            'original_key': key
        })
        gt_values[norm_value].append({
            'key': key, 'norm_key': norm_key,
            'key_priority': key_prio, 'attribute_priority': attr_prio
        })
        gt_key_value_pairs.add((norm_key, norm_value))
    
    # Model: same structure
    model_keys = defaultdict(list)
    model_values = defaultdict(list)
    model_key_value_pairs = set()
    
    for attr in model_attrs:
        key = attr.get('attribute_key', '')
        value = attr.get('value', '')
        key_prio = attr.get('key_priority', 0)
        attr_prio = attr.get('attribute_priority', 0)
        
        norm_key = normalize_key(key)
        norm_value = normalize_value(value)
        
        model_keys[norm_key].append({
            'value': value, 'norm_value': norm_value,
            'key_priority': key_prio, 'attribute_priority': attr_prio,
            'original_key': key
        })
        model_values[norm_value].append({
            'key': key, 'norm_key': norm_key,
            'key_priority': key_prio, 'attribute_priority': attr_prio
        })
        model_key_value_pairs.add((norm_key, norm_value))
    
    # Calculate matches
    matched_keys = set(gt_keys.keys()) & set(model_keys.keys())
    matched_values = set(gt_values.keys()) & set(model_values.keys())
    gt_only_keys = set(gt_keys.keys()) - set(model_keys.keys())
    model_only_keys = set(model_keys.keys()) - set(gt_keys.keys())
    
    # Count priority matches
    key_priority_matches = 0
    attr_priority_matches = 0
    match_details = []
    
    for norm_key in matched_keys:
        gt_entries = gt_keys[norm_key]
        model_entries = model_keys[norm_key]
        
        for gt_e in gt_entries:
            for model_e in model_entries:
                value_match = gt_e['norm_value'] == model_e['norm_value']
                key_prio_match = gt_e['key_priority'] == model_e['key_priority']
                attr_prio_match = gt_e['attribute_priority'] == model_e['attribute_priority']
                
                if value_match:
                    if key_prio_match:
                        key_priority_matches += 1
                    if attr_prio_match:
                        attr_priority_matches += 1
                    
                    match_details.append({
                        'key': norm_key,
                        'value': gt_e['norm_value'],
                        'gt_key_prio': gt_e['key_priority'],
                        'gt_attr_prio': gt_e['attribute_priority'],
                        'model_key_prio': model_e['key_priority'],
                        'model_attr_prio': model_e['attribute_priority'],
                        'key_prio_match': key_prio_match,
                        'attr_prio_match': attr_prio_match
                    })
    
    result.update({
        'key_match_count': len(matched_keys),
        'value_match_count': len(matched_values),
        'key_priority_match_count': key_priority_matches,
        'attr_priority_match_count': attr_priority_matches,
        'gt_formatted': format_value_keys(gt_attrs),
        'model_formatted': format_value_keys(model_attrs),
        'matched_keys': list(matched_keys),
        'matched_values': list(matched_values),
        'gt_only_keys': list(gt_only_keys),
        'model_only_keys': list(model_only_keys),
        'match_details': match_details,
        'gt_unique_keys': len(set(gt_keys.keys())),
        'model_unique_keys': len(set(model_keys.keys())),
        'gt_unique_values': len(set(gt_values.keys())),
        'model_unique_values': len(set(model_values.keys()))
    })
    
    return result


def generate_comparison_csv(comparisons, output_path, model_name):
    """Generate clean, readable comparison CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Query',
            'Key Match Count',
            'Value Match Count', 
            'Key Priority Match',
            'Attr Priority Match',
            'GT Unique Keys',
            f'{model_name} Unique Keys',
            'GT Unique Values',
            f'{model_name} Unique Values',
            'Key Match %',
            'Value Match %',
            'GT: Value - Keys (by priority)',
            f'{model_name}: Value - Keys (by priority)',
            'Matched Keys',
            'Matched Values',
            'GT Only Keys',
            f'{model_name} Only Keys'
        ])
        
        for comp in comparisons:
            key_match_pct = f"{comp['key_match_count']/comp['gt_unique_keys']*100:.1f}%" if comp['gt_unique_keys'] > 0 else "0%"
            value_match_pct = f"{comp['value_match_count']/comp['gt_unique_values']*100:.1f}%" if comp['gt_unique_values'] > 0 else "0%"
            
            writer.writerow([
                comp['query'],
                comp['key_match_count'],
                comp['value_match_count'],
                comp['key_priority_match_count'],
                comp['attr_priority_match_count'],
                comp['gt_unique_keys'],
                comp['model_unique_keys'],
                comp['gt_unique_values'],
                comp['model_unique_values'],
                key_match_pct,
                value_match_pct,
                comp['gt_formatted'],
                comp['model_formatted'],
                ' | '.join(sorted(comp['matched_keys'])),
                ' | '.join(sorted(comp['matched_values'])),
                ' | '.join(sorted(comp['gt_only_keys'])),
                ' | '.join(sorted(comp['model_only_keys']))
            ])


def generate_summary_csv(comparisons, output_path, model_name, gt_results, model_results):
    """Generate clean summary/analysis CSV."""
    
    total = len(comparisons)
    both_success = sum(1 for c in comparisons if c['gt_success'] and c['model_success'])
    
    total_key_matches = sum(c['key_match_count'] for c in comparisons)
    total_value_matches = sum(c['value_match_count'] for c in comparisons)
    total_key_prio_matches = sum(c['key_priority_match_count'] for c in comparisons)
    total_attr_prio_matches = sum(c['attr_priority_match_count'] for c in comparisons)
    
    queries_with_key_match = sum(1 for c in comparisons if c['key_match_count'] > 0)
    queries_with_value_match = sum(1 for c in comparisons if c['value_match_count'] > 0)
    queries_with_full_key_match = sum(1 for c in comparisons if c['key_match_count'] == c['gt_unique_keys'] and c['gt_unique_keys'] > 0)
    queries_with_full_value_match = sum(1 for c in comparisons if c['value_match_count'] == c['gt_unique_values'] and c['gt_unique_values'] > 0)
    
    # Key frequency analysis
    all_gt_keys = defaultdict(int)
    all_model_keys = defaultdict(int)
    matched_key_freq = defaultdict(int)
    
    for comp in comparisons:
        gt_data = gt_results.get(comp['query'], {})
        for attr in gt_data.get('attributes', []):
            norm_key = normalize_key(attr.get('attribute_key', ''))
            all_gt_keys[norm_key] += 1
        
        model_data = model_results.get(comp['query'], {})
        for attr in model_data.get('attributes', []):
            norm_key = normalize_key(attr.get('attribute_key', ''))
            all_model_keys[norm_key] += 1
        
        for key in comp['matched_keys']:
            matched_key_freq[key] += 1
    
    # Key match rate distribution
    rate_buckets = {'0%': 0, '1-25%': 0, '26-50%': 0, '51-75%': 0, '76-99%': 0, '100%': 0}
    for comp in comparisons:
        if comp['gt_unique_keys'] == 0:
            continue
        rate = comp['key_match_count'] / comp['gt_unique_keys']
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
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        writer.writerow([f'GROUND TRUTH vs {model_name.upper()} - ANALYSIS SUMMARY'])
        writer.writerow(['=' * 60])
        writer.writerow([])
        
        writer.writerow(['OVERVIEW'])
        writer.writerow(['Metric', 'Count', 'Percentage'])
        writer.writerow(['Total Queries', total, '100%'])
        writer.writerow(['Both Successful', both_success, f'{both_success/total*100:.1f}%'])
        writer.writerow([])
        
        writer.writerow(['KEY MATCHING'])
        writer.writerow(['Metric', 'Count', 'Percentage'])
        writer.writerow(['Total Key Matches', total_key_matches, '-'])
        writer.writerow(['Queries with ≥1 Key Match', queries_with_key_match, f'{queries_with_key_match/total*100:.1f}%'])
        writer.writerow(['Queries with 100% Key Match', queries_with_full_key_match, f'{queries_with_full_key_match/total*100:.1f}%'])
        writer.writerow([])
        
        writer.writerow(['VALUE MATCHING'])
        writer.writerow(['Metric', 'Count', 'Percentage'])
        writer.writerow(['Total Value Matches', total_value_matches, '-'])
        writer.writerow(['Queries with ≥1 Value Match', queries_with_value_match, f'{queries_with_value_match/total*100:.1f}%'])
        writer.writerow(['Queries with 100% Value Match', queries_with_full_value_match, f'{queries_with_full_value_match/total*100:.1f}%'])
        writer.writerow([])
        
        writer.writerow(['PRIORITY ALIGNMENT'])
        writer.writerow(['Metric', 'Count'])
        writer.writerow(['Key Priority Matches', total_key_prio_matches])
        writer.writerow(['Attribute Priority Matches', total_attr_prio_matches])
        writer.writerow([])
        
        writer.writerow(['KEY MATCH DISTRIBUTION'])
        writer.writerow(['Match Rate', 'Query Count', 'Percentage'])
        for bucket, count in rate_buckets.items():
            writer.writerow([bucket, count, f'{count/total*100:.1f}%'])
        writer.writerow([])
        
        writer.writerow(['TOP 20 MATCHED KEYS'])
        writer.writerow(['Key', 'Match Count', 'GT Frequency', f'{model_name} Frequency', 'Match Rate'])
        for key, count in sorted(matched_key_freq.items(), key=lambda x: -x[1])[:20]:
            gt_freq = all_gt_keys.get(key, 0)
            model_freq = all_model_keys.get(key, 0)
            match_rate = f'{count/gt_freq*100:.1f}%' if gt_freq > 0 else '0%'
            writer.writerow([key, count, gt_freq, model_freq, match_rate])
        writer.writerow([])
        
        writer.writerow(['GT KEYS NOT IN MODEL (Top 15)'])
        writer.writerow(['Key', 'GT Frequency'])
        gt_only = [(k, v) for k, v in all_gt_keys.items() if k not in all_model_keys]
        for key, count in sorted(gt_only, key=lambda x: -x[1])[:15]:
            writer.writerow([key, count])
        writer.writerow([])
        
        writer.writerow([f'{model_name.upper()} KEYS NOT IN GT (Top 15)'])
        writer.writerow(['Key', f'{model_name} Frequency'])
        model_only = [(k, v) for k, v in all_model_keys.items() if k not in all_gt_keys]
        for key, count in sorted(model_only, key=lambda x: -x[1])[:15]:
            writer.writerow([key, count])


def main():
    print("="*70)
    print("COMPREHENSIVE GT COMPARISON - CLEAN OUTPUT")
    print("="*70)
    
    # Load Ground Truth
    print("\nLoading Ground Truth (Claude Opus)...")
    gt_results = load_csv_results('claude_1000_results.csv')
    print(f"  Loaded {len(gt_results)} queries")
    
    # Load Gemma V4
    print("Loading Gemma V4...")
    gemma_results = load_csv_results('../present/gemma_v4_1000_results.csv')
    print(f"  Loaded {len(gemma_results)} queries")
    
    # Load Gemini
    print("Loading Gemini...")
    gemini_results = load_csv_results('gemini_final_results.csv')
    print(f"  Loaded {len(gemini_results)} queries")
    
    # Load QMeans
    print("Loading QMeans...")
    qmeans_results = load_qmeans_json('qmeans_results.json')
    print(f"  Loaded {len(qmeans_results)} queries")
    
    # Compare GT vs Gemma
    print("\n" + "-"*50)
    print("Comparing GT vs Gemma V4...")
    gemma_comparisons = []
    for query in sorted(gt_results.keys()):
        gt_data = gt_results.get(query)
        model_data = gemma_results.get(query)
        comp = compare_query(gt_data, model_data, query)
        gemma_comparisons.append(comp)
    
    generate_comparison_csv(gemma_comparisons, '../present/gt_vs_gemma_clean.csv', 'Gemma')
    generate_summary_csv(gemma_comparisons, '../present/gt_vs_gemma_analysis.csv', 'Gemma', gt_results, gemma_results)
    
    gemma_key_match = sum(1 for c in gemma_comparisons if c['key_match_count'] > 0)
    gemma_value_match = sum(1 for c in gemma_comparisons if c['value_match_count'] > 0)
    print(f"  Key Match: {gemma_key_match}/{len(gemma_comparisons)} ({gemma_key_match/len(gemma_comparisons)*100:.1f}%)")
    print(f"  Value Match: {gemma_value_match}/{len(gemma_comparisons)} ({gemma_value_match/len(gemma_comparisons)*100:.1f}%)")
    
    # Compare GT vs Gemini
    print("\n" + "-"*50)
    print("Comparing GT vs Gemini...")
    gemini_comparisons = []
    for query in sorted(gt_results.keys()):
        gt_data = gt_results.get(query)
        model_data = gemini_results.get(query)
        comp = compare_query(gt_data, model_data, query)
        gemini_comparisons.append(comp)
    
    generate_comparison_csv(gemini_comparisons, '../present/gt_vs_gemini_clean.csv', 'Gemini')
    generate_summary_csv(gemini_comparisons, '../present/gt_vs_gemini_analysis.csv', 'Gemini', gt_results, gemini_results)
    
    gemini_key_match = sum(1 for c in gemini_comparisons if c['key_match_count'] > 0)
    gemini_value_match = sum(1 for c in gemini_comparisons if c['value_match_count'] > 0)
    print(f"  Key Match: {gemini_key_match}/{len(gemini_comparisons)} ({gemini_key_match/len(gemini_comparisons)*100:.1f}%)")
    print(f"  Value Match: {gemini_value_match}/{len(gemini_comparisons)} ({gemini_value_match/len(gemini_comparisons)*100:.1f}%)")
    
    # Compare GT vs QMeans
    print("\n" + "-"*50)
    print("Comparing GT vs QMeans...")
    qmeans_comparisons = []
    for query in sorted(gt_results.keys()):
        gt_data = gt_results.get(query)
        model_data = qmeans_results.get(query)
        comp = compare_query(gt_data, model_data, query)
        qmeans_comparisons.append(comp)
    
    generate_comparison_csv(qmeans_comparisons, '../present/gt_vs_qmeans_clean.csv', 'QMeans')
    generate_summary_csv(qmeans_comparisons, '../present/gt_vs_qmeans_analysis.csv', 'QMeans', gt_results, qmeans_results)
    
    qmeans_key_match = sum(1 for c in qmeans_comparisons if c['key_match_count'] > 0)
    qmeans_value_match = sum(1 for c in qmeans_comparisons if c['value_match_count'] > 0)
    print(f"  Key Match: {qmeans_key_match}/{len(qmeans_comparisons)} ({qmeans_key_match/len(qmeans_comparisons)*100:.1f}%)")
    print(f"  Value Match: {qmeans_value_match}/{len(qmeans_comparisons)} ({qmeans_value_match/len(qmeans_comparisons)*100:.1f}%)")
    
    # Final Summary
    print("\n" + "="*70)
    print("FINAL COMPARISON SUMMARY")
    print("="*70)
    print(f"\n{'Model':<12} | {'Key Match':<15} | {'Value Match':<15} | {'100% Key':<12} | {'100% Value':<12}")
    print("-"*70)
    
    gemma_full_key = sum(1 for c in gemma_comparisons if c['key_match_count'] == c['gt_unique_keys'] and c['gt_unique_keys'] > 0)
    gemma_full_val = sum(1 for c in gemma_comparisons if c['value_match_count'] == c['gt_unique_values'] and c['gt_unique_values'] > 0)
    
    gemini_full_key = sum(1 for c in gemini_comparisons if c['key_match_count'] == c['gt_unique_keys'] and c['gt_unique_keys'] > 0)
    gemini_full_val = sum(1 for c in gemini_comparisons if c['value_match_count'] == c['gt_unique_values'] and c['gt_unique_values'] > 0)
    
    qmeans_full_key = sum(1 for c in qmeans_comparisons if c['key_match_count'] == c['gt_unique_keys'] and c['gt_unique_keys'] > 0)
    qmeans_full_val = sum(1 for c in qmeans_comparisons if c['value_match_count'] == c['gt_unique_values'] and c['gt_unique_values'] > 0)
    
    total = len(gemma_comparisons)
    
    print(f"{'Gemma':<12} | {gemma_key_match:>4} ({gemma_key_match/total*100:>5.1f}%)   | {gemma_value_match:>4} ({gemma_value_match/total*100:>5.1f}%)   | {gemma_full_key:>4} ({gemma_full_key/total*100:>4.1f}%) | {gemma_full_val:>4} ({gemma_full_val/total*100:>4.1f}%)")
    print(f"{'Gemini':<12} | {gemini_key_match:>4} ({gemini_key_match/total*100:>5.1f}%)   | {gemini_value_match:>4} ({gemini_value_match/total*100:>5.1f}%)   | {gemini_full_key:>4} ({gemini_full_key/total*100:>4.1f}%) | {gemini_full_val:>4} ({gemini_full_val/total*100:>4.1f}%)")
    print(f"{'QMeans':<12} | {qmeans_key_match:>4} ({qmeans_key_match/total*100:>5.1f}%)   | {qmeans_value_match:>4} ({qmeans_value_match/total*100:>5.1f}%)   | {qmeans_full_key:>4} ({qmeans_full_key/total*100:>4.1f}%) | {qmeans_full_val:>4} ({qmeans_full_val/total*100:>4.1f}%)")
    
    print("\n" + "="*70)
    print("OUTPUT FILES GENERATED:")
    print("="*70)
    print("  ../present/gt_vs_gemma_clean.csv     - Detailed comparison")
    print("  ../present/gt_vs_gemma_analysis.csv  - Summary statistics")
    print("  ../present/gt_vs_gemini_clean.csv    - Detailed comparison")
    print("  ../present/gt_vs_gemini_analysis.csv - Summary statistics")
    print("  ../present/gt_vs_qmeans_clean.csv    - Detailed comparison")
    print("  ../present/gt_vs_qmeans_analysis.csv - Summary statistics")


if __name__ == '__main__':
    main()
