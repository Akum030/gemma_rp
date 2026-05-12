"""
Ground Truth + QMeans + Gemma V4 Comparison Pipeline
=====================================================
This script:
  1. Generates Ground Truth (Claude-quality rule-based extraction for Electric Motors)
  2. Fetches QMeans results via API
  3. Reads Gemma V4 results from CSV
  4. Builds final comparison CSV

Usage:
  Step 1 (GT + QMeans only, while waiting for Gemma):
    python generate_gt_qmeans_compare.py --queries 76cat_queries.csv --step prepare

  Step 2 (Full comparison after Gemma results available):
    python generate_gt_qmeans_compare.py --queries 76cat_queries.csv --gemma gemma_v4_1000_results.csv --step compare
"""

import re
import csv
import json
import time
import urllib.parse
import urllib.request
import argparse
import os


# ===========================================================================
# PART 1: GROUND TRUTH GENERATOR (Claude-quality rule-based for Electric Motors)
# ===========================================================================

BRANDS = {
    # Major motor brands
    'siemens': 'Siemens', 'abb': 'ABB', 'crompton': 'Crompton', 'crompton greaves': 'Crompton Greaves',
    'havells': 'Havells', 'kirloskar': 'Kirloskar', 'bharat bijlee': 'Bharat Bijlee',
    'lubi': 'Lubi', 'panasonic': 'Panasonic', 'bosch': 'Bosch', 'makita': 'Makita',
    'schneider': 'Schneider', 'allen bradley': 'Allen Bradley', 'mitsubishi': 'Mitsubishi',
    'kollmorgen': 'Kollmorgen', 'honeywell': 'Honeywell', 'danfoss': 'Danfoss',
    'eaton': 'Eaton', 'parker': 'Parker', 'rotork': 'Rotork', 'belimo': 'Belimo',
    'oriental': 'Oriental', 'godrej': 'Godrej', 'lawkim': 'Lawkim',
    'sunflag': 'Sunflag', 'kenstar': 'Kenstar', 'leadshine': 'Leadshine',
    'tata': 'Tata', 'voltas': 'Voltas', 'baldor': 'Baldor',
    'rexroth': 'Rexroth', 'hydromatik': 'Hydromatik', 'sew': 'SEW',
    'sew-eurodrive': 'SEW-Eurodrive', 'foredom': 'Foredom',
    'remi': 'Remi', 'rhino': 'Rhino', 'pbl': 'PBL', 'impel': 'Impel',
    'transtech': 'Transtech', 'weishaupt': 'Weishaupt', 'ecoflam': 'Ecoflam',
    'hanning': 'Hanning', 'festo': 'Festo', 'spal': 'Spal',
    'gold power': 'Gold Power', 'venex': 'Venex', 'suguna': 'Suguna',
    'paragon': 'Paragon', 'petrosa': 'Petrosa', 'happymodel': 'Happymodel',
    'yako': 'Yako', 'spg': 'SPG', 'powerspeed': 'PowerSpeed',
    'vtv': 'VTV', 'dz': 'DZ', 'dys': 'DYS',
    'ti motion': 'Ti Motion', 'jencoder': 'Jencoder', 'jayashree': 'Jayashree',
    'rexnord': 'Rexnord', 'rotomotive': 'Rotomotive', 'autonic': 'Autonic',
    'hindustan': 'Hindustan', 'bch': 'BCH', 'ge': 'GE',
    'l&t': 'L&T', 'l & t': 'L&T', 'landt': 'L&T',
    'cg': 'CG', 'bhavani': 'Bhavani', 'rawat': 'Rawat', 'delton': 'Delton',
    'arun': 'Arun', 'jyoti': 'Jyoti', 'alqer': 'Alqer', 'elldo': 'ELLDO',
    'vishal': 'Vishal', 'amdo': 'Amdo', 'kapcon': 'Kapcon',
    'apex cool': 'Apex Cool', 'am gold': 'AM Gold', 'peco': 'Peco',
    'boparai': 'Boparai', 'skn kelson': 'SKN Kelson',
    'crompton greaves': 'Crompton Greaves', 'godrej lawkim': 'Godrej Lawkim',
    'brueninghaus': 'Brueninghaus', 'intermot': 'Intermot',
    'laxmi': 'Laxmi', 'symphony': 'Symphony',
}

