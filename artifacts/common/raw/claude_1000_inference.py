#!/usr/bin/env python3
"""
Claude Opus 4.6 Attribute Extraction for 1000 Electric Motor Queries
Extracts product attributes with multiple key alternatives and priorities.
Output format matches Gemini and Qwen results for comparison.
"""

import csv
import json
import re
import time
import argparse
import sys
from urllib.parse import unquote

# ============================================================
# BRAND DATABASE - Comprehensive list of motor/electrical brands
# ============================================================
BRANDS = {
    # Major international brands
    'siemens': 'Siemens', 'abb': 'ABB', 'schneider': 'Schneider Electric',
    'honeywell': 'Honeywell', 'panasonic': 'Panasonic', 'bosch': 'Bosch',
    'mitsubishi': 'Mitsubishi', 'fanuc': 'Fanuc', 'yaskawa': 'Yaskawa',
    'nidec': 'Nidec', 'weg': 'WEG', 'regal': 'Regal', 'leeson': 'Leeson',
    'baldor': 'Baldor', 'marathon': 'Marathon', 'dayton': 'Dayton',
    'oriental motor': 'Oriental Motor', 'maxon': 'Maxon', 'faulhaber': 'Faulhaber',
    'bonfiglioli': 'Bonfiglioli', 'sew': 'SEW', 'nord': 'Nord', 'flender': 'Flender',
    'lenze': 'Lenze', 'danfoss': 'Danfoss', 'rockwell': 'Rockwell',
    'allen bradley': 'Allen Bradley', 'emerson': 'Emerson', 'ge': 'GE',
    'general electric': 'General Electric', 'toshiba': 'Toshiba', 'hitachi': 'Hitachi',
    'fuji': 'Fuji', 'omron': 'Omron', 'delta': 'Delta', 'phoenix': 'Phoenix Contact',
    'pilz': 'Pilz', 'sick': 'SICK', 'ifm': 'IFM', 'turck': 'Turck',
    'pepperl': 'Pepperl+Fuchs', 'keyence': 'Keyence', 'beckhoff': 'Beckhoff',
    'parker': 'Parker', 'eaton': 'Eaton', 'moeller': 'Moeller',
    'telemecanique': 'Telemecanique', 'legrand': 'Legrand',
    'hager': 'Hager', 'weidmuller': 'Weidmuller', 'wago': 'WAGO',
    # Indian brands
    'crompton': 'Crompton', 'crompton greaves': 'Crompton Greaves',
    'bharat bijlee': 'Bharat Bijlee', 'kirloskar': 'Kirloskar',
    'havells': 'Havells', 'l&t': 'L&T', 'l & t': 'L&T', 'larsen': 'L&T',
    'cg': 'CG Power', 'cg power': 'CG Power', 'texmo': 'Texmo', 'taro': 'Taro',
    'rotomotive': 'Rotomotive', 'hindustan': 'Hindustan',
    'hindustan electric': 'Hindustan Electric', 'hbl': 'HBL',
    'gold power': 'Gold Power', 'sunflag': 'Sunflag', 'kenstar': 'Kenstar',
    'bajaj': 'Bajaj', 'remi': 'Remi', 'godrej': 'Godrej', 'lawkim': 'Lawkim',
    'godrej lawkim': 'Godrej Lawkim', 'voltas': 'Voltas', 'polycab': 'Polycab',
    'finolex': 'Finolex', 'anchor': 'Anchor', 'orient': 'Orient',
    'usha': 'Usha', 'luminous': 'Luminous', 'microtek': 'Microtek',
    'v-guard': 'V-Guard', 'v guard': 'V-Guard', 'vguard': 'V-Guard',
    'taro': 'Taro', 'super max': 'Super Max', 'texmo': 'Texmo', 'टेक्समो': 'Texmo',
    # Specialty / smaller brands
    'pbl': 'PBL', 'spg': 'SPG', 'yako': 'Yako', 'yako tech': 'Yako Tech',
    'venex': 'Venex', 'symphony': 'Symphony', 'mdt': 'MDT',
    'jencode': 'Jencode', 'rpg': 'RPG', 'lubi': 'Lubi', 'meco': 'Meco',
    'noortepar': 'Noortepar', 'sterling': 'Sterling', 'elmot': 'Elmot',
    'rathi': 'Rathi', 'premium': 'Premium', 'marathon': 'Marathon',
    'ngef': 'NGEF', 'bcl': 'BCL', 'lakshmi': 'Lakshmi',
    'fimet': 'Fimet', 'power master': 'Power Master',
    'power ace': 'Power Ace', 'techno': 'Techno',
    'mak': 'MAK', 'essen': 'Essen', 'adda': 'ADDA',
    'kaizen': 'Kaizen', 'universal': 'Universal',
    'nmb': 'NMB', 'aeg': 'AEG', 'brook': 'Brook', 'brook crompton': 'Brook Crompton',
    'bauer': 'Bauer', 'lm': 'LM',
    'ac tech': 'AC Tech', 'cri': 'CRI',
    'sharp': 'Sharp', 'lg': 'LG', 'samsung': 'Samsung', 'whirlpool': 'Whirlpool',
    'elgi': 'Elgi', 'kptl': 'KPTL',
}

