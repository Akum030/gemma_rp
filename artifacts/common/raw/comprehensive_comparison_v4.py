"""
Comprehensive comparison with Ground Truth, QMeans, and Gemini results.
Version 4: Fixed merge issue + value normalization
Saves to NEW file: comprehensive_comparison_v4.csv
"""

import pandas as pd
import re
import ast

def normalize_value(value):
    """
    Normalize a value for consistent storage and comparison.
    """
    if value is None or pd.isna(value):
        return ''
    
    value = str(value).strip()
    
    # Remove leading/trailing quotes (multiple passes)
    while len(value) >= 2 and (
        (value.startswith('"') and value.endswith('"')) or
        (value.startswith("'") and value.endswith("'"))
    ):
        value = value[1:-1].strip()
    
    # Remove leading quotes only
    while value.startswith('"') or value.startswith("'"):
        value = value[1:]
    
    # Remove trailing quotes only
    while value.endswith('"') or value.endswith("'"):
        value = value[:-1]
    
    value = value.strip()
    value = value.rstrip(',').strip()
    value = value.lower()
    value = re.sub(r'\s+', ' ', value)
    
    return value


def parse_isq_qmeans(isq_list_str):
    """Parse QMeans ISQ list format: 'value:key:specification'"""
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
    """Parse Gemini ISQ list format"""
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
    """Parse ground truth attributes from row"""
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
    """Sort attributes alphabetically by key name"""
    return sorted(attr_list, key=lambda x: x[0])


