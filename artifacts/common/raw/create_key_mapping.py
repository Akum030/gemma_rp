"""
Step 1: Analyze all Gemma keys and create mapping to QMeans keys
"""
import pandas as pd
import json
import ast
from collections import Counter

print('Analyzing all keys from both models...\n')

# Load data
qm_df = pd.read_csv('qmeans_results.csv')
gemma_df = pd.read_csv('compare/gemma_v1_validation_results.csv')

# Collect all keys
qmeans_keys = Counter()
gemma_keys = Counter()

for _, row in qm_df.iterrows():
    try:
        isq_list = ast.literal_eval(row['qmeans_isq_list'])
        for item in isq_list:
            parts = item.split(':')
            if len(parts) >= 2:
                key = parts[1].strip().lower()
                qmeans_keys[key] += 1
    except:
        pass

for _, row in gemma_df.iterrows():
    try:
        attrs = json.loads(row['normalized_isqs'].replace("'", '"'))
        for key in attrs.keys():
            gemma_keys[key.lower()] += 1
    except:
        pass

print('='*80)
print('TOP QMEANS KEYS')
print('='*80)
for key, count in qmeans_keys.most_common(20):
    print(f'{key:30s} : {count:4d} occurrences')

print('\n' + '='*80)
print('TOP GEMMA KEYS')
print('='*80)
for key, count in gemma_keys.most_common(20):
    print(f'{key:30s} : {count:4d} occurrences')

print('\n' + '='*80)
print('SUGGESTED KEY MAPPING (Gemma → QMeans)')
print('='*80)

# Create mapping based on semantic similarity
mapping = {
    # Common mappings
    'type': 'type',
    'machine_type': 'type',
    'extractor_type': 'product',
    'design_type': 'usage',
    
    'material': 'material',
    'machine_material': 'material',
    'material_to_be_extruded': 'material',
    
    'usage': 'usage',
    'industry_type': 'usage',
    'application_usage': 'usage',
    
    'brand': 'brand',
    'make': 'brand',
    
    'capacity': 'capacity',
    'production_capacity': 'capacity',
    'packaging_size': 'capacity',
    
    'voltage': 'voltage',
    'voltage_v': 'voltage',
    'voltage_volt': 'voltage',
    'power_supply': 'voltage',
    
    'automation_grade': 'automation grade',
    'automatic_grade': 'automation grade',
    'autoamatic_grade': 'automation grade',
    'control_panel': 'automation grade',
    
    'power_source': 'power source',
    'charger': 'power source',
    
    'form': 'form',
    'shape': 'form',
    
    'location': 'location',
    'service_type': 'service type',
    
    'screw_design': 'screw design',
    'screw_type': 'screw type',
    
    'layer': 'layer',
    'phase': 'phase',
    'model_name/number': 'model name/number',
}

for gemma_key, qmeans_key in sorted(mapping.items()):
    print(f'{gemma_key:30s} → {qmeans_key}')

# Save mapping to file
import json
with open('gemma_to_qmeans_key_mapping.json', 'w') as f:
    json.dump(mapping, f, indent=2)

print(f'\n✅ Mapping saved to: gemma_to_qmeans_key_mapping.json')
print(f'   Total mappings: {len(mapping)}')