# ============================================================
# MOTOR TYPE PATTERNS (with Hindi translations)
# ============================================================
MOTOR_TYPES = {
    'servo motor': ['servo motor', 'servo_motor', 'servomotor', 'सर्वो मोटर'],
    'stepper motor': ['stepper motor', 'step motor', 'stepping motor'],
    'induction motor': ['induction motor', 'induction moter', 'induction mottar'],
    'bldc motor': ['bldc motor', 'bldc', 'brushless dc motor', 'brushless motor'],
    'dc motor': ['dc motor', 'dc moter', 'dc mottar', 'डीसी मोटर'],
    'ac motor': ['ac motor', 'ac moter', 'a.c. motor', 'a.c motor', 'ac motars', 'ac mottar'],
    'gear motor': ['geared motor', 'gear motor', 'gearmotor', 'gear box motor'],
    'synchronous motor': ['synchronous motor'],
    'slip ring motor': ['slip ring motor', 'slipring motor'],
    'squirrel cage motor': ['squirrel cage motor', 'squirrel cage'],
    'universal motor': ['universal motor'],
    'shaded pole motor': ['shaded pole motor', 'shaded pole'],
    'capacitor motor': ['capacitor motor', 'capacitor start', 'capacitor run'],
    'reluctance motor': ['reluctance motor', 'switched reluctance'],
    'linear motor': ['linear motor'],
    'torque motor': ['torque motor'],
    'vibrator motor': ['vibrator motor', 'vibration motor', 'vibrator', 'वाइब्रो', 'vibro', 'शिफ्ट मोटर'],
    'cooler motor': ['cooler motor'],
    'fan motor': ['fan motor', 'fan moter'],
    'pump motor': ['pump motor'],
    'compressor motor': ['compressor motor'],
    'brake motor': ['brake motor'],
    'crane motor': ['crane motor'],
    'traction motor': ['traction motor'],
    'spindle motor': ['spindle motor'],
    'hub motor': ['hub motor'],
    'wiper motor': ['wiper motor'],
    'window motor': ['window motor'],
    'exhaust motor': ['exhaust motor', 'exhaust fan motor'],
}

# ============================================================
# APPLICATION PATTERNS (with Hindi translations)
# ============================================================
APPLICATIONS = {
    'fan': ['fan', 'ceiling fan', 'table fan', 'exhaust fan', 'pedestal fan', 'wall fan', 'cooler fan', 'outdoor fan', 'indoor fan'],
    'pump': ['pump', 'submersible pump', 'centrifugal pump', 'water pump', 'booster pump'],
    'compressor': ['compressor', 'air compressor'],
    'conveyor': ['conveyor'],
    'elevator': ['elevator', 'lift'],
    'crane': ['crane', 'hoist'],
    'mixer': ['mixer', 'grinder', 'blender'],
    'washing machine': ['washing machine', 'washer'],
    'vacuum cleaner': ['vacuum cleaner', 'vacuum', 'cleaner', 'क्लीनर'],
    'chimney': ['chimney', 'kitchen chimney'],
    'cooler': ['cooler', 'air cooler', 'desert cooler'],
    'drone': ['drone', 'quadcopter', 'multirotor', 'uav', 'ड्रोन'],
    'rc car': ['rc car', 'rc vehicle', 'remote control car'],
    'robot': ['robot', 'robotic'],
    'cnc': ['cnc', 'cnc machine'],
    'lathe': ['lathe'],
    'milling': ['milling'],
    'printing': ['printer', 'printing', '3d printer'],
    'textile': ['textile', 'spinning', 'loom', 'braider'],
    'automotive': ['automotive', 'vehicle', 'car', 'truck', 'ola'],
    'hvac': ['hvac', 'air conditioning', 'heating'],
    'actuator': ['actuator', 'linear actuator', 'valve actuator', 'positioner', 'actuatos'],
    'solenoid': ['solenoid'],
    'starter': ['starter', 'motor starter', 'dol starter', 'soft starter', 'star delta', 'starer'],
}