# Motor type keywords
MOTOR_TYPES = {
    'induction': 'induction motor',
    'servo': 'servo motor',
    'bldc': 'BLDC motor',
    'brushless dc': 'BLDC motor',
    'brushless': 'brushless motor',
    'stepper': 'stepper motor',
    'gear motor': 'gear motor',
    'geared motor': 'geared motor',
    'geared': 'geared motor',
    'dc motor': 'DC motor',
    'ac motor': 'AC motor',
    'synchronous': 'synchronous motor',
    'pmdc': 'PMDC motor',
    'hydraulic motor': 'hydraulic motor',
    'hydraulic piston': 'hydraulic piston motor',
    'pneumatic': 'pneumatic motor',
    'slip ring': 'slip ring motor',
    'squirrel cage': 'squirrel cage motor',
    'vibratory': 'vibratory motor',
    'vibration motor': 'vibration motor',
    'shaded pole': 'shaded pole motor',
    'universal motor': 'universal motor',
    'worm gear': 'worm geared motor',
    'helical gear': 'helical geared motor',
    'planetary gear': 'planetary geared motor',
    'orbital motor': 'orbital motor',
}

# Product types (not motors)
PRODUCT_TYPES = {
    'starter': 'starter',
    'dol starter': 'DOL starter',
    'soft starter': 'soft starter',
    'star delta starter': 'star delta starter',
    'motor starter': 'motor starter',
    'actuator': 'actuator',
    'linear actuator': 'linear actuator',
    'rotary actuator': 'rotary actuator',
    'pneumatic actuator': 'pneumatic actuator',
    'encoder': 'encoder',
    'rotary encoder': 'rotary encoder',
    'shaft encoder': 'shaft encoder',
    'carbon brush': 'carbon brush',
    'armature': 'armature',
    'positioner': 'positioner',
    'valve positioner': 'valve positioner',
    'slip ring': 'slip ring',
    'esc': 'ESC',
}

# Usage/application keywords
USAGE_MAP = {
    'cooler': 'cooler', 'chimney': 'chimney', 'exhaust': 'exhaust',
    'blower': 'blower', 'fan': 'fan', 'pump': 'pump',
    'vacuum cleaner': 'vacuum cleaner', 'mixer grinder': 'mixer grinder',
    'mixer': 'mixer', 'grinder': 'grinder',
    'shutter': 'rolling shutter', 'rolling shutter': 'rolling shutter',
    'gate': 'gate', 'sliding gate': 'sliding gate', 'swing gate': 'swing gate',
    'door': 'door', 'sliding door': 'sliding door',
    'lift': 'lift', 'crane': 'crane', 'sewing': 'sewing machine',
    'centrifuge': 'centrifuge', 'polisher': 'polisher',
    'incubator': 'incubator', 'table fan': 'table fan',
    'ceiling fan': 'ceiling fan', 'wall fan': 'wall fan',
    'desert': 'desert cooler', 'air conditioner': 'air conditioner',
    'kitchen hood': 'kitchen hood', 'burner': 'burner',
    'concrete vibrator': 'concrete vibrator', 'spindle': 'spindle',
    'tower fan': 'tower fan', 'air cooler': 'air cooler',
    'submersible': 'submersible pump', 'drone': 'drone',
    'rc car': 'RC car', 'dvd': 'DVD player', 'mig': 'MIG welding',
}

# Mounting types
MOUNTING_MAP = {
    'foot mounted': 'foot mounted', 'foot mount': 'foot mounted',
    'flange mounted': 'flange mounted', 'flange mount': 'flange mounted',
    'foot cum flange': 'foot cum flange mounted',
    'face mounted': 'face mounted',
    'vertical': 'vertical',
}

# Enclosure types
ENCLOSURE_MAP = {
    'tefc': 'TEFC', 'ip55': 'IP55', 'ip54': 'IP54', 'ip44': 'IP44',
    'flameproof': 'flameproof', 'flame proof': 'flameproof',
    'fireproof': 'flameproof', 'drip proof': 'drip proof',
    'explosion proof': 'explosion proof',
}


def clean_query(query):
    """Clean URL-encoded and special characters from query."""
    q = query.strip()
    # Decode URL encoding
    try:
        q = urllib.parse.unquote(q)
    except:
        pass
    # Replace + with space
    q = q.replace('+', ' ')
    # Replace hyphens between words (but keep hyphens in model numbers)
    # Remove extra spaces
    q = re.sub(r'\s+', ' ', q).strip()
    return q


