"""
Analyze source files and create accurate comparison
"""
import pandas as pd

print('='*80)
print('DETAILED FILE ANALYSIS')
print('='*80)

# Load files
gt = pd.read_csv('synthetic_validation_dataset.csv')
qm = pd.read_csv('qmeans_1000_validation.csv')
gm = pd.read_csv('gemini_with_dataset_validation_queries.csv')

print(f'\n1. GROUND TRUTH (synthetic_validation_dataset.csv)')
print(f'   Total rows: {len(gt)}')
print(f'   Unique queries: {gt["query"].nunique()}')
print(f'   Duplicate queries: {gt["query"].duplicated().sum()}')

print(f'\n2. QMEANS (qmeans_1000_validation.csv)')
print(f'   Total rows: {len(qm)}')
print(f'   Unique queries: {qm["query"].nunique()}')
print(f'   Duplicate queries: {qm["query"].duplicated().sum()}')

print(f'\n3. GEMINI (gemini_with_dataset_validation_queries.csv)')
print(f'   Total rows: {len(gm)}')
print(f'   Unique queries: {gm["query"].nunique()}')
print(f'   Duplicate queries: {gm["query"].duplicated().sum()}')

# Show duplicate queries
print(f'\n4. DUPLICATE QUERIES IN GROUND TRUTH:')
dupes = gt[gt['query'].duplicated(keep=False)]['query'].unique()
for d in dupes[:15]:
    count = (gt['query'] == d).sum()
    print(f'   "{d[:60]}..." appears {count} times')

# Check overlap
print(f'\n5. QUERY OVERLAP:')
gt_queries = set(gt['query'].unique())
qm_queries = set(qm['query'].unique())
gm_queries = set(gm['query'].unique())

print(f'   Ground Truth unique: {len(gt_queries)}')
print(f'   QMeans unique: {len(qm_queries)}')
print(f'   Gemini unique: {len(gm_queries)}')
print(f'   Common to all three: {len(gt_queries & qm_queries & gm_queries)}')
print(f'   In GT but not in QMeans: {len(gt_queries - qm_queries)}')
print(f'   In GT but not in Gemini: {len(gt_queries - gm_queries)}')
print(f'   In QMeans but not in GT: {len(qm_queries - gt_queries)}')
print(f'   In Gemini but not in GT: {len(gm_queries - gt_queries)}')