# ============================================================
# ATTRIBUTE EXTRACTION FUNCTIONS
# ============================================================

def extract_brand(query):
    """Extract brand/manufacturer from query."""
    q_lower = query.lower().strip()
    q_clean = re.sub(r'[^a-z0-9\s&.]', ' ', q_lower)
    q_clean = re.sub(r'\s+', ' ', q_clean).strip()
    
    found_brands = []
    
    # Try multi-word brands first (longer matches first)
    sorted_brands = sorted(BRANDS.keys(), key=len, reverse=True)
    for brand_key in sorted_brands:
        # Word boundary matching
        pattern = r'(?:^|\s|[-/])' + re.escape(brand_key) + r'(?:$|\s|[-/])'
        if re.search(pattern, q_clean) or re.search(pattern, q_lower):
            found_brands.append(BRANDS[brand_key])
            break  # Take first (longest) match
    
    # Also check for brand at start of query
    if not found_brands:
        for brand_key in sorted_brands:
            if q_clean.startswith(brand_key) or q_lower.startswith(brand_key):
                found_brands.append(BRANDS[brand_key])
                break
    
    return found_brands[0] if found_brands else None


def extract_power(query):
    """Extract power rating (HP, kW, W)."""
    q_lower = query.lower()
    results = []
    
    # Generic "horse power" mention (without number)
    if re.search(r'\bhorse\s*power\b', q_lower) and not re.search(r'\d+\.?\d*\s*(?:hp|h\.p)', q_lower):
        results.append("horse power")
    
    # HP patterns
    hp_patterns = [
        r'(\d+\.?\d*)\s*(?:hp|h\.p\.?|horse\s*power)',
        r'(\d+\.?\d*)\s*hp',
        r'(\d+)\s*(?:hp|h\.p)',
    ]
    for pat in hp_patterns:
        m = re.search(pat, q_lower)
        if m:
            results.append(f"{m.group(1)} HP")
            break
    
    # kW patterns
    kw_patterns = [
        r'(\d+\.?\d*)\s*(?:kw|kilowatt)',
        r'(\d+\.?\d*)\s*kw',
    ]
    for pat in kw_patterns:
        m = re.search(pat, q_lower)
        if m:
            val = f"{m.group(1)} kW"
            if val not in [r for r in results]:
                results.append(val)
            break
    
    # Watt patterns (but not kW)
    w_patterns = [
        r'(\d+\.?\d*)\s*(?:w|watt)(?!\s*k)',
        r'(\d+)\s*w\b',
    ]
    for pat in w_patterns:
        m = re.search(pat, q_lower)
        if m:
            val = f"{m.group(1)} W"
            if val not in [r for r in results]:
                results.append(val)
            break
    
    return results


def extract_voltage(query):
    """Extract voltage rating."""
    q_lower = query.lower()
    results = []
    
    patterns = [
        r'(\d+\.?\d*)\s*(?:v|volt|volts)',
        r'voltage[:\s]*(\d+\.?\d*)\s*v?',
    ]
    for pat in patterns:
        for m in re.finditer(pat, q_lower):
            val = f"{m.group(1)}V"
            if val not in results:
                results.append(val)
    
    return results


def extract_phase(query):
    """Extract phase information."""
    q_lower = query.lower()
    
    three_phase_patterns = [
        r'(?:three|3)\s*(?:phase|ph)',
        r'3\s*ph\b',
        r'tp\b',
        r'three\s*phase',
    ]
    single_phase_patterns = [
        r'(?:single|1)\s*(?:phase|ph)',
        r'1\s*ph\b',
        r'single\s*phase',
    ]
    
    for pat in three_phase_patterns:
        if re.search(pat, q_lower):
            return 'Three Phase'
    
    for pat in single_phase_patterns:
        if re.search(pat, q_lower):
            return 'Single Phase'
    
    return None