def extract_ground_truth(query):
    """Extract attributes from query using comprehensive rules for Electric Motors domain."""
    original_query = query
    query_clean = clean_query(query)
    q = query_clean.lower()
    attrs = {}

    # --- BRAND detection ---
    # Sort by length (longest first) to match "crompton greaves" before "crompton"
    for brand_key in sorted(BRANDS.keys(), key=len, reverse=True):
        # Word boundary matching
        pattern = r'(?:^|\s|,)' + re.escape(brand_key) + r'(?:\s|,|$|\'s)'
        if re.search(pattern, q):
            attrs['brand'] = BRANDS[brand_key]
            break
        # Also try without strict boundaries for some brands
        if brand_key in q and len(brand_key) >= 3:
            # Avoid false positives for very short brand names
            if brand_key not in ('ge', 'dz', 'cg', 'spg'):
                attrs['brand'] = BRANDS[brand_key]
                break
            elif re.search(r'\b' + re.escape(brand_key) + r'\b', q):
                attrs['brand'] = BRANDS[brand_key]
                break

    # --- POWER detection ---
    # HP
    hp_match = re.search(r'(\d+\.?\d*)\s*(?:hp|horse\s*power)', q)
    if hp_match:
        attrs['power'] = hp_match.group(1) + ' HP'

    # KW
    kw_match = re.search(r'(\d+\.?\d*)\s*(?:kw|kilowatt)', q)
    if kw_match:
        if 'power' not in attrs:
            attrs['power'] = kw_match.group(1) + ' KW'
        else:
            attrs['power_kw'] = kw_match.group(1) + ' KW'

    # Watt (but not Kilowatt)
    w_match = re.search(r'(\d+\.?\d*)\s*(?:watt|watts|w)(?:\b)', q)
    if w_match and not re.search(r'(\d+\.?\d*)\s*kw', q):
        val = w_match.group(1)
        if val not in q.split('v')[0] if 'v' in q else True:  # Avoid confusing voltage with wattage
            if 'power' not in attrs:
                attrs['power'] = val + ' W'

    # --- PHASE detection ---
    if re.search(r'(?:single|1)\s*(?:-\s*)?phase', q):
        attrs['phase'] = 'single phase'
    elif re.search(r'(?:three|3)\s*(?:-\s*)?phase', q):
        attrs['phase'] = 'three phase'
    elif re.search(r'(?:two|2)\s*(?:-\s*)?phase', q):
        attrs['phase'] = 'two phase'

    # --- VOLTAGE detection ---
    # Match patterns like 415v, 415 v, 415V, 415 volt
    v_match = re.search(r'(\d+\.?\d*)\s*(?:v|volt|volts)(?:\b)', q)
    if v_match:
        attrs['voltage'] = v_match.group(1) + 'V'

    # --- SPEED (RPM) detection ---
    rpm_match = re.search(r'(\d+)\s*(?:rpm)', q)
    if rpm_match:
        attrs['speed'] = rpm_match.group(1) + ' RPM'

    # --- MOTOR TYPE detection ---
    for mtype_key in sorted(MOTOR_TYPES.keys(), key=len, reverse=True):
        if mtype_key in q:
            attrs['motor_type'] = MOTOR_TYPES[mtype_key]
            break

    # --- PRODUCT TYPE detection (for non-motor products) ---
    if 'motor_type' not in attrs:
        for ptype_key in sorted(PRODUCT_TYPES.keys(), key=len, reverse=True):
            if ptype_key in q:
                attrs['product_type'] = PRODUCT_TYPES[ptype_key]
                break

    # --- USAGE / APPLICATION detection ---
    for usage_key in sorted(USAGE_MAP.keys(), key=len, reverse=True):
        if usage_key in q:
            attrs['usage'] = USAGE_MAP[usage_key]
            break

    # --- MOUNTING detection ---
    for mount_key in sorted(MOUNTING_MAP.keys(), key=len, reverse=True):
        if mount_key in q:
            attrs['mounting'] = MOUNTING_MAP[mount_key]
            break

    # --- ENCLOSURE detection ---
    for enc_key in sorted(ENCLOSURE_MAP.keys(), key=len, reverse=True):
        if enc_key in q:
            attrs['enclosure'] = ENCLOSURE_MAP[enc_key]
            break

    # --- EFFICIENCY detection ---
    eff_match = re.search(r'\b(ie[234])\b', q)
    if eff_match:
        attrs['efficiency'] = eff_match.group(1).upper()

    # --- POLES detection ---
    pole_match = re.search(r'(\d+)\s*pole', q)
    if pole_match:
        attrs['poles'] = pole_match.group(1) + ' pole'

    # --- SHAFT type ---
    if re.search(r'dual\s*shaft|double\s*shaft', q):
        attrs['shaft_type'] = 'dual shaft'
    elif re.search(r'hollow\s*shaft', q):
        attrs['shaft_type'] = 'hollow shaft'
    elif re.search(r'side\s*shaft', q):
        attrs['shaft_type'] = 'side shaft'

    # --- MODEL NUMBER detection ---
    # Siemens model patterns
    siemens_match = re.search(r'(1fk2[\w-]+|1fl[26][\w-]+|1le[\w-]+|3tw[\w-]+|6dr[\w-]+)', q)
    if siemens_match:
        attrs['model_number'] = siemens_match.group(1).upper()

    # General model number patterns (alphanumeric with hyphens)
    if 'model_number' not in attrs:
        model_match = re.search(r'\b([a-z]{1,4}\d{2,}[\w-]*)\b', q)
        if model_match:
            candidate = model_match.group(1)
            # Filter out common false positives
            if len(candidate) >= 5 and not re.match(r'^\d+$', candidate):
                if candidate.lower() not in ('motor', 'phase', 'three', 'single', 'volts', 'watt'):
                    attrs['model_number'] = candidate.upper()

    # --- FRAME SIZE / NEMA detection ---
    nema_match = re.search(r'nema\s*(\d+)', q)
    if nema_match:
        attrs['frame_size'] = 'NEMA ' + nema_match.group(1)

    # --- STEP ANGLE for stepper motors ---
    angle_match = re.search(r'(\d+\.?\d*)\s*degree', q)
    if angle_match:
        attrs['step_angle'] = angle_match.group(1) + ' degree'

    # --- WEIGHT ---
    weight_match = re.search(r'(\d+\.?\d*)\s*(?:kg|gram|grams|gm)', q)
    if weight_match:
        unit = 'kg' if 'kg' in q[weight_match.start():weight_match.end()+3] else 'gm'
        attrs['weight'] = weight_match.group(1) + ' ' + unit

    # --- CURRENT (Amps) ---
    amp_match = re.search(r'(\d+\.?\d*)\s*(?:amp|amps|a)\b', q)
    if amp_match:
        attrs['current'] = amp_match.group(1) + ' A'

    # --- IP RATING ---
    ip_match = re.search(r'\b(ip\d{2})\b', q)
    if ip_match:
        attrs['ip_rating'] = ip_match.group(1).upper()

    # --- MATERIAL ---
    if 'aluminium' in q or 'aluminum' in q:
        attrs['material'] = 'aluminium'
    elif 'cast iron' in q:
        attrs['material'] = 'cast iron'
    elif 'copper' in q:
        attrs['material'] = 'copper'
    elif 'mild steel' in q:
        attrs['material'] = 'mild steel'

    # --- KV rating for brushless ---
    kv_match = re.search(r'(\d+)\s*kv\b', q)
    if kv_match and 'kw' not in q:
        attrs['kv_rating'] = kv_match.group(1) + ' KV'

    # --- GEAR RATIO ---
    ratio_match = re.search(r'(?:ratio|reducer)\s*(\d+:\d+)', q)
    if ratio_match:
        attrs['gear_ratio'] = ratio_match.group(1)

    # If we found nothing meaningful, try to at least identify the product category
    if len(attrs) == 0:
        # Check if it's a motor-related query at all
        if re.search(r'motor|motar|moter|starter|actuator|encoder|brush|armature|positioner', q):
            if 'motor' in q or 'motar' in q or 'moter' in q:
                attrs['product_type'] = 'motor'
            elif 'starter' in q:
                attrs['product_type'] = 'starter'
            elif 'actuator' in q:
                attrs['product_type'] = 'actuator'
            elif 'encoder' in q:
                attrs['product_type'] = 'encoder'

    return attrs


