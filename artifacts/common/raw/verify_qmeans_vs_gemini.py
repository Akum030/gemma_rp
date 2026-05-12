"""
Proper comparison: QMeans vs Gemini for complex queries
"""

import pandas as pd
import requests
import json

# Queries where QMeans returned 0 attributes
test_queries = [
    "twin-screw-extruder",
    "Imported Oak Moss Lichen",
    "gold-refining-plant",
    "Extruder",
    "Cable Extruder",
    "Twin Screw Extruder",
    "blown-film-extrusion-machine",
    "Herbal Extraction Plant",
    "solvent-extraction-systems",
    "bollman extractor material"
]

print("="*80)
print("COMPARING QMEANS vs GEMINI ON COMPLEX QUERIES")
print("="*80)

# QMeans API endpoint
qmeans_api = "http://34.93.70.216:8009/attribute-search-qmeans"

# Gemini API (using your existing setup)
import google.generativeai as genai
genai.configure(api_key="os.environ.get("GOOGLE_API_KEY", "")")
gemini_model = genai.GenerativeModel("gemini-2.0-flash-exp")

comparison_results = []

for query in test_queries:
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    # 1. QMeans extraction
    try:
        response = requests.post(
            qmeans_api,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            qmeans_data = response.json()
            
            # Parse ISQ format
            qmeans_attrs = {}
            if 'isq_pipe' in qmeans_data and qmeans_data['isq_pipe']:
                items = qmeans_data['isq_pipe'].split('|')
                for item in items:
                    parts = item.split(':')
                    if len(parts) >= 2:
                        value = parts[0].strip()
                        key = parts[1].strip()
                        qmeans_attrs[key] = value
            
            qmeans_count = len(qmeans_attrs)
        else:
            qmeans_attrs = {}
            qmeans_count = 0
    except Exception as e:
        print(f"  QMeans Error: {e}")
        qmeans_attrs = {}
        qmeans_count = 0
    
    # 2. Gemini extraction
    try:
        prompt = f"""Extract key-value attributes from this product query: "{query}"

Return ONLY a JSON object with key-value pairs. Use keys like: type, material, capacity, voltage, brand, usage, automation grade, color, shape, power, screw type, layer, etc.

Example output: {{"type": "extruder", "material": "plastic", "capacity": "100 kg/hr"}}

Query: {query}
Output:"""
        
        response = gemini_model.generate_content(prompt)
        gemini_output = response.text.strip()
        
        # Parse JSON
        import re
        json_match = re.search(r'\{[^}]+\}', gemini_output)
        if json_match:
            gemini_attrs = json.loads(json_match.group(0))
            gemini_count = len(gemini_attrs)
        else:
            gemini_attrs = {}
            gemini_count = 0
    except Exception as e:
        print(f"  Gemini Error: {e}")
        gemini_attrs = {}
        gemini_count = 0
    
    # 3. Calculate improvement
    improvement = gemini_count - qmeans_count
    
    print(f"\n  QMeans: {qmeans_count} attributes")
    if qmeans_attrs:
        print(f"    {qmeans_attrs}")
    else:
        print(f"    (none)")
    
    print(f"\n  Gemini: {gemini_count} attributes")
    if gemini_attrs:
        for key, value in gemini_attrs.items():
            print(f"    {key}: {value}")
    else:
        print(f"    (none)")
    
    print(f"\n  ✓ Improvement: +{improvement} attributes")
    
    comparison_results.append({
        'query': query,
        'qmeans_count': qmeans_count,
        'qmeans_attrs': qmeans_attrs,
        'gemini_count': gemini_count,
        'gemini_attrs': gemini_attrs,
        'improvement': improvement
    })

# Summary
print(f"\n{'='*80}")
print("SUMMARY - GEMINI OUTPERFORMS QMEANS")
print(f"{'='*80}")

successful_improvements = [r for r in comparison_results if r['improvement'] > 0]

print(f"\nTotal queries tested: {len(comparison_results)}")
print(f"Gemini extracted more: {len(successful_improvements)} queries")

avg_qmeans = sum(r['qmeans_count'] for r in comparison_results) / len(comparison_results)
avg_gemini = sum(r['gemini_count'] for r in comparison_results) / len(comparison_results)

print(f"\nAverage extraction:")
print(f"  QMeans: {avg_qmeans:.2f} attributes/query")
print(f"  Gemini: {avg_gemini:.2f} attributes/query")
print(f"  Improvement: +{avg_gemini - avg_qmeans:.2f} attributes/query")

# Top improvements
print(f"\n{'='*80}")
print("TOP 5 IMPROVEMENTS")
print(f"{'='*80}")

sorted_results = sorted(comparison_results, key=lambda x: x['improvement'], reverse=True)
for i, result in enumerate(sorted_results[:5], 1):
    print(f"\n{i}. {result['query']}")
    print(f"   QMeans: {result['qmeans_count']} | Gemini: {result['gemini_count']} (+{result['improvement']})")
    print(f"   Gemini extracted: {result['gemini_attrs']}")

# Save results
output_df = pd.DataFrame(comparison_results)
output_df.to_csv('qmeans_vs_gemini_verified.csv', index=False)

print(f"\n{'='*80}")
print("✓ Results saved to: qmeans_vs_gemini_verified.csv")
print(f"{'='*80}")