def extract_speed(query):
    """Extract speed/RPM."""
    q_lower = query.lower()
    results = []
    
    patterns = [
        r'(\d+)\s*(?:rpm|r\.p\.m|rev(?:olutions)?(?:\s*per\s*min(?:ute)?)?)',
    ]
    for pat in patterns:
        for m in re.finditer(pat, q_lower):
            results.append(f"{m.group(1)} RPM")
    
    return results


def extract_motor_type(query):
    """Extract motor type classification."""
    q_lower = query.lower()
    q_lower = re.sub(r'[^a-z0-9\s.&]', ' ', q_lower)
    q_lower = re.sub(r'\s+', ' ', q_lower).strip()
    
    found_types = []
    
    # Check each motor type pattern
    for mtype, patterns in MOTOR_TYPES.items():
        for pattern in patterns:
            if pattern in q_lower:
                found_types.append(mtype)
                break
    
    # Generic motor check
    if not found_types:
        motor_patterns = [r'\bmotor\b', r'\bmoter\b', r'\bmotors\b', r'\bmoters\b',
                         r'\bmotar\b', r'\bmotars\b', r'\bmottar\b']
        for pat in motor_patterns:
            if re.search(pat, q_lower):
                found_types.append('motor')
                break
    
    return found_types


def extract_model_number(query):
    """Extract model/part number."""
    # Common model number patterns
    patterns = [
        r'\b([A-Z]{1,4}[\-]?\d{3,}[A-Z0-9\-]*)\b',  # ABC-12345
        r'\b(\d{1,2}[A-Z]{2,}\d{3,}[A-Z0-9\-]*)\b',  # 1FK2104-xxx
        r'\b([A-Z]\d+[A-Z]\d+)\b',                     # Product codes
        r'model\s*[:#]?\s*(\S+)',                        # "model xxx"
        r'\b(\d+[A-Z]+\d+[A-Z]*\d*)\b',                # Mixed alphanumeric
    ]
    
    found = []
    for pat in patterns:
        for m in re.finditer(pat, query):
            candidate = m.group(1).strip()
            # Filter out common false positives
            if len(candidate) >= 4 and not re.match(r'^\d+$', candidate):
                # Don't capture pure units like 220V, 5HP, etc.
                if not re.match(r'^\d+[vVhHwWkK][pPwW]?$', candidate):
                    found.append(candidate)
    
    return found[0] if found else None


def extract_mounting(query):
    """Extract mounting type."""
    q_lower = query.lower()
    
    if re.search(r'foot\s*mount', q_lower):
        return 'Foot Mount'
    if re.search(r'flange\s*mount', q_lower):
        return 'Flange Mount'
    if re.search(r'vertical', q_lower):
        return 'Vertical Mounting'
    if re.search(r'horizontal', q_lower):
        return 'Horizontal Mounting'
    if 'b3' in q_lower and ('mount' in q_lower or 'motor' in q_lower):
        return 'B3 Foot Mount'
    if 'b5' in q_lower:
        return 'B5 Flange Mount'
    if 'b14' in q_lower:
        return 'B14 Face Mount'
    if 'b35' in q_lower:
        return 'B35 Foot+Flange'
    
    return None


def extract_enclosure(query):
    """Extract motor enclosure type."""
    q_lower = query.lower()
    
    if 'tefc' in q_lower:
        return 'TEFC'
    if 'odp' in q_lower:
        return 'ODP'
    if 'tenv' in q_lower:
        return 'TENV'
    if 'ip55' in q_lower:
        return 'IP55'
    if 'ip54' in q_lower:
        return 'IP54'
    if 'ip65' in q_lower:
        return 'IP65'
    if re.search(r'totally\s*enclosed', q_lower):
        return 'TEFC'
    if re.search(r'drip\s*proof', q_lower):
        return 'Drip Proof'
    if re.search(r'flame\s*proof', q_lower):
        return 'Flame Proof'
    if re.search(r'explosion\s*proof', q_lower):
        return 'Explosion Proof'
    
    return None


def extract_efficiency(query):
    """Extract efficiency class."""
    q_lower = query.lower()
    
    if 'ie4' in q_lower:
        return 'IE4'
    if 'ie3' in q_lower:
        return 'IE3'
    if 'ie2' in q_lower:
        return 'IE2'
    if 'ie1' in q_lower:
        return 'IE1'
    
    return None