def compare_attrs(source_attrs, target_attrs):
    """
    Compare source attributes against target attributes.
    """
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
    print("=" * 80)
    print("COMPREHENSIVE COMPARISON v4 (Fixed Merge + Normalization)")
    print("=" * 80)
    
    # Load all data sources
    print("\n1. Loading data sources...")
    
    ground_truth_df = pd.read_csv('synthetic_validation_dataset.csv')
    print(f"   Ground Truth: {len(ground_truth_df)} rows")
    
    qmeans_df = pd.read_csv('qmeans_1000_validation.csv')
    print(f"   QMeans: {len(qmeans_df)} rows")
    
    gemini_df = pd.read_csv('gemini_with_dataset_validation_queries.csv')
    print(f"   Gemini: {len(gemini_df)} rows")
    
    # Check for duplicates
    print("\n2. Checking for duplicates...")
    gt_dupes = ground_truth_df['query'].duplicated().sum()
    qm_dupes = qmeans_df['query'].duplicated().sum()
    gm_dupes = gemini_df['query'].duplicated().sum()
    print(f"   Ground Truth duplicates: {gt_dupes}")
    print(f"   QMeans duplicates: {qm_dupes}")
    print(f"   Gemini duplicates: {gm_dupes}")
    
    # Remove duplicates - keep first occurrence
    ground_truth_df = ground_truth_df.drop_duplicates(subset=['query'], keep='first')
    qmeans_df = qmeans_df.drop_duplicates(subset=['query'], keep='first')
    gemini_df = gemini_df.drop_duplicates(subset=['query'], keep='first')
    
    print(f"\n   After dedup - Ground Truth: {len(ground_truth_df)} rows")
    print(f"   After dedup - QMeans: {len(qmeans_df)} rows")
    print(f"   After dedup - Gemini: {len(gemini_df)} rows")
    
    # Use ground truth as base - INNER join to only keep matching queries
    print("\n3. Merging dataframes (using ground truth as base)...")
    
    merged_df = ground_truth_df.merge(
        qmeans_df[['query', 'qmeans_attr_count', 'qmeans_isq_list']],
        on='query', how='inner'
    )
    merged_df = merged_df.merge(
        gemini_df[['query', 'gemini_dataset_attr_count', 'gemini_dataset_isq_list']],
        on='query', how='inner'
    )
    merged_df = merged_df.rename(columns={
        'gemini_dataset_attr_count': 'gemini_attr_count',
        'gemini_dataset_isq_list': 'gemini_isq_list'
    })
    
    print(f"   Merged (inner join): {len(merged_df)} rows")
    
    # Parse and normalize all attributes
    print("\n4. Parsing and normalizing attributes...")
    
    gt_attrs_list = []
    qmeans_attrs_list = []
    gemini_attrs_list = []
    
    for idx, row in merged_df.iterrows():
        gt = parse_ground_truth(row)
        gt = sort_attributes(gt)
        gt_attrs_list.append(gt)
        
        qm = parse_isq_qmeans(row.get('qmeans_isq_list', '[]'))
        qm = sort_attributes(qm)
        qmeans_attrs_list.append(qm)
        
        gm = parse_isq_gemini(row.get('gemini_isq_list', '[]'))
        gm = sort_attributes(gm)
        gemini_attrs_list.append(gm)
    
    max_attrs = 9
    
    # Build output
    print("\n5. Building comprehensive output...")
    output_data = []
    
    for i, (idx, row) in enumerate(merged_df.iterrows()):
        gt = gt_attrs_list[i]
        qm = qmeans_attrs_list[i]
        gm = gemini_attrs_list[i]
        
        qm_count = len(qm)
        gm_count = len(gm)
        gt_count = len(gt)
        
        output_row = {
            'query': row['query'],
            'ground_truth_count': gt_count,
            'qmeans_attr_count': qm_count,
            'gemini_attr_count': gm_count
        }
        
        # Add ground truth attributes
        for j in range(max_attrs):
            if j < len(gt):
                output_row[f'groundtruth_attr_key_{j+1}'] = gt[j][0]
                output_row[f'groundtruth_attr_value_{j+1}'] = gt[j][1]
            else:
                output_row[f'groundtruth_attr_key_{j+1}'] = ''
                output_row[f'groundtruth_attr_value_{j+1}'] = ''
        
        # Add QMeans and Gemini attributes
        for j in range(max_attrs):
            if j < len(qm):
                output_row[f'qmeans_attr_key_{j+1}'] = qm[j][0]
                output_row[f'qmeans_attr_value_{j+1}'] = qm[j][1]
            else:
                output_row[f'qmeans_attr_key_{j+1}'] = ''
                output_row[f'qmeans_attr_value_{j+1}'] = ''
            
            if j < len(gm):
                output_row[f'gemini_attr_key_{j+1}'] = gm[j][0]
                output_row[f'gemini_attr_value_{j+1}'] = gm[j][1]
            else:
                output_row[f'gemini_attr_key_{j+1}'] = ''
                output_row[f'gemini_attr_value_{j+1}'] = ''
        
        # COUNT_MATCH and HIGH_COUNT
        output_row['COUNT_MATCH'] = 'TRUE' if qm_count == gm_count else 'FALSE'
        if qm_count > gm_count:
            output_row['HIGH_COUNT'] = 'qmeans'
        elif gm_count > qm_count:
            output_row['HIGH_COUNT'] = 'gemini'
        else:
            output_row['HIGH_COUNT'] = 'same'
        
        # Comparison: QMeans vs Gemini
        qm_vs_gm = compare_attrs(qm, gm)
        for j in range(max_attrs):
            if j < len(qm_vs_gm):
                key_match, val_match = qm_vs_gm[j]
                output_row[f'qmeans_vs_gemini_attr_{j+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                if val_match is None:
                    output_row[f'qmeans_vs_gemini_attr_{j+1}_value_match'] = 'NA'
                else:
                    output_row[f'qmeans_vs_gemini_attr_{j+1}_value_match'] = 'TRUE' if val_match else 'FALSE'
            else:
                output_row[f'qmeans_vs_gemini_attr_{j+1}_key_match'] = ''
                output_row[f'qmeans_vs_gemini_attr_{j+1}_value_match'] = ''
        
        # Comparison: Gemini vs QMeans
        gm_vs_qm = compare_attrs(gm, qm)
        for j in range(max_attrs):
            if j < len(gm_vs_qm):
                key_match, val_match = gm_vs_qm[j]
                output_row[f'gemini_vs_qmeans_attr_{j+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                if val_match is None:
                    output_row[f'gemini_vs_qmeans_attr_{j+1}_value_match'] = 'NA'
                else:
                    output_row[f'gemini_vs_qmeans_attr_{j+1}_value_match'] = 'TRUE' if val_match else 'FALSE'
            else:
                output_row[f'gemini_vs_qmeans_attr_{j+1}_key_match'] = ''
                output_row[f'gemini_vs_qmeans_attr_{j+1}_value_match'] = ''
        
        # Comparison: Ground Truth vs QMeans
        gt_vs_qm = compare_attrs(gt, qm)
        for j in range(max_attrs):
            if j < len(gt_vs_qm):
                key_match, val_match = gt_vs_qm[j]
                output_row[f'groundtruth_vs_qmeans_attr_{j+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                if val_match is None:
                    output_row[f'groundtruth_vs_qmeans_attr_{j+1}_value_match'] = 'NA'
                else:
                    output_row[f'groundtruth_vs_qmeans_attr_{j+1}_value_match'] = 'TRUE' if val_match else 'FALSE'
            else:
                output_row[f'groundtruth_vs_qmeans_attr_{j+1}_key_match'] = ''
                output_row[f'groundtruth_vs_qmeans_attr_{j+1}_value_match'] = ''
        
        # Comparison: Ground Truth vs Gemini
        gt_vs_gm = compare_attrs(gt, gm)
        for j in range(max_attrs):
            if j < len(gt_vs_gm):
                key_match, val_match = gt_vs_gm[j]
                output_row[f'groundtruth_vs_gemini_attr_{j+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                if val_match is None:
                    output_row[f'groundtruth_vs_gemini_attr_{j+1}_value_match'] = 'NA'
                else:
                    output_row[f'groundtruth_vs_gemini_attr_{j+1}_value_match'] = 'TRUE' if val_match else 'FALSE'
            else:
                output_row[f'groundtruth_vs_gemini_attr_{j+1}_key_match'] = ''
                output_row[f'groundtruth_vs_gemini_attr_{j+1}_value_match'] = ''
        
        output_data.append(output_row)
    
    # Create column order
    columns = ['query', 'ground_truth_count', 'qmeans_attr_count', 'gemini_attr_count']
    
    for j in range(max_attrs):
        columns.extend([f'groundtruth_attr_key_{j+1}', f'groundtruth_attr_value_{j+1}'])
    
    for j in range(max_attrs):
        columns.extend([
            f'qmeans_attr_key_{j+1}', f'qmeans_attr_value_{j+1}',
            f'gemini_attr_key_{j+1}', f'gemini_attr_value_{j+1}'
        ])
    
    columns.extend(['COUNT_MATCH', 'HIGH_COUNT'])
    
    for j in range(max_attrs):
        columns.extend([
            f'qmeans_vs_gemini_attr_{j+1}_key_match', f'qmeans_vs_gemini_attr_{j+1}_value_match'
        ])
    
    for j in range(max_attrs):
        columns.extend([
            f'gemini_vs_qmeans_attr_{j+1}_key_match', f'gemini_vs_qmeans_attr_{j+1}_value_match'
        ])
    
    for j in range(max_attrs):
        columns.extend([
            f'groundtruth_vs_qmeans_attr_{j+1}_key_match', f'groundtruth_vs_qmeans_attr_{j+1}_value_match'
        ])
    
    for j in range(max_attrs):
        columns.extend([
            f'groundtruth_vs_gemini_attr_{j+1}_key_match', f'groundtruth_vs_gemini_attr_{j+1}_value_match'
        ])
    
    output_df = pd.DataFrame(output_data, columns=columns)
    
    # Save to NEW file
    output_file = 'comprehensive_comparison_v4.csv'
    output_df.to_csv(output_file, index=False)
    print(f"\n✅ Saved to: {output_file}")
    
    # Statistics
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    print(f"Total queries: {len(output_df)}")
    print(f"Total columns: {len(output_df.columns)}")
    print(f"\nAttribute counts:")
    print(f"  Ground Truth avg: {output_df['ground_truth_count'].mean():.2f}")
    print(f"  QMeans avg: {output_df['qmeans_attr_count'].mean():.2f}")
    print(f"  Gemini avg: {output_df['gemini_attr_count'].mean():.2f}")
    
    # Ground Truth vs QMeans - detailed stats
    print("\n" + "=" * 80)
    print("GROUND TRUTH vs QMEANS - VALUE MATCH STATS")
    print("=" * 80)
    
    gt_qm_true = 0
    gt_qm_false = 0
    gt_qm_na = 0
    
    for j in range(1, max_attrs + 1):
        col = f'groundtruth_vs_qmeans_attr_{j}_value_match'
        if col in output_df.columns:
            gt_qm_true += (output_df[col] == 'TRUE').sum()
            gt_qm_false += (output_df[col] == 'FALSE').sum()
            gt_qm_na += (output_df[col] == 'NA').sum()
    
    total_gt_attrs = gt_qm_true + gt_qm_false + gt_qm_na
    print(f"  Total ground truth attributes: {total_gt_attrs}")
    print(f"  TRUE (key found, value matched): {gt_qm_true} ({100*gt_qm_true/total_gt_attrs:.1f}%)")
    print(f"  FALSE (key found, value different): {gt_qm_false} ({100*gt_qm_false/total_gt_attrs:.1f}%)")
    print(f"  NA (key not found in QMeans): {gt_qm_na} ({100*gt_qm_na/total_gt_attrs:.1f}%)")
    
    # Ground Truth vs Gemini - detailed stats
    print("\n" + "=" * 80)
    print("GROUND TRUTH vs GEMINI - VALUE MATCH STATS")
    print("=" * 80)
    
    gt_gm_true = 0
    gt_gm_false = 0
    gt_gm_na = 0
    
    for j in range(1, max_attrs + 1):
        col = f'groundtruth_vs_gemini_attr_{j}_value_match'
        if col in output_df.columns:
            gt_gm_true += (output_df[col] == 'TRUE').sum()
            gt_gm_false += (output_df[col] == 'FALSE').sum()
            gt_gm_na += (output_df[col] == 'NA').sum()
    
    total_gt_attrs2 = gt_gm_true + gt_gm_false + gt_gm_na
    print(f"  Total ground truth attributes: {total_gt_attrs2}")
    print(f"  TRUE (key found, value matched): {gt_gm_true} ({100*gt_gm_true/total_gt_attrs2:.1f}%)")
    print(f"  FALSE (key found, value different): {gt_gm_false} ({100*gt_gm_false/total_gt_attrs2:.1f}%)")
    print(f"  NA (key not found in Gemini): {gt_gm_na} ({100*gt_gm_na/total_gt_attrs2:.1f}%)")
    
    # QMeans vs Gemini stats
    print("\n" + "=" * 80)
    print("QMEANS vs GEMINI - VALUE MATCH STATS")
    print("=" * 80)
    
    qm_gm_true = 0
    qm_gm_false = 0
    qm_gm_na = 0
    
    for j in range(1, max_attrs + 1):
        col = f'qmeans_vs_gemini_attr_{j}_value_match'
        if col in output_df.columns:
            qm_gm_true += (output_df[col] == 'TRUE').sum()
            qm_gm_false += (output_df[col] == 'FALSE').sum()
            qm_gm_na += (output_df[col] == 'NA').sum()
    
    total_qm_attrs = qm_gm_true + qm_gm_false + qm_gm_na
    if total_qm_attrs > 0:
        print(f"  Total QMeans attributes: {total_qm_attrs}")
        print(f"  TRUE (key found, value matched): {qm_gm_true} ({100*qm_gm_true/total_qm_attrs:.1f}%)")
        print(f"  FALSE (key found, value different): {qm_gm_false} ({100*qm_gm_false/total_qm_attrs:.1f}%)")
        print(f"  NA (key not found in Gemini): {qm_gm_na} ({100*qm_gm_na/total_qm_attrs:.1f}%)")
    
    return output_df


if __name__ == "__main__":
    main()