# ===========================================================================
# PART 2: QMEANS API FETCHER
# ===========================================================================

QMEANS_URL = "http://34.93.70.216:8009/attribute-search-qmeans"


def fetch_qmeans(query, timeout=30, retries=2):
    """Fetch QMeans attributes for a single query."""
    encoded_query = urllib.parse.quote(query, safe='')
    url = f"{QMEANS_URL}?query={encoded_query}"

    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))

            if data.get('response_code') == 200:
                attrs = {}
                for token, info in data.get('attributes', {}).items():
                    attr_name = info.get('attr_name', '')
                    attr_value = info.get('attr_value', '')
                    if attr_name and attr_value:
                        attrs[attr_name] = attr_value
                return {
                    'success': True,
                    'attributes': attrs,
                    'response_time': data.get('response_time', 0)
                }
            else:
                return {'success': False, 'attributes': {}, 'response_time': 0}

        except Exception as e:
            if attempt < retries:
                time.sleep(1)
                continue
            return {'success': False, 'attributes': {}, 'error': str(e), 'response_time': 0}


def fetch_all_qmeans(queries, output_file='qmeans_results.json'):
    """Fetch QMeans for all queries with progress tracking."""
    results = []
    total = len(queries)

    print(f"\nFetching QMeans for {total} queries...")
    print("=" * 80)

    for idx, query in enumerate(queries):
        result = fetch_qmeans(query)
        result['query'] = query
        results.append(result)

        if (idx + 1) % 50 == 0:
            print(f"  [{idx + 1}/{total}] QMeans processed "
                  f"({sum(1 for r in results if r['success'])}/{idx + 1} success)")
            # Save checkpoint
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

        time.sleep(0.05)  # Small delay to not overload API

    # Final save
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    success_count = sum(1 for r in results if r['success'])
    print(f"\nQMeans done: {success_count}/{total} successful")

    return results


