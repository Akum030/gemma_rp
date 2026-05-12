"""
Comprehensive comparison for FULL dataset (1198 queries):
- QMeans (qmeans_results.csv)
- Gemini (gemini_with_dataset_full.csv)
- Gemma (gemma_v1_validation_results.csv)

Cross-model comparisons:
- QMeans vs Gemini, Gemini vs QMeans
- QMeans vs Gemma, Gemma vs QMeans
- Gemini vs Gemma, Gemma vs Gemini

Note: No ground truth available for these queries
"""

import pandas as pd
import re
import ast
import json

def normalize_value(value):
    """Normalize value: trim, remove quotes, lowercase"""
    if value is None or pd.isna(value):
        return ''
    
    value = str(value).strip()
    
    # Remove paired quotes
    while len(value) >= 2 and (
        (value.startswith('"') and value.endswith('"')) or
        (value.startswith("'") and value.endswith("'"))
    ):
        value = value[1:-1].strip()
    
    # Remove leading quotes
    while value.startswith('"') or value.startswith("'"):
        value = value[1:]
    
    # Remove trailing quotes
    while value.endswith('"') or value.endswith("'"):
        value = value[:-1]
    
    value = value.strip()
    value = value.rstrip(',').strip()
    value = value.lower()
    value = re.sub(r'\s+', ' ', value)
    
    return value


def parse_isq_qmeans(isq_list_str):
    """Parse QMeans ISQ format: value:key:spec"""
    if pd.isna(isq_list_str) or str(isq_list_str).strip() in ['[]', '', 'nan']:
        return []
    
    try:
        items = ast.literal_eval(str(isq_list_str))
        result = []
        for item in items:
            item = str(item).strip().strip('"').strip("'")
            parts = item.split(':')
            if len(parts) >= 2:
                value = normalize_value(parts[0])
                key = normalize_value(parts[1])
                if key:
                    result.append((key, value))
        return result
    except:
        return []


def parse_isq_gemini(isq_list_str):
    """Parse Gemini ISQ format: value:key:spec"""
    if pd.isna(isq_list_str) or str(isq_list_str).strip() in ['[]', '', 'nan']:
        return []
    
    try:
        clean_str = str(isq_list_str).replace('[', '').replace(']', '')
        clean_str = clean_str.replace('""', '"').replace("''", "'")
        
        items = re.split(r"['\"],\s*['\"]", clean_str)
        
        result = []
        for item in items:
            item = item.strip().strip('"').strip("'").strip('[').strip(']')
            if ':' in item:
                parts = item.split(':')
                if len(parts) >= 2:
                    value = normalize_value(parts[0])
                    key = normalize_value(parts[1])
                    if key:
                        result.append((key, value))
        return result
    except:
        return []


def parse_gemma_json(json_str):
    """Parse Gemma JSON format: {"key": "value", ...}"""
    if pd.isna(json_str) or str(json_str).strip() in ['{}', '', 'nan', '[]']:
        return []
    
    try:
        # Parse JSON
        data = json.loads(str(json_str).replace("'", '"'))
        result = []
        for key, value in data.items():
            key = normalize_value(key)
            value = normalize_value(value)
            if key:
                result.append((key, value))
        return result
    except:
        try:
            # Try ast.literal_eval for Python dict format
            data = ast.literal_eval(str(json_str))
            result = []
            for key, value in data.items():
                key = normalize_value(key)
                value = normalize_value(value)
                if key:
                    result.append((key, value))
            return result
        except:
            return []


def sort_attributes(attr_list):
    """Sort alphabetically by key"""
    return sorted(attr_list, key=lambda x: x[0])


def compare_attrs(source_attrs, target_attrs):
    """Compare source vs target attributes"""
    target_dict = {k: v for k, v in target_attrs}
    results = []
    
    for key, value in source_attrs:
        if key in target_dict:
            key_match = True
            value_match = (value == target_dict[key])
        else:
            key_match = False
            value_match = None
        results.append((key_match, value_match))
    
    return results


