"""
Find complex multi-attribute queries from existing data
These are most likely to have relevance issues on search
"""

import pandas as pd

# Load query data
qmeans_df = pd.read_csv('qmeans_results.csv')

# Find queries with multiple specific attributes (color + location, color + size, etc)
# These often have relevance issues

# Calculate query complexity
qmeans_df['word_count'] = qmeans_df['query'].str.split().str.len()
qmeans_df['has_color'] = qmeans_df['query'].str.contains(
    'red|blue|green|black|white|yellow|pink|brown|grey|orange|purple|golden|silver',
    case=False, na=False
)
qmeans_df['has_location'] = qmeans_df['query'].str.contains(
    'noida|delhi|mumbai|bangalore|pune|hyderabad|chennai|kolkata|ahmedabad|jaipur',
    case=False, na=False
)
qmeans_df['has_size'] = qmeans_df['query'].str.contains(
    '\\d+kg|\\d+mm|\\d+cm|size \\d+|\\d+ inch|\\d+ liter|waist \\d+',
    case=False, na=False
)
qmeans_df['has_material'] = qmeans_df['query'].str.contains(
    'cotton|leather|plastic|steel|aluminum|wood|glass|ceramic|metal',
    case=False, na=False
)

# Complex queries with multiple specific attributes
complex_queries = qmeans_df[
    (qmeans_df['word_count'] >= 4) &
    ((qmeans_df['has_color'] & qmeans_df['has_location']) |
     (qmeans_df['has_color'] & qmeans_df['has_size']) |
     (qmeans_df['has_color'] & qmeans_df['has_material']) |
     (qmeans_df['has_size'] & qmeans_df['has_location']))
].copy()

print(f"Found {len(complex_queries)} complex multi-attribute queries")
print("\nThese queries are MOST LIKELY to have relevance issues:")
print("="*80)

# Show top 20 candidates
for idx, row in complex_queries.head(20).iterrows():
    print(f"\n{row['query']}")
    attrs = []
    if row['has_color']:
        attrs.append("Color")
    if row['has_location']:
        attrs.append("Location")
    if row['has_size']:
        attrs.append("Size")
    if row['has_material']:
        attrs.append("Material")
    print(f"  Attributes: {', '.join(attrs)} | Words: {row['word_count']}")

print("\n" + "="*80)
print("\nMANUALLY TEST THESE QUERIES ON dir.indiamart.com")
print("Check if first result matches ALL attributes (color, size, location, material)")
print("="*80)
