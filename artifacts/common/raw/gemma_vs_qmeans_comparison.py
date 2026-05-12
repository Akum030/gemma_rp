#!/usr/bin/env python3
"""
Gemma V4 vs QMeans Direct Comparison
"""

import csv
import json
import os
from collections import defaultdict

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

def compare_query(gemma_data, qmeans_data, query):
    """Compare Gemma with QMeans data for a single query."""
    gemma_attrs = gemma_data.get('attributes', []) if gemma_data else []
    qmeans_attrs = qmeans_data.get('attributes', []) if qmeans_data else []
    
    gemma_keys = get_unique_normalized_keys(gemma_attrs)
    qmeans_keys = get_unique_normalized_keys(qmeans_attrs)
    gemma_values = get_unique_normalized_values(gemma_attrs)
    qmeans_values = get_unique_normalized_values(qmeans_attrs)
    
    matched_keys = gemma_keys & qmeans_keys
    matched_values = gemma_values & qmeans_values
    
    return {
        'query': query,
        'gemma_in_source': gemma_data is not None,
        'qmeans_in_source': qmeans_data is not None,
        'gemma_success': gemma_data.get('success', False) if gemma_data else False,
        'qmeans_success': qmeans_data.get('success', False) if qmeans_data else False,
        'key_match_count': len(matched_keys),
        'value_match_count': len(matched_values),
        'gemma_unique_keys': len(gemma_keys),
        'qmeans_unique_keys': len(qmeans_keys),
        'gemma_unique_values': len(gemma_values),
        'qmeans_unique_values': len(qmeans_values),
        'gemma_formatted': format_value_keys(gemma_attrs),
        'qmeans_formatted': format_value_keys(qmeans_attrs),
        'matched_keys': sorted(matched_keys),
        'matched_values': sorted(matched_values),
        'gemma_only_keys': sorted(gemma_keys - qmeans_keys),
        'qmeans_only_keys': sorted(qmeans_keys - gemma_keys)
    }


def generate_comparison_csv(comparisons, output_path):
    """Generate clean comparison CSV."""
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        writer.writerow([
            'Query',
            'Key Match Count',
            'Value Match Count',
            'Gemma Unique Keys',
            'QMeans Unique Keys',
            'Gemma Unique Values',
            'QMeans Unique Values',
            'Key Match % (vs Gemma)',
            'Value Match % (vs Gemma)',
            'Gemma: Value - Keys (by priority)',
            'QMeans: Value - Keys (by priority)',
            'Matched Keys',
            'Matched Values',
            'Gemma Only Keys',
            'QMeans Only Keys',
            'Gemma In Source',
            'QMeans In Source'
        ])
        
        for comp in comparisons:
            key_match_pct = f"{comp['key_match_count']/comp['gemma_unique_keys']*100:.1f}%" if comp['gemma_unique_keys'] > 0 else "N/A"
            value_match_pct = f"{comp['value_match_count']/comp['gemma_unique_values']*100:.1f}%" if comp['gemma_unique_values'] > 0 else "N/A"
            
            writer.writerow([
                comp['query'],
                comp['key_match_count'],
                comp['value_match_count'],
                comp['gemma_unique_keys'],
                comp['qmeans_unique_keys'],
                comp['gemma_unique_values'],
                comp['qmeans_unique_values'],
                key_match_pct,
                value_match_pct,
                comp['gemma_formatted'],
                comp['qmeans_formatted'],
                ' | '.join(comp['matched_keys']),
                ' | '.join(comp['matched_values']),
                ' | '.join(comp['gemma_only_keys']),
                ' | '.join(comp['qmeans_only_keys']),
                'Yes' if comp['gemma_in_source'] else 'NO - Missing',
                'Yes' if comp['qmeans_in_source'] else 'NO - Missing'
            ])