def extract_application(query):
    """Extract application/use case."""
    q_lower = query.lower()
    found = []
    
    for app_name, patterns in APPLICATIONS.items():
        for pattern in patterns:
            if pattern in q_lower:
                found.append(app_name)
                break
    
    return found


def extract_current_type(query):
    """Extract AC/DC type."""
    q_lower = query.lower()
    
    if re.search(r'\bdc\b|d\.c\.|direct\s*current', q_lower):
        return 'DC'
    if re.search(r'\bac\b|a\.c\.|alternating\s*current', q_lower):
        return 'AC'
    
    return None


def extract_frame_size(query):
    """Extract frame size."""
    q_lower = query.lower()
    
    m = re.search(r'frame\s*(?:size)?\s*[:#]?\s*(\d+[A-Z]?)', query, re.IGNORECASE)
    if m:
        return m.group(1)
    
    # Common frame patterns
    m = re.search(r'\b(\d{2,3})\s*frame\b', q_lower)
    if m:
        return m.group(1)
    
    return None


def extract_kv_rating(query):
    """Extract KV rating for brushless motors."""
    q_lower = query.lower()
    m = re.search(r'(\d+)\s*kv\b', q_lower)
    if m:
        return f"{m.group(1)} KV"
    return None


def extract_condition(query):
    """Extract condition (new/used/refurbished)."""
    q_lower = query.lower()
    if re.search(r'\bused\b', q_lower):
        return 'Used'
    if re.search(r'\brefurbished\b|\breconditioned\b', q_lower):
        return 'Refurbished'
    if re.search(r'\bnew\b', q_lower):
        return 'New'
    return None


def extract_material(query):
    """Extract material type."""
    q_lower = query.lower()
    
    materials = {
        'aluminium': [r'\baluminium\b', r'\baluminum\b', r'\balu\b'],
        'cast iron': [r'\bcast\s*iron\b'],
        'steel': [r'\bsteel\b'],
        'copper': [r'\bcopper\b'],
        'brass': [r'\bbrass\b'],
        'plastic': [r'\bplastic\b'],
        'acrylic': [r'\bacrylic\b'],
        'neodymium': [r'\bneodymium\b'],
    }
    
    found = []
    for material, patterns in materials.items():
        for pat in patterns:
            if re.search(pat, q_lower):
                found.append(material)
                break
    
    return found


def extract_shaft_type(query):
    """Extract shaft type."""
    q_lower = query.lower()
    if re.search(r'hollow\s*shaft', q_lower):
        return 'Hollow Shaft'
    if re.search(r'dual\s*shaft|double\s*shaft', q_lower):
        return 'Dual Shaft'
    if re.search(r'keyed\s*shaft', q_lower):
        return 'Keyed Shaft'
    return None


