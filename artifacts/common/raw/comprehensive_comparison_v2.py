#!/usr/bin/env python3
"""
Comprehensive GT Comparison Tool - Fixed Version
Handles query mismatches between datasets properly
Shows model data even when queries don't match
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

def load_csv_results(filepath):
    """Load results from CSV file."""
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

def format_value_keys(attrs):
    """Format as 'value - key1 | key2 |||| value2 - key3 | key4'"""
    if not attrs:
        return ''
    
    # Group by attribute_priority
    value_groups = defaultdict(list)
    for attr in attrs:
        attr_prio = attr.get('attribute_priority', 1)
        value_groups[attr_prio].append(attr)
    
    parts = []
    for attr_prio in sorted(value_groups.keys()):
        group = sorted(value_groups[attr_prio], key=lambda x: x.get('key_priority', 1))
        if group:
            value = group[0].get('value', '')
            keys = [a.get('attribute_key', '') for a in group]
            keys_str = ' | '.join(keys)
            parts.append(f"{value} - {keys_str}")
    
    return ' |||| '.join(parts)

def get_unique_normalized_keys(attrs):
    """Get unique normalized keys from attributes."""
    return set(normalize_key(a.get('attribute_key', '')) for a in attrs if a.get('attribute_key'))

def get_unique_normalized_values(attrs):
    """Get unique normalized values from attributes."""
    return set(normalize_value(a.get('value', '')) for a in attrs if a.get('value'))

def compare_query(gt_data, model_data, query):
    """Compare GT with model data for a single query."""
    gt_attrs = gt_data.get('attributes', []) if gt_data else []
    model_attrs = model_data.get('attributes', []) if model_data else []
    
    gt_keys = get_unique_normalized_keys(gt_attrs)
    model_keys = get_unique_normalized_keys(model_attrs)
    gt_values = get_unique_normalized_values(gt_attrs)
    model_values = get_unique_normalized_values(model_attrs)
    
    matched_keys = gt_keys & model_keys
    matched_values = gt_values & model_values
    
    # Count priority matches
    key_priority_matches = 0
    attr_priority_matches = 0
    
    gt_lookup = defaultdict(list)
    for attr in gt_attrs:
        norm_key = normalize_key(attr.get('attribute_key', ''))
        gt_lookup[norm_key].append(attr)
    
    model_lookup = defaultdict(list)
    for attr in model_attrs:
        norm_key = normalize_key(attr.get('attribute_key', ''))
        model_lookup[norm_key].append(attr)
    
    for norm_key in matched_keys:
        for gt_attr in gt_lookup[norm_key]:
            gt_norm_val = normalize_value(gt_attr.get('value', ''))
            for model_attr in model_lookup[norm_key]:
                model_norm_val = normalize_value(model_attr.get('value', ''))
                if gt_norm_val == model_norm_val:
                    if gt_attr.get('key_priority') == model_attr.get('key_priority'):
                        key_priority_matches += 1
                    if gt_attr.get('attribute_priority') == model_attr.get('attribute_priority'):
                        attr_priority_matches += 1
    
    return {
        'query': query,
        'gt_in_source': gt_data is not None,
        'model_in_source': model_data is not None,
        'gt_success': gt_data.get('success', False) if gt_data else False,
        'model_success': model_data.get('success', False) if model_data else False,
        'key_match_count': len(matched_keys),
        'value_match_count': len(matched_values),
        'key_priority_match_count': key_priority_matches,
        'attr_priority_match_count': attr_priority_matches,
        'gt_unique_keys': len(gt_keys),
        'model_unique_keys': len(model_keys),
        'gt_unique_values': len(gt_values),
        'model_unique_values': len(model_values),
        'gt_formatted': format_value_keys(gt_attrs),
        'model_formatted': format_value_keys(model_attrs),
        'matched_keys': sorted(matched_keys),
        'matched_values': sorted(matched_values),
        'gt_only_keys': sorted(gt_keys - model_keys),
        'model_only_keys': sorted(model_keys - gt_keys)
    }


def generate_comparison_csv(comparisons, output_path, model_name):
    """Generate clean, readable comparison CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
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
            f'{model_name} Only Keys',
            'GT In Source',
            f'{model_name} In Source'
        ])
        
        for comp in comparisons:
            key_match_pct = f"{comp['key_match_count']/comp['gt_unique_keys']*100:.1f}%" if comp['gt_unique_keys'] > 0 else "N/A"
            value_match_pct = f"{comp['value_match_count']/comp['gt_unique_values']*100:.1f}%" if comp['gt_unique_values'] > 0 else "N/A"
            
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
                ' | '.join(comp['matched_keys']),
                ' | '.join(comp['matched_values']),
                ' | '.join(comp['gt_only_keys']),
                ' | '.join(comp['model_only_keys']),
                'Yes' if comp['gt_in_source'] else 'NO - Missing',
                'Yes' if comp['model_in_source'] else 'NO - Missing'
            ])


