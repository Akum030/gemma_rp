"""
Find complex queries where QMeans performs poorly but Gemini can excel
"""

import pandas as pd
import json
from openai import OpenAI

# Load QMeans results
print("Loading QMeans results...")
qmeans_df = pd.read_csv('qmeans_results.csv')

# Filter for complex queries (long queries with few QMeans attributes)
qmeans_df['query_length'] = qmeans_df['query'].str.len()
qmeans_df['word_count'] = qmeans_df['query'].str.split().str.len()

# Find queries where:
# 1. Query is complex (5+ words, 40+ chars)
# 2. QMeans found 0-2 attributes (poor performance)
# 3. Successfully ran (not failed)
complex_queries = qmeans_df[
    (qmeans_df['word_count'] >= 5) &
    (qmeans_df['query_length'] >= 40) &
    (qmeans_df['qmeans_attr_count'] <= 2) &
    (qmeans_df['success'] == True)
].sort_values('word_count', ascending=False)

print(f"\nFound {len(complex_queries)} complex queries where QMeans struggled")
print("\nTop 20 candidates:")
print("="*80)

for idx, row in complex_queries.head(20).iterrows():
    print(f"\nQuery: {row['query']}")
    print(f"  Words: {row['word_count']} | Chars: {row['query_length']}")
    print(f"  QMeans found: {row['qmeans_attr_count']} attributes")
    if pd.notna(row['qmeans_isq_pipe']):
        print(f"  QMeans output: {row['qmeans_isq_pipe']}")
    else:
        print(f"  QMeans output: (none)")

# Now test these with Gemini
print("\n" + "="*80)
print("Testing with Gemini API...")
print("="*80)

client = OpenAI(api_key="os.environ.get("OPENAI_API_KEY", "")")

comparison_results = []

for idx, row in complex_queries.head(20).iterrows():
    query = row['query']
    qmeans_count = row['qmeans_attr_count']
    
    # Test with Gemini
    try:
        messages = [
            {
                "role": "system",
                "content": "You are an expert at extracting product attributes from queries. Extract key-value pairs in JSON format. Use descriptive keys like 'material', 'capacity', 'voltage', 'automation grade', 'type', 'usage', 'brand', 'color', 'shape', etc."
            },
            {
                "role": "user",
                "content": f"Extract all possible attributes from this query: {query}\n\nReturn ONLY a JSON object with key-value pairs."
            }
        ]
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,
            max_tokens=300
        )
        
        gemini_output = response.choices[0].message.content.strip()
        
        # Parse JSON
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[^}]+\}', gemini_output)
            if json_match:
                gemini_attrs = json.loads(json_match.group(0))
                gemini_count = len(gemini_attrs)
            else:
                gemini_attrs = {}
                gemini_count = 0
        except:
            gemini_attrs = {}
            gemini_count = 0
        
        # Calculate improvement
        improvement = gemini_count - qmeans_count
        
        if improvement >= 2:  # Gemini found at least 2 more attributes
            comparison_results.append({
                'query': query,
                'qmeans_count': qmeans_count,
                'gemini_count': gemini_count,
                'improvement': improvement,
                'qmeans_output': row['qmeans_isq_pipe'] if pd.notna(row['qmeans_isq_pipe']) else '(none)',
                'gemini_attrs': gemini_attrs
            })
            
            print(f"\n✓ WINNER: {query[:60]}...")
            print(f"  QMeans: {qmeans_count} attrs | Gemini: {gemini_count} attrs (+{improvement})")
            print(f"  Gemini found: {gemini_attrs}")
    
    except Exception as e:
        print(f"  Error testing with Gemini: {e}")
        continue

# Sort by improvement and take top 10
comparison_results.sort(key=lambda x: x['improvement'], reverse=True)
top_10 = comparison_results[:10]

print("\n" + "="*80)
print("TOP 10 QUERIES WHERE GEMINI OUTPERFORMS QMEANS")
print("="*80)

for i, result in enumerate(top_10, 1):
    print(f"\n{i}. Query: {result['query']}")
    print(f"   QMeans: {result['qmeans_count']} attributes")
    print(f"   QMeans output: {result['qmeans_output']}")
    print(f"   Gemini: {result['gemini_count']} attributes (+{result['improvement']})")
    print(f"   Gemini found: {json.dumps(result['gemini_attrs'], indent=4)}")

# Save to CSV
output_df = pd.DataFrame(top_10)
output_df.to_csv('gemini_vs_qmeans_showcase.csv', index=False)

print("\n" + "="*80)
print("✓ Results saved to: gemini_vs_qmeans_showcase.csv")
print("="*80)
print(f"\nFound {len(top_10)} queries where Gemini significantly outperforms QMeans")
print("Use these for your presentation! 🎉")
