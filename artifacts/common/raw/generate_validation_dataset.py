"""
Generate Synthetic Validation Dataset for Attribute Extraction
Creates ~1000 queries with extracted attributes based on real query patterns
and human-evaluated attribute key-value pairs.
"""

import pandas as pd
import random
import csv
from collections import defaultdict

# Load the attribute key-value pairs
def load_attributes(filepath):
    """Load and organize attributes by key"""
    attr_by_key = defaultdict(list)
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if ',' in line:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip().lower()
                    if key and value:
                        attr_by_key[key].append(value)
    return attr_by_key

# Define product types for this category (extruders, refineries, extraction plants)
PRODUCTS = [
    "twin screw extruder", "extruder machine", "blown film extrusion machine",
    "gold refining machine", "silver refining plant", "solvent extraction plant",
    "herbal extraction plant", "cable extruder", "monolayer extruder",
    "centrifuge extractor", "bitumen extractor", "metal recovery plant",
    "rice bran extraction plant", "tube extrusion machine", "sheet extruder",
    "basket extruder", "conical twin screw extruder", "lab extruder",
    "aluminium extrusion plant", "gold refinery plant", "silver refinery machine",
    "co-rotating twin screw extruder", "plastic extruder", "pvc extruder",
    "ldpe blown film machine", "hdpe extruder", "curcumin extraction plant",
    "oleoresin extraction plant", "oil extraction plant", "film extrusion machine",
    "wire extruder", "polymer extruder", "foam extruder", "pipe extrusion machine",
    "multi layer extruder", "aba blown film machine", "double die extruder",
    "single die extruder", "jockey extruder", "mother baby extruder",
    "hydro extractor", "solid phase extraction system", "liquid extraction system",
    "copper extraction plant", "zinc recovery unit", "metal refining plant",
    "pet extruder", "epe foam extruder", "wpc extruder", "pp extruder"
]

# Key attributes that are commonly used
KEY_ATTRIBUTES = [
    "capacity", "production capacity", "capacity(kg)", "voltage", "power",
    "automation grade", "phase", "body material", "material", "brand",
    "usage/application", "machine type", "screw design", "plastic processed",
    "motor power", "frequency", "weight", "dimension", "temperature",
    "purity", "type", "power source", "driven type", "screw diameter",
    "output", "color", "warranty", "condition", "model name/number"
]

def generate_simple_queries(attr_by_key, count=200):
    """Generate simple queries with 1-2 attributes"""
    queries = []
    
    simple_templates = [
        "{product}",
        "{product} machine",
        "{product} plant",
        "automatic {product}",
        "semi automatic {product}",
        "industrial {product}",
        "{capacity} {product}",
        "{product} {voltage}",
        "{product} {brand}",
        "{material} {product}",
        "{product} for {application}",
        "new {product}",
        "used {product}",
        "mini {product}",
        "lab {product}",
        "commercial {product}",
    ]
    
    for _ in range(count):
        template = random.choice(simple_templates)
        product = random.choice(PRODUCTS)
        
        # Get random attribute values
        capacity_vals = attr_by_key.get('capacity', ['100 kg/hr', '500 kg/hr', '50 kg'])
        voltage_vals = attr_by_key.get('voltage', ['220 v', '440 v', '380 v'])
        brand_vals = attr_by_key.get('brand', ['kabra', 'rajco', 'teknik'])
        material_vals = attr_by_key.get('body material', ['stainless steel', 'mild steel', 'ss'])
        app_vals = attr_by_key.get('usage/application', ['industrial', 'laboratory', 'pharmaceutical'])
        
        query = template.format(
            product=product,
            capacity=random.choice(capacity_vals),
            voltage=random.choice(voltage_vals),
            brand=random.choice(brand_vals),
            material=random.choice(material_vals),
            application=random.choice(app_vals)
        )
        
        # Extract attributes from the query
        attrs = extract_attributes_from_query(query, attr_by_key, product)
        queries.append((query, attrs))
    
    return queries