def main():
    print('='*80)
    print('COMPREHENSIVE COMPARISON - FULL DATASET (1198 Queries)')
    print('QMeans vs Gemini vs Gemma')
    print('='*80)
    
    # Load files
    print('\n1. Loading files...')
    qm_df = pd.read_csv('qmeans_results.csv')
    gm_df = pd.read_csv('gemini_with_dataset_full.csv')
    gemma_df = pd.read_csv('compare/gemma_v1_validation_results.csv')
    
    print(f'   QMeans: {len(qm_df)} rows')
    print(f'   Gemini: {len(gm_df)} rows')
    print(f'   Gemma: {len(gemma_df)} rows')
    
    # Find common queries
    qm_queries = set(qm_df['query'])
    gm_queries = set(gm_df['query'])
    gemma_queries = set(gemma_df['query'])
    common_queries = qm_queries & gm_queries & gemma_queries
    print(f'   Common queries: {len(common_queries)}')
    
    # Create lookup dictionaries
    print('\n2. Creating lookup dictionaries...')
    qm_lookup = {}
    for idx, row in qm_df.iterrows():
        query = row['query']
        if query not in qm_lookup:
            qm_lookup[query] = row
    
    gm_lookup = {}
    for idx, row in gm_df.iterrows():
        query = row['query']
        if query not in gm_lookup:
            gm_lookup[query] = row
    
    gemma_lookup = {}
    for idx, row in gemma_df.iterrows():
        query = row['query']
        if query not in gemma_lookup:
            gemma_lookup[query] = row
    
    # Process all common queries
    print('\n3. Processing all rows...')
    
    max_attrs = 9
    output_data = []
    
    for query in common_queries:
        qm_row = qm_lookup.get(query)
        gm_row = gm_lookup.get(query)
        gemma_row = gemma_lookup.get(query)
        
        # Parse attributes
        qm_attrs = sort_attributes(parse_isq_qmeans(qm_row.get('qmeans_isq_list', '[]'))) if qm_row is not None else []
        gm_attrs = sort_attributes(parse_isq_gemini(gm_row.get('gemini_dataset_isq_list', '[]'))) if gm_row is not None else []
        gemma_attrs = sort_attributes(parse_gemma_json(gemma_row.get('normalized_isqs', '{}'))) if gemma_row is not None else []
        
        qm_count = len(qm_attrs)
        gm_count = len(gm_attrs)
        gemma_count = len(gemma_attrs)
        
        output_row = {
            'query': query,
            'qmeans_attr_count': qm_count,
            'gemini_attr_count': gm_count,
            'gemma_attr_count': gemma_count
        }
        
        # Model attributes
        for i in range(max_attrs):
            if i < len(qm_attrs):
                output_row[f'qmeans_attr_key_{i+1}'] = qm_attrs[i][0]
                output_row[f'qmeans_attr_value_{i+1}'] = qm_attrs[i][1]
            else:
                output_row[f'qmeans_attr_key_{i+1}'] = ''
                output_row[f'qmeans_attr_value_{i+1}'] = ''
            
            if i < len(gm_attrs):
                output_row[f'gemini_attr_key_{i+1}'] = gm_attrs[i][0]
                output_row[f'gemini_attr_value_{i+1}'] = gm_attrs[i][1]
            else:
                output_row[f'gemini_attr_key_{i+1}'] = ''
                output_row[f'gemini_attr_value_{i+1}'] = ''
            
            if i < len(gemma_attrs):
                output_row[f'gemma_attr_key_{i+1}'] = gemma_attrs[i][0]
                output_row[f'gemma_attr_value_{i+1}'] = gemma_attrs[i][1]
            else:
                output_row[f'gemma_attr_key_{i+1}'] = ''
                output_row[f'gemma_attr_value_{i+1}'] = ''
        
        # COUNT_MATCH and HIGH_COUNT
        counts = {'qmeans': qm_count, 'gemini': gm_count, 'gemma': gemma_count}
        max_count = max(counts.values())
        highest = [k for k, v in counts.items() if v == max_count]
        
        output_row['COUNT_MATCH'] = 'TRUE' if len(set(counts.values())) == 1 else 'FALSE'
        output_row['HIGH_COUNT'] = ','.join(highest) if len(highest) > 1 else highest[0] if highest else 'same'
        
        # ===============================
        # QMeans vs Gemini
        # ===============================
        qm_vs_gm = compare_attrs(qm_attrs, gm_attrs)
        for i in range(max_attrs):
            if i < len(qm_vs_gm):
                key_match, val_match = qm_vs_gm[i]
                output_row[f'qmeans_vs_gemini_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                output_row[f'qmeans_vs_gemini_attr_{i+1}_value_match'] = 'NA' if val_match is None else ('TRUE' if val_match else 'FALSE')
            else:
                output_row[f'qmeans_vs_gemini_attr_{i+1}_key_match'] = ''
                output_row[f'qmeans_vs_gemini_attr_{i+1}_value_match'] = ''
        
        # Gemini vs QMeans
        gm_vs_qm = compare_attrs(gm_attrs, qm_attrs)
        for i in range(max_attrs):
            if i < len(gm_vs_qm):
                key_match, val_match = gm_vs_qm[i]
                output_row[f'gemini_vs_qmeans_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                output_row[f'gemini_vs_qmeans_attr_{i+1}_value_match'] = 'NA' if val_match is None else ('TRUE' if val_match else 'FALSE')
            else:
                output_row[f'gemini_vs_qmeans_attr_{i+1}_key_match'] = ''
                output_row[f'gemini_vs_qmeans_attr_{i+1}_value_match'] = ''
        
        # ===============================
        # QMeans vs Gemma
        # ===============================
        qm_vs_gemma = compare_attrs(qm_attrs, gemma_attrs)
        for i in range(max_attrs):
            if i < len(qm_vs_gemma):
                key_match, val_match = qm_vs_gemma[i]
                output_row[f'qmeans_vs_gemma_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                output_row[f'qmeans_vs_gemma_attr_{i+1}_value_match'] = 'NA' if val_match is None else ('TRUE' if val_match else 'FALSE')
            else:
                output_row[f'qmeans_vs_gemma_attr_{i+1}_key_match'] = ''
                output_row[f'qmeans_vs_gemma_attr_{i+1}_value_match'] = ''
        
        # Gemma vs QMeans
        gemma_vs_qm = compare_attrs(gemma_attrs, qm_attrs)
        for i in range(max_attrs):
            if i < len(gemma_vs_qm):
                key_match, val_match = gemma_vs_qm[i]
                output_row[f'gemma_vs_qmeans_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                output_row[f'gemma_vs_qmeans_attr_{i+1}_value_match'] = 'NA' if val_match is None else ('TRUE' if val_match else 'FALSE')
            else:
                output_row[f'gemma_vs_qmeans_attr_{i+1}_key_match'] = ''
                output_row[f'gemma_vs_qmeans_attr_{i+1}_value_match'] = ''
        
        # ===============================
        # Gemini vs Gemma
        # ===============================
        gm_vs_gemma = compare_attrs(gm_attrs, gemma_attrs)
        for i in range(max_attrs):
            if i < len(gm_vs_gemma):
                key_match, val_match = gm_vs_gemma[i]
                output_row[f'gemini_vs_gemma_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                output_row[f'gemini_vs_gemma_attr_{i+1}_value_match'] = 'NA' if val_match is None else ('TRUE' if val_match else 'FALSE')
            else:
                output_row[f'gemini_vs_gemma_attr_{i+1}_key_match'] = ''
                output_row[f'gemini_vs_gemma_attr_{i+1}_value_match'] = ''
        
        # Gemma vs Gemini
        gemma_vs_gm = compare_attrs(gemma_attrs, gm_attrs)
        for i in range(max_attrs):
            if i < len(gemma_vs_gm):
                key_match, val_match = gemma_vs_gm[i]
                output_row[f'gemma_vs_gemini_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                output_row[f'gemma_vs_gemini_attr_{i+1}_value_match'] = 'NA' if val_match is None else ('TRUE' if val_match else 'FALSE')
            else:
                output_row[f'gemma_vs_gemini_attr_{i+1}_key_match'] = ''
                output_row[f'gemma_vs_gemini_attr_{i+1}_value_match'] = ''
        
        output_data.append(output_row)
    
    # Create column order
    columns = ['query', 'qmeans_attr_count', 'gemini_attr_count', 'gemma_attr_count']
    
    # Model attributes
    for i in range(max_attrs):
        columns.extend([
            f'qmeans_attr_key_{i+1}', f'qmeans_attr_value_{i+1}',
            f'gemini_attr_key_{i+1}', f'gemini_attr_value_{i+1}',
            f'gemma_attr_key_{i+1}', f'gemma_attr_value_{i+1}'
        ])
    
    columns.extend(['COUNT_MATCH', 'HIGH_COUNT'])
    
    # Comparisons
    for i in range(max_attrs):
        columns.extend([f'qmeans_vs_gemini_attr_{i+1}_key_match', f'qmeans_vs_gemini_attr_{i+1}_value_match'])
    for i in range(max_attrs):
        columns.extend([f'gemini_vs_qmeans_attr_{i+1}_key_match', f'gemini_vs_qmeans_attr_{i+1}_value_match'])
    for i in range(max_attrs):
        columns.extend([f'qmeans_vs_gemma_attr_{i+1}_key_match', f'qmeans_vs_gemma_attr_{i+1}_value_match'])
    for i in range(max_attrs):
        columns.extend([f'gemma_vs_qmeans_attr_{i+1}_key_match', f'gemma_vs_qmeans_attr_{i+1}_value_match'])
    for i in range(max_attrs):
        columns.extend([f'gemini_vs_gemma_attr_{i+1}_key_match', f'gemini_vs_gemma_attr_{i+1}_value_match'])
    for i in range(max_attrs):
        columns.extend([f'gemma_vs_gemini_attr_{i+1}_key_match', f'gemma_vs_gemini_attr_{i+1}_value_match'])
    
    output_df = pd.DataFrame(output_data, columns=columns)
    
    # Sort by query for consistency
    output_df = output_df.sort_values('query').reset_index(drop=True)
    
    # Save
    output_file = 'comprehensive_comparison_full_dataset.csv'
    output_df.to_csv(output_file, index=False)
    
    print(f'\n✅ Saved to: {output_file}')
    print(f'   Total rows: {len(output_df)}')
    print(f'   Total columns: {len(output_df.columns)}')
    
    # STATISTICS
    print('\n' + '='*80)
    print('STATISTICS')
    print('='*80)
    
    total_qm_attrs = output_df['qmeans_attr_count'].sum()
    total_gm_attrs = output_df['gemini_attr_count'].sum()
    total_gemma_attrs = output_df['gemma_attr_count'].sum()
    
    print(f'\nTotal Attributes:')
    print(f'   QMeans: {total_qm_attrs} ({output_df["qmeans_attr_count"].mean():.2f} avg per query)')
    print(f'   Gemini: {total_gm_attrs} ({output_df["gemini_attr_count"].mean():.2f} avg per query)')
    print(f'   Gemma:  {total_gemma_attrs} ({output_df["gemma_attr_count"].mean():.2f} avg per query)')
    
    def print_comparison_stats(name, prefix):
        """Print comparison statistics"""
        true_count = 0
        false_count = 0
        na_count = 0
        
        for i in range(1, max_attrs + 1):
            col = f'{prefix}_attr_{i}_value_match'
            if col in output_df.columns:
                true_count += (output_df[col] == 'TRUE').sum()
                false_count += (output_df[col] == 'FALSE').sum()
                na_count += (output_df[col] == 'NA').sum()
        
        total = true_count + false_count + na_count
        if total > 0:
            print(f'\n{name}:')
            print(f'   TRUE  (key + value match):  {true_count:4d} ({100*true_count/total:.1f}%)')
            print(f'   FALSE (key found, diff val): {false_count:4d} ({100*false_count/total:.1f}%)')
            print(f'   NA    (key not found):       {na_count:4d} ({100*na_count/total:.1f}%)')
            print(f'   Key Found Rate: {100*(true_count+false_count)/total:.1f}%')
    
    print('\n' + '-'*60)
    print('CROSS-MODEL COMPARISONS')
    print('-'*60)
    print_comparison_stats('QMeans vs Gemini', 'qmeans_vs_gemini')
    print_comparison_stats('Gemini vs QMeans', 'gemini_vs_qmeans')
    print_comparison_stats('QMeans vs Gemma', 'qmeans_vs_gemma')
    print_comparison_stats('Gemma vs QMeans', 'gemma_vs_qmeans')
    print_comparison_stats('Gemini vs Gemma', 'gemini_vs_gemma')
    print_comparison_stats('Gemma vs Gemini', 'gemma_vs_gemini')
    
    # Count match stats
    print('\n' + '-'*60)
    print('COUNT MATCH (All 3 Models)')
    print('-'*60)
    count_true = (output_df['COUNT_MATCH'] == 'TRUE').sum()
    count_false = (output_df['COUNT_MATCH'] == 'FALSE').sum()
    print(f'   Same count (all 3): {count_true} ({100*count_true/len(output_df):.1f}%)')
    print(f'   Different count: {count_false} ({100*count_false/len(output_df):.1f}%)')
    
    high_counts = output_df['HIGH_COUNT'].value_counts()
    print(f'\n   Highest attribute count:')
    for val, cnt in high_counts.items():
        print(f'      {val}: {cnt}')
    
    return output_df


if __name__ == '__main__':
    main()
