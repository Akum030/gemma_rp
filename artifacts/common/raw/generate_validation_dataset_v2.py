"""
Generate Synthetic Validation Dataset for Attribute Extraction - v2
Creates ~1000 queries with accurately extracted attributes based on real query patterns
and human-evaluated attribute key-value pairs.
"""

import pandas as pd
import random
import csv
from collections import defaultdict
import re

# Load the attribute key-value pairs
def load_attributes(filepath):
    """Load and organize attributes by key"""
    attr_by_key = defaultdict(set)
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if ',' in line:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip().lower()
                    if key and value and len(value) > 1:
                        # Filter out garbage values
                        if value not in ['abc', 'xxx', 'zzz', 'na', 'nil', 'see pdf']:
                            attr_by_key[key].add(value)
    # Convert sets to lists
    return {k: list(v) for k, v in attr_by_key.items()}

# Define product types for this category
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
    "pet extruder", "epe foam extruder", "wpc extruder", "pp extruder",
    "pvc pipe extruder", "xlpe cable extruder", "plastic recycling extruder"
]

# Clean capacity values
CAPACITIES = [
    "5 kg", "10 kg", "20 kg", "25 kg", "30 kg", "50 kg", "100 kg", "200 kg", "500 kg",
    "5 kg/hr", "10 kg/hr", "25 kg/hr", "50 kg/hr", "100 kg/hr", "150 kg/hr", "200 kg/hr",
    "250 kg/hr", "300 kg/hr", "500 kg/hr", "750 kg/hr", "1000 kg/hr",
    "1 tpd", "5 tpd", "10 tpd", "20 tpd", "50 tpd", "100 tpd", "200 tpd", "500 tpd",
    "1 ton", "5 ton", "10 ton", "50 ton", "100 ton", "500 ton",
    "100 liter", "200 liter", "500 liter", "1000 liter"
]

VOLTAGES = ["220 v", "230 v", "240 v", "380 v", "400 v", "415 v", "440 v", "480 v"]

PHASES = ["single phase", "three phase", "3 phase", "1 phase"]

AUTOMATION_GRADES = ["automatic", "semi-automatic", "fully automatic", "manual"]

BODY_MATERIALS = [
    "stainless steel", "mild steel", "ss 304", "ss 316", "ms", "ss",
    "cast iron", "aluminium", "titanium", "pp", "hdpe", "pvc"
]

BRANDS = [
    "kabra", "rajco", "teknik", "labh group", "swaraj", "eureka", "prism",
    "gold star", "popular", "unique", "mahindra", "turbo", "laxmi"
]

APPLICATIONS = [
    "industrial", "laboratory", "pharmaceutical", "food processing",
    "chemical industries", "plastic processing", "wire & cable",
    "packaging", "agricultural", "recycling", "research"
]

POWERS = [
    "1 hp", "2 hp", "3 hp", "5 hp", "7.5 hp", "10 hp", "15 hp", "20 hp", "25 hp", "50 hp",
    "1 kw", "2 kw", "3 kw", "5 kw", "7.5 kw", "10 kw", "15 kw", "20 kw", "50 kw"
]

FREQUENCIES = ["50 hz", "60 hz", "50/60 hz"]

SCREW_DESIGNS = ["twin screw", "single screw", "conical", "parallel", "co-rotating"]

COLORS = ["silver", "blue", "white", "gray", "green"]

PURITIES = ["99%", "99.9%", "99.99%", "99.95%", "999"]

CONDITIONS = ["new", "used", "refurbished"]

WARRANTIES = ["1 year", "2 years", "12 months", "24 months"]


