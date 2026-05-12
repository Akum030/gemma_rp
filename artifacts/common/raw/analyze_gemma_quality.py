"""
Analyze Gemma quality with concrete examples
"""
import pandas as pd
import json
import ast

# Load data
qm = pd.read_csv('qmeans_results.csv').head(20)
gemma = pd.read_csv('compare/gemma_v1_validation_results.csv').head(20)

print('='*80)
print('GEMMA QUALITY ANALYSIS - CONCRETE EXAMPLES')
print('='*80)

for idx in range(10):
    query = qm.iloc[idx]['query']
    
    # Parse QMeans
    try:
        qm_isq = ast.literal_eval(qm.iloc[idx]['qmeans_isq_list'])
        qm_attrs = {}
        for item in qm_isq:
            parts = item.split(':')
            if len(parts) >= 2:
                qm_attrs[parts[1].strip().lower()] = parts[0].strip().lower()
    except:
        qm_attrs = {}
    
    # Parse Gemma
    try:
        gemma_json = json.loads(gemma.iloc[idx]['normalized_isqs'].replace("'", '"'))
        gemma_attrs = {k.lower(): v.lower() for k, v in gemma_json.items()}
    except:
        gemma_attrs = {}
    
    if len(gemma_attrs) > 0:
        print(f'\n{"="*80}')
        print(f'EXAMPLE {idx+1}')
        print(f'{"="*80}')
        print(f'Query: "{query}"')
        print()
        
        print(f'QMeans extracted ({len(qm_attrs)} attrs):')
        for k, v in qm_attrs.items():
            print(f'  {k}: {v}')
        
        print()
        print(f'Gemma extracted ({len(gemma_attrs)} attrs):')
        for k, v in gemma_attrs.items():
            print(f'  {k}: {v}')
        
        print()
        print('Analysis:')
        
        # Check if Gemma values are present in query
        query_lower = query.lower()
        valid_values = 0
        hallucinated = 0
        
        for k, v in gemma_attrs.items():
            # Check if value appears in query
            if v in query_lower or any(word in query_lower for word in v.split()):
                valid_values += 1
                print(f'  ✓ "{v}" - FOUND in query (key: {k})')
            else:
                hallucinated += 1
                print(f'  ✗ "{v}" - NOT in query (key: {k}) - POSSIBLE HALLUCINATION')
        
        # Key comparison
        common_keys = set(qm_attrs.keys()) & set(gemma_attrs.keys())
        if common_keys:
            print(f'\n  Common keys: {common_keys}')
            for key in common_keys:
                if qm_attrs[key] == gemma_attrs[key]:
                    print(f'    ✓ {key}: EXACT MATCH')
                else:
                    print(f'    ≈ {key}: QMeans="{qm_attrs[key]}" vs Gemma="{gemma_attrs[key]}"')
        else:
            print(f'\n  ✗ NO COMMON KEYS between QMeans and Gemma')
        
        print(f'\n  Verdict: {valid_values}/{len(gemma_attrs)} values are valid, {hallucinated} may be hallucinated')

print('\n' + '='*80)
print('SUMMARY')
print('='*80)