# ===========================================================================
# PART 3: READ GEMMA V4 RESULTS
# ===========================================================================

def read_gemma_results(csv_path):
    """Read Gemma V4 inference results from CSV."""
    results = {}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            query = row.get('query', '').strip()
            if not query:
                continue

            parsed_attrs = []
            try:
                if row.get('attributes_json'):
                    parsed = json.loads(row['attributes_json'])
                    parsed_attrs = parsed.get('attributes', [])
            except:
                pass

            # Group by unique values, collect all keys per value
            value_groups = {}
            for attr in parsed_attrs:
                val = str(attr.get('value', '')).strip()
                key = str(attr.get('attribute_key', '')).strip()
                key_p = attr.get('key_priority', 0)
                attr_p = attr.get('attribute_priority', 0)
                val_lower = val.lower()

                if val_lower not in value_groups:
                    value_groups[val_lower] = {
                        'value': val,
                        'keys': [],
                        'attr_priority': attr_p
                    }
                value_groups[val_lower]['keys'].append({
                    'key': key,
                    'key_priority': key_p
                })

            results[query] = {
                'success': row.get('success', 'False') == 'True',
                'raw_output': row.get('raw_output', ''),
                'unique_value_count': int(row.get('unique_value_count', 0)),
                'total_key_count': int(row.get('total_key_count', 0)),
                'all_attributes': parsed_attrs,
                'value_groups': value_groups
            }

    return results


# ===========================================================================
# PART 4: COMPARISON ENGINE
# ===========================================================================

def normalize_key(key):
    """Normalize an attribute key for comparison."""
    k = key.lower().strip()
    k = re.sub(r'[_\-\s]+', ' ', k)

    # Key synonym mapping for matching
    key_synonyms = {
        'brand': ['brand', 'company', 'manufacturer', 'make'],
        'power': ['power', 'wattage', 'motor power', 'power rating', 'horsepower', 'horse power', 'hp'],
        'voltage': ['voltage', 'operating voltage', 'supply voltage', 'rated voltage'],
        'phase': ['phase', 'phase type', 'number of phase'],
        'speed': ['speed', 'rpm', 'motor speed', 'rated speed'],
        'motor type': ['motor type', 'type', 'product type', 'machine type'],
        'mounting': ['mounting', 'mounting type', 'mount type'],
        'usage': ['usage', 'application', 'usage application'],
        'enclosure': ['enclosure', 'body enclosure', 'enclosure type'],
        'efficiency': ['efficiency', 'efficiency class', 'energy efficiency'],
        'model number': ['model number', 'model', 'part number', 'model no'],
        'material': ['material', 'body material', 'construction material'],
        'weight': ['weight', 'product weight'],
        'current': ['current', 'rated current', 'ampere'],
        'ip rating': ['ip rating', 'protection', 'ingress protection'],
        'frame size': ['frame size', 'frame', 'nema size'],
        'shaft type': ['shaft type', 'shaft'],
        'poles': ['poles', 'no of poles', 'number of poles'],
        'product type': ['product type', 'type', 'product'],
        'part type': ['part type', 'type', 'product type'],
        'gear ratio': ['gear ratio', 'ratio', 'reduction ratio'],
        'kv rating': ['kv rating', 'kv'],
        'step angle': ['step angle', 'angle'],
        'power kw': ['power kw', 'power', 'wattage', 'motor power'],
    }

    for canonical, synonyms in key_synonyms.items():
        if k in synonyms:
            return canonical

    return k


def normalize_value(value):
    """Normalize a value for comparison."""
    v = str(value).lower().strip()
    v = re.sub(r'\s+', ' ', v)
    return v


def check_key_match(gt_key, compare_keys):
    """Check if GT key matches any of the comparison keys."""
    gt_norm = normalize_key(gt_key)
    for ck in compare_keys:
        if normalize_key(ck) == gt_norm:
            return True
    return False


def check_value_match(gt_value, compare_values):
    """Check if GT value matches any comparison value (fuzzy)."""
    gt_v = normalize_value(gt_value)
    for cv in compare_values:
        cv_norm = normalize_value(cv)
        if gt_v == cv_norm:
            return True
        if gt_v in cv_norm or cv_norm in gt_v:
            return True
        # Number-aware match: "1.5" matches "1.5 kw"
        gt_nums = set(re.findall(r'\d+\.?\d*', gt_v))
        cv_nums = set(re.findall(r'\d+\.?\d*', cv_norm))
        if gt_nums and gt_nums == cv_nums:
            return True
    return False