def generate_analysis_csv(comparisons, output_path, gemma_results, qmeans_results):
    """Generate analysis CSV."""
    
    valid_comparisons = [c for c in comparisons if c['gemma_in_source'] and c['qmeans_in_source']]
    
    total = len(comparisons)
    valid = len(valid_comparisons)
    both_success = sum(1 for c in valid_comparisons if c['gemma_success'] and c['qmeans_success'])
    
    total_key_matches = sum(c['key_match_count'] for c in valid_comparisons)
    total_value_matches = sum(c['value_match_count'] for c in valid_comparisons)
    
    queries_with_key_match = sum(1 for c in valid_comparisons if c['key_match_count'] > 0)
    queries_with_value_match = sum(1 for c in valid_comparisons if c['value_match_count'] > 0)
    
    # For 100% match, use min of both as denominator
    queries_with_full_key_match = sum(1 for c in valid_comparisons 
        if c['key_match_count'] > 0 and c['key_match_count'] == min(c['gemma_unique_keys'], c['qmeans_unique_keys']))
    queries_with_full_value_match = sum(1 for c in valid_comparisons 
        if c['value_match_count'] > 0 and c['value_match_count'] == min(c['gemma_unique_values'], c['qmeans_unique_values']))
    
    # Key frequency analysis
    all_gemma_keys = defaultdict(int)
    all_qmeans_keys = defaultdict(int)
    matched_key_freq = defaultdict(int)
    
    for comp in valid_comparisons:
        gemma_data = gemma_results.get(comp['query'], {})
        for attr in gemma_data.get('attributes', []):
            norm_key = normalize_key(attr.get('attribute_key', ''))
            if norm_key:
                all_gemma_keys[norm_key] += 1
        
        qmeans_data = qmeans_results.get(comp['query'], {})
        for attr in qmeans_data.get('attributes', []):
            norm_key = normalize_key(attr.get('attribute_key', ''))
            if norm_key:
                all_qmeans_keys[norm_key] += 1
        
        for key in comp['matched_keys']:
            matched_key_freq[key] += 1
    
    # Key match rate distribution
    rate_buckets = {'0%': 0, '1-25%': 0, '26-50%': 0, '51-75%': 0, '76-99%': 0, '100%': 0}
    for comp in valid_comparisons:
        denom = max(comp['gemma_unique_keys'], comp['qmeans_unique_keys'])
        if denom == 0:
            continue
        rate = comp['key_match_count'] / denom
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
        
        writer.writerow(['GEMMA V4 vs QMEANS - ANALYSIS SUMMARY'])
        writer.writerow(['=' * 60])
        writer.writerow([])
        
        writer.writerow(['DATA AVAILABILITY'])
        writer.writerow(['Metric', 'Count'])
        writer.writerow(['Total Queries (union)', total])
        writer.writerow(['Queries in Both Sources', valid])
        writer.writerow(['Queries Only in Gemma', sum(1 for c in comparisons if c['gemma_in_source'] and not c['qmeans_in_source'])])
        writer.writerow(['Queries Only in QMeans', sum(1 for c in comparisons if not c['gemma_in_source'] and c['qmeans_in_source'])])
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
        writer.writerow(['Queries with Full Key Overlap', queries_with_full_key_match, f'{queries_with_full_key_match/valid*100:.1f}%' if valid > 0 else 'N/A'])
        writer.writerow([])
        
        writer.writerow(['VALUE MATCHING'])
        writer.writerow(['Metric', 'Count', 'Percentage'])
        writer.writerow(['Total Value Matches', total_value_matches, '-'])
        writer.writerow(['Queries with ≥1 Value Match', queries_with_value_match, f'{queries_with_value_match/valid*100:.1f}%' if valid > 0 else 'N/A'])
        writer.writerow(['Queries with Full Value Overlap', queries_with_full_value_match, f'{queries_with_full_value_match/valid*100:.1f}%' if valid > 0 else 'N/A'])
        writer.writerow([])
        
        writer.writerow(['KEY MATCH DISTRIBUTION'])
        writer.writerow(['Match Rate', 'Query Count', 'Percentage'])
        for bucket, count in rate_buckets.items():
            writer.writerow([bucket, count, f'{count/valid*100:.1f}%' if valid > 0 else 'N/A'])
        writer.writerow([])
        
        writer.writerow(['TOP 20 MATCHED KEYS (Common between Gemma & QMeans)'])
        writer.writerow(['Key', 'Match Count', 'Gemma Frequency', 'QMeans Frequency'])
        for key, count in sorted(matched_key_freq.items(), key=lambda x: -x[1])[:20]:
            gemma_freq = all_gemma_keys.get(key, 0)
            qmeans_freq = all_qmeans_keys.get(key, 0)
            writer.writerow([key, count, gemma_freq, qmeans_freq])
        writer.writerow([])
        
        writer.writerow(['GEMMA KEYS NOT IN QMEANS (Top 15)'])
        writer.writerow(['Key', 'Gemma Frequency'])
        gemma_only = [(k, v) for k, v in all_gemma_keys.items() if k not in all_qmeans_keys]
        for key, count in sorted(gemma_only, key=lambda x: -x[1])[:15]:
            writer.writerow([key, count])
        writer.writerow([])
        
        writer.writerow(['QMEANS KEYS NOT IN GEMMA (Top 15)'])
        writer.writerow(['Key', 'QMeans Frequency'])
        qmeans_only = [(k, v) for k, v in all_qmeans_keys.items() if k not in all_gemma_keys]
        for key, count in sorted(qmeans_only, key=lambda x: -x[1])[:15]:
            writer.writerow([key, count])


def main():
    print("="*70)
    print("GEMMA V4 vs QMEANS COMPARISON")
    print("="*70)
    
    print("\nLoading Gemma V4...")
    gemma_results = load_csv_results('../present/gemma_v4_1000_results.csv')
    print(f"  Loaded {len(gemma_results)} queries")
    
    print("Loading QMeans...")
    qmeans_results = load_qmeans_json('qmeans_results.json')
    print(f"  Loaded {len(qmeans_results)} queries")
    
    # Get all unique queries
    all_queries = set(gemma_results.keys()) | set(qmeans_results.keys())
    print(f"\nTotal unique queries: {len(all_queries)}")
    
    # Compare
    print("\nComparing Gemma V4 vs QMeans...")
    comparisons = []
    for query in sorted(all_queries):
        gemma_data = gemma_results.get(query)
        qmeans_data = qmeans_results.get(query)
        comp = compare_query(gemma_data, qmeans_data, query)
        comparisons.append(comp)
    
    generate_comparison_csv(comparisons, '../present/gemma_vs_qmeans.csv')
    generate_analysis_csv(comparisons, '../present/gemma_vs_qmeans_analysis.csv', gemma_results, qmeans_results)
    
    valid = [c for c in comparisons if c['gemma_in_source'] and c['qmeans_in_source']]
    key_match = sum(1 for c in valid if c['key_match_count'] > 0)
    value_match = sum(1 for c in valid if c['value_match_count'] > 0)
    
    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"Valid Queries (in both): {len(valid)}")
    print(f"Queries with Key Match:   {key_match}/{len(valid)} ({key_match/len(valid)*100:.1f}%)")
    print(f"Queries with Value Match: {value_match}/{len(valid)} ({value_match/len(valid)*100:.1f}%)")
    print(f"\nOutput Files:")
    print(f"  ../present/gemma_vs_qmeans.csv")
    print(f"  ../present/gemma_vs_qmeans_analysis.csv")


if __name__ == '__main__':
    main()
