"""
Show what was actually compared - parsed data, not raw strings
"""
import pandas as pd
import json
import ast

# Load first 3 rows
qm = pd.read_csv('qmeans_results.csv').head(3)
gemma = pd.read_csv('compare/gemma_v1_validation_results.csv').head(3)

for idx in range(3):
    print('='*80)
    print(f'SAMPLE {idx+1}')
    print('='*80)
    print(f'Query: {qm.iloc[idx]["query"]}')
    print()
    
    # Show raw formats
    print('RAW FORMATS (NOT compared):')
    print('-'*80)
    print(f'QMeans raw: {qm.iloc[idx]["qmeans_isq_list"]}')
    print(f'Gemma raw:  {gemma.iloc[idx]["normalized_isqs"]}')
    print()
    
    # Parse QMeans
    print('PARSED FORMATS (ACTUALLY compared):')
    print('-'*80)
    try:
        qm_isq = ast.literal_eval(qm.iloc[idx]['qmeans_isq_list'])
        print('QMeans parsed tuples (key, value):')
        for item in qm_isq:
            parts = item.split(':')
            if len(parts) >= 2:
                key = parts[1].strip().lower()
                value = parts[0].strip().lower()
                print(f'  ("{key}", "{value}")')
    except:
        print('  (empty)')
    print()
    
    # Parse Gemma
    try:
        gemma_json = json.loads(gemma.iloc[idx]['normalized_isqs'].replace("'", '"'))
        print('Gemma parsed tuples (key, value):')
        for k, v in gemma_json.items():
            key = k.strip().lower()
            value = v.strip().lower()
            print(f'  ("{key}", "{value}")')
    except:
        print('  (empty)')
    print()
    
    # Show if keys match
    try:
        qm_isq = ast.literal_eval(qm.iloc[idx]['qmeans_isq_list'])
        qm_keys = set([item.split(':')[1].strip().lower() for item in qm_isq if len(item.split(':')) >= 2])
        
        gemma_json = json.loads(gemma.iloc[idx]['normalized_isqs'].replace("'", '"'))
        gemma_keys = set([k.strip().lower() for k in gemma_json.keys()])
        
        common = qm_keys & gemma_keys
        
        print('KEY COMPARISON:')
        print(f'  QMeans keys: {qm_keys}')
        print(f'  Gemma keys:  {gemma_keys}')
        print(f'  Common keys: {common if common else "(NONE)"}')
        print(f'  Overlap:     {len(common)}/{max(len(qm_keys), len(gemma_keys))} keys match')
    except:
        print('KEY COMPARISON: Error parsing')
    
    print()