def build_comparison(queries, gt_results, qmeans_results, gemma_results):
    """Build the full comparison dataset."""
    comparison_rows = []

    for idx, query in enumerate(queries):
        gt_attrs = gt_results.get(query, {})
        qm_data = qmeans_results.get(query, {})
        qm_attrs = qm_data.get('attributes', {}) if isinstance(qm_data, dict) else {}
        gem_data = gemma_results.get(query, {})

        # GT info
        gt_count = len(gt_attrs)
        gt_json = json.dumps(gt_attrs, ensure_ascii=False) if gt_attrs else ''

        # QMeans info
        qm_count = len(qm_attrs)
        qm_json = json.dumps(qm_attrs, ensure_ascii=False) if qm_attrs else ''

        # Gemma info
        gem_unique = gem_data.get('unique_value_count', 0) if gem_data else 0
        gem_total_keys = gem_data.get('total_key_count', 0) if gem_data else 0
        gem_all_attrs = gem_data.get('all_attributes', []) if gem_data else []
        gem_value_groups = gem_data.get('value_groups', {}) if gem_data else {}

        # Build Gemma attrs dict (primary keys only, key_priority=1)
        gem_primary_attrs = {}
        gem_priority_info = []
        for vg in gem_value_groups.values():
            primary_key = None
            all_keys = []
            for k in sorted(vg['keys'], key=lambda x: x.get('key_priority', 99)):
                all_keys.append(k['key'])
                if k.get('key_priority', 99) == 1:
                    primary_key = k['key']
            if not primary_key and all_keys:
                primary_key = all_keys[0]
            if primary_key:
                gem_primary_attrs[primary_key] = vg['value']
                gem_priority_info.append(f"{primary_key}={vg['value']}(P{vg.get('attr_priority', '?')})")

        gem_primary_json = json.dumps(gem_primary_attrs, ensure_ascii=False) if gem_primary_attrs else ''

        # All gemma keys (for matching - any key counts as match)
        all_gemma_keys = set()
        all_gemma_values = set()
        for attr in gem_all_attrs:
            all_gemma_keys.add(str(attr.get('attribute_key', '')).strip())
            all_gemma_values.add(normalize_value(attr.get('value', '')))

        # === COMPARISON: GT vs QMeans ===
        gt_vs_qm_key_match = 0
        gt_vs_qm_value_match = 0
        for gt_key, gt_val in gt_attrs.items():
            qm_keys = list(qm_attrs.keys())
            qm_vals = list(qm_attrs.values())
            if check_key_match(gt_key, qm_keys):
                gt_vs_qm_key_match += 1
            if check_value_match(gt_val, qm_vals):
                gt_vs_qm_value_match += 1

        # === COMPARISON: GT vs Gemma ===
        gt_vs_gem_key_match = 0
        gt_vs_gem_value_match = 0
        gt_vs_gem_details = []
        for gt_key, gt_val in gt_attrs.items():
            # For Gemma, check against ALL keys (not just primary)
            key_matched = check_key_match(gt_key, all_gemma_keys)
            val_matched = check_value_match(gt_val, all_gemma_values)
            if key_matched:
                gt_vs_gem_key_match += 1
            if val_matched:
                gt_vs_gem_value_match += 1

            # Find the matching Gemma attribute with its priority
            gem_match_priority = ''
            for vg in gem_value_groups.values():
                if check_value_match(gt_val, [vg['value']]):
                    for k in vg['keys']:
                        if check_key_match(gt_key, [k['key']]):
                            gem_match_priority = f"key_p={k['key_priority']},attr_p={vg.get('attr_priority', '?')}"
                            break
                    break

            gt_vs_gem_details.append(f"{gt_key}:{gt_val}->{'MATCH' if key_matched else 'MISS'}"
                                     f"{'(' + gem_match_priority + ')' if gem_match_priority else ''}")

        # === COMPARISON: QMeans vs Gemma ===
        qm_vs_gem_key_match = 0
        qm_vs_gem_value_match = 0
        for qm_key, qm_val in qm_attrs.items():
            if check_key_match(qm_key, all_gemma_keys):
                qm_vs_gem_key_match += 1
            if check_value_match(qm_val, all_gemma_values):
                qm_vs_gem_value_match += 1

        # Build row
        row = {
            'query': query,
            'gt_attr_count': gt_count,
            'qmeans_attr_count': qm_count,
            'gemma_unique_values': gem_unique,
            'gemma_total_keys': gem_total_keys,
            'gt_attrs': gt_json,
            'qmeans_attrs': qm_json,
            'gemma_primary_attrs': gem_primary_json,
            'gemma_full_attrs': json.dumps(gem_all_attrs, ensure_ascii=False) if gem_all_attrs else '',
            'gt_vs_qmeans_key_match': gt_vs_qm_key_match,
            'gt_vs_qmeans_value_match': gt_vs_qm_value_match,
            'gt_vs_gemma_key_match': gt_vs_gem_key_match,
            'gt_vs_gemma_value_match': gt_vs_gem_value_match,
            'qmeans_vs_gemma_key_match': qm_vs_gem_key_match,
            'qmeans_vs_gemma_value_match': qm_vs_gem_value_match,
            'gt_vs_qmeans_key_pct': f"{gt_vs_qm_key_match / max(1, gt_count) * 100:.0f}%",
            'gt_vs_gemma_key_pct': f"{gt_vs_gem_key_match / max(1, gt_count) * 100:.0f}%",
            'gemma_priority_info': ' | '.join(gem_priority_info) if gem_priority_info else '',
            'gemma_wins_over_qmeans': 'YES' if gt_vs_gem_key_match > gt_vs_qm_key_match else ('TIE' if gt_vs_gem_key_match == gt_vs_qm_key_match else 'NO'),
        }

        comparison_rows.append(row)

    return comparison_rows