def generate_simple_queries(count=200):
    """Generate simple queries with 1-2 attributes"""
    queries = []
    
    for _ in range(count):
        product = random.choice(PRODUCTS)
        attrs = [("product", product)]
        query_parts = []
        
        pattern = random.randint(1, 8)
        
        if pattern == 1:
            # Just product name
            query = product
            
        elif pattern == 2:
            # Product + capacity
            cap = random.choice(CAPACITIES)
            query = f"{cap} {product}"
            attrs.append(("capacity", cap))
            
        elif pattern == 3:
            # Automation + product
            auto = random.choice(AUTOMATION_GRADES)
            query = f"{auto} {product}"
            attrs.append(("automation grade", auto))
            
        elif pattern == 4:
            # Product + voltage
            volt = random.choice(VOLTAGES)
            query = f"{product} {volt}"
            attrs.append(("voltage", volt))
            
        elif pattern == 5:
            # Brand + product
            brand = random.choice(BRANDS)
            query = f"{brand} {product}"
            attrs.append(("brand", brand))
            
        elif pattern == 6:
            # Material + product
            mat = random.choice(BODY_MATERIALS)
            query = f"{mat} {product}"
            attrs.append(("body material", mat))
            
        elif pattern == 7:
            # Product for application
            app = random.choice(APPLICATIONS)
            query = f"{product} for {app}"
            attrs.append(("usage/application", app))
            
        elif pattern == 8:
            # Condition + product
            cond = random.choice(CONDITIONS)
            query = f"{cond} {product}"
            attrs.append(("condition", cond))
        
        queries.append((query, attrs))
    
    return queries


def generate_medium_queries(count=400):
    """Generate medium complexity queries with 2-4 attributes"""
    queries = []
    
    for _ in range(count):
        product = random.choice(PRODUCTS)
        attrs = [("product", product)]
        
        pattern = random.randint(1, 15)
        
        if pattern == 1:
            # Capacity + automation + product
            cap = random.choice(CAPACITIES)
            auto = random.choice(AUTOMATION_GRADES)
            query = f"{cap} {auto} {product}"
            attrs.extend([("capacity", cap), ("automation grade", auto)])
            
        elif pattern == 2:
            # Product + voltage + phase
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            query = f"{product} {volt} {phase}"
            attrs.extend([("voltage", volt), ("phase", phase)])
            
        elif pattern == 3:
            # Brand + product + capacity
            brand = random.choice(BRANDS)
            cap = random.choice(CAPACITIES)
            query = f"{brand} {product} {cap}"
            attrs.extend([("brand", brand), ("capacity", cap)])
            
        elif pattern == 4:
            # Material + product + capacity
            mat = random.choice(BODY_MATERIALS)
            cap = random.choice(CAPACITIES)
            query = f"{mat} {product} {cap} capacity"
            attrs.extend([("body material", mat), ("capacity", cap)])
            
        elif pattern == 5:
            # Product for application + capacity
            app = random.choice(APPLICATIONS)
            cap = random.choice(CAPACITIES)
            query = f"{product} for {app} {cap}"
            attrs.extend([("usage/application", app), ("capacity", cap)])
            
        elif pattern == 6:
            # Automation + product + voltage
            auto = random.choice(AUTOMATION_GRADES)
            volt = random.choice(VOLTAGES)
            query = f"{auto} {product} {volt}"
            attrs.extend([("automation grade", auto), ("voltage", volt)])
            
        elif pattern == 7:
            # Capacity + product + material body
            cap = random.choice(CAPACITIES)
            mat = random.choice(BODY_MATERIALS)
            query = f"{cap} {product} {mat} body"
            attrs.extend([("capacity", cap), ("body material", mat)])
            
        elif pattern == 8:
            # Product + power + capacity
            power = random.choice(POWERS)
            cap = random.choice(CAPACITIES)
            query = f"{product} {power} motor {cap}"
            attrs.extend([("motor power", power), ("capacity", cap)])
            
        elif pattern == 9:
            # Automation + material + product
            auto = random.choice(AUTOMATION_GRADES)
            mat = random.choice(BODY_MATERIALS)
            query = f"{auto} {mat} {product}"
            attrs.extend([("automation grade", auto), ("body material", mat)])
            
        elif pattern == 10:
            # Product + screw design + capacity
            screw = random.choice(SCREW_DESIGNS)
            cap = random.choice(CAPACITIES)
            query = f"{product} {screw} design {cap}"
            attrs.extend([("screw design", screw), ("capacity", cap)])
            
        elif pattern == 11:
            # Brand + automation + product
            brand = random.choice(BRANDS)
            auto = random.choice(AUTOMATION_GRADES)
            query = f"{brand} {auto} {product}"
            attrs.extend([("brand", brand), ("automation grade", auto)])
            
        elif pattern == 12:
            # Product with power + voltage
            power = random.choice(POWERS)
            volt = random.choice(VOLTAGES)
            query = f"{product} with {power} power {volt}"
            attrs.extend([("power", power), ("voltage", volt)])
            
        elif pattern == 13:
            # Material body + product + capacity
            mat = random.choice(BODY_MATERIALS)
            cap = random.choice(CAPACITIES)
            query = f"{mat} body {product} {cap}"
            attrs.extend([("body material", mat), ("capacity", cap)])
            
        elif pattern == 14:
            # Product + voltage + frequency
            volt = random.choice(VOLTAGES)
            freq = random.choice(FREQUENCIES)
            query = f"{product} {volt} {freq}"
            attrs.extend([("voltage", volt), ("frequency", freq)])
            
        elif pattern == 15:
            # Capacity + phase + product
            cap = random.choice(CAPACITIES)
            phase = random.choice(PHASES)
            query = f"{cap} {phase} {product}"
            attrs.extend([("capacity", cap), ("phase", phase)])
        
        queries.append((query, attrs))
    
    return queries