def generate_medium_queries(attr_by_key, count=400):
    """Generate medium complexity queries with 2-4 attributes"""
    queries = []
    
    templates = [
        "{capacity} {automation} {product}",
        "{product} {voltage} {phase}",
        "{brand} {product} {capacity}",
        "{material} {product} {capacity}",
        "{product} for {application} {capacity}",
        "automatic {product} {capacity} {voltage}",
        "{capacity} {product} {material} body",
        "{product} {power} motor {capacity}",
        "{automation} {material} {product}",
        "{product} {screw_design} {capacity}",
        "{brand} {automation} {product} {capacity}",
        "{product} with {power} power {voltage}",
        "{material} body {product} {capacity}",
        "{product} {voltage} {frequency}",
        "{capacity} {phase} {product}",
        "{product} production capacity {production_capacity}",
        "{purity} purity {product}",
        "{product} {color} color",
        "{warranty} warranty {product}",
        "{product} {dimension} size",
    ]
    
    for _ in range(count):
        template = random.choice(templates)
        product = random.choice(PRODUCTS)
        
        # Get random values from attributes
        capacity = random.choice(attr_by_key.get('capacity', ['100 kg/hr']))
        voltage = random.choice(attr_by_key.get('voltage', ['440 v']))
        phase = random.choice(attr_by_key.get('phase', ['three phase']))
        brand = random.choice(attr_by_key.get('brand', ['kabra']))
        material = random.choice(attr_by_key.get('body material', ['stainless steel']))
        automation = random.choice(attr_by_key.get('automation grade', ['automatic']))
        application = random.choice(attr_by_key.get('usage/application', ['industrial']))
        power = random.choice(attr_by_key.get('power', ['5 kw']))
        screw_design = random.choice(attr_by_key.get('screw design', ['twin screw']))
        production_capacity = random.choice(attr_by_key.get('production capacity', ['500 kg/hr']))
        purity = random.choice(attr_by_key.get('purity', ['99.9%']))
        color = random.choice(attr_by_key.get('color', ['silver']))
        warranty = random.choice(attr_by_key.get('warranty', ['1 year']))
        dimension = random.choice(attr_by_key.get('dimension', ['10 x 10']))
        frequency = random.choice(attr_by_key.get('frequency', ['50 hz']))
        
        try:
            query = template.format(
                product=product,
                capacity=capacity,
                voltage=voltage,
                phase=phase,
                brand=brand,
                material=material,
                automation=automation,
                application=application,
                power=power,
                screw_design=screw_design,
                production_capacity=production_capacity,
                purity=purity,
                color=color,
                warranty=warranty,
                dimension=dimension,
                frequency=frequency
            )
        except KeyError:
            continue
        
        attrs = extract_attributes_from_query(query, attr_by_key, product)
        queries.append((query, attrs))
    
    return queries

def generate_complex_queries(attr_by_key, count=250):
    """Generate complex queries with 4-6 attributes"""
    queries = []
    
    templates = [
        "{brand} {automation} {product}, {capacity}, {voltage}, {phase}",
        "{material} body {product} with {capacity} capacity and {voltage} voltage",
        "{automation} {product} for {application}, capacity: {capacity}, power: {power}",
        "{product} - {brand} make, {capacity}, {material}, {phase}",
        "{capacity} {automation} {product} {voltage} {phase} {material} body",
        "industrial {product} {brand} {capacity} {voltage} {automation}",
        "{product} machine {capacity} output {voltage} {phase} {material}",
        "{screw_design} {product} {capacity} {automation} {voltage}",
        "{product} for {application} use, {capacity}, {voltage}, {brand} brand",
        "{automation} {material} {product}, capacity: {capacity}, voltage: {voltage}, phase: {phase}",
        "{brand} {product} {screw_design} design {capacity} {voltage}",
        "{product} with {power} motor power, {capacity} capacity, {phase}",
        "new {automation} {product} {capacity} {material} body {voltage}",
        "{product} plant {capacity} {voltage} {phase} {automation}",
        "{material} {product} {brand} {capacity} production {voltage}",
    ]
    
    for _ in range(count):
        template = random.choice(templates)
        product = random.choice(PRODUCTS)
        
        capacity = random.choice(attr_by_key.get('capacity', ['100 kg/hr']))
        voltage = random.choice(attr_by_key.get('voltage', ['440 v']))
        phase = random.choice(attr_by_key.get('phase', ['three phase']))
        brand = random.choice(attr_by_key.get('brand', ['kabra']))
        material = random.choice(attr_by_key.get('body material', ['stainless steel']))
        automation = random.choice(attr_by_key.get('automation grade', ['automatic']))
        application = random.choice(attr_by_key.get('usage/application', ['industrial']))
        power = random.choice(attr_by_key.get('motor power', ['5 hp']))
        screw_design = random.choice(attr_by_key.get('screw design', ['twin screw']))
        
        try:
            query = template.format(
                product=product,
                capacity=capacity,
                voltage=voltage,
                phase=phase,
                brand=brand,
                material=material,
                automation=automation,
                application=application,
                power=power,
                screw_design=screw_design
            )
        except KeyError:
            continue
        
        attrs = extract_attributes_from_query(query, attr_by_key, product)
        queries.append((query, attrs))
    
    return queries