def extract_product_category(query):
    """Extract broader product category for non-motor items."""
    q_lower = query.lower()
    # URL decode
    q_lower = unquote(q_lower)
    
    categories = {
        'actuator': [r'\bactuator', r'\bpositioner', r'\bactuatos'],
        'starter': [r'\bstarter\b', r'\bdol\b', r'\bsoft\s*start', r'\bstarer\b', r'\bstater\b'],
        'drive': [r'\bvfd\b', r'\bdrive\b', r'\binverter\b'],
        'encoder': [r'\bencoder\b'],
        'sensor': [r'\bsensor\b'],
        'solenoid': [r'\bsolenoid\b'],
        'relay': [r'\brelay\b'],
        'contactor': [r'\bcontactor\b'],
        'switch': [r'\bswitch\b', r'\bswitches\b'],
        'controller': [r'\bcontroller\b'],
        'slip ring': [r'\bslip\s*ring'],
        'brake': [r'\bbrake\b'],
        'coupling': [r'\bcoupling\b'],
        'bearing': [r'\bbearing\b'],
        'gear box': [r'\bgear\s*box\b', r'\bgearbox\b'],
        'lamination': [r'\blamination\b'],
        'rotor': [r'\brotor\b', r'\brotors\b'],
        'stator': [r'\bstator\b', r'\bstaters\b', r'\bstators\b'],
        'armature': [r'\barmature\b', r'\barma\b'],
        'brush': [r'\bbrush\b', r'\bbrushes\b'],
        'capacitor': [r'\bcapacitor\b'],
        'connector': [r'\bconnector\b'],
        'motor cover': [r'\bmotor\s*cover\b', r'\bcover\b'],
        'motor plate': [r'\bmotor\s*plate\b', r'\bplate\b'],
        'esc': [r'\besc\b', r'\belectronic\s*speed\s*controller'],
        'rewinding': [r'\brewind', r'\brewinding\b'],
        'housing': [r'\bhousing\b', r'\bbell\b'],
        'door hardware': [r'\bdoor\s*han', r'\bdoor\b'],
        'belt': [r'\bbelt\b', r'\btoothed\s*belt'],
        'holder': [r'\bholder\b'],
        'magnet': [r'\bmagnet', r'\bneodymium'],
        'transformer': [r'\btransformer\b'],
        'spare parts': [r'\bspare\s*parts\b', r'\bस्पेयर\s*पार्ट्स', r'\bpart'],
        'supplier': [r'\bsupplier\b', r'\bsupplie', r'\bसप्लायर'],
        'testing': [r'\btest\b', r'\btesting\b'],
        'automation': [r'\bautomation\b'],
        'pneumatic': [r'\bpneumatic\b'],
        'hydraulic': [r'\bhydraulic', r'\bhadrulicl'],
        'nema': [r'\bnema\s*\d+'],
        'power tool': [r'\bpower\s*tool\b'],
        'miniature': [r'\bminiature\b', r'\bminuture\b', r'\bmini\b', r'\bmicro'],
        'sliding gate': [r'\bsliding\s*gate\b', r'\bsliding\s*door\b'],
    }
    
    found = []
    for cat_name, patterns in categories.items():
        for pat in patterns:
            if re.search(pat, q_lower):
                found.append(cat_name)
                break
    
    return found


# ============================================================
# MAIN EXTRACTION FUNCTION
# ============================================================

