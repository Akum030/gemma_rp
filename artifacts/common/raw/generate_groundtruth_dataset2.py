"""
Generate Ground Truth for Dataset 2 (Full dataset queries)
Uses Claude Opus 4.5 API or similar to extract attributes

Run this script to generate ground truth, then we'll calculate metrics
"""

import pandas as pd
import json
import time
import os
from openai import OpenAI

# Initialize OpenAI client (compatible with various APIs)
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # or ANTHROPIC_API_KEY
    base_url=os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
)

def extract_attributes_with_llm(query, model="gpt-4"):
    """
    Extract attributes from query using LLM
    Returns dict of {attr_key_1: ..., attr_value_1: ..., attr_key_2: ...}
    """
    
    prompt = f"""You are an expert at extracting product attributes from search queries.

Query: "{query}"

Extract all relevant attributes from this query. For each attribute, identify:
1. The attribute key (e.g., "material", "type", "capacity", "brand", "voltage")
2. The attribute value (e.g., "steel", "extruder", "100 kg", "prism", "380v")

Return ONLY a JSON object with this format:
{{
    "attr_key_1": "key name",
    "attr_value_1": "value",
    "attr_key_2": "key name",
    "attr_value_2": "value",
    ...
}}

Rules:
- Use standardized key names (e.g., "material", "type", "capacity", "voltage", "brand", "automation grade")
- Extract ALL meaningful attributes, even if minor
- Use lowercase for consistency
- If no attributes found, return {{}}

Examples:
Query: "automatic gold refining machine 2kg"
Output: {{"attr_key_1": "automation grade", "attr_value_1": "automatic", "attr_key_2": "usage", "attr_value_2": "gold refining", "attr_key_3": "capacity", "attr_value_3": "2kg"}}

Query: "twin screw extruder"
Output: {{"attr_key_1": "screw design", "attr_value_1": "twin screw", "attr_key_2": "type", "attr_value_2": "extruder"}}

Now extract attributes for the given query. Return ONLY the JSON, no explanation."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an attribute extraction expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        result = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        attrs = json.loads(result)
        
        # Count attributes
        attr_count = len([k for k in attrs.keys() if k.startswith('attr_key_')])
        
        return {
            'success': True,
            'attr_count': attr_count,
            'attributes': attrs,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'attr_count': 0,
            'attributes': {},
            'error': str(e)
        }


def generate_ground_truth(input_file, output_file, sample_size=None, model="gpt-4"):
    """
    Generate ground truth for queries
    
    Parameters:
    - input_file: CSV with 'query' column
    - output_file: Output CSV with ground truth
    - sample_size: If set, only process N queries (for testing/sampling)
    - model: LLM model to use
    """
    
    print(f'Loading queries from {input_file}...')
    df = pd.read_csv(input_file)
    
    if sample_size:
        print(f'Taking random sample of {sample_size} queries...')
        df = df.sample(n=min(sample_size, len(df)), random_state=42)
    
    print(f'Processing {len(df)} queries...')
    
    results = []
    
    for idx, row in df.iterrows():
        query = row['query']
        
        print(f'\n[{idx+1}/{len(df)}] Processing: {query[:60]}...')
        
        result = extract_attributes_with_llm(query, model=model)
        
        output_row = {
            'query': query,
            'success': result['success'],
            'attr_count': result['attr_count'],
            'error': result['error']
        }
        
        # Add attributes
        attrs = result['attributes']
        for i in range(1, 10):  # Support up to 9 attributes
            key_col = f'attr_key_{i}'
            val_col = f'attr_value_{i}'
            
            if key_col in attrs:
                output_row[key_col] = attrs[key_col]
                output_row[val_col] = attrs.get(val_col, '')
            else:
                output_row[key_col] = ''
                output_row[val_col] = ''
        
        results.append(output_row)
        
        # Save periodically
        if (idx + 1) % 50 == 0:
            temp_df = pd.DataFrame(results)
            temp_df.to_csv(output_file + '.temp', index=False)
            print(f'  ✓ Saved checkpoint at {idx+1} queries')
        
        # Rate limiting
        time.sleep(0.5)
    
    # Save final results
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_file, index=False)
    
    print(f'\n✅ Complete! Saved to {output_file}')
    print(f'   Total queries: {len(output_df)}')
    print(f'   Success rate: {output_df["success"].sum()}/{len(output_df)} ({100*output_df["success"].sum()/len(output_df):.1f}%)')
    print(f'   Avg attributes: {output_df["attr_count"].mean():.2f}')
    
    return output_df


if __name__ == '__main__':
    import sys
    
    print('='*80)
    print('GROUND TRUTH GENERATION FOR DATASET 2')
    print('='*80)
    print()
    print('This script will use LLM to generate ground truth attributes.')
    print()
    print('Options:')
    print('  1. Generate for ALL 1198 queries (4-6 hours, high cost)')
    print('  2. Generate for 300 query sample (1 hour, medium cost) - RECOMMENDED')
    print('  3. Generate for 200 query sample (40 mins, low cost)')
    print('  4. Test with 10 queries first')
    print()
    
    choice = input('Enter choice (1-4): ').strip()
    
    sample_sizes = {
        '1': None,      # All queries
        '2': 300,
        '3': 200,
        '4': 10
    }
    
    sample_size = sample_sizes.get(choice)
    
    if sample_size is None and choice != '1':
        print('Invalid choice. Exiting.')
        sys.exit(1)
    
    # Check API key
    if not os.environ.get("OPENAI_API_KEY"):
        print()
        print('⚠️  ERROR: OPENAI_API_KEY environment variable not set!')
        print()
        print('Please set your API key:')
        print('  Windows: $env:OPENAI_API_KEY="your-key-here"')
        print('  Linux:   export OPENAI_API_KEY="your-key-here"')
        print()
        sys.exit(1)
    
    # Model selection
    print()
    print('Select model:')
    print('  1. gpt-4 (most accurate, expensive)')
    print('  2. gpt-4-turbo (balanced)')
    print('  3. gpt-3.5-turbo (fast, cheap)')
    print()
    
    model_choice = input('Enter model choice (1-3) [default: 2]: ').strip() or '2'
    
    models = {
        '1': 'gpt-4',
        '2': 'gpt-4-turbo',
        '3': 'gpt-3.5-turbo'
    }
    
    model = models.get(model_choice, 'gpt-4-turbo')
    
    print()
    print(f'Configuration:')
    print(f'  Input:  qmeans_results.csv')
    print(f'  Output: ground_truth_dataset2.csv')
    print(f'  Sample: {sample_size if sample_size else "ALL (1198)"} queries')
    print(f'  Model:  {model}')
    print()
    
    confirm = input('Proceed? (yes/no): ').strip().lower()
    
    if confirm != 'yes':
        print('Cancelled.')
        sys.exit(0)
    
    print()
    print('Starting generation...')
    print()
    
    generate_ground_truth(
        input_file='qmeans_results.csv',
        output_file='ground_truth_dataset2.csv',
        sample_size=sample_size,
        model=model
    )