def generate_complex_queries(count=250):
    """Generate complex queries with 4-6 attributes"""
    queries = []
    
    for _ in range(count):
        product = random.choice(PRODUCTS)
        attrs = [("product", product)]
        
        pattern = random.randint(1, 10)
        
        if pattern == 1:
            # Brand + automation + product, capacity, voltage, phase
            brand = random.choice(BRANDS)
            auto = random.choice(AUTOMATION_GRADES)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            query = f"{brand} {auto} {product}, {cap}, {volt}, {phase}"
            attrs.extend([("brand", brand), ("automation grade", auto), 
                         ("capacity", cap), ("voltage", volt), ("phase", phase)])
            
        elif pattern == 2:
            # Material body product with capacity and voltage
            mat = random.choice(BODY_MATERIALS)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            query = f"{mat} body {product} with {cap} capacity and {volt} voltage"
            attrs.extend([("body material", mat), ("capacity", cap), ("voltage", volt)])
            
        elif pattern == 3:
            # Automation product for application, capacity, power
            auto = random.choice(AUTOMATION_GRADES)
            app = random.choice(APPLICATIONS)
            cap = random.choice(CAPACITIES)
            power = random.choice(POWERS)
            query = f"{auto} {product} for {app}, capacity: {cap}, power: {power}"
            attrs.extend([("automation grade", auto), ("usage/application", app),
                         ("capacity", cap), ("power", power)])
            
        elif pattern == 4:
            # Product - brand make, capacity, material, phase
            brand = random.choice(BRANDS)
            cap = random.choice(CAPACITIES)
            mat = random.choice(BODY_MATERIALS)
            phase = random.choice(PHASES)
            query = f"{product} - {brand} make, {cap}, {mat}, {phase}"
            attrs.extend([("brand", brand), ("capacity", cap), 
                         ("body material", mat), ("phase", phase)])
            
        elif pattern == 5:
            # Capacity automation product voltage phase material body
            cap = random.choice(CAPACITIES)
            auto = random.choice(AUTOMATION_GRADES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            mat = random.choice(BODY_MATERIALS)
            query = f"{cap} {auto} {product} {volt} {phase} {mat} body"
            attrs.extend([("capacity", cap), ("automation grade", auto), 
                         ("voltage", volt), ("phase", phase), ("body material", mat)])
            
        elif pattern == 6:
            # Industrial product brand capacity voltage automation
            brand = random.choice(BRANDS)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            auto = random.choice(AUTOMATION_GRADES)
            query = f"industrial {product} {brand} {cap} {volt} {auto}"
            attrs.extend([("usage/application", "industrial"), ("brand", brand),
                         ("capacity", cap), ("voltage", volt), ("automation grade", auto)])
            
        elif pattern == 7:
            # Product machine capacity output voltage phase material
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            mat = random.choice(BODY_MATERIALS)
            query = f"{product} machine {cap} output {volt} {phase} {mat}"
            attrs.extend([("capacity", cap), ("voltage", volt), 
                         ("phase", phase), ("body material", mat)])
            
        elif pattern == 8:
            # Screw design product capacity automation voltage
            screw = random.choice(SCREW_DESIGNS)
            cap = random.choice(CAPACITIES)
            auto = random.choice(AUTOMATION_GRADES)
            volt = random.choice(VOLTAGES)
            query = f"{screw} {product} {cap} {auto} {volt}"
            attrs.extend([("screw design", screw), ("capacity", cap),
                         ("automation grade", auto), ("voltage", volt)])
            
        elif pattern == 9:
            # Product for application, capacity, voltage, brand
            app = random.choice(APPLICATIONS)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            brand = random.choice(BRANDS)
            query = f"{product} for {app} use, {cap}, {volt}, {brand} brand"
            attrs.extend([("usage/application", app), ("capacity", cap),
                         ("voltage", volt), ("brand", brand)])
            
        elif pattern == 10:
            # Automation material product, capacity, voltage, phase
            auto = random.choice(AUTOMATION_GRADES)
            mat = random.choice(BODY_MATERIALS)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            query = f"{auto} {mat} {product}, capacity: {cap}, voltage: {volt}, phase: {phase}"
            attrs.extend([("automation grade", auto), ("body material", mat),
                         ("capacity", cap), ("voltage", volt), ("phase", phase)])
        
        queries.append((query, attrs))
    
    return queries


def generate_long_queries(count=150):
    """Generate longer descriptive queries with many attributes"""
    queries = []
    
    for _ in range(count):
        product = random.choice(PRODUCTS)
        attrs = [("product", product)]
        
        pattern = random.randint(1, 8)
        
        if pattern == 1:
            brand = random.choice(BRANDS)
            auto = random.choice(AUTOMATION_GRADES)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            mat = random.choice(BODY_MATERIALS)
            app = random.choice(APPLICATIONS)
            query = f"{brand} {auto} {product} machine with {cap} capacity, {volt} voltage, {phase}, {mat} body, suitable for {app}"
            attrs.extend([("brand", brand), ("automation grade", auto), ("capacity", cap),
                         ("voltage", volt), ("phase", phase), ("body material", mat),
                         ("usage/application", app)])
            
        elif pattern == 2:
            screw = random.choice(SCREW_DESIGNS)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            mat = random.choice(BODY_MATERIALS)
            brand = random.choice(BRANDS)
            auto = random.choice(AUTOMATION_GRADES)
            query = f"{product} - {screw} design, {cap} output, {volt}, {phase}, {mat} construction, {brand} brand, {auto} operation"
            attrs.extend([("screw design", screw), ("capacity", cap), ("voltage", volt),
                         ("phase", phase), ("body material", mat), ("brand", brand),
                         ("automation grade", auto)])
            
        elif pattern == 3:
            auto = random.choice(AUTOMATION_GRADES)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            mat = random.choice(BODY_MATERIALS)
            app = random.choice(APPLICATIONS)
            query = f"looking for {auto} {product} with specifications: capacity {cap}, voltage {volt}, phase {phase}, body material {mat}, application {app}"
            attrs.extend([("automation grade", auto), ("capacity", cap), ("voltage", volt),
                         ("phase", phase), ("body material", mat), ("usage/application", app)])
            
        elif pattern == 4:
            brand = random.choice(BRANDS)
            auto = random.choice(AUTOMATION_GRADES)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            mat = random.choice(BODY_MATERIALS)
            power = random.choice(POWERS)
            query = f"{brand} make {auto} {product}, production capacity: {cap}, voltage: {volt}, phase: {phase}, material: {mat}, power: {power}"
            attrs.extend([("brand", brand), ("automation grade", auto), ("capacity", cap),
                         ("voltage", volt), ("phase", phase), ("body material", mat),
                         ("motor power", power)])
            
        elif pattern == 5:
            auto = random.choice(AUTOMATION_GRADES)
            screw = random.choice(SCREW_DESIGNS)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            mat = random.choice(BODY_MATERIALS)
            brand = random.choice(BRANDS)
            app = random.choice(APPLICATIONS)
            query = f"high quality {auto} {product} {screw} type, {cap}, {volt} supply, {phase}, {mat} body, {brand} brand for {app}"
            attrs.extend([("automation grade", auto), ("screw design", screw), ("capacity", cap),
                         ("voltage", volt), ("phase", phase), ("body material", mat),
                         ("brand", brand), ("usage/application", app)])
            
        elif pattern == 6:
            brand = random.choice(BRANDS)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            mat = random.choice(BODY_MATERIALS)
            auto = random.choice(AUTOMATION_GRADES)
            query = f"{product} machine specifications - brand: {brand}, capacity: {cap}, voltage: {volt}, phase: {phase}, body material: {mat}, automation: {auto}"
            attrs.extend([("brand", brand), ("capacity", cap), ("voltage", volt),
                         ("phase", phase), ("body material", mat), ("automation grade", auto)])
            
        elif pattern == 7:
            auto = random.choice(AUTOMATION_GRADES)
            screw = random.choice(SCREW_DESIGNS)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            mat = random.choice(BODY_MATERIALS)
            query = f"industrial grade {auto} {product} with {screw} design, {cap} capacity, operating voltage {volt}, {phase}, {mat} body material"
            attrs.extend([("usage/application", "industrial"), ("automation grade", auto),
                         ("screw design", screw), ("capacity", cap), ("voltage", volt),
                         ("phase", phase), ("body material", mat)])
            
        elif pattern == 8:
            auto = random.choice(AUTOMATION_GRADES)
            app = random.choice(APPLICATIONS)
            cap = random.choice(CAPACITIES)
            volt = random.choice(VOLTAGES)
            phase = random.choice(PHASES)
            mat = random.choice(BODY_MATERIALS)
            query = f"{auto} {product} for {app} applications, {cap} capacity, {volt} voltage rating, {phase} power supply, {mat} body"
            attrs.extend([("automation grade", auto), ("usage/application", app),
                         ("capacity", cap), ("voltage", volt), ("phase", phase),
                         ("body material", mat)])
        
        queries.append((query, attrs))
    
    return queries


def main():
    print("Generating synthetic validation dataset...")
    print("=" * 60)
    
    # Generate different types of queries
    simple_queries = generate_simple_queries(count=200)
    print(f"Generated {len(simple_queries)} simple queries (1-2 attributes)")
    
    medium_queries = generate_medium_queries(count=400)
    print(f"Generated {len(medium_queries)} medium queries (2-4 attributes)")
    
    complex_queries = generate_complex_queries(count=250)
    print(f"Generated {len(complex_queries)} complex queries (4-6 attributes)")
    
    long_queries = generate_long_queries(count=150)
    print(f"Generated {len(long_queries)} long queries (6-8 attributes)")
    
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
    print("\n" + "=" * 80)
    print("SAMPLE QUERIES FROM GENERATED DATASET:")
    print("=" * 80)
    
    # Show examples from each category
    print("\n--- SIMPLE QUERIES (1-2 attributes) ---")
    for query, attrs in simple_queries[:3]:
        print(f"\nQuery: {query}")
        print("Attributes:", ", ".join([f"{k}: {v}" for k, v in attrs]))
    
    print("\n--- MEDIUM QUERIES (2-4 attributes) ---")
    for query, attrs in medium_queries[:3]:
        print(f"\nQuery: {query}")
        print("Attributes:", ", ".join([f"{k}: {v}" for k, v in attrs]))
    
    print("\n--- COMPLEX QUERIES (4-6 attributes) ---")
    for query, attrs in complex_queries[:3]:
        print(f"\nQuery: {query}")
        print("Attributes:", ", ".join([f"{k}: {v}" for k, v in attrs]))
    
    print("\n--- LONG QUERIES (6-8 attributes) ---")
    for query, attrs in long_queries[:3]:
        print(f"\nQuery: {query}")
        print("Attributes:", ", ".join([f"{k}: {v}" for k, v in attrs]))
    
    # Statistics
    print("\n" + "=" * 80)
    print("DATASET STATISTICS:")
    print("=" * 80)
    attr_counts = [len(attrs) for _, attrs in all_queries]
    print(f"Minimum attributes per query: {min(attr_counts)}")
    print(f"Maximum attributes per query: {max(attr_counts)}")
    print(f"Average attributes per query: {sum(attr_counts)/len(attr_counts):.2f}")
    
    # Count attribute key frequencies
    key_freq = defaultdict(int)
    for _, attrs in all_queries:
        for key, _ in attrs:
            key_freq[key] += 1
    
    print("\nAttribute key frequencies:")
    for key, count in sorted(key_freq.items(), key=lambda x: -x[1])[:15]:
        print(f"  {key}: {count}")


if __name__ == "__main__":
    main()