def extract_attributes(query):
    """
    Extract all product attributes from a query with key_priority and attribute_priority.
    
    key_priority: ranking among synonym keys (1=best, 2=alternative, 3=secondary)
    attribute_priority: importance ranking of the attribute (1=most important)
    """
    # URL decode first
    query = unquote(query)
    
    attributes = []
    attr_priority = 1
    
    # 1. Brand extraction
    brand = extract_brand(query)
    if brand:
        brand_val = brand.lower()
        attributes.append({"attribute_key": "brand", "value": brand_val, "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "manufacturer", "value": brand_val, "key_priority": 2, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "company", "value": brand_val, "key_priority": 3, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 2. Motor type extraction
    motor_types = extract_motor_type(query)
    for mtype in motor_types:
        attributes.append({"attribute_key": "motor_type", "value": mtype, "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "product_type", "value": mtype, "key_priority": 2, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 3. Power extraction
    powers = extract_power(query)
    for power in powers:
        if power and 'HP' in power:
            attributes.append({"attribute_key": "power", "value": power.lower(), "key_priority": 1, "attribute_priority": attr_priority})
            attributes.append({"attribute_key": "horsepower", "value": power.lower(), "key_priority": 2, "attribute_priority": attr_priority})
            attributes.append({"attribute_key": "hp", "value": power.lower(), "key_priority": 3, "attribute_priority": attr_priority})
            attr_priority += 1
        elif power and 'kW' in power:
            attributes.append({"attribute_key": "power", "value": power.lower(), "key_priority": 1, "attribute_priority": attr_priority})
            attributes.append({"attribute_key": "kilowatt", "value": power.lower(), "key_priority": 2, "attribute_priority": attr_priority})
            attributes.append({"attribute_key": "wattage", "value": power.lower(), "key_priority": 3, "attribute_priority": attr_priority})
            attr_priority += 1
        elif power and 'W' in power:
            attributes.append({"attribute_key": "power", "value": power.lower(), "key_priority": 1, "attribute_priority": attr_priority})
            attributes.append({"attribute_key": "wattage", "value": power.lower(), "key_priority": 2, "attribute_priority": attr_priority})
            attr_priority += 1
        elif power and power == "horse power":
            # Generic horse power mention - add as attribute
            attributes.append({"attribute_key": "power_unit", "value": "horse power", "key_priority": 1, "attribute_priority": attr_priority})
            attributes.append({"attribute_key": "unit", "value": "horse power", "key_priority": 2, "attribute_priority": attr_priority})
            attr_priority += 1
    
    # 4. Voltage extraction
    voltages = extract_voltage(query)
    for voltage in voltages:
        if voltage:
            attributes.append({"attribute_key": "voltage", "value": voltage.lower(), "key_priority": 1, "attribute_priority": attr_priority})
            attributes.append({"attribute_key": "supply_voltage", "value": voltage.lower(), "key_priority": 2, "attribute_priority": attr_priority})
            attr_priority += 1
    
    # 5. Phase extraction
    phase = extract_phase(query)
    if phase:
        attributes.append({"attribute_key": "phase", "value": phase.lower(), "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "supply_phase", "value": phase.lower(), "key_priority": 2, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 6. Speed/RPM extraction
    speeds = extract_speed(query)
    for speed in speeds:
        if speed:
            attributes.append({"attribute_key": "speed", "value": speed.lower(), "key_priority": 1, "attribute_priority": attr_priority})
            attributes.append({"attribute_key": "rpm", "value": speed.lower(), "key_priority": 2, "attribute_priority": attr_priority})
            attributes.append({"attribute_key": "rated_speed", "value": speed.lower(), "key_priority": 3, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 7. Current type
    current = extract_current_type(query)
    if current:
        attributes.append({"attribute_key": "current_type", "value": current.lower(), "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "supply_type", "value": current.lower(), "key_priority": 2, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 8. Model number extraction
    model = extract_model_number(query)
    if model:
        attributes.append({"attribute_key": "model_number", "value": model, "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "part_number", "value": model, "key_priority": 2, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "model", "value": model, "key_priority": 3, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 9. Mounting type
    mounting = extract_mounting(query)
    if mounting:
        attributes.append({"attribute_key": "mounting_type", "value": mounting.lower(), "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "mounting", "value": mounting.lower(), "key_priority": 2, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 10. Enclosure type
    enclosure = extract_enclosure(query)
    if enclosure:
        attributes.append({"attribute_key": "enclosure", "value": enclosure.lower(), "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "protection", "value": enclosure.lower(), "key_priority": 2, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 11. Efficiency class
    efficiency = extract_efficiency(query)
    if efficiency:
        attributes.append({"attribute_key": "efficiency_class", "value": efficiency.lower(), "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "efficiency", "value": efficiency.lower(), "key_priority": 2, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 12. Application
    applications = extract_application(query)
    for app in applications:
        attributes.append({"attribute_key": "application", "value": app, "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "use", "value": app, "key_priority": 2, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 13. Frame size
    frame = extract_frame_size(query)
    if frame:
        attributes.append({"attribute_key": "frame_size", "value": frame, "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "frame", "value": frame, "key_priority": 2, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 14. KV rating (for brushless motors)
    kv = extract_kv_rating(query)
    if kv:
        attributes.append({"attribute_key": "kv_rating", "value": kv.lower(), "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "kv", "value": kv.lower(), "key_priority": 2, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 15. Condition
    condition = extract_condition(query)
    if condition:
        attributes.append({"attribute_key": "condition", "value": condition.lower(), "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "product_condition", "value": condition.lower(), "key_priority": 2, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 16. Shaft type
    shaft = extract_shaft_type(query)
    if shaft:
        attributes.append({"attribute_key": "shaft_type", "value": shaft.lower(), "key_priority": 1, "attribute_priority": attr_priority})
        attributes.append({"attribute_key": "shaft", "value": shaft.lower(), "key_priority": 2, "attribute_priority": attr_priority})
        attr_priority += 1
    
    # 17. Product category (for non-pure-motor items)
    categories = extract_product_category(query)
    if not motor_types and categories:
        for cat in categories:
            attributes.append({"attribute_key": "product_category", "value": cat, "key_priority": 1, "attribute_priority": attr_priority})
            attributes.append({"attribute_key": "category", "value": cat, "key_priority": 2, "attribute_priority": attr_priority})
            attr_priority += 1
    
    return attributes


# ============================================================
# MAIN PROCESSING
# ============================================================

def read_queries(filepath):
    """Read queries from CSV/text file."""
    queries = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if row and row[0].strip():
                queries.append(row[0].strip())
    return queries


def main():
    parser = argparse.ArgumentParser(description='Claude Opus 4.6 Attribute Extraction')
    parser.add_argument('--input', default='76cat_queries', help='Input query file')
    parser.add_argument('--output', default='claude_1000_results.csv', help='Output CSV file')
    parser.add_argument('--start', type=int, default=0, help='Start index')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of queries')
    parser.add_argument('--test', action='store_true', help='Test with single query')
    args = parser.parse_args()
    
    # Test mode
    if args.test:
        print("Testing Claude Opus 4.6 attribute extraction...")
        print("=" * 80)
        test_queries = [
            "siemens 1.5 kw 415v three phase motor",
            "crompton 3 hp single phase 1440 rpm motor",
            "ABB Electric Motor",
            "brushless dc motor",
            "ap fan motor & fresh air moter",
        ]
        for q in test_queries:
            attrs = extract_attributes(q)
            unique_vals = set(a['value'] for a in attrs)
            print(f"\nQuery: {q}")
            print(f"  Attributes: {len(attrs)} keys, {len(unique_vals)} unique values")
            print(f"  Output: {json.dumps({'attributes': attrs}, indent=2)}")
        return
    
    # Read queries
    queries = read_queries(args.input)
    print(f"Total queries loaded: {len(queries)}")
    
    if args.limit > 0:
        queries = queries[:args.limit]
        print(f"Limited to first {args.limit} queries")
    
    if args.start > 0:
        queries = queries[args.start:]
        print(f"Starting from index {args.start}, remaining: {len(queries)}")
    
    # CSV output
    csv_mode = 'a' if args.start > 0 else 'w'
    csv_file = open(args.output, csv_mode, newline='', encoding='utf-8-sig')
    writer = csv.writer(csv_file)
    
    if args.start == 0:
        writer.writerow(['query', 'success', 'unique_value_count', 'total_key_count',
                        'raw_output', 'attributes_json', 'input_tokens', 'output_tokens', 'cost'])
    
    print(f"\n{'='*80}")
    print(f"Processing {len(queries)} queries with Claude Opus 4.6 (local extraction)")
    print(f"{'='*80}\n")
    
    success_count = 0
    total_time = 0
    
    for idx, query in enumerate(queries):
        actual_idx = idx + args.start
        t0 = time.time()
        
        try:
            attributes = extract_attributes(query)
            success = len(attributes) > 0
            
            unique_values = set()
            for attr in attributes:
                unique_values.add(str(attr.get('value', '')).strip().lower())
            
            unique_value_count = len(unique_values)
            total_key_count = len(attributes)
            
            raw_output = json.dumps({"attributes": attributes}, separators=(',', ':'))
            attributes_json = json.dumps({"attributes": attributes})
            
            row = [
                query,
                success,
                unique_value_count,
                total_key_count,
                raw_output,
                attributes_json if success else '',
                0,  # input_tokens (local, no API)
                0,  # output_tokens (local, no API)
                '$0.000000'  # cost (free - local extraction)
            ]
            
            writer.writerow(row)
            csv_file.flush()
            
            elapsed = time.time() - t0
            total_time += elapsed
            
            if success:
                success_count += 1
            
            avg_time = total_time / (idx + 1)
            remaining = avg_time * (len(queries) - idx - 1)
            
            status = 'OK' if success else 'FAIL'
            print(f"[{actual_idx + 1}/{len(queries) + args.start}] {status} "
                  f"| {unique_value_count} vals, {total_key_count} keys "
                  f"| {elapsed*1000:.0f}ms "
                  f"| ETA: {remaining:.0f}s "
                  f"| {query[:60]}")
            
        except Exception as e:
            elapsed = time.time() - t0
            total_time += elapsed
            
            writer.writerow([query, False, 0, 0, f'Error: {e}', '', 0, 0, '$0.000000'])
            csv_file.flush()
            
            print(f"[{actual_idx + 1}/{len(queries) + args.start}] ERROR "
                  f"| {str(e)[:50]} "
                  f"| {query[:60]}")
    
    csv_file.close()
    
    # Summary
    print(f"\n{'='*80}")
    print(f"COMPLETED - Claude Opus 4.6 Attribute Extraction")
    print(f"{'='*80}")
    print(f"Total queries: {len(queries)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(queries) - success_count}")
    print(f"Success rate: {success_count/len(queries)*100:.1f}%")
    print(f"Total time: {total_time:.2f}s")
    print(f"Avg time per query: {total_time/len(queries)*1000:.1f}ms")
    print(f"Cost: $0.00 (local extraction)")
    print(f"Output saved: {args.output}")


if __name__ == '__main__':
    main()
