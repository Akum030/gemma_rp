"""
Calculate metrics for Dataset 2 with Ground Truth
Same format as Dataset 1 analysis
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
    
    # Remove leading/trailing quotes
    while value.startswith('"') or value.startswith("'"):
        value = value[1:]
    while value.endswith('"') or value.endswith("'"):
        value = value[:-1]
    
    value = value.strip().rstrip(',').strip().lower()
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


def parse_gemma_json(json_str):
    """Parse Gemma JSON format"""
    if pd.isna(json_str) or str(json_str).strip() in ['{}', '', 'nan', '[]']:
        return []
    
    try:
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


def calculate_metrics(gt_attrs, model_attrs):
    """Calculate TRUE/FALSE/NA metrics"""
    true_count = 0
    false_count = 0
    na_count = 0
    
    model_dict = {k: v for k, v in model_attrs}
    
    for gt_key, gt_value in gt_attrs:
        if gt_key in model_dict:
            # Key found
            if model_dict[gt_key] == gt_value:
                true_count += 1  # Value matches
            else:
                false_count += 1  # Value different
        else:
            na_count += 1  # Key not found
    
    total = len(gt_attrs)
    
    if total == 0:
        return {
            'total': 0,
            'true': 0,
            'false': 0,
            'na': 0,
            'true_pct': 0,
            'false_pct': 0,
            'na_pct': 0,
            'key_found_rate': 0
        }
    
    return {
        'total': total,
        'true': true_count,
        'false': false_count,
        'na': na_count,
        'true_pct': 100 * true_count / total,
        'false_pct': 100 * false_count / total,
        'na_pct': 100 * na_count / total,
        'key_found_rate': 100 * (true_count + false_count) / total
    }


def main():
    print('='*80)
    print('DATASET 2 METRICS CALCULATION WITH GROUND TRUTH')
    print('='*80)
    
    # Load files
    print('\n1. Loading files...')
    
    try:
        gt_df = pd.read_csv('ground_truth_dataset2.csv')
        print(f'   Ground Truth: {len(gt_df)} rows')
    except FileNotFoundError:
        print('   ERROR: ground_truth_dataset2.csv not found!')
        print('   Please run generate_groundtruth_dataset2.py first')
        return
    
    qm_df = pd.read_csv('qmeans_results.csv')
    gm_df = pd.read_csv('gemini_with_dataset_full.csv')
    gemma_df = pd.read_csv('compare/gemma_v1_validation_results.csv')
    
    print(f'   QMeans: {len(qm_df)} rows')
    print(f'   Gemini: {len(gm_df)} rows')
    print(f'   Gemma: {len(gemma_df)} rows')
    
    # Create lookup
    print('\n2. Creating lookups...')
    qm_lookup = {row['query']: row for _, row in qm_df.iterrows()}
    gm_lookup = {row['query']: row for _, row in gm_df.iterrows()}
    gemma_lookup = {row['query']: row for _, row in gemma_df.iterrows()}
    
    # Calculate metrics
    print('\n3. Calculating metrics...')
    
    qm_metrics = []
    gm_metrics = []
    gemma_metrics = []
    
    qm_attr_counts = []
    gm_attr_counts = []
    gemma_attr_counts = []
    
    for _, gt_row in gt_df.iterrows():
        query = gt_row['query']
        gt_attrs = parse_ground_truth(gt_row)
        
        # QMeans
        if query in qm_lookup:
            qm_attrs = parse_isq_qmeans(qm_lookup[query].get('qmeans_isq_list', '[]'))
            qm_metrics.append(calculate_metrics(gt_attrs, qm_attrs))
            qm_attr_counts.append(len(qm_attrs))
        
        # Gemini
        if query in gm_lookup:
            gm_attrs = parse_isq_gemini(gm_lookup[query].get('gemini_dataset_isq_list', '[]'))
            gm_metrics.append(calculate_metrics(gt_attrs, gm_attrs))
            gm_attr_counts.append(len(gm_attrs))
        
        # Gemma
        if query in gemma_lookup:
            gemma_attrs = parse_gemma_json(gemma_lookup[query].get('normalized_isqs', '{}'))
            gemma_metrics.append(calculate_metrics(gt_attrs, gemma_attrs))
            gemma_attr_counts.append(len(gemma_attrs))
    
    # Aggregate metrics
    def aggregate_metrics(metrics_list):
        total_gt = sum(m['total'] for m in metrics_list)
        total_true = sum(m['true'] for m in metrics_list)
        total_false = sum(m['false'] for m in metrics_list)
        total_na = sum(m['na'] for m in metrics_list)
        
        return {
            'total': total_gt,
            'true': total_true,
            'false': total_false,
            'na': total_na,
            'true_pct': 100 * total_true / total_gt if total_gt > 0 else 0,
            'false_pct': 100 * total_false / total_gt if total_gt > 0 else 0,
            'na_pct': 100 * total_na / total_gt if total_gt > 0 else 0,
            'key_found_rate': 100 * (total_true + total_false) / total_gt if total_gt > 0 else 0
        }
    
    qm_agg = aggregate_metrics(qm_metrics)
    gm_agg = aggregate_metrics(gm_metrics)
    gemma_agg = aggregate_metrics(gemma_metrics)
    
    # Print results
    print('\n' + '='*80)
    print('RESULTS - GROUND TRUTH VS MODELS')
    print('='*80)
    
    print('\n' + '-'*60)
    print('QMEANS vs GROUND TRUTH')
    print('-'*60)
    print(f'  Total GT attributes:          {qm_agg["total"]}')
    print(f'  TRUE  (key + value match):    {qm_agg["true"]:4d} ({qm_agg["true_pct"]:.1f}%)')
    print(f'  FALSE (key found, diff val):  {qm_agg["false"]:4d} ({qm_agg["false_pct"]:.1f}%)')
    print(f'  NA    (key not found):        {qm_agg["na"]:4d} ({qm_agg["na_pct"]:.1f}%)')
    print(f'  Key Found Rate:               {qm_agg["key_found_rate"]:.1f}%')
    print(f'  Avg Attributes/Query:         {sum(qm_attr_counts)/len(qm_attr_counts):.2f}')
    
    print('\n' + '-'*60)
    print('GEMINI vs GROUND TRUTH')
    print('-'*60)
    print(f'  Total GT attributes:          {gm_agg["total"]}')
    print(f'  TRUE  (key + value match):    {gm_agg["true"]:4d} ({gm_agg["true_pct"]:.1f}%)')
    print(f'  FALSE (key found, diff val):  {gm_agg["false"]:4d} ({gm_agg["false_pct"]:.1f}%)')
    print(f'  NA    (key not found):        {gm_agg["na"]:4d} ({gm_agg["na_pct"]:.1f}%)')
    print(f'  Key Found Rate:               {gm_agg["key_found_rate"]:.1f}%')
    print(f'  Avg Attributes/Query:         {sum(gm_attr_counts)/len(gm_attr_counts):.2f}')
    
    print('\n' + '-'*60)
    print('GEMMA vs GROUND TRUTH')
    print('-'*60)
    print(f'  Total GT attributes:          {gemma_agg["total"]}')
    print(f'  TRUE  (key + value match):    {gemma_agg["true"]:4d} ({gemma_agg["true_pct"]:.1f}%)')
    print(f'  FALSE (key found, diff val):  {gemma_agg["false"]:4d} ({gemma_agg["false_pct"]:.1f}%)')
    print(f'  NA    (key not found):        {gemma_agg["na"]:4d} ({gemma_agg["na_pct"]:.1f}%)')
    print(f'  Key Found Rate:               {gemma_agg["key_found_rate"]:.1f}%')
    print(f'  Avg Attributes/Query:         {sum(gemma_attr_counts)/len(gemma_attr_counts):.2f}')
    
    print('\n' + '='*80)
    print('SUMMARY TABLE FOR TEAM PRESENTATION')
    print('='*80)
    print()
    print('| Rank | Model | Key Found | Value Match | Avg Attrs/Query | Verdict |')
    print('|------|-------|-----------|-------------|-----------------|---------|')
    
    # Sort by value match (true_pct)
    models = [
        ('QMeans', qm_agg['key_found_rate'], qm_agg['true_pct'], sum(qm_attr_counts)/len(qm_attr_counts)),
        ('Gemini', gm_agg['key_found_rate'], gm_agg['true_pct'], sum(gm_attr_counts)/len(gm_attr_counts)),
        ('Gemma', gemma_agg['key_found_rate'], gemma_agg['true_pct'], sum(gemma_attr_counts)/len(gemma_attr_counts))
    ]
    
    models_sorted = sorted(models, key=lambda x: x[2], reverse=True)
    
    ranks = ['🥇', '🥈', '🥉']
    verdicts = ['Best accuracy', 'Good baseline', 'Needs improvement']
    
    for i, (name, key_found, value_match, avg_attrs) in enumerate(models_sorted):
        print(f'| {ranks[i]} | **{name}** | {key_found:.1f}% | {value_match:.1f}% | {avg_attrs:.2f} | {verdicts[i]} |')
    
    print()
    print('Extraction Volume Ranking:')
    print()
    print('| Rank | Model | Avg Attributes/Query | Verdict |')
    print('|------|-------|---------------------|---------|')
    
    models_by_volume = sorted(models, key=lambda x: x[3], reverse=True)
    volume_verdicts = ['Most comprehensive', 'Moderate', 'Conservative']
    
    for i, (name, _, _, avg_attrs) in enumerate(models_by_volume):
        print(f'| {ranks[i]} | **{name}** | {avg_attrs:.2f} | {volume_verdicts[i]} |')
    
    print()
    print('='*80)


if __name__ == '__main__':
    main()
