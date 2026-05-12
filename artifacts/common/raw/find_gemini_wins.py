"""
Find examples where Gemini performs better than QMeans
in terms of key and value matches against Ground Truth
"""
import pandas as pd

# Load the comprehensive comparison file
df = pd.read_csv('comprehensive_comparison_with_gemma.csv')

print("=" * 80)
print("FINDING EXAMPLES WHERE GEMINI OUTPERFORMS QMEANS")
print("=" * 80)

results = []

for idx, row in df.iterrows():
    query = row['query']
    gt_count = row['ground_truth_count']
    qmeans_count = row['qmeans_attr_count']
    gemini_count = row['gemini_attr_count']
    
    # Count TRUE matches for QMeans vs Ground Truth
    qmeans_key_matches = 0
    qmeans_value_matches = 0
    
    for i in range(1, 10):
        key_col = f'groundtruth_vs_qmeans_attr_{i}_key_match'
        val_col = f'groundtruth_vs_qmeans_attr_{i}_value_match'
        
        if key_col in row and row[key_col] == 'TRUE':
            qmeans_key_matches += 1
        if val_col in row and row[val_col] == 'TRUE':
            qmeans_value_matches += 1
    
    # Count TRUE matches for Gemini vs Ground Truth
    gemini_key_matches = 0
    gemini_value_matches = 0
    
    for i in range(1, 10):
        key_col = f'groundtruth_vs_gemini_attr_{i}_key_match'
        val_col = f'groundtruth_vs_gemini_attr_{i}_value_match'
        
        if key_col in row and row[key_col] == 'TRUE':
            gemini_key_matches += 1
        if val_col in row and row[val_col] == 'TRUE':
            gemini_value_matches += 1
    
    # Check if Gemini performed better
    total_gemini = gemini_key_matches + gemini_value_matches
    total_qmeans = qmeans_key_matches + qmeans_value_matches
    
    if total_gemini > total_qmeans:
        # Get attributes for display
        gt_attrs = []
        qmeans_attrs = []
        gemini_attrs = []
        
        for i in range(1, 10):
            gt_key = row.get(f'groundtruth_attr_key_{i}', '')
            gt_val = row.get(f'groundtruth_attr_value_{i}', '')
            if pd.notna(gt_key) and gt_key != '':
                gt_attrs.append(f"{gt_key}: {gt_val}")
            
            qm_key = row.get(f'qmeans_attr_key_{i}', '')
            qm_val = row.get(f'qmeans_attr_value_{i}', '')
            if pd.notna(qm_key) and qm_key != '':
                qmeans_attrs.append(f"{qm_key}: {qm_val}")
            
            gm_key = row.get(f'gemini_attr_key_{i}', '')
            gm_val = row.get(f'gemini_attr_value_{i}', '')
            if pd.notna(gm_key) and gm_key != '':
                gemini_attrs.append(f"{gm_key}: {gm_val}")
        
        results.append({
            'query': query,
            'gt_count': gt_count,
            'qmeans_count': qmeans_count,
            'gemini_count': gemini_count,
            'qmeans_key_matches': qmeans_key_matches,
            'qmeans_value_matches': qmeans_value_matches,
            'qmeans_total_matches': total_qmeans,
            'gemini_key_matches': gemini_key_matches,
            'gemini_value_matches': gemini_value_matches,
            'gemini_total_matches': total_gemini,
            'improvement': total_gemini - total_qmeans,
            'gt_attrs': gt_attrs,
            'qmeans_attrs': qmeans_attrs,
            'gemini_attrs': gemini_attrs
        })

# Sort by improvement (biggest improvements first)
results.sort(key=lambda x: x['improvement'], reverse=True)

print(f"\nFound {len(results)} examples where Gemini outperforms QMeans")
print("\n" + "=" * 80)
print("TOP 15 EXAMPLES WHERE GEMINI SIGNIFICANTLY OUTPERFORMS QMEANS")
print("=" * 80)

for i, result in enumerate(results[:15], 1):
    print(f"\n{'━' * 80}")
    print(f"EXAMPLE {i}")
    print(f"{'━' * 80}")
    print(f"Query: {result['query']}")
    print(f"\nGround Truth Attributes ({result['gt_count']}):")
    for attr in result['gt_attrs']:
        print(f"  ✓ {attr}")
    
    print(f"\n{'─' * 80}")
    print(f"QMeans Extracted ({result['qmeans_count']} attrs):")
    if result['qmeans_attrs']:
        for attr in result['qmeans_attrs']:
            print(f"  • {attr}")
    else:
        print(f"  (none)")
    print(f"  Match Score: {result['qmeans_key_matches']} key matches, {result['qmeans_value_matches']} value matches")
    print(f"  Total Score: {result['qmeans_total_matches']}")
    
    print(f"\n{'─' * 80}")
    print(f"Gemini Extracted ({result['gemini_count']} attrs):")
    if result['gemini_attrs']:
        for attr in result['gemini_attrs']:
            print(f"  ✓ {attr}")
    else:
        print(f"  (none)")
    print(f"  Match Score: {result['gemini_key_matches']} key matches, {result['gemini_value_matches']} value matches")
    print(f"  Total Score: {result['gemini_total_matches']}")
    
    print(f"\n{'─' * 80}")
    print(f"🏆 GEMINI WINS BY +{result['improvement']} MATCHES!")
    print(f"   Improvement: {result['improvement']} more correct key+value matches vs Ground Truth")

print("\n" + "=" * 80)
print("SUMMARY STATISTICS")
print("=" * 80)

# Calculate average improvements
avg_improvement = sum(r['improvement'] for r in results) / len(results)
avg_qmeans_score = sum(r['qmeans_total_matches'] for r in results) / len(results)
avg_gemini_score = sum(r['gemini_total_matches'] for r in results) / len(results)

print(f"\nTotal cases where Gemini outperforms: {len(results)}")
print(f"Average QMeans score (in winning cases): {avg_qmeans_score:.2f} matches")
print(f"Average Gemini score (in winning cases): {avg_gemini_score:.2f} matches")
print(f"Average improvement: +{avg_improvement:.2f} matches")

# Distribution of improvements
print(f"\nImprovement Distribution:")
print(f"  +1-2 matches: {len([r for r in results if 1 <= r['improvement'] <= 2])} cases")
print(f"  +3-5 matches: {len([r for r in results if 3 <= r['improvement'] <= 5])} cases")
print(f"  +6+ matches:  {len([r for r in results if r['improvement'] >= 6])} cases")

print("\n" + "=" * 80)
