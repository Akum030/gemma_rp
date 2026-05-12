import openai
import json
import time

# Configuration
openai.api_key = "os.environ.get("OPENAI_API_KEY", "")"
openai.base_url = "https://imllm.intermesh.net/v1"

# Test queries
exclusion_queries = [
    "assam tea wholesale suppliers",
    "mango bags for packing fruits",
    "kerala cotton saree latest designs",
    "kerala saree manufacturers",
    "gota lace for lehenga decoration",
    "cow beef suppliers",
    "beef cow meat wholesale",
    "dog labrador puppies for sale",
    "vim dishwash bar 1 rupee",
    "radhe radhe sweets and namkeen"
]

def test_gemini_zero_shot(query):
    """Test Gemini WITHOUT any context"""
    prompt = f"""Extract product attributes from this e-commerce search query:

Query: "{query}"

Identify:
- Product name/type
- Brand (if mentioned)
- Any specifications
- If it's a restricted/banned item

Return ONLY valid JSON:
{{"product": "...", "brand": "...", "specifications": {{}}, "restricted": true/false}}"""

    try:
        response = openai.ChatCompletion.create(
            model="google/gemini-2.0-flash-lite",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"ERROR: {str(e)}"

# Run tests
print("=" * 80)
print("GEMINI ZERO-SHOT TEST - EXCLUSION LIST")
print("=" * 80)

results = []
for i, query in enumerate(exclusion_queries, 1):
    print(f"\n[{i}/10] Testing: {query}")
    
    gemini_result = test_gemini_zero_shot(query)
    
    results.append({
        "query": query,
        "gemini_zero_shot": gemini_result
    })
    
    print(f"Gemini Output: {gemini_result}")
    
    time.sleep(1)  # Rate limit safety

# Save results
with open('exclusion_test_results.json', 'w') as f:
    json.dump(results, indent=2, fp=f)

print("\n" + "=" * 80)
print("TEST COMPLETE! Results saved to: exclusion_test_results.json")
print("=" * 80)
