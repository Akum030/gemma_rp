"""
Improved attribute extraction prompt that treats attributes as training examples
rather than strict category restrictions.
"""

def create_dataset_prompt(query, attr_dict):
    """
    Create prompt with attribute dataset as training examples.
    The model learns patterns from these attributes and applies them to any query.
    """

    # Build attribute reference (compressed format)
    attr_reference = "ATTRIBUTE EXTRACTION TRAINING DATA:\n\n"
    attr_reference += "These are example attributes and their values from previous extractions. "
    attr_reference += "Learn from these patterns and apply similar extraction logic to ANY product query.\n\n"
    
    for attr_name, values in attr_dict.items():
        value_list = ' | '.join(values[:20])
        if len(values) > 20:
            value_list += f" ... (+{len(values)-20} more)"
        attr_reference += f"• {attr_name}: {value_list}\n"

    prompt = f"""{attr_reference}

TASK: Extract product attributes from the given query.

OUTPUT FORMAT (ISQ):
- attribute_value:attribute_name:attribute_type
- attribute_type is always "specification"
- Return as a Python list

EXTRACTION GUIDELINES:
1. Identify ALL product-related attributes in the query (brand, capacity, voltage, material, color, size, weight, etc.)
2. Use attribute names from the training data when applicable
3. For new product categories, infer appropriate attribute names based on the query context
4. Extract quantities with units (e.g., "500 gm", "1 kg", "750 ml")
5. Extract specifications (voltage, phase, power, capacity, etc.)
6. Extract materials, colors, sizes, and other descriptive attributes
7. Identify brand names if mentioned
8. If no clear attributes are found, return empty list []

EXAMPLES:

Query: "440V three phase automatic extruder"
Output: ['440 v:voltage:specification', 'three phase:phase:specification', 'automatic:automation grade:specification', 'extruder:product:specification']

Query: "stainless steel paint coated extraction plant"
Output: ['stainless steel:body material:specification', 'paint coated:surface finishing:specification', 'extraction plant:product:specification']

Query: "vim bar lemon 500 gm pack of 3"
Output: ['vim:brand:specification', 'bar:product type:specification', 'lemon:variant:specification', '500 gm:weight:specification', 'pack of 3:packaging:specification']

Query: "kerala cotton saree white gold border"
Output: ['kerala:origin:specification', 'cotton:material:specification', 'saree:product:specification', 'white:color:specification', 'gold border:design:specification']

Query: "assam tea 1 kg organic loose leaf"
Output: ['assam:origin:specification', 'tea:product:specification', '1 kg:weight:specification', 'organic:type:specification', 'loose leaf:form:specification']

Query: "radhe radhe printed tshirt men"
Output: ['radhe radhe:print/design:specification', 'printed:style:specification', 'tshirt:product:specification', 'men:target gender:specification']

Now extract attributes:

Query: "{query}"
Output: """

    return prompt


def create_dataset_prompt_v2(query, attr_dict):
    """
    Alternative version with even more flexibility - focuses on pattern learning
    """

    # Build attribute reference showing diversity
    attr_reference = "LEARN FROM THESE ATTRIBUTE PATTERNS:\n\n"
    
    for attr_name, values in attr_dict.items():
        # Show first 15 examples
        value_list = ' | '.join(values[:15])
        if len(values) > 15:
            value_list += f" ... (+{len(values)-15} more)"
        attr_reference += f"• {attr_name}: {value_list}\n"

    prompt = f"""{attr_reference}

OBJECTIVE: You are an attribute extraction model trained on the above examples. 
Extract attributes from ANY product query using the learned patterns.

FORMAT: attribute_value:attribute_name:specification (always use "specification" as type)

CORE PRINCIPLES:
✓ Extract: brand, product, capacity, voltage, material, color, size, weight, packaging
✓ Keep quantities with units: "500 gm", "1 kg", "2 inch", "750 ml"
✓ Identify specifications: power, voltage, phase, frequency, dimensions
✓ Recognize origins/regions: assam, kerala, rajasthan, etc.
✓ Capture descriptive terms: organic, premium, handmade, traditional
✓ For text on products (like "radhe radhe"), use: print/design or text as attribute name

TRAINING EXAMPLES:

Input: "premium assam tea loose leaf 500 gm"
Output: ['premium:quality:specification', 'assam:origin:specification', 'tea:product:specification', 'loose leaf:form:specification', '500 gm:weight:specification']

Input: "kerala cotton saree kasavu gold border"
Output: ['kerala:origin:specification', 'cotton:material:specification', 'saree:product:specification', 'kasavu:style:specification', 'gold border:design:specification']

Input: "mango bags jute eco friendly large"
Output: ['mango bags:product:specification', 'jute:material:specification', 'eco friendly:feature:specification', 'large:size:specification']

Input: "vim liquid dishwash 750 ml lemon"
Output: ['vim:brand:specification', 'liquid:form:specification', 'dishwash:product type:specification', '750 ml:volume:specification', 'lemon:variant:specification']

Input: "gota lace golden 2 inch width designer"
Output: ['gota lace:product:specification', 'golden:color:specification', '2 inch:width:specification', 'designer:style:specification']

Input: "radhe radhe printed kurta cotton men"
Output: ['radhe radhe:print/design:specification', 'printed:style:specification', 'kurta:product:specification', 'cotton:material:specification', 'men:target gender:specification']

Now analyze and extract:

Query: "{query}"
Output: """

    return prompt


# Example usage comparison
if __name__ == "__main__":
    # Sample attribute dictionary (subset)
    sample_attrs = {
        "voltage": ["220 v", "440 v", "380 v", "415 v"],
        "material": ["cotton", "silk", "jute", "stainless steel", "plastic"],
        "brand": ["vim", "rajco", "kabra", "teknik"],
        "weight": ["500 gm", "1 kg", "250 gm", "750 ml"],
        "color": ["white", "golden", "silver", "blue", "green"]
    }
    
    # Test with different queries
    test_queries = [
        "assam tea 500 gm organic",
        "kerala cotton saree white gold border",
        "vim bar lemon 200 gm",
        "radhe radhe printed tshirt"
    ]
    
    print("=" * 80)
    print("TESTING IMPROVED PROMPTS")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n\nQuery: {query}")
        print("-" * 80)
        prompt = create_dataset_prompt(query, sample_attrs)
        print("Prompt Preview (first 500 chars):")
        print(prompt[:500] + "...\n")
