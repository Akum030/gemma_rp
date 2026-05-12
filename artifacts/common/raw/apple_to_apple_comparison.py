#!/usr/bin/env python3
"""
Apple-to-Apple Comparison - Only uses queries that exist in Ground Truth
QMeans comparison only includes 978 overlapping queries
"""

import csv
import json
import os
from collections import defaultdict

def normalize_key(key):
    if key is None:
        return ''
    return ' '.join(str(key).lower().strip().replace('_', ' ').replace('-', ' ').split())

def normalize_value(value):
    if value is None:
        return ''
    return ' '.join(str(value).lower().strip().split())

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

def format_value_keys(attrs):
    if not attrs:
        return ''
    
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
    return set(normalize_key(a.get('attribute_key', '')) for a in attrs if a.get('attribute_key'))

def get_unique_normalized_values(attrs):
    return set(normalize_value(a.get('value', '')) for a in attrs if a.get('value'))

def compare_query(gt_data, model_data, query):
    gt_attrs = gt_data.get('attributes', []) if gt_data else []
    model_attrs = model_data.get('attributes', []) if model_data else []
    
    gt_keys = get_unique_normalized_keys(gt_attrs)
    model_keys = get_unique_normalized_keys(model_attrs)
    gt_values = get_unique_normalized_values(gt_attrs)
    model_values = get_unique_normalized_values(model_attrs)
    
    matched_keys = gt_keys & model_keys
    matched_values = gt_values & model_values
    
    return {
        'query': query,
        'key_match_count': len(matched_keys),
        'value_match_count': len(matched_values),
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
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        writer.writerow([
            'Query',
            'Key Match Count',
            'Value Match Count',
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
            key_match_pct = f"{comp['key_match_count']/comp['gt_unique_keys']*100:.1f}%" if comp['gt_unique_keys'] > 0 else "N/A"
            value_match_pct = f"{comp['value_match_count']/comp['gt_unique_values']*100:.1f}%" if comp['gt_unique_values'] > 0 else "N/A"
            
            writer.writerow([
                comp['query'],
                comp['key_match_count'],
                comp['value_match_count'],
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
                ' | '.join(comp['model_only_keys'])
            ])


def generate_analysis_csv(comparisons, output_path, model_name, gt_results, model_results):
    total = len(comparisons)
    
    total_key_matches = sum(c['key_match_count'] for c in comparisons)
    total_value_matches = sum(c['value_match_count'] for c in comparisons)
    
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
            if norm_key:
                all_gt_keys[norm_key] += 1
        
        model_data = model_results.get(comp['query'], {})
        for attr in model_data.get('attributes', []):
            norm_key = normalize_key(attr.get('attribute_key', ''))
            if norm_key:
                all_model_keys[norm_key] += 1
        
        for key in comp['matched_keys']:
            matched_key_freq[key] += 1
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        writer.writerow([f'GROUND TRUTH vs {model_name.upper()} - APPLE TO APPLE COMPARISON'])
        writer.writerow(['=' * 60])
        writer.writerow([])
        
        writer.writerow(['OVERVIEW'])
        writer.writerow(['Metric', 'Count', 'Percentage'])
        writer.writerow(['Total Queries Compared', total, '100%'])
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
        
        writer.writerow(['TOP 20 MATCHED KEYS'])
        writer.writerow(['Key', 'Match Count', 'GT Frequency', f'{model_name} Frequency'])
        for key, count in sorted(matched_key_freq.items(), key=lambda x: -x[1])[:20]:
            gt_freq = all_gt_keys.get(key, 0)
            model_freq = all_model_keys.get(key, 0)
            writer.writerow([key, count, gt_freq, model_freq])
        writer.writerow([])
        
        writer.writerow(['GT KEYS NOT IN MODEL (Top 15)'])
        writer.writerow(['Key', 'GT Frequency'])
        gt_only = [(k, v) for k, v in all_gt_keys.items() if k not in all_model_keys]
        for key, count in sorted(gt_only, key=lambda x: -x[1])[:15]:
            writer.writerow([key, count])


def main():
    print("="*70)
    print("APPLE-TO-APPLE COMPARISON")
    print("Only queries in Ground Truth are compared")
    print("="*70)
    
    # Load all data
    print("\nLoading Ground Truth (Claude Opus)...")
    gt_results = load_csv_results('claude_1000_results.csv')
    gt_queries = set(gt_results.keys())
    print(f"  Loaded {len(gt_queries)} queries")
    
    print("Loading Gemma V4...")
    gemma_results = load_csv_results('../present/gemma_v4_1000_results.csv')
    print(f"  Loaded {len(gemma_results)} queries")
    
    print("Loading Gemini...")
    gemini_results = load_csv_results('gemini_final_results.csv')
    print(f"  Loaded {len(gemini_results)} queries")
    
    print("Loading QMeans...")
    qmeans_results = load_qmeans_json('qmeans_results.json')
    print(f"  Loaded {len(qmeans_results)} queries")
    
    # Find overlaps
    gemma_overlap = gt_queries & set(gemma_results.keys())
    gemini_overlap = gt_queries & set(gemini_results.keys())
    qmeans_overlap = gt_queries & set(qmeans_results.keys())
    
    print(f"\nOverlap with GT:")
    print(f"  Gemma:  {len(gemma_overlap)}/{len(gt_queries)} queries")
    print(f"  Gemini: {len(gemini_overlap)}/{len(gt_queries)} queries")
    print(f"  QMeans: {len(qmeans_overlap)}/{len(gt_queries)} queries")
    
    # Remove old files
    old_files = [
        '../present/gt_vs_gemma_v2.csv', '../present/gt_vs_gemma_analysis_v2.csv',
        '../present/gt_vs_gemini_v2.csv', '../present/gt_vs_gemini_analysis_v2.csv',
        '../present/gt_vs_qmeans_v2.csv', '../present/gt_vs_qmeans_analysis_v2.csv',
        '../present/gemma_vs_qmeans.csv', '../present/gemma_vs_qmeans_analysis.csv',
        '../present/gemma_vs_qmeans_v2.csv', '../present/gemma_vs_qmeans_analysis_v2.csv'
    ]
    for f in old_files:
        if os.path.exists(f):
            os.remove(f)
            print(f"  Removed: {f}")
    
    # GT vs Gemma (996 queries - all GT)
    print("\n" + "-"*50)
    print(f"Comparing GT vs Gemma ({len(gemma_overlap)} queries)...")
    gemma_comparisons = []
    for query in sorted(gemma_overlap):
        comp = compare_query(gt_results[query], gemma_results.get(query), query)
        gemma_comparisons.append(comp)
    
    generate_comparison_csv(gemma_comparisons, '../present/gt_vs_gemma_final.csv', 'Gemma')
    generate_analysis_csv(gemma_comparisons, '../present/gt_vs_gemma_analysis_final.csv', 'Gemma', gt_results, gemma_results)
    
    gemma_key_match = sum(1 for c in gemma_comparisons if c['key_match_count'] > 0)
    gemma_value_match = sum(1 for c in gemma_comparisons if c['value_match_count'] > 0)
    print(f"  Key Match: {gemma_key_match}/{len(gemma_comparisons)} ({gemma_key_match/len(gemma_comparisons)*100:.1f}%)")
    print(f"  Value Match: {gemma_value_match}/{len(gemma_comparisons)} ({gemma_value_match/len(gemma_comparisons)*100:.1f}%)")
    
    # GT vs Gemini (996 queries - all GT)
    print("\n" + "-"*50)
    print(f"Comparing GT vs Gemini ({len(gemini_overlap)} queries)...")
    gemini_comparisons = []
    for query in sorted(gemini_overlap):
        comp = compare_query(gt_results[query], gemini_results.get(query), query)
        gemini_comparisons.append(comp)
    
    generate_comparison_csv(gemini_comparisons, '../present/gt_vs_gemini_final.csv', 'Gemini')
    generate_analysis_csv(gemini_comparisons, '../present/gt_vs_gemini_analysis_final.csv', 'Gemini', gt_results, gemini_results)
    
    gemini_key_match = sum(1 for c in gemini_comparisons if c['key_match_count'] > 0)
    gemini_value_match = sum(1 for c in gemini_comparisons if c['value_match_count'] > 0)
    print(f"  Key Match: {gemini_key_match}/{len(gemini_comparisons)} ({gemini_key_match/len(gemini_comparisons)*100:.1f}%)")
    print(f"  Value Match: {gemini_value_match}/{len(gemini_comparisons)} ({gemini_value_match/len(gemini_comparisons)*100:.1f}%)")
    
    # GT vs QMeans (978 queries - only overlap)
    print("\n" + "-"*50)
    print(f"Comparing GT vs QMeans ({len(qmeans_overlap)} queries - ONLY OVERLAP)...")
    qmeans_comparisons = []
    for query in sorted(qmeans_overlap):
        comp = compare_query(gt_results[query], qmeans_results.get(query), query)
        qmeans_comparisons.append(comp)
    
    generate_comparison_csv(qmeans_comparisons, '../present/gt_vs_qmeans_final.csv', 'QMeans')
    generate_analysis_csv(qmeans_comparisons, '../present/gt_vs_qmeans_analysis_final.csv', 'QMeans', gt_results, qmeans_results)
    
    qmeans_key_match = sum(1 for c in qmeans_comparisons if c['key_match_count'] > 0)
    qmeans_value_match = sum(1 for c in qmeans_comparisons if c['value_match_count'] > 0)
    print(f"  Key Match: {qmeans_key_match}/{len(qmeans_comparisons)} ({qmeans_key_match/len(qmeans_comparisons)*100:.1f}%)")
    print(f"  Value Match: {qmeans_value_match}/{len(qmeans_comparisons)} ({qmeans_value_match/len(qmeans_comparisons)*100:.1f}%)")
    
    # Gemma vs QMeans (only 978 overlap queries)
    print("\n" + "-"*50)
    print(f"Comparing Gemma vs QMeans ({len(qmeans_overlap)} queries - ONLY OVERLAP)...")
    gemma_qmeans_comparisons = []
    for query in sorted(qmeans_overlap):
        gemma_attrs = gemma_results.get(query, {}).get('attributes', [])
        qmeans_attrs = qmeans_results.get(query, {}).get('attributes', [])
        
        gemma_keys = get_unique_normalized_keys(gemma_attrs)
        qmeans_keys = get_unique_normalized_keys(qmeans_attrs)
        gemma_values = get_unique_normalized_values(gemma_attrs)
        qmeans_values = get_unique_normalized_values(qmeans_attrs)
        
        matched_keys = gemma_keys & qmeans_keys
        matched_values = gemma_values & qmeans_values
        
        gemma_qmeans_comparisons.append({
            'query': query,
            'key_match_count': len(matched_keys),
            'value_match_count': len(matched_values),
            'gt_unique_keys': len(gemma_keys),
            'model_unique_keys': len(qmeans_keys),
            'gt_unique_values': len(gemma_values),
            'model_unique_values': len(qmeans_values),
            'gt_formatted': format_value_keys(gemma_attrs),
            'model_formatted': format_value_keys(qmeans_attrs),
            'matched_keys': sorted(matched_keys),
            'matched_values': sorted(matched_values),
            'gt_only_keys': sorted(gemma_keys - qmeans_keys),
            'model_only_keys': sorted(qmeans_keys - gemma_keys)
        })
    
    # Write Gemma vs QMeans comparison
    with open('../present/gemma_vs_qmeans_final.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Query', 'Key Match Count', 'Value Match Count',
            'Gemma Unique Keys', 'QMeans Unique Keys',
            'Gemma Unique Values', 'QMeans Unique Values',
            'Key Match %', 'Value Match %',
            'Gemma: Value - Keys', 'QMeans: Value - Keys',
            'Matched Keys', 'Matched Values',
            'Gemma Only Keys', 'QMeans Only Keys'
        ])
        for comp in gemma_qmeans_comparisons:
            key_match_pct = f"{comp['key_match_count']/comp['gt_unique_keys']*100:.1f}%" if comp['gt_unique_keys'] > 0 else "N/A"
            value_match_pct = f"{comp['value_match_count']/comp['gt_unique_values']*100:.1f}%" if comp['gt_unique_values'] > 0 else "N/A"
            writer.writerow([
                comp['query'], comp['key_match_count'], comp['value_match_count'],
                comp['gt_unique_keys'], comp['model_unique_keys'],
                comp['gt_unique_values'], comp['model_unique_values'],
                key_match_pct, value_match_pct,
                comp['gt_formatted'], comp['model_formatted'],
                ' | '.join(comp['matched_keys']), ' | '.join(comp['matched_values']),
                ' | '.join(comp['gt_only_keys']), ' | '.join(comp['model_only_keys'])
            ])
    
    gq_key_match = sum(1 for c in gemma_qmeans_comparisons if c['key_match_count'] > 0)
    gq_value_match = sum(1 for c in gemma_qmeans_comparisons if c['value_match_count'] > 0)
    print(f"  Key Match: {gq_key_match}/{len(gemma_qmeans_comparisons)} ({gq_key_match/len(gemma_qmeans_comparisons)*100:.1f}%)")
    print(f"  Value Match: {gq_value_match}/{len(gemma_qmeans_comparisons)} ({gq_value_match/len(gemma_qmeans_comparisons)*100:.1f}%)")
    
    # Final Summary
    print("\n" + "="*70)
    print("APPLE-TO-APPLE COMPARISON SUMMARY")
    print("="*70)
    print(f"\n{'Comparison':<25} | {'Queries':<10} | {'Key Match':<18} | {'Value Match':<18}")
    print("-"*75)
    print(f"{'GT vs Gemma':<25} | {len(gemma_comparisons):<10} | {gemma_key_match:>4} ({gemma_key_match/len(gemma_comparisons)*100:>5.1f}%)    | {gemma_value_match:>4} ({gemma_value_match/len(gemma_comparisons)*100:>5.1f}%)")
    print(f"{'GT vs Gemini':<25} | {len(gemini_comparisons):<10} | {gemini_key_match:>4} ({gemini_key_match/len(gemini_comparisons)*100:>5.1f}%)    | {gemini_value_match:>4} ({gemini_value_match/len(gemini_comparisons)*100:>5.1f}%)")
    print(f"{'GT vs QMeans':<25} | {len(qmeans_comparisons):<10} | {qmeans_key_match:>4} ({qmeans_key_match/len(qmeans_comparisons)*100:>5.1f}%)    | {qmeans_value_match:>4} ({qmeans_value_match/len(qmeans_comparisons)*100:>5.1f}%)")
    print(f"{'Gemma vs QMeans':<25} | {len(gemma_qmeans_comparisons):<10} | {gq_key_match:>4} ({gq_key_match/len(gemma_qmeans_comparisons)*100:>5.1f}%)    | {gq_value_match:>4} ({gq_value_match/len(gemma_qmeans_comparisons)*100:>5.1f}%)")
    
    print("\n" + "="*70)
    print("OUTPUT FILES (All in ../present/ folder):")
    print("="*70)
    print("  gt_vs_gemma_final.csv           - GT vs Gemma (996 queries)")
    print("  gt_vs_gemma_analysis_final.csv")
    print("  gt_vs_gemini_final.csv          - GT vs Gemini (996 queries)")
    print("  gt_vs_gemini_analysis_final.csv")
    print("  gt_vs_qmeans_final.csv          - GT vs QMeans (978 queries)")
    print("  gt_vs_qmeans_analysis_final.csv")
    print("  gemma_vs_qmeans_final.csv       - Gemma vs QMeans (978 queries)")


if __name__ == '__main__':
    main()
