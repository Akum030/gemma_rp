"""
FINAL Comprehensive comparison - keeps ALL 1000 rows
With value normalization (trim, lowercase, remove quotes)
"""

import pandas as pd
import re
import ast

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
    """Parse QMeans ISQ format"""
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
    """Parse Gemini ISQ format"""
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


def parse_ground_truth(row):
    """Parse ground truth attributes"""
    attrs = []
    for i in range(1, 10):
        key_col = f'attr_key_{i}'
        val_col = f'attr_value_{i}'
        if key_col in row and val_col in row:
            key = row[key_col]
            value = row[val_col]
            if pd.notna(key) and str(key).strip():
                key = normalize_value(key)
                value = normalize_value(value)
                attrs.append((key, value))
    return attrs


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
    print('FINAL COMPARISON - ALL 1000 ROWS')
    print('='*80)
    
    # Load files
    print('\n1. Loading files...')
    gt_df = pd.read_csv('synthetic_validation_dataset.csv')
    qm_df = pd.read_csv('qmeans_1000_validation.csv')
    gm_df = pd.read_csv('gemini_with_dataset_validation_queries.csv')
    
    print(f'   Ground Truth: {len(gt_df)} rows')
    print(f'   QMeans: {len(qm_df)} rows')
    print(f'   Gemini: {len(gm_df)} rows')
    
    # Create lookup dictionaries for QMeans and Gemini
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
    
    # Process all 1000 ground truth rows
    print('\n3. Processing all 1000 rows...')
    
    max_attrs = 9
    output_data = []
    
    for idx, gt_row in gt_df.iterrows():
        query = gt_row['query']
        
        # Get QMeans data for this query
        qm_row = qm_lookup.get(query, None)
        # Get Gemini data for this query
        gm_row = gm_lookup.get(query, None)
        
        # Parse attributes
        gt_attrs = sort_attributes(parse_ground_truth(gt_row))
        
        if qm_row is not None:
            qm_attrs = sort_attributes(parse_isq_qmeans(qm_row.get('qmeans_isq_list', '[]')))
        else:
            qm_attrs = []
        
        if gm_row is not None:
            gm_attrs = sort_attributes(parse_isq_gemini(gm_row.get('gemini_dataset_isq_list', '[]')))
        else:
            gm_attrs = []
        
        gt_count = len(gt_attrs)
        qm_count = len(qm_attrs)
        gm_count = len(gm_attrs)
        
        output_row = {
            'query': query,
            'ground_truth_count': gt_count,
            'qmeans_attr_count': qm_count,
            'gemini_attr_count': gm_count
        }
        
        # Ground truth attributes
        for i in range(max_attrs):
            if i < len(gt_attrs):
                output_row[f'groundtruth_attr_key_{i+1}'] = gt_attrs[i][0]
                output_row[f'groundtruth_attr_value_{i+1}'] = gt_attrs[i][1]
            else:
                output_row[f'groundtruth_attr_key_{i+1}'] = ''
                output_row[f'groundtruth_attr_value_{i+1}'] = ''
        
        # QMeans and Gemini attributes
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
        
        # COUNT_MATCH and HIGH_COUNT
        output_row['COUNT_MATCH'] = 'TRUE' if qm_count == gm_count else 'FALSE'
        if qm_count > gm_count:
            output_row['HIGH_COUNT'] = 'qmeans'
        elif gm_count > qm_count:
            output_row['HIGH_COUNT'] = 'gemini'
        else:
            output_row['HIGH_COUNT'] = 'same'
        
        # QMeans vs Gemini
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
        
        # Ground Truth vs QMeans
        gt_vs_qm = compare_attrs(gt_attrs, qm_attrs)
        for i in range(max_attrs):
            if i < len(gt_vs_qm):
                key_match, val_match = gt_vs_qm[i]
                output_row[f'groundtruth_vs_qmeans_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                output_row[f'groundtruth_vs_qmeans_attr_{i+1}_value_match'] = 'NA' if val_match is None else ('TRUE' if val_match else 'FALSE')
            else:
                output_row[f'groundtruth_vs_qmeans_attr_{i+1}_key_match'] = ''
                output_row[f'groundtruth_vs_qmeans_attr_{i+1}_value_match'] = ''
        
        # Ground Truth vs Gemini
        gt_vs_gm = compare_attrs(gt_attrs, gm_attrs)
        for i in range(max_attrs):
            if i < len(gt_vs_gm):
                key_match, val_match = gt_vs_gm[i]
                output_row[f'groundtruth_vs_gemini_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                output_row[f'groundtruth_vs_gemini_attr_{i+1}_value_match'] = 'NA' if val_match is None else ('TRUE' if val_match else 'FALSE')
            else:
                output_row[f'groundtruth_vs_gemini_attr_{i+1}_key_match'] = ''
                output_row[f'groundtruth_vs_gemini_attr_{i+1}_value_match'] = ''
        
        output_data.append(output_row)
    
    # Create column order
    columns = ['query', 'ground_truth_count', 'qmeans_attr_count', 'gemini_attr_count']
    
    for i in range(max_attrs):
        columns.extend([f'groundtruth_attr_key_{i+1}', f'groundtruth_attr_value_{i+1}'])
    
    for i in range(max_attrs):
        columns.extend([
            f'qmeans_attr_key_{i+1}', f'qmeans_attr_value_{i+1}',
            f'gemini_attr_key_{i+1}', f'gemini_attr_value_{i+1}'
        ])
    
    columns.extend(['COUNT_MATCH', 'HIGH_COUNT'])
    
    for i in range(max_attrs):
        columns.extend([f'qmeans_vs_gemini_attr_{i+1}_key_match', f'qmeans_vs_gemini_attr_{i+1}_value_match'])
    
    for i in range(max_attrs):
        columns.extend([f'gemini_vs_qmeans_attr_{i+1}_key_match', f'gemini_vs_qmeans_attr_{i+1}_value_match'])
    
    for i in range(max_attrs):
        columns.extend([f'groundtruth_vs_qmeans_attr_{i+1}_key_match', f'groundtruth_vs_qmeans_attr_{i+1}_value_match'])
    
    for i in range(max_attrs):
        columns.extend([f'groundtruth_vs_gemini_attr_{i+1}_key_match', f'groundtruth_vs_gemini_attr_{i+1}_value_match'])
    
    output_df = pd.DataFrame(output_data, columns=columns)
    
    # Save
    output_file = 'comprehensive_comparison_final.csv'
    output_df.to_csv(output_file, index=False)
    
    print(f'\n✅ Saved to: {output_file}')
    print(f'   Total rows: {len(output_df)}')
    print(f'   Total columns: {len(output_df.columns)}')
    
    # STATISTICS
    print('\n' + '='*80)
    print('STATISTICS')
    print('='*80)
    
    total_gt_attrs = output_df['ground_truth_count'].sum()
    total_qm_attrs = output_df['qmeans_attr_count'].sum()
    total_gm_attrs = output_df['gemini_attr_count'].sum()
    
    print(f'\nTotal Attributes:')
    print(f'   Ground Truth: {total_gt_attrs} ({output_df["ground_truth_count"].mean():.2f} avg per query)')
    print(f'   QMeans: {total_qm_attrs} ({output_df["qmeans_attr_count"].mean():.2f} avg per query)')
    print(f'   Gemini: {total_gm_attrs} ({output_df["gemini_attr_count"].mean():.2f} avg per query)')
    
    # Ground Truth vs QMeans
    print('\n' + '-'*60)
    print('GROUND TRUTH vs QMEANS')
    print('-'*60)
    
    gt_qm_true = 0
    gt_qm_false = 0
    gt_qm_na = 0
    
    for i in range(1, max_attrs + 1):
        col = f'groundtruth_vs_qmeans_attr_{i}_value_match'
        gt_qm_true += (output_df[col] == 'TRUE').sum()
        gt_qm_false += (output_df[col] == 'FALSE').sum()
        gt_qm_na += (output_df[col] == 'NA').sum()
    
    total = gt_qm_true + gt_qm_false + gt_qm_na
    print(f'   Total GT attributes checked: {total}')
    print(f'   TRUE  (key found + value matched):    {gt_qm_true:4d} ({100*gt_qm_true/total:.1f}%)')
    print(f'   FALSE (key found + value different):  {gt_qm_false:4d} ({100*gt_qm_false/total:.1f}%)')
    print(f'   NA    (key NOT found in QMeans):      {gt_qm_na:4d} ({100*gt_qm_na/total:.1f}%)')
    print(f'   Key Found Rate: {100*(gt_qm_true+gt_qm_false)/total:.1f}%')
    
    # Ground Truth vs Gemini
    print('\n' + '-'*60)
    print('GROUND TRUTH vs GEMINI')
    print('-'*60)
    
    gt_gm_true = 0
    gt_gm_false = 0
    gt_gm_na = 0
    
    for i in range(1, max_attrs + 1):
        col = f'groundtruth_vs_gemini_attr_{i}_value_match'
        gt_gm_true += (output_df[col] == 'TRUE').sum()
        gt_gm_false += (output_df[col] == 'FALSE').sum()
        gt_gm_na += (output_df[col] == 'NA').sum()
    
    total2 = gt_gm_true + gt_gm_false + gt_gm_na
    print(f'   Total GT attributes checked: {total2}')
    print(f'   TRUE  (key found + value matched):    {gt_gm_true:4d} ({100*gt_gm_true/total2:.1f}%)')
    print(f'   FALSE (key found + value different):  {gt_gm_false:4d} ({100*gt_gm_false/total2:.1f}%)')
    print(f'   NA    (key NOT found in Gemini):      {gt_gm_na:4d} ({100*gt_gm_na/total2:.1f}%)')
    print(f'   Key Found Rate: {100*(gt_gm_true+gt_gm_false)/total2:.1f}%')
    
    # QMeans vs Gemini
    print('\n' + '-'*60)
    print('QMEANS vs GEMINI')
    print('-'*60)
    
    qm_gm_true = 0
    qm_gm_false = 0
    qm_gm_na = 0
    
    for i in range(1, max_attrs + 1):
        col = f'qmeans_vs_gemini_attr_{i}_value_match'
        qm_gm_true += (output_df[col] == 'TRUE').sum()
        qm_gm_false += (output_df[col] == 'FALSE').sum()
        qm_gm_na += (output_df[col] == 'NA').sum()
    
    total3 = qm_gm_true + qm_gm_false + qm_gm_na
    if total3 > 0:
        print(f'   Total QMeans attributes checked: {total3}')
        print(f'   TRUE  (key found + value matched):    {qm_gm_true:4d} ({100*qm_gm_true/total3:.1f}%)')
        print(f'   FALSE (key found + value different):  {qm_gm_false:4d} ({100*qm_gm_false/total3:.1f}%)')
        print(f'   NA    (key NOT found in Gemini):      {qm_gm_na:4d} ({100*qm_gm_na/total3:.1f}%)')
    
    # Count match stats
    print('\n' + '-'*60)
    print('COUNT MATCH (QMeans vs Gemini)')
    print('-'*60)
    count_true = (output_df['COUNT_MATCH'] == 'TRUE').sum()
    count_false = (output_df['COUNT_MATCH'] == 'FALSE').sum()
    print(f'   Same count: {count_true} ({100*count_true/len(output_df):.1f}%)')
    print(f'   Different count: {count_false} ({100*count_false/len(output_df):.1f}%)')
    
    high_counts = output_df['HIGH_COUNT'].value_counts()
    print(f'\n   Higher attribute count:')
    for val, cnt in high_counts.items():
        print(f'      {val}: {cnt}')
    
    return output_df


if __name__ == '__main__':
    main()