def generate_analysis_csv(comparisons, output_path, model_name, gt_results, model_results):
    """Generate clean analysis CSV."""
    
    # Filter to only queries that exist in both
    valid_comparisons = [c for c in comparisons if c['gt_in_source'] and c['model_in_source']]
    
    total = len(comparisons)
    valid = len(valid_comparisons)
    both_success = sum(1 for c in valid_comparisons if c['gt_success'] and c['model_success'])
    
    total_key_matches = sum(c['key_match_count'] for c in valid_comparisons)
    total_value_matches = sum(c['value_match_count'] for c in valid_comparisons)
    
    queries_with_key_match = sum(1 for c in valid_comparisons if c['key_match_count'] > 0)
    queries_with_value_match = sum(1 for c in valid_comparisons if c['value_match_count'] > 0)
    queries_with_full_key_match = sum(1 for c in valid_comparisons if c['key_match_count'] == c['gt_unique_keys'] and c['gt_unique_keys'] > 0)
    queries_with_full_value_match = sum(1 for c in valid_comparisons if c['value_match_count'] == c['gt_unique_values'] and c['gt_unique_values'] > 0)
    
    # Key frequency analysis
    all_gt_keys = defaultdict(int)
    all_model_keys = defaultdict(int)
    matched_key_freq = defaultdict(int)
    
    for comp in valid_comparisons:
        gt_data = gt_results.get(comp['query'], {})
        for attr in gt_data.get('attributes', []):
            norm_key = normalize_key(attr.get('attribute_key', ''))
            if norm_key:
                all_gt_keys[norm_key] += 1
        
        model_data = model_results.get(comp['query'], {})
        for attr in model_data.get('attributes', []):
            norm_key = normalize_key(attr.get('attribute_key', ''))
            if norm_key:
                all_model_keys[norm_key] += 1
        
        for key in comp['matched_keys']:
            matched_key_freq[key] += 1
    
    # Key match rate distribution
    rate_buckets = {'0%': 0, '1-25%': 0, '26-50%': 0, '51-75%': 0, '76-99%': 0, '100%': 0}
    for comp in valid_comparisons:
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
        
        writer.writerow(['DATA AVAILABILITY'])
        writer.writerow(['Metric', 'Count'])
        writer.writerow(['Total Queries (union)', total])
        writer.writerow(['Queries in Both Sources', valid])
        writer.writerow(['Queries Only in GT', sum(1 for c in comparisons if c['gt_in_source'] and not c['model_in_source'])])
        writer.writerow([f'Queries Only in {model_name}', sum(1 for c in comparisons if not c['gt_in_source'] and c['model_in_source'])])
        writer.writerow([])
        
        writer.writerow(['OVERVIEW (Queries in Both Sources)'])
        writer.writerow(['Metric', 'Count', 'Percentage'])
        writer.writerow(['Valid Queries', valid, '100%'])
        writer.writerow(['Both Successful', both_success, f'{both_success/valid*100:.1f}%' if valid > 0 else 'N/A'])
        writer.writerow([])
        
        writer.writerow(['KEY MATCHING'])
        writer.writerow(['Metric', 'Count', 'Percentage'])
        writer.writerow(['Total Key Matches', total_key_matches, '-'])
        writer.writerow(['Queries with ≥1 Key Match', queries_with_key_match, f'{queries_with_key_match/valid*100:.1f}%' if valid > 0 else 'N/A'])
        writer.writerow(['Queries with 100% Key Match', queries_with_full_key_match, f'{queries_with_full_key_match/valid*100:.1f}%' if valid > 0 else 'N/A'])
        writer.writerow([])
        
        writer.writerow(['VALUE MATCHING'])
        writer.writerow(['Metric', 'Count', 'Percentage'])
        writer.writerow(['Total Value Matches', total_value_matches, '-'])
        writer.writerow(['Queries with ≥1 Value Match', queries_with_value_match, f'{queries_with_value_match/valid*100:.1f}%' if valid > 0 else 'N/A'])
        writer.writerow(['Queries with 100% Value Match', queries_with_full_value_match, f'{queries_with_full_value_match/valid*100:.1f}%' if valid > 0 else 'N/A'])
        writer.writerow([])
        
        writer.writerow(['KEY MATCH DISTRIBUTION'])
        writer.writerow(['Match Rate', 'Query Count', 'Percentage'])
        for bucket, count in rate_buckets.items():
            writer.writerow([bucket, count, f'{count/valid*100:.1f}%' if valid > 0 else 'N/A'])
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
    print("COMPREHENSIVE GT COMPARISON - FIXED VERSION")
    print("="*70)
    
    # Load all data
    print("\nLoading Ground Truth (Claude Opus)...")
    gt_results = load_csv_results('claude_1000_results.csv')
    print(f"  Loaded {len(gt_results)} queries")
    
    print("Loading Gemma V4...")
    gemma_results = load_csv_results('../present/gemma_v4_1000_results.csv')
    print(f"  Loaded {len(gemma_results)} queries")
    
    print("Loading Gemini...")
    gemini_results = load_csv_results('gemini_final_results.csv')
    print(f"  Loaded {len(gemini_results)} queries")
    
    print("Loading QMeans...")
    qmeans_results = load_qmeans_json('qmeans_results.json')
    print(f"  Loaded {len(qmeans_results)} queries")
    
    # Get all unique queries
    all_queries = set(gt_results.keys()) | set(gemma_results.keys()) | set(gemini_results.keys()) | set(qmeans_results.keys())
    print(f"\nTotal unique queries across all sources: {len(all_queries)}")
    
    # Remove old files
    old_files = [
        '../present/gt_vs_gemma_clean.csv',
        '../present/gt_vs_gemma_analysis.csv',
        '../present/gt_vs_gemini_clean.csv',
        '../present/gt_vs_gemini_analysis.csv',
        '../present/gt_vs_qmeans_clean.csv',
        '../present/gt_vs_qmeans_analysis.csv'
    ]
    for f in old_files:
        if os.path.exists(f):
            os.remove(f)
            print(f"  Removed: {f}")
    
    # Compare GT vs Gemma
    print("\n" + "-"*50)
    print("Comparing GT vs Gemma V4...")
    gemma_queries = set(gt_results.keys()) | set(gemma_results.keys())
    gemma_comparisons = []
    for query in sorted(gemma_queries):
        gt_data = gt_results.get(query)
        model_data = gemma_results.get(query)
        comp = compare_query(gt_data, model_data, query)
        gemma_comparisons.append(comp)
    
    generate_comparison_csv(gemma_comparisons, '../present/gt_vs_gemma_v2.csv', 'Gemma')
    generate_analysis_csv(gemma_comparisons, '../present/gt_vs_gemma_analysis_v2.csv', 'Gemma', gt_results, gemma_results)
    
    valid_gemma = [c for c in gemma_comparisons if c['gt_in_source'] and c['model_in_source']]
    gemma_key_match = sum(1 for c in valid_gemma if c['key_match_count'] > 0)
    gemma_value_match = sum(1 for c in valid_gemma if c['value_match_count'] > 0)
    print(f"  Valid queries: {len(valid_gemma)}")
    print(f"  Key Match: {gemma_key_match}/{len(valid_gemma)} ({gemma_key_match/len(valid_gemma)*100:.1f}%)")
    print(f"  Value Match: {gemma_value_match}/{len(valid_gemma)} ({gemma_value_match/len(valid_gemma)*100:.1f}%)")
    
    # Compare GT vs Gemini
    print("\n" + "-"*50)
    print("Comparing GT vs Gemini...")
    gemini_queries = set(gt_results.keys()) | set(gemini_results.keys())
    gemini_comparisons = []
    for query in sorted(gemini_queries):
        gt_data = gt_results.get(query)
        model_data = gemini_results.get(query)
        comp = compare_query(gt_data, model_data, query)
        gemini_comparisons.append(comp)
    
    generate_comparison_csv(gemini_comparisons, '../present/gt_vs_gemini_v2.csv', 'Gemini')
    generate_analysis_csv(gemini_comparisons, '../present/gt_vs_gemini_analysis_v2.csv', 'Gemini', gt_results, gemini_results)
    
    valid_gemini = [c for c in gemini_comparisons if c['gt_in_source'] and c['model_in_source']]
    gemini_key_match = sum(1 for c in valid_gemini if c['key_match_count'] > 0)
    gemini_value_match = sum(1 for c in valid_gemini if c['value_match_count'] > 0)
    print(f"  Valid queries: {len(valid_gemini)}")
    print(f"  Key Match: {gemini_key_match}/{len(valid_gemini)} ({gemini_key_match/len(valid_gemini)*100:.1f}%)")
    print(f"  Value Match: {gemini_value_match}/{len(valid_gemini)} ({gemini_value_match/len(valid_gemini)*100:.1f}%)")
    
    # Compare GT vs QMeans
    print("\n" + "-"*50)
    print("Comparing GT vs QMeans...")
    qmeans_queries = set(gt_results.keys()) | set(qmeans_results.keys())
    qmeans_comparisons = []
    for query in sorted(qmeans_queries):
        gt_data = gt_results.get(query)
        model_data = qmeans_results.get(query)
        comp = compare_query(gt_data, model_data, query)
        qmeans_comparisons.append(comp)
    
    generate_comparison_csv(qmeans_comparisons, '../present/gt_vs_qmeans_v2.csv', 'QMeans')
    generate_analysis_csv(qmeans_comparisons, '../present/gt_vs_qmeans_analysis_v2.csv', 'QMeans', gt_results, qmeans_results)
    
    valid_qmeans = [c for c in qmeans_comparisons if c['gt_in_source'] and c['model_in_source']]
    qmeans_key_match = sum(1 for c in valid_qmeans if c['key_match_count'] > 0)
    qmeans_value_match = sum(1 for c in valid_qmeans if c['value_match_count'] > 0)
    print(f"  Valid queries: {len(valid_qmeans)}")
    print(f"  Key Match: {qmeans_key_match}/{len(valid_qmeans)} ({qmeans_key_match/len(valid_qmeans)*100:.1f}%)")
    print(f"  Value Match: {qmeans_value_match}/{len(valid_qmeans)} ({qmeans_value_match/len(valid_qmeans)*100:.1f}%)")
    
    # Final Summary
    print("\n" + "="*70)
    print("FINAL COMPARISON SUMMARY")
    print("="*70)
    print(f"\n{'Model':<12} | {'Valid Queries':<14} | {'Key Match':<15} | {'Value Match':<15}")
    print("-"*65)
    print(f"{'Gemma':<12} | {len(valid_gemma):>4}             | {gemma_key_match:>4} ({gemma_key_match/len(valid_gemma)*100:>5.1f}%)   | {gemma_value_match:>4} ({gemma_value_match/len(valid_gemma)*100:>5.1f}%)")
    print(f"{'Gemini':<12} | {len(valid_gemini):>4}             | {gemini_key_match:>4} ({gemini_key_match/len(valid_gemini)*100:>5.1f}%)   | {gemini_value_match:>4} ({gemini_value_match/len(valid_gemini)*100:>5.1f}%)")
    print(f"{'QMeans':<12} | {len(valid_qmeans):>4}             | {qmeans_key_match:>4} ({qmeans_key_match/len(valid_qmeans)*100:>5.1f}%)   | {qmeans_value_match:>4} ({qmeans_value_match/len(valid_qmeans)*100:>5.1f}%)")
    
    print("\n" + "="*70)
    print("NEW OUTPUT FILES GENERATED:")
    print("="*70)
    print("  ../present/gt_vs_gemma_v2.csv          - Detailed comparison")
    print("  ../present/gt_vs_gemma_analysis_v2.csv - Summary statistics")
    print("  ../present/gt_vs_gemini_v2.csv         - Detailed comparison")
    print("  ../present/gt_vs_gemini_analysis_v2.csv- Summary statistics")
    print("  ../present/gt_vs_qmeans_v2.csv         - Detailed comparison")
    print("  ../present/gt_vs_qmeans_analysis_v2.csv- Summary statistics")


if __name__ == '__main__':
    main()
