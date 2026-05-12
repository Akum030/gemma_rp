import pandas as pd
import requests
import time
import json
import sys
import io
import os
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================
MODEL_NAME = "google/gemini-3-pro-preview"
MODEL_SHORT_NAME = "gemini_3_pro"

# Configuration
INPUT_CSV = "validation_queries.csv"
GEMINI_API_KEY = "os.environ.get("API_KEY", "")"
GEMINI_API_URL = "https://imllm.intermesh.net/v1/chat/completions"
DELAY_MS = 50
OUTPUT_CSV = f"compare/{MODEL_SHORT_NAME}_output.csv"
LOG_FILE = f"compare/{MODEL_SHORT_NAME}_log.txt"
BATCH_SIZE = 100
SAVE_INTERVAL = 10  # Save every 10 queries to prevent data loss

# ============================================================================
# PASTE YOUR COMPRESSED ATTRIBUTES HERE
# Copy ALL lines from compressed_attributes_isq.txt and paste below
# ============================================================================
ATTRIBUTE_DATASET = r"""
440 v:voltage:specification
380 v:voltage:specification
415 v:voltage:specification
440 v:voltage:specification
380 v:voltage:specification
415 v:voltage:specification
240 v:voltage:specification
400 v:voltage:specification
220 v:voltage:specification
230 volts:voltage:specification
220v:voltage:specification
440v:voltage:specification
220-400 vac:voltage:specification
360 v:voltage:specification
340 v:voltage:specification
230vac:voltage:specification
1000:voltage:specification
230v:voltage:specification
paint coated:surface finishing:specification
color coated:surface finishing:specification
painted:surface finishing:specification
powder coated:surface finishing:specification
good:surface finishing:specification
ms:surface finishing:specification
polished:surface finishing:specification
superior quality paint finish:surface finishing:specification
galvanised:surface finishing:specification
powder coated paint:surface finishing:specification
coated:surface finishing:specification
power coated / painted / chrome plated:surface finishing:specification
automatic:automation grade:specification
semi-automatic:automation grade:specification
fully:automation grade:specification
fully automatic:automation grade:specification
semiautomatic:automation grade:specification
manual:automation grade:specification
semi automatic:automation grade:specification
as per client requirement.:automation grade:specification
yes:automation grade:specification
a:automation grade:specification
semi automated:automation grade:specification
manual/automation:automation grade:specification
a grade:automation grade:specification
fully automatic touch screen:automation grade:specification
gold refining plant:automation grade:specification
three phase:phase:specification
3 phase:phase:specification
silver refining plant:phase:specification
single phase:phase:specification
1 phase:phase:specification
single:phase:specification
3:phase:specification
hand operated:phase:specification
single/three:phase:specification
shegal face 1.5kelo wat:phase:specification
1:phase:specification
three:phase:specification
single phase a.c:phase:specification
single or triple:phase:specification
single 220:phase:specification
stainless steel:body material:specification
mild steel:body material:specification
titanium,pp:body material:specification
titanium, glass, pph:body material:specification
ms:body material:specification
ss:body material:specification
iron:body material:specification
pp, upvc, titanium:body material:specification
p.p:body material:specification
poly proplyene:body material:specification
pp:body material:specification
pph:body material:specification
pu:body material:specification
steel:body material:specification
ms / ss:body material:specification
new only:i deal in:specification
new and second hand:i deal in:specification
second hand only:i deal in:specification
new:i deal in:specification
new one only:i deal in:specification
only new:i deal in:specification
30 inch:size:specification
45mm*45mm:size:specification
12 mm:size:specification
65/132:size:specification
2250x540x1160mm. (lxwxh):size:specification
5 x 5 x 5 to 22 x 8 12 ( l x w x h ):size:specification
x.x.x:size:specification
see pdf:size:specification
18 inch:size:specification
as per customer requirement:size:specification
19*50:size:specification
55 mm, height 750mm(approx:size:specification
65 mm:size:specification
dia 500:size:specification
as per design:size:specification
made in india:country of origin:specification
india:country of origin:specification
silver refining plant:heating range:specification
80c:heating range:specification
900:heating range:specification
35:heating range:specification
standard:heating range:specification
100:heating range:specification
fully automatic:heating range:specification
100c:heating range:specification
good:heating range:specification
50:heating range:specification
up to 1100 degree c:heating range:specification
auto heating:heating range:specification
110 degreec:heating range:specification
50 to 250 degree c:heating range:specification
50 to 250 deg c:heating range:specification
58 rpm:screw speed:specification
600 rpm:screw speed:specification
45 rpm:screw speed:specification
see pdf:screw speed:specification
50 rpm:screw speed:specification
5-5 rpm:screw speed:specification
1200 rpm:screw speed:specification
110 rpm:screw speed:specification
0-80 rpm:screw speed:specification
0-90 rpm:screw speed:specification
5-52 rpm:screw speed:specification
90 rpm:screw speed:specification
5.52 rpm:screw speed:specification
80rpm:screw speed:specification
4-45 rpm:screw speed:specification
plastic:material to be extruded:specification
aluminium:material to be extruded:specification
alumunium:material to be extruded:specification
noodle:material to be extruded:specification
puff:material to be extruded:specification
metal:material to be extruded:specification
pp tape:material to be extruded:specification
yarn:material to be extruded:specification
aluminum profiles:material to be extruded:specification
welding electrodes:material to be extruded:specification
aluminm melting furnace , 90 feet handling system with rotcutter & finish cutter and puller & streacher and handling table with all conveior belt and roller sleeve and agin oven and die oven and pollution system and dross recovery machine:material to be extruded:specification
any:material to be extruded:specification
pbat:material to be extruded:specification
copper and aluminium:material to be extruded:specification
pp abs hips hm:material to be extruded:specification
edr:brand:specification
gurukrupa enterprises:brand:specification
hulk lokpal:brand:specification
rajco:brand:specification
k-jhil:brand:specification
gold star:brand:specification
he:brand:specification
ek danta refiners:brand:specification
aec:brand:specification
microgold:brand:specification
prasad enterprise:brand:specification
kabra:brand:specification
jt:brand:specification
m tech jewel equipment:brand:specification
ddri:brand:specification
industrial:usage/application:specification
pharmaceutical industry, food and beverages and cosmetics industries:usage/application:specification
cosmetics:usage/application:specification
garbage bags,medical bags:usage/application:specification
wire & cable:usage/application:specification
chemical laboratory:usage/application:specification
mulch film:usage/application:specification
for the determination of bitumen percentage in bituminous mixtures:usage/application:specification
herbal extraction:usage/application:specification
herbal extractor plant:usage/application:specification
hospital and hotal:usage/application:specification
fire fighting:usage/application:specification
laundry:usage/application:specification
pharma lab:usage/application:specification
aluminium extrusion:usage/application:specification
0.5 kva:power:specification
2 hp:power:specification
5.5 hp:power:specification
50 hp:power:specification
0.75 hp:power:specification
10 hp:specification
1 hp:power:specification
20 hp:power:specification
30-40 hp:power:specification
15 hp:power:specification
3 hp:power:specification
40 hp:power:specification
60 hp:power:specification
2.5 kw:power:specification
4 hp:power:specification
30 hp:power:specification
11 kw:power:specification
25 kw:power:specification
7.5 hp:power:specification
300 kw:power:specification
22 kw:power:specification
gold refining plant:brand:specification
silver refining plant:brand:specification
prism:brand:specification
turbo:brand:specification
teknik:brand:specification
eureka:brand:specification
mahindra:brand:specification
laxmi:brand:specification
popular:brand:specification
unique:brand:specification
labh group:brand:specification
micro gold:brand:specification
best price gold:brand:specification
bhagirath:brand:specification
100 kg/hr:capacity:specification
1000 liter:capacity:specification
10 tpd:capacity:specification
5 ton:capacity:specification
200 kg:capacity:specification
10 kg/hr:capacity:specification
25 hp:capacity:specification
500 tpd:capacity:specification
500 ton:capacity:specification
30 kg:capacity:specification
5 kg:capacity:specification
200 kg/hr:capacity:specification
50 ton:capacity:specification
100 ton:capacity:specification
200 liter:capacity:specification
10 ton:capacity:specification
20 tpd:capacity:specification
100 tpd:capacity:specification
300 kg/hr:capacity:specification
10 kg:capacity:specification
20 kg:capacity:specification
100 liter:capacity:specification
50 kg/hr:capacity:specification
25 kg/hr:capacity:specification
1 tpd:capacity:specification
150 kg/hr:capacity:specification
50 hp:capacity:specification
1200 kg/hr:capacity:specification
twin screw:design:specification
parallel:design:specification
conical:design:specification
co-rotating:design:specification
cast iron:body material:specification
hdpe:body material:specification
pvc:body material:specification
titanium:body material:specification
ss 304:body material:specification
aluminium:body material:specification
copper:body material:specification
plastic:body material:specification
sheet metal:body material:specification
3 phase:phase:specification
1 phase:phase:specification
three phase:phase:specification
single phase:phase:specification
50 hz:frequency:specification
60 hz:frequency:specification
50-60 hz:frequency:specification
pharmaceutical:usage/application:specification
food processing:usage/application:specification
plastic processing:usage/application:specification
packaging:usage/application:specification
chemical:usage/application:specification
recycling:usage/application:specification
agriculture:usage/application:specification
herbal:usage/application:specification
cable:usage/application:specification
textile:usage/application:specification
paint coated:surface finishing:specification
powder coated:surface finishing:specification
polished:surface finishing:specification
galvanized:surface finishing:specification
stainless steel:surface finishing:specification
painted:surface finishing:specification
chrome plated:surface finishing:specification
anodized:surface finishing:specification
epe foam:product type:specification
pvc:product type:specification
ldpe:product type:specification
hdpe:product type:specification
pp:product type:specification
xlpe:product type:specification
film:product type:specification
sheet:product type:specification
pipe:product type:specification
cable:product type:specification
tube:product type:specification
pet:product type:specification
wpc:product type:specification
blown film:machine type:specification
extrusion:machine type:specification
extraction:machine type:specification
refinery:machine type:specification
mother baby:machine type:specification
twin screw:machine type:specification
monolayer:machine type:specification
multi layer:machine type:specification
co-rotating:screw type:specification
parallel:screw type:specification
conical:screw type:specification
counter-rotating:screw type:specification
190 kn:continuous load:specification
318 kn:continuous load:specification
223 kn:short term load:specification
420 kn:short term load:specification
320 kn:short term load:specification
470 kn:short term load:specification
190-250 kg/hr:output spvc filled:specification
130-170 kg/hr:output spvc filled:specification
530-700 kg/hr:output spvc filled:specification
90-100 kg/hr:max. output:specification
180-200 kg/hr:max. output:specification
130-140 kg/hr:max. output:specification
13nm/cm3:specific torque:specification
11.3 nm/cm3:specific torque:specification
7.2 nm/cm:specific torque:specification
14.6nm/cm3:specific torque:specification
8.7 nm/cm3:specific torque:specification
5.46nm/cm3:specific torque:specification

"""

