"""
Comprehensive comparison with Ground Truth, QMeans, and Gemini results.
Version 3: Added value normalization to fix quote, space, and case issues.
"""

import pandas as pd
import re
import ast

def normalize_value(value):
    """
    Normalize a value for consistent storage and comparison.
    - Trim whitespace
    - Remove unnecessary quotes (single and double) from start/end
    - Convert to lowercase
    - Handle common edge cases
    """
    if value is None or pd.isna(value):
        return ''
    
    # Convert to string
    value = str(value)
    
    # Strip whitespace
    value = value.strip()
    
    # Remove leading/trailing quotes (multiple passes for nested quotes)
    while len(value) >= 2 and (
        (value.startswith('"') and value.endswith('"')) or
        (value.startswith("'") and value.endswith("'"))
    ):
        value = value[1:-1].strip()
    
    # Remove leading quotes only (like """automatic" -> automatic)
    while value.startswith('"') or value.startswith("'"):
        value = value[1:]
    
    # Remove trailing quotes only
    while value.endswith('"') or value.endswith("'"):
        value = value[:-1]
    
    # Strip again after quote removal
    value = value.strip()
    
    # Remove trailing commas (e.g., "1 ton," -> "1 ton")
    value = value.rstrip(',').strip()
    
    # Convert to lowercase
    value = value.lower()
    
    # Normalize multiple spaces to single space
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
                if key:  # Only add if key is not empty
                    result.append((key, value))
        return result
    except:
        return []


def parse_isq_gemini(isq_list_str):
    """Parse Gemini ISQ list format: '["value:key:specification", ...]'"""
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
                    if key:  # Only add if key is not empty
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
    """Sort attributes alphabetically by key name (already lowercase)"""
    return sorted(attr_list, key=lambda x: x[0])


def compare_attrs(source_attrs, target_attrs):
    """
    Compare source attributes against target attributes.
    For each source attribute, check if target has matching key.
    If key matches, check if value matches.
    Returns list of (key_match, value_match) for each source attr.
    Values are already normalized (lowercase, no extra quotes/spaces).
    """
    target_dict = {k: v for k, v in target_attrs}
    results = []
    
    for key, value in source_attrs:
        if key in target_dict:
            key_match = True
            value_match = (value == target_dict[key])
        else:
            key_match = False
            value_match = None  # NA - key not found
        results.append((key_match, value_match))
    
    return results