def generate_long_queries(attr_by_key, count=150):
    """Generate longer descriptive queries with many attributes"""
    queries = []
    
    templates = [
        "{brand} {automation} {product} machine with {capacity} capacity, {voltage} voltage, {phase} phase, {material} body, suitable for {application}",
        "{product} - {screw_design} design, {capacity} output, {voltage}, {phase}, {material} construction, {brand} brand, {automation} operation",
        "looking for {automation} {product} with specifications: capacity {capacity}, voltage {voltage}, phase {phase}, body material {material}, application {application}",
        "{brand} make {automation} {product}, production capacity: {capacity}, voltage: {voltage}, phase: {phase}, material: {material}, power: {power}",
        "high quality {automation} {product} {screw_design} type, {capacity}, {voltage} supply, {phase}, {material} body, {brand} brand for {application}",
        "{product} machine specifications - brand: {brand}, capacity: {capacity}, voltage: {voltage}, phase: {phase}, body material: {material}, automation: {automation}",
        "industrial grade {automation} {product} with {screw_design} design, {capacity} capacity, operating voltage {voltage}, {phase}, {material} body material",
        "{automation} {product} for {application} applications, {capacity} capacity, {voltage} voltage rating, {phase} power supply, {material} body",
    ]
    
    for _ in range(count):
        template = random.choice(templates)
        product = random.choice(PRODUCTS)
        
        capacity = random.choice(attr_by_key.get('capacity', ['100 kg/hr']))
        voltage = random.choice(attr_by_key.get('voltage', ['440 v']))
        phase = random.choice(attr_by_key.get('phase', ['three phase']))
        brand = random.choice(attr_by_key.get('brand', ['kabra']))
        material = random.choice(attr_by_key.get('body material', ['stainless steel']))
        automation = random.choice(attr_by_key.get('automation grade', ['automatic']))
        application = random.choice(attr_by_key.get('usage/application', ['industrial']))
        power = random.choice(attr_by_key.get('motor power', ['5 hp']))
        screw_design = random.choice(attr_by_key.get('screw design', ['twin screw']))
        
        try:
            query = template.format(
                product=product,
                capacity=capacity,
                voltage=voltage,
                phase=phase,
                brand=brand,
                material=material,
                automation=automation,
                application=application,
                power=power,
                screw_design=screw_design
            )
        except KeyError:
            continue
        
        attrs = extract_attributes_from_query(query, attr_by_key, product)
        queries.append((query, attrs))
    
    return queries