def read_queries(filepath):
    """Read queries from CSV or text file."""
    queries = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames and 'query' in reader.fieldnames:
                for row in reader:
                    q = row['query'].strip()
                    if q:
                        queries.append(q)
                return queries
    except:
        pass

    # Fall back to line-by-line
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line and line.lower() != 'query':
            queries.append(line)
    return queries


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(description='GT + QMeans + Gemma V4 Comparison')
    parser.add_argument('--queries', default='compare/76cat_queries.csv',
                        help='Input queries file (CSV or text, one per line)')
    parser.add_argument('--gemma', default='', help='Gemma V4 results CSV')
    parser.add_argument('--step', default='all',
                        choices=['prepare', 'compare', 'all'],
                        help='prepare=GT+QMeans only, compare=full comparison')
    parser.add_argument('--output', default='compare/final_gt_qmeans_gemma_comparison.csv',
                        help='Output comparison CSV')
    parser.add_argument('--skip-qmeans', action='store_true',
                        help='Skip QMeans API calls (use cached results)')
    args = parser.parse_args()

    # Read queries
    queries = read_queries(args.queries)
    print(f"Loaded {len(queries)} queries from {args.queries}")

    if len(queries) == 0:
        print("ERROR: No queries found! Make sure the file is saved and has content.")
        return

    # ---- STEP 1: Ground Truth ----
    gt_cache = args.output.replace('.csv', '_gt.json')

    if os.path.exists(gt_cache):
        print(f"Loading cached GT from {gt_cache}")
        with open(gt_cache, 'r', encoding='utf-8') as f:
            gt_all = json.load(f)
    else:
        print("\n--- Generating Ground Truth ---")
        gt_all = {}
        for idx, query in enumerate(queries):
            attrs = extract_ground_truth(query)
            gt_all[query] = attrs
            if (idx + 1) % 100 == 0:
                print(f"  GT [{idx + 1}/{len(queries)}] generated")

        with open(gt_cache, 'w', encoding='utf-8') as f:
            json.dump(gt_all, f, indent=2, ensure_ascii=False)

        # GT stats
        total_attrs = sum(len(v) for v in gt_all.values())
        queries_with_attrs = sum(1 for v in gt_all.values() if v)
        print(f"GT done: {queries_with_attrs}/{len(queries)} queries have attributes "
              f"({total_attrs} total attrs, avg {total_attrs / max(1, len(queries)):.1f}/query)")

    # ---- STEP 2: QMeans ----
    qm_cache = args.output.replace('.csv', '_qmeans.json')

    if args.skip_qmeans and os.path.exists(qm_cache):
        print(f"Loading cached QMeans from {qm_cache}")
        with open(qm_cache, 'r', encoding='utf-8') as f:
            qm_list = json.load(f)
            qm_all = {r['query']: r for r in qm_list}
    elif os.path.exists(qm_cache):
        print(f"Loading cached QMeans from {qm_cache}")
        with open(qm_cache, 'r', encoding='utf-8') as f:
            qm_list = json.load(f)
            qm_all = {r['query']: r for r in qm_list}
    else:
        qm_list = fetch_all_qmeans(queries, qm_cache)
        qm_all = {r['query']: r for r in qm_list}

    if args.step == 'prepare':
        print("\n✅ GT and QMeans prepared. Now run Gemma inference, then re-run with:")
        print(f"   python {os.path.basename(__file__)} --queries {args.queries} "
              f"--gemma gemma_v4_1000_results.csv --step compare")
        return

    # ---- STEP 3: Read Gemma results ----
    gemma_all = {}
    if args.gemma and os.path.exists(args.gemma):
        print(f"\nLoading Gemma V4 results from {args.gemma}")
        gemma_all = read_gemma_results(args.gemma)
        print(f"  Loaded {len(gemma_all)} Gemma results")
    else:
        print("\n⚠️  No Gemma results provided - comparison will only have GT vs QMeans")

    # ---- STEP 4: Build comparison ----
    print("\n--- Building Comparison ---")
    comparison = build_comparison(queries, gt_all, qm_all, gemma_all)

    # Write CSV
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    fieldnames = list(comparison[0].keys()) if comparison else []

    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comparison)

    print(f"\n✅ Comparison saved to: {args.output}")

    # ---- Summary Stats ----
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)

    total = len(comparison)
    gt_has_attrs = sum(1 for r in comparison if r['gt_attr_count'] > 0)
    qm_has_attrs = sum(1 for r in comparison if r['qmeans_attr_count'] > 0)
    gem_has_attrs = sum(1 for r in comparison if r['gemma_unique_values'] > 0)

    print(f"\nQueries with attributes detected:")
    print(f"  Ground Truth:  {gt_has_attrs}/{total} ({gt_has_attrs * 100 / total:.1f}%)")
    print(f"  QMeans:        {qm_has_attrs}/{total} ({qm_has_attrs * 100 / total:.1f}%)")
    print(f"  Gemma V4:      {gem_has_attrs}/{total} ({gem_has_attrs * 100 / total:.1f}%)")

    # Key match rates (GT vs QMeans and GT vs Gemma)
    gt_qm_key_matches = sum(r['gt_vs_qmeans_key_match'] for r in comparison)
    gt_qm_total_gt = sum(r['gt_attr_count'] for r in comparison)
    gt_gem_key_matches = sum(r['gt_vs_gemma_key_match'] for r in comparison)

    print(f"\nGT vs QMeans key match rate: {gt_qm_key_matches}/{gt_qm_total_gt} "
          f"({gt_qm_key_matches * 100 / max(1, gt_qm_total_gt):.1f}%)")
    print(f"GT vs Gemma key match rate:  {gt_gem_key_matches}/{gt_qm_total_gt} "
          f"({gt_gem_key_matches * 100 / max(1, gt_qm_total_gt):.1f}%)")

    # Who wins
    if gemma_all:
        gemma_wins = sum(1 for r in comparison if r['gemma_wins_over_qmeans'] == 'YES')
        qmeans_wins = sum(1 for r in comparison if r['gemma_wins_over_qmeans'] == 'NO')
        ties = sum(1 for r in comparison if r['gemma_wins_over_qmeans'] == 'TIE')
        print(f"\nHead-to-head (GT key match):")
        print(f"  Gemma wins:  {gemma_wins} ({gemma_wins * 100 / total:.1f}%)")
        print(f"  QMeans wins: {qmeans_wins} ({qmeans_wins * 100 / total:.1f}%)")
        print(f"  Ties:        {ties} ({ties * 100 / total:.1f}%)")

    # Value match rates
    gt_qm_val_matches = sum(r['gt_vs_qmeans_value_match'] for r in comparison)
    gt_gem_val_matches = sum(r['gt_vs_gemma_value_match'] for r in comparison)
    print(f"\nGT vs QMeans value match rate: {gt_qm_val_matches}/{gt_qm_total_gt} "
          f"({gt_qm_val_matches * 100 / max(1, gt_qm_total_gt):.1f}%)")
    print(f"GT vs Gemma value match rate:  {gt_gem_val_matches}/{gt_qm_total_gt} "
          f"({gt_gem_val_matches * 100 / max(1, gt_qm_total_gt):.1f}%)")

    # Avg attributes per query
    avg_gt = sum(r['gt_attr_count'] for r in comparison) / max(1, total)
    avg_qm = sum(r['qmeans_attr_count'] for r in comparison) / max(1, total)
    avg_gem = sum(r['gemma_unique_values'] for r in comparison) / max(1, total)
    avg_gem_keys = sum(r['gemma_total_keys'] for r in comparison) / max(1, total)

    print(f"\nAvg attributes per query:")
    print(f"  Ground Truth:     {avg_gt:.2f}")
    print(f"  QMeans:           {avg_qm:.2f}")
    print(f"  Gemma (unique):   {avg_gem:.2f}")
    print(f"  Gemma (all keys): {avg_gem_keys:.2f}")

    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    main()