def log_message(message, also_print=True):
    """Log message to file and optionally print"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    if also_print:
        print(message)

def parse_attribute_dataset(raw_data):
    """Parse the attribute dataset into a structured format"""
    lines = [line.strip() for line in raw_data.strip().split('\n') if line.strip()]
    
    # Remove placeholder text
    lines = [line for line in lines if not line.startswith('PASTE_') and not line.startswith('EACH_')]
    
    # Group by attribute name
    attr_dict = {}
    for line in lines:
        parts = line.split(':')
        if len(parts) == 3:
            value, name, attr_type = parts
            if name not in attr_dict:
                attr_dict[name] = []
            if value not in attr_dict[name]:
                attr_dict[name].append(value)
    
    return attr_dict

def create_dataset_prompt(query, attr_dict):
    """Create prompt with attribute dataset as training examples"""
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

def call_api(query, attr_dict, request_count, max_retries=3):
    """Call API with dataset context and return result"""
    for attempt in range(max_retries):
        try:
            prompt = create_dataset_prompt(query, attr_dict)
            
            payload = {
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 300
            }
            
            headers = {
                "Authorization": f"Bearer {GEMINI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content'].strip()
                content = content.replace("'", '"')
                
                try:
                    if content.startswith('[') and content.endswith(']'):
                        isq_list = json.loads(content)
                    else:
                        isq_list = [item.strip() for item in content.replace('\n', ',').split(',') if item.strip()]
                except:
                    isq_list = [content] if content else []
                
                valid_isqs = [isq for isq in isq_list if isq.count(':') == 2]
                
                return {
                    'success': True,
                    'query': query,
                    'attr_count': len(valid_isqs),
                    'isq_list': str(valid_isqs),
                    'isq_pipe': ' | '.join(valid_isqs),
                    'raw_output': content,
                    'request_number': request_count
                }
            else:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return {
                    'success': False,
                    'query': query,
                    'attr_count': 0,
                    'isq_list': '[]',
                    'isq_pipe': '',
                    'error': f"HTTP {response.status_code}",
                    'request_number': request_count
                }
                
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return {
                'success': False,
                'query': query,
                'attr_count': 0,
                'isq_list': '[]',
                'isq_pipe': '',
                'error': str(e),
                'request_number': request_count
            }

def save_results(results, output_file):
    """Save results to CSV file"""
    if results:
        df = pd.DataFrame(results)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        return True
    return False

def main():
    # Initialize log file
    os.makedirs('compare', exist_ok=True)
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"=== {MODEL_NAME} Processing Log ===\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Parse attribute dataset
    log_message("Parsing attribute dataset...")
    attr_dict = parse_attribute_dataset(ATTRIBUTE_DATASET)
    total_attrs = sum(len(values) for values in attr_dict.values())
    log_message(f"Loaded {len(attr_dict)} unique attribute types")
    log_message(f"Total attribute values: {total_attrs}")
    
    # Read queries
    log_message(f"Reading queries from: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    
    if 'query' not in df.columns:
        log_message("ERROR: 'query' column not found in CSV!")
        return
    
    queries = df['query'].dropna().tolist()
    total_queries = len(queries)
    
    log_message(f"Processing {total_queries} queries with {MODEL_NAME}")
    log_message(f"Output file: {OUTPUT_CSV}")
    log_message("=" * 80)
    
    results = []
    success_count = 0
    fail_count = 0
    request_count = 0
    
    try:
        for i, query in enumerate(queries, 1):
            request_count = i
            
            # Simple progress indicator
            print(f"[{MODEL_SHORT_NAME}] Request #{request_count}/{total_queries}", end="\r")
            
            result = call_api(str(query), attr_dict, request_count)
            
            if result['success']:
                success_count += 1
            else:
                fail_count += 1
                log_message(f"Failed query #{request_count}: {str(query)[:60]}", also_print=False)
            
            results.append(result)
            
            # Save incrementally every SAVE_INTERVAL queries
            if i % SAVE_INTERVAL == 0:
                save_results(results, OUTPUT_CSV)
            
            # Batch summary
            if i % BATCH_SIZE == 0:
                save_results(results, OUTPUT_CSV)
                progress_pct = (i/total_queries)*100
                log_message(f"Progress: {i}/{total_queries} ({progress_pct:.1f}%) | Success: {success_count} | Failed: {fail_count}")
            
            time.sleep(DELAY_MS / 1000)
        
        # Final save
        save_results(results, OUTPUT_CSV)
        
        # Final summary
        log_message("=" * 80)
        log_message(f"COMPLETED - {MODEL_NAME}")
        log_message(f"Total requests: {request_count}")
        log_message(f"Successful: {success_count} ({(success_count/total_queries)*100:.1f}%)")
        log_message(f"Failed: {fail_count} ({(fail_count/total_queries)*100:.1f}%)")
        
        total_attrs_extracted = sum(r.get('attr_count', 0) for r in results)
        avg_attrs = total_attrs_extracted / total_queries if total_queries > 0 else 0
        log_message(f"Total attributes extracted: {total_attrs_extracted}")
        log_message(f"Average attributes per query: {avg_attrs:.2f}")
        log_message(f"Results saved to: {OUTPUT_CSV}")
        log_message("=" * 80)
        
    except KeyboardInterrupt:
        log_message("\n\nInterrupted by user. Saving progress...")
        save_results(results, OUTPUT_CSV)
        log_message(f"Partial results saved. Processed {request_count}/{total_queries} queries")
    except Exception as e:
        log_message(f"\n\nERROR: {str(e)}")
        save_results(results, OUTPUT_CSV)
        log_message(f"Partial results saved. Processed {request_count}/{total_queries} queries")

if __name__ == "__main__":
    main()