def extract_attributes_from_query(query, attr_by_key, product):
    """
    Extract attributes from query based on matching values in attr_by_key.
    Returns a list of (key, value) tuples.
    """
    attrs = []
    query_lower = query.lower()
    
    # Check for product type
    attrs.append(("product", product))
    
    # Priority order for attribute matching
    priority_keys = [
        'capacity', 'production capacity', 'capacity(kg)', 'voltage', 'power',
        'automation grade', 'automatic grade', 'phase', 'body material', 'material',
        'brand', 'usage/application', 'machine type', 'screw design', 'plastic processed',
        'motor power', 'frequency', 'weight', 'purity', 'type', 'color',
        'driven type', 'screw diameter', 'output', 'condition', 'warranty',
        'temperature', 'pressure', 'dimension', 'size'
    ]
    
    found_values = set()  # Track found values to avoid duplicates
    
    for key in priority_keys:
        if key in attr_by_key:
            for value in attr_by_key[key]:
                if value and len(value) > 1 and value not in found_values:
                    # Clean the value for matching
                    value_clean = value.lower().strip()
                    if value_clean in query_lower:
                        attrs.append((key, value))
                        found_values.add(value)
                        break  # Only one value per key
    
    # Special handling for common patterns
    # Capacity patterns
    import re
    capacity_pattern = r'(\d+(?:\.\d+)?)\s*(kg/hr|kg/h|tpd|ton|kg|tph|liter|litre|ltr|l)'
    capacity_match = re.search(capacity_pattern, query_lower)
    if capacity_match and not any(k == 'capacity' for k, v in attrs):
        attrs.append(("capacity", capacity_match.group(0)))
    
    # Voltage patterns  
    voltage_pattern = r'(\d+)\s*(v|volt|volts)'
    voltage_match = re.search(voltage_pattern, query_lower)
    if voltage_match and not any(k == 'voltage' for k, v in attrs):
        attrs.append(("voltage", voltage_match.group(0)))
    
    # Power patterns
    power_pattern = r'(\d+(?:\.\d+)?)\s*(hp|kw|kva|watt|w)'
    power_match = re.search(power_pattern, query_lower)
    if power_match and not any(k in ['power', 'motor power'] for k, v in attrs):
        attrs.append(("power", power_match.group(0)))
    
    # Automation grade
    if 'automatic' in query_lower and not any(k == 'automation grade' for k, v in attrs):
        if 'fully automatic' in query_lower:
            attrs.append(("automation grade", "fully automatic"))
        elif 'semi automatic' in query_lower or 'semi-automatic' in query_lower:
            attrs.append(("automation grade", "semi-automatic"))
        else:
            attrs.append(("automation grade", "automatic"))
    elif 'manual' in query_lower and not any(k == 'automation grade' for k, v in attrs):
        attrs.append(("automation grade", "manual"))
    
    # Phase
    if 'three phase' in query_lower or '3 phase' in query_lower:
        if not any(k == 'phase' for k, v in attrs):
            attrs.append(("phase", "three phase"))
    elif 'single phase' in query_lower or '1 phase' in query_lower:
        if not any(k == 'phase' for k, v in attrs):
            attrs.append(("phase", "single phase"))
    
    # Condition
    if 'new' in query_lower.split() and not any(k == 'condition' for k, v in attrs):
        attrs.append(("condition", "new"))
    elif 'used' in query_lower.split() and not any(k == 'condition' for k, v in attrs):
        attrs.append(("condition", "used"))
    
    # Country of origin
    if 'made in india' in query_lower or 'indian' in query_lower:
        attrs.append(("country of origin", "made in india"))
    
    return attrs

def format_output_row(query, attrs):
    """Format a query and its attributes as a CSV row"""
    row = [query]
    for key, value in attrs:
        row.extend([key, value])
    return row

def main():
    print("Loading attributes...")
    attr_by_key = load_attributes('unique_key_val_96_cat.csv')
    print(f"Loaded {len(attr_by_key)} attribute keys")
    
    # Print some stats
    print("\nTop attribute keys by value count:")
    for key in sorted(attr_by_key.keys(), key=lambda k: len(attr_by_key[k]), reverse=True)[:15]:
        print(f"  {key}: {len(attr_by_key[key])} values")
    
    print("\nGenerating queries...")
    
    # Generate different types of queries
    simple_queries = generate_simple_queries(attr_by_key, count=200)
    print(f"Generated {len(simple_queries)} simple queries")
    
    medium_queries = generate_medium_queries(attr_by_key, count=400)
    print(f"Generated {len(medium_queries)} medium queries")
    
    complex_queries = generate_complex_queries(attr_by_key, count=250)
    print(f"Generated {len(complex_queries)} complex queries")
    
    long_queries = generate_long_queries(attr_by_key, count=150)
    print(f"Generated {len(long_queries)} long queries")
    
    # Combine all queries
    all_queries = simple_queries + medium_queries + complex_queries + long_queries
    
    # Shuffle to mix different types
    random.shuffle(all_queries)
    
    print(f"\nTotal queries generated: {len(all_queries)}")
    
    # Find max number of attributes
    max_attrs = max(len(attrs) for _, attrs in all_queries)
    print(f"Maximum attributes per query: {max_attrs}")
    
    # Create header
    header = ['query']
    for i in range(1, max_attrs + 1):
        header.extend([f'attr_key_{i}', f'attr_value_{i}'])
    
    # Write to CSV
    output_file = 'synthetic_validation_dataset.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for query, attrs in all_queries:
            row = [query]
            for key, value in attrs:
                row.extend([key, value])
            # Pad with empty strings if needed
            while len(row) < len(header):
                row.append('')
            writer.writerow(row)
    
    print(f"\nDataset saved to: {output_file}")
    
    # Print some examples
    print("\n" + "="*80)
    print("SAMPLE QUERIES FROM GENERATED DATASET:")
    print("="*80)
    
    for i, (query, attrs) in enumerate(all_queries[:10]):
        print(f"\n{i+1}. Query: {query}")
        print("   Attributes:")
        for key, value in attrs:
            print(f"     - {key}: {value}")

if __name__ == "__main__":
    main()
