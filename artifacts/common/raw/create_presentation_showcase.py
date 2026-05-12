"""
Real comparison using existing test data: QMeans vs Gemini
Finding queries where Gemini significantly outperforms QMeans
"""

import pandas as pd

# Load both datasets
print("Loading test results...")
qmeans_df = pd.read_csv('qmeans_results.csv')
gemini_df = pd.read_csv('gemini_zero_shot_full.csv')

# Merge on query
merged_df = qmeans_df.merge(gemini_df, on='query', suffixes=('_qmeans', '_gemini'))

print(f"Total queries with both QMeans and Gemini results: {len(merged_df)}")

# Calculate improvement
merged_df['improvement'] = merged_df['gemini_attr_count'] - merged_df['qmeans_attr_count']

# Find cases where Gemini performs significantly better
# 1. QMeans found 0-1 attributes but Gemini found 2+
significant_improvements = merged_df[
    (merged_df['qmeans_attr_count'] <= 1) &
    (merged_df['gemini_attr_count'] >= 2) &
    (merged_df['improvement'] >= 2)
].copy()

print(f"\nFound {len(significant_improvements)} queries where Gemini extracted 2+ more attributes")

# Sort by improvement
significant_improvements = significant_improvements.sort_values('improvement', ascending=False)

# Top 10 for presentation
top_10 = significant_improvements.head(10)

print("\n" + "="*80)
print("TOP 10 QUERIES WHERE GEMINI OUTPERFORMS QMEANS")
print("="*80)

for i, (idx, row) in enumerate(top_10.iterrows(), 1):
    print(f"\n{i}. Query: {row['query']}")
    print(f"   -"*40)
    print(f"   QMeans: {int(row['qmeans_attr_count'])} attributes")
    if row['qmeans_isq_pipe']:
        print(f"     {row['qmeans_isq_pipe']}")
    else:
        print(f"     (no attributes found)")
    
    print(f"\n   Gemini: {int(row['gemini_attr_count'])} attributes (+{int(row['improvement'])})")
    print(f"     {row['gemini_isq_pipe']}")
    print()

# Summary stats
print("\n" + "="*80)
print("STATISTICAL SUMMARY")
print("="*80)

total_queries = len(merged_df)
qmeans_avg = merged_df['qmeans_attr_count'].mean()
gemini_avg = merged_df['gemini_attr_count'].mean()

print(f"\nTotal queries analyzed: {total_queries}")
print(f"\nAverage attributes extracted:")
print(f"  QMeans: {qmeans_avg:.2f} attributes/query")
print(f"  Gemini: {gemini_avg:.2f} attributes/query")
print(f"  Improvement: +{gemini_avg - qmeans_avg:.2f} attributes/query (+{(gemini_avg - qmeans_avg)/qmeans_avg * 100:.1f}%)")

# Cases where each performs better
gemini_better = len(merged_df[merged_df['improvement'] > 0])
qmeans_better = len(merged_df[merged_df['improvement'] < 0])
equal = len(merged_df[merged_df['improvement'] == 0])

print(f"\nPerformance comparison:")
print(f"  Gemini extracted more: {gemini_better} queries ({gemini_better/total_queries*100:.1f}%)")
print(f"  QMeans extracted more: {qmeans_better} queries ({qmeans_better/total_queries*100:.1f}%)")
print(f"  Equal: {equal} queries ({equal/total_queries*100:.1f}%)")

# Save results
output_file = 'presentation_showcase_queries.csv'
top_10.to_csv(output_file, index=False)

print("\n" + "="*80)
print(f"✓ Top 10 showcase queries saved to: {output_file}")
print("="*80)
print("\nUse these verified examples in your presentation!")