def main():
    print("=" * 80)
    print("COMPREHENSIVE COMPARISON v3 (With Value Normalization)")
    print("=" * 80)
    
    # Load all data sources
    print("\n1. Loading data sources...")
    
    ground_truth_df = pd.read_csv('synthetic_validation_dataset.csv')
    print(f"   Ground Truth: {len(ground_truth_df)} rows")
    
    qmeans_df = pd.read_csv('qmeans_1000_validation.csv')
    print(f"   QMeans: {len(qmeans_df)} rows")
    
    gemini_df = pd.read_csv('gemini_with_dataset_validation_queries.csv')
    print(f"   Gemini: {len(gemini_df)} rows")
    
    # Merge all three
    print("\n2. Merging dataframes on query...")
    
    merged_df = ground_truth_df.merge(
        qmeans_df[['query', 'qmeans_attr_count', 'qmeans_isq_list']],
        on='query', how='left'
    )
    merged_df = merged_df.merge(
        gemini_df[['query', 'gemini_dataset_attr_count', 'gemini_dataset_isq_list']],
        on='query', how='left'
    )
    merged_df = merged_df.rename(columns={
        'gemini_dataset_attr_count': 'gemini_attr_count',
        'gemini_dataset_isq_list': 'gemini_isq_list'
    })
    
    print(f"   Merged: {len(merged_df)} rows")
    
    # Parse and normalize all attributes
    print("\n3. Parsing and normalizing attributes...")
    
    gt_attrs_list = []
    qmeans_attrs_list = []
    gemini_attrs_list = []
    
    for idx, row in merged_df.iterrows():
        # Ground truth
        gt = parse_ground_truth(row)
        gt = sort_attributes(gt)
        gt_attrs_list.append(gt)
        
        # QMeans
        qm = parse_isq_qmeans(row.get('qmeans_isq_list', '[]'))
        qm = sort_attributes(qm)
        qmeans_attrs_list.append(qm)
        
        # Gemini
        gm = parse_isq_gemini(row.get('gemini_isq_list', '[]'))
        gm = sort_attributes(gm)
        gemini_attrs_list.append(gm)
    
    # Calculate ground truth counts (based on actual parsed attrs)
    gt_counts = [len(a) for a in gt_attrs_list]
    
    max_attrs = 9  # Fixed to 9 for consistency
    
    # Build output
    print("\n4. Building comprehensive output...")
    output_data = []
    
    for idx, row in merged_df.iterrows():
        gt = gt_attrs_list[idx]
        qm = qmeans_attrs_list[idx]
        gm = gemini_attrs_list[idx]
        
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
        for i in range(max_attrs):
            if i < len(gt):
                output_row[f'groundtruth_attr_key_{i+1}'] = gt[i][0]
                output_row[f'groundtruth_attr_value_{i+1}'] = gt[i][1]
            else:
                output_row[f'groundtruth_attr_key_{i+1}'] = ''
                output_row[f'groundtruth_attr_value_{i+1}'] = ''
        
        # Add QMeans and Gemini attributes (interleaved)
        for i in range(max_attrs):
            if i < len(qm):
                output_row[f'qmeans_attr_key_{i+1}'] = qm[i][0]
                output_row[f'qmeans_attr_value_{i+1}'] = qm[i][1]
            else:
                output_row[f'qmeans_attr_key_{i+1}'] = ''
                output_row[f'qmeans_attr_value_{i+1}'] = ''
            
            if i < len(gm):
                output_row[f'gemini_attr_key_{i+1}'] = gm[i][0]
                output_row[f'gemini_attr_value_{i+1}'] = gm[i][1]
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
        
        # Comparison: QMeans vs Gemini
        qm_vs_gm = compare_attrs(qm, gm)
        for i in range(max_attrs):
            if i < len(qm_vs_gm):
                key_match, val_match = qm_vs_gm[i]
                output_row[f'qmeans_vs_gemini_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                if val_match is None:
                    output_row[f'qmeans_vs_gemini_attr_{i+1}_value_match'] = 'NA'
                else:
                    output_row[f'qmeans_vs_gemini_attr_{i+1}_value_match'] = 'TRUE' if val_match else 'FALSE'
            else:
                output_row[f'qmeans_vs_gemini_attr_{i+1}_key_match'] = ''
                output_row[f'qmeans_vs_gemini_attr_{i+1}_value_match'] = ''
        
        # Comparison: Gemini vs QMeans
        gm_vs_qm = compare_attrs(gm, qm)
        for i in range(max_attrs):
            if i < len(gm_vs_qm):
                key_match, val_match = gm_vs_qm[i]
                output_row[f'gemini_vs_qmeans_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                if val_match is None:
                    output_row[f'gemini_vs_qmeans_attr_{i+1}_value_match'] = 'NA'
                else:
                    output_row[f'gemini_vs_qmeans_attr_{i+1}_value_match'] = 'TRUE' if val_match else 'FALSE'
            else:
                output_row[f'gemini_vs_qmeans_attr_{i+1}_key_match'] = ''
                output_row[f'gemini_vs_qmeans_attr_{i+1}_value_match'] = ''
        
        # Comparison: Ground Truth vs QMeans
        gt_vs_qm = compare_attrs(gt, qm)
        for i in range(max_attrs):
            if i < len(gt_vs_qm):
                key_match, val_match = gt_vs_qm[i]
                output_row[f'groundtruth_vs_qmeans_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                if val_match is None:
                    output_row[f'groundtruth_vs_qmeans_attr_{i+1}_value_match'] = 'NA'
                else:
                    output_row[f'groundtruth_vs_qmeans_attr_{i+1}_value_match'] = 'TRUE' if val_match else 'FALSE'
            else:
                output_row[f'groundtruth_vs_qmeans_attr_{i+1}_key_match'] = ''
                output_row[f'groundtruth_vs_qmeans_attr_{i+1}_value_match'] = ''
        
        # Comparison: Ground Truth vs Gemini
        gt_vs_gm = compare_attrs(gt, gm)
        for i in range(max_attrs):
            if i < len(gt_vs_gm):
                key_match, val_match = gt_vs_gm[i]
                output_row[f'groundtruth_vs_gemini_attr_{i+1}_key_match'] = 'TRUE' if key_match else 'FALSE'
                if val_match is None:
                    output_row[f'groundtruth_vs_gemini_attr_{i+1}_value_match'] = 'NA'
                else:
                    output_row[f'groundtruth_vs_gemini_attr_{i+1}_value_match'] = 'TRUE' if val_match else 'FALSE'
            else:
                output_row[f'groundtruth_vs_gemini_attr_{i+1}_key_match'] = ''
                output_row[f'groundtruth_vs_gemini_attr_{i+1}_value_match'] = ''
        
        output_data.append(output_row)
    
    # Create column order
    columns = ['query', 'ground_truth_count', 'qmeans_attr_count', 'gemini_attr_count']
    
    # Ground truth columns
    for i in range(max_attrs):
        columns.extend([f'groundtruth_attr_key_{i+1}', f'groundtruth_attr_value_{i+1}'])
    
    # QMeans and Gemini interleaved
    for i in range(max_attrs):
        columns.extend([
            f'qmeans_attr_key_{i+1}', f'qmeans_attr_value_{i+1}',
            f'gemini_attr_key_{i+1}', f'gemini_attr_value_{i+1}'
        ])
    
    # Comparison columns
    columns.extend(['COUNT_MATCH', 'HIGH_COUNT'])
    
    for i in range(max_attrs):
        columns.extend([
            f'qmeans_vs_gemini_attr_{i+1}_key_match', f'qmeans_vs_gemini_attr_{i+1}_value_match'
        ])
    
    for i in range(max_attrs):
        columns.extend([
            f'gemini_vs_qmeans_attr_{i+1}_key_match', f'gemini_vs_qmeans_attr_{i+1}_value_match'
        ])
    
    for i in range(max_attrs):
        columns.extend([
            f'groundtruth_vs_qmeans_attr_{i+1}_key_match', f'groundtruth_vs_qmeans_attr_{i+1}_value_match'
        ])
    
    for i in range(max_attrs):
        columns.extend([
            f'groundtruth_vs_gemini_attr_{i+1}_key_match', f'groundtruth_vs_gemini_attr_{i+1}_value_match'
        ])
    
    output_df = pd.DataFrame(output_data, columns=columns)
    
    # Save
    output_file = 'comprehensive_comparison_results.csv'
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
    
    # Count match stats
    count_match_true = (output_df['COUNT_MATCH'] == 'TRUE').sum()
    count_match_false = (output_df['COUNT_MATCH'] == 'FALSE').sum()
    print(f"\nCount match (QMeans vs Gemini):")
    print(f"  TRUE: {count_match_true}, FALSE: {count_match_false}")
    
    high_count_stats = output_df['HIGH_COUNT'].value_counts()
    print(f"\nHigher count:")
    for val, cnt in high_count_stats.items():
        print(f"  {val}: {cnt}")
    
    # Value match statistics for QMeans vs Gemini
    print("\n" + "=" * 80)
    print("VALUE MATCH STATISTICS (QMeans vs Gemini)")
    print("=" * 80)
    
    total_true = 0
    total_false = 0
    total_na = 0
    
    for i in range(1, max_attrs + 1):
        col = f'qmeans_vs_gemini_attr_{i}_value_match'
        if col in output_df.columns:
            true_count = (output_df[col] == 'TRUE').sum()
            false_count = (output_df[col] == 'FALSE').sum()
            na_count = (output_df[col] == 'NA').sum()
            total_true += true_count
            total_false += false_count
            total_na += na_count
    
    print(f"  Total TRUE matches: {total_true}")
    print(f"  Total FALSE matches: {total_false}")
    print(f"  Total NA (key not found): {total_na}")
    
    # Sample with normalization demonstration
    print("\n" + "=" * 80)
    print("SAMPLE OUTPUT (First 3 rows - normalized values)")
    print("=" * 80)
    sample_cols = ['query', 'qmeans_attr_key_1', 'qmeans_attr_value_1', 
                   'gemini_attr_key_1', 'gemini_attr_value_1',
                   'qmeans_vs_gemini_attr_1_key_match', 'qmeans_vs_gemini_attr_1_value_match']
    print(output_df[sample_cols].head(3).to_string())
    
    return output_df


if __name__ == "__main__":
    main()
