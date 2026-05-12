"""
Merge and format QMeans and Gemini results into a single comparison file
with attributes sorted alphabetically by key name.
"""

import pandas as pd
import re
import ast

def parse_isq_qmeans(isq_list_str):
    """Parse QMeans ISQ list format: 'value:key:specification'"""
    if pd.isna(isq_list_str) or isq_list_str == '[]':
        return []
    
    try:
        # Try to parse as Python list
        items = ast.literal_eval(isq_list_str)
        result = []
        for item in items:
            item = item.strip().strip('"').strip("'")
            parts = item.split(':')
            if len(parts) >= 2:
                value = parts[0].strip()
                key = parts[1].strip()
                result.append((key, value))
        return result
    except:
        return []

def parse_isq_gemini(isq_list_str):
    """Parse Gemini ISQ list format: '["value:key:specification", ...]'"""
    if pd.isna(isq_list_str) or isq_list_str == '[]':
        return []
    
    try:
        # Clean up the string
        clean_str = isq_list_str.replace('[', '').replace(']', '')
        clean_str = clean_str.replace('""', '"').replace("''", "'")
        
        # Split by common delimiters
        items = re.split(r"['\"],\s*['\"]", clean_str)
        
        result = []
        for item in items:
            item = item.strip().strip('"').strip("'").strip('[').strip(']')
            if ':' in item:
                parts = item.split(':')
                if len(parts) >= 2:
                    value = parts[0].strip()
                    key = parts[1].strip()
                    result.append((key, value))
        return result
    except:
        return []

def sort_attributes(attr_list):
    """Sort attributes alphabetically by key name"""
    return sorted(attr_list, key=lambda x: x[0].lower())

def main():
    print("Loading QMeans results...")
    qmeans_df = pd.read_csv('qmeans_1000_validation.csv')
    print(f"  Loaded {len(qmeans_df)} rows")
    
    print("Loading Gemini results...")
    gemini_df = pd.read_csv('gemini_with_dataset_validation_queries.csv')
    print(f"  Loaded {len(gemini_df)} rows")
    
    # Merge on query
    print("\nMerging dataframes...")
    merged_df = pd.merge(
        qmeans_df[['query', 'qmeans_attr_count', 'qmeans_isq_list']],
        gemini_df[['query', 'gemini_dataset_attr_count', 'gemini_dataset_isq_list']],
        on='query',
        how='outer'
    )
    print(f"  Merged: {len(merged_df)} rows")
    
    # Rename columns
    merged_df = merged_df.rename(columns={
        'gemini_dataset_attr_count': 'gemini_attr_count',
        'gemini_dataset_isq_list': 'gemini_isq_list'
    })
    
    # Fill NaN counts with 0
    merged_df['qmeans_attr_count'] = merged_df['qmeans_attr_count'].fillna(0).astype(int)
    merged_df['gemini_attr_count'] = merged_df['gemini_attr_count'].fillna(0).astype(int)
    
    # Parse and sort attributes
    print("\nParsing and sorting attributes...")
    qmeans_attrs = []
    gemini_attrs = []
    
    for idx, row in merged_df.iterrows():
        # Parse QMeans
        q_attrs = parse_isq_qmeans(row.get('qmeans_isq_list', '[]'))
        q_attrs = sort_attributes(q_attrs)
        qmeans_attrs.append(q_attrs)
        
        # Parse Gemini
        g_attrs = parse_isq_gemini(row.get('gemini_isq_list', '[]'))
        g_attrs = sort_attributes(g_attrs)
        gemini_attrs.append(g_attrs)
    
    # Find max attributes count
    max_attrs = max(
        max(len(a) for a in qmeans_attrs),
        max(len(a) for a in gemini_attrs)
    )
    print(f"  Max attributes per query: {max_attrs}")
    
    # Build output dataframe
    print("\nBuilding formatted output...")
    output_data = []
    
    for idx, row in merged_df.iterrows():
        q_attrs = qmeans_attrs[idx]
        g_attrs = gemini_attrs[idx]
        
        output_row = {
            'query': row['query'],
            'qmeans_attr_count': row['qmeans_attr_count'],
            'gemini_attr_count': row['gemini_attr_count']
        }
        
        # Add attribute columns (sorted alphabetically)
        for i in range(max_attrs):
            # QMeans attributes
            if i < len(q_attrs):
                output_row[f'qmeans_attr_key_{i+1}'] = q_attrs[i][0]
                output_row[f'qmeans_attr_value_{i+1}'] = q_attrs[i][1]
            else:
                output_row[f'qmeans_attr_key_{i+1}'] = ''
                output_row[f'qmeans_attr_value_{i+1}'] = ''
            
            # Gemini attributes
            if i < len(g_attrs):
                output_row[f'gemini_attr_key_{i+1}'] = g_attrs[i][0]
                output_row[f'gemini_attr_value_{i+1}'] = g_attrs[i][1]
            else:
                output_row[f'gemini_attr_key_{i+1}'] = ''
                output_row[f'gemini_attr_value_{i+1}'] = ''
        
        output_data.append(output_row)
    
    # Create ordered column list
    columns = ['query', 'qmeans_attr_count', 'gemini_attr_count']
    for i in range(max_attrs):
        columns.extend([
            f'qmeans_attr_key_{i+1}', f'qmeans_attr_value_{i+1}',
            f'gemini_attr_key_{i+1}', f'gemini_attr_value_{i+1}'
        ])
    
    output_df = pd.DataFrame(output_data, columns=columns)
    
    # Save to CSV
    output_file = 'formatted_comparison_results.csv'
    output_df.to_csv(output_file, index=False)
    print(f"\n✅ Saved to: {output_file}")
    
    # Print sample
    print("\n" + "=" * 100)
    print("SAMPLE OUTPUT (First 5 rows):")
    print("=" * 100)
    print(output_df.head().to_string())
    
    # Print column names
    print("\n" + "=" * 100)
    print("COLUMN STRUCTURE:")
    print("=" * 100)
    for col in columns:
        print(f"  {col}")
    
    # Print stats
    print("\n" + "=" * 100)
    print("STATISTICS:")
    print("=" * 100)
    print(f"Total queries: {len(output_df)}")
    print(f"QMeans avg attributes: {output_df['qmeans_attr_count'].mean():.2f}")
    print(f"Gemini avg attributes: {output_df['gemini_attr_count'].mean():.2f}")
    
    return output_df

if __name__ == "__main__":
    main()
