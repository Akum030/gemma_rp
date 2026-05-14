"""
build_gold_smart.py — Generate new gold labels by combining:
1. Exact/near-exact match lookup from product_train_with_keys.jsonl (10K rows)
2. Rule-based extraction for brand names, part types, specs from query text

This avoids needing an API key and produces annotations consistent with
the IndiaMART vocabulary used in both training data AND compare_v5.py.

Output: bee/gold_smart.jsonl — same format as gold_1k_v2.jsonl:
  {"query": "...", "attributes": {"part type": "motor", "brand": "Siemens", ...}}

Usage:
  python bee/build_gold_smart.py
"""

import json, re, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUERIES_FILE = ROOT / "v4_inputs.jsonl"
TRAIN_FILE   = ROOT.parent / "product_train_with_keys.jsonl"
OLD_GOLD     = ROOT / "gold_1k_v2.jsonl"
OUTPUT       = ROOT / "gold_smart.jsonl"

# ========================
# KNOWN BRANDS (IndiaMART industrial domain)
# ========================
KNOWN_BRANDS = {
    # big names
    "siemens", "abb", "schneider", "mitsubishi", "fanuc", "yaskawa", "bosch",
    "rexroth", "allen bradley", "rockwell", "omron", "panasonic", "hitachi",
    "toshiba", "fuji", "ls", "delta", "danfoss", "vacon", "lenze", "sew",
    "nidec", "marathon", "leeson", "baldor", "weg", "crompton", "greaves",
    "kirloskar", "havells", "bharat bijlee", "abb motors", "simotics",
    "crompton greaves", "bharat", "emerson", "flender", "bonfiglioli",
    "nord", "sumitomo", "dodge", "regal", "sterling", "elmec", "havells",
    "legrand", "larsen", "toubro", "l&t", "c&s", "bpl",
    # motor-specific
    "amrut", "rotomotive", "spg", "venex", "yako", "makita", "dewalt",
    "stanley", "hilti", "ingersoll", "rand", "ingersoll rand", "atlas copco",
    "kaeser", "elgi", "everest", "chicago pneumatic",
    # Indian brands
    "bajaj", "cg", "cg motors", "marathwada", "general electric", "ge",
    "honeywell", "eaton", "moeller", "weg electric",
}

BRAND_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(b) for b in sorted(KNOWN_BRANDS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)

# ========================
# PART TYPE VOCABULARY
# ========================
PART_TYPES = [
    ("servo motor", "motor"), ("induction motor", "motor"), ("gear motor", "motor"),
    ("gearmotor", "motor"), ("stepper motor", "motor"), ("bldc motor", "motor"),
    ("dc motor", "motor"), ("ac motor", "motor"), ("brushless motor", "motor"),
    ("synchronous motor", "motor"), ("asynchronous motor", "motor"),
    ("brake motor", "motor"), ("flame proof motor", "motor"),
    ("submersible motor", "motor"), ("pump motor", "motor"),
    ("fan motor", "motor"), ("spindle motor", "motor"), ("traction motor", "motor"),
    ("torque motor", "motor"), ("linear motor", "motor"),
    ("motor", "motor"),
    ("gearbox", "gearbox"), ("gear box", "gearbox"), ("worm gearbox", "gearbox"),
    ("gear reducer", "gearbox"), ("reduction gear", "gearbox"),
    ("actuator", "actuator"), ("linear actuator", "actuator"),
    ("pneumatic actuator", "actuator"), ("electric actuator", "actuator"),
    ("valve actuator", "actuator"),
    ("pump", "pump"), ("centrifugal pump", "pump"), ("submersible pump", "pump"),
    ("vacuum pump", "pump"), ("gear pump", "pump"), ("hydraulic pump", "pump"),
    ("compressor", "compressor"), ("air compressor", "compressor"),
    ("screw compressor", "compressor"), ("piston compressor", "compressor"),
    ("transformer", "transformer"), ("distribution transformer", "transformer"),
    ("power transformer", "transformer"), ("servo stabilizer", "transformer"),
    ("drive", "drive"), ("vfd", "drive"), ("vfd drive", "drive"),
    ("variable frequency drive", "drive"), ("inverter", "inverter"),
    ("servo drive", "drive"), ("ac drive", "drive"), ("dc drive", "drive"),
    ("encoder", "encoder"), ("rotary encoder", "encoder"),
    ("sensor", "sensor"), ("proximity sensor", "sensor"),
    ("temperature sensor", "sensor"), ("pressure sensor", "sensor"),
    ("switch", "switch"), ("limit switch", "switch"), ("toggle switch", "switch"),
    ("contactor", "contactor"), ("motor starter", "starter"),
    ("dol starter", "starter"), ("star delta starter", "starter"),
    ("relay", "relay"), ("overload relay", "relay"),
    ("positioner", "positioner"), ("valve positioner", "positioner"),
    ("solenoid valve", "valve"), ("control valve", "valve"), ("valve", "valve"),
    ("coupling", "coupling"), ("flexible coupling", "coupling"),
    ("bearing", "bearing"), ("ball bearing", "bearing"),
    ("brake", "brake"), ("electromagnetic brake", "brake"),
    ("slip ring", "slip ring"), ("collector ring", "slip ring"),
    ("rotor", "rotor"), ("stator", "stator"), ("armature", "armature"),
    ("capacitor", "capacitor"), ("resistor", "resistor"),
    ("controller", "controller"), ("plc", "plc"), ("hmi", "hmi"),
    ("servo controller", "controller"),
    ("fan", "fan"), ("blower", "blower"), ("exhaust fan", "fan"),
    ("heat sink", "heat sink"), ("cooling fan", "fan"),
]

# ========================
# SPEC PATTERNS
# ========================
HP_PAT   = re.compile(r'(\d+(?:\.\d+)?)\s*(?:hp|h\.p\.|horse\s*power)', re.IGNORECASE)
KW_PAT   = re.compile(r'(\d+(?:\.\d+)?)\s*(?:kw|kilo\s*watt)', re.IGNORECASE)
W_PAT    = re.compile(r'(\d+(?:\.\d+)?)\s*(?:w|watt)(?!\w)', re.IGNORECASE)
PHASE_PAT = re.compile(r'\b(1|2|3|single|double|three|1-phase|2-phase|3-phase)\s*phase\b', re.IGNORECASE)
VOLT_PAT = re.compile(r'(\d+(?:\.\d+)?)\s*(?:v|volt|volts|voltage)(?!\w)', re.IGNORECASE)
RPM_PAT  = re.compile(r'(\d[\d,/]*)\s*(?:rpm|r\.?p\.?m)', re.IGNORECASE)
HZ_PAT   = re.compile(r'(\d+(?:\.\d+)?)\s*(?:hz|hertz)', re.IGNORECASE)

# model number: typically uppercase/mixed token with digits and sometimes hyphens
MODEL_PAT = re.compile(r'\b([A-Z][A-Z0-9\-/_]{3,})\b')
# Also: numeric-leading tokens like "1FK2104-6AF01"
MODEL_PAT2 = re.compile(r'\b(\d[A-Z0-9\-/_]{3,})\b')

DRIVEN_TYPES = {
    "servo": "servo", "stepper": "stepper", "bldc": "brushless DC",
    "brushless": "brushless DC", "brushed": "brushed DC",
    "induction": "induction", "synchronous": "synchronous",
    "asynchronous": "induction", "slip ring": "slip ring",
    "wound rotor": "wound rotor", "squirrel cage": "squirrel cage",
    "permanent magnet": "permanent magnet", "pmdc": "permanent magnet DC",
}

POWER_SOURCES = {
    r'\bac\b': "AC", r'\bdc\b': "DC",
    r'\ba\.c\.?\b': "AC", r'\bd\.c\.?\b': "DC",
    r'\belectric\b': "electric",
}

ORIENTATIONS = {
    "vertical": "vertical", "horizontal": "horizontal",
    "flange": "flange mounted", "foot": "foot mounted",
    "hollow shaft": "hollow shaft",
}


def norm_phase(m: str) -> str:
    mapping = {"1": "1", "single": "1", "2": "2", "double": "2",
               "3": "3", "three": "3"}
    base = m.lower().replace("-phase", "").strip()
    return mapping.get(base, base)


def extract_attrs(query: str) -> dict:
    """Rule-based attribute extractor."""
    attrs = {}
    q = query.strip()
    ql = q.lower()

    # 1. Part type — longest match first
    for phrase, canonical in PART_TYPES:
        if re.search(r'\b' + re.escape(phrase) + r'\b', ql):
            attrs["part type"] = canonical
            break

    # 2. Brand
    bm = BRAND_PATTERN.search(q)
    if bm:
        brand = bm.group(1)
        # Special: "Crompton Greaves" is two words
        cg_m = re.search(r'crompton\s+greaves', q, re.IGNORECASE)
        if cg_m:
            brand = "Crompton Greaves"
        attrs["brand"] = brand

    # 3. Horsepower
    hp_m = HP_PAT.search(q)
    if hp_m:
        attrs["horsepower"] = f"{hp_m.group(1)} hp"

    # 4. Power (kW / W)
    if "horsepower" not in attrs:
        kw_m = KW_PAT.search(q)
        if kw_m:
            attrs["power"] = f"{kw_m.group(1)} kW"
        else:
            w_m = W_PAT.search(q)
            if w_m and float(w_m.group(1)) > 0:
                attrs["power"] = f"{w_m.group(1)} W"

    # 5. Phase
    ph_m = PHASE_PAT.search(q)
    if ph_m:
        attrs["phase"] = norm_phase(ph_m.group(1))

    # 6. Voltage
    volt_m = VOLT_PAT.search(q)
    if volt_m:
        attrs["voltage"] = f"{volt_m.group(1)} V"

    # 7. RPM / Speed
    rpm_m = RPM_PAT.search(q)
    if rpm_m:
        attrs["rated speed"] = f"{rpm_m.group(1)} rpm"

    # 8. Frequency
    hz_m = HZ_PAT.search(q)
    if hz_m:
        attrs["frequency"] = f"{hz_m.group(1)} Hz"

    # 9. Driven type
    for kw, val in DRIVEN_TYPES.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', ql):
            if not (kw == "servo" and attrs.get("part type") == "drive"):
                attrs["driven type"] = val
            break

    # 10. Power source
    for pat, val in POWER_SOURCES.items():
        if re.search(pat, ql):
            attrs["power source"] = val
            break

    # 11. Orientation
    for kw, val in ORIENTATIONS.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', ql):
            attrs["orientation"] = val
            break

    # 12. Model number — only if brand or part type was found (avoid false positives)
    if attrs.get("brand") or attrs.get("part type"):
        model_tokens = []
        for m in MODEL_PAT.finditer(q):
            tok = m.group(1)
            # Skip if it's a known brand name
            if tok.lower() in {b.lower() for b in KNOWN_BRANDS}:
                continue
            # Skip common non-model uppercase words
            if tok.upper() in {"AC", "DC", "HP", "KW", "VFD", "PLC", "HMI",
                                "RPM", "ABB", "CG", "AMP", "FOR", "AND",
                                "THE", "NEW", "OLD", "USE", "LED", "USED"}:
                continue
            # Must contain at least one digit to be a model number
            if re.search(r'\d', tok):
                model_tokens.append(tok)
        for m2 in MODEL_PAT2.finditer(q):
            tok = m2.group(1)
            if tok not in model_tokens:
                model_tokens.append(tok)
        if model_tokens:
            attrs["model name/number"] = " ".join(model_tokens[:2])

    return attrs


# ========================
# TRAIN LOOKUP (exact + normalized)
# ========================
def load_train_lookup(path: Path) -> dict:
    """Build query→attrs lookup from training data."""
    lkp = {}
    if not path.exists():
        return lkp
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            instr = row.get("instruction", "")
            marker = "this query:"
            idx = instr.find(marker)
            q = instr[idx + len(marker):].strip() if idx != -1 else ""
            try:
                attrs = json.loads(row.get("output", "{}"))
                if q and isinstance(attrs, dict) and attrs:
                    lkp[q.lower().strip()] = attrs
            except Exception:
                pass
    return lkp


def merge_attrs(base: dict, extra: dict) -> dict:
    """Merge: extra fills in missing keys only."""
    merged = dict(base)
    for k, v in extra.items():
        if k not in merged:
            merged[k] = v
    return merged


def main():
    # Load existing old gold as reference
    old_gold = {}
    if OLD_GOLD.exists():
        with open(OLD_GOLD, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    row = json.loads(line)
                    old_gold[row["query"]] = row.get("attributes", {})

    # Load train lookup
    train_lkp = load_train_lookup(TRAIN_FILE)
    print(f"Train lookup: {len(train_lkp)} entries")

    # Load test queries
    queries = []
    with open(QUERIES_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line)["query"])
    print(f"Queries: {len(queries)}")

    results = []
    stats = {"exact": 0, "rule": 0, "empty": 0, "old_gold": 0}

    for q in queries:
        ql = q.lower().strip()

        # Priority 1: Old gold (already audited, trustworthy)
        if q in old_gold:
            attrs = old_gold[q]
            stats["old_gold"] += 1
        # Priority 2: Exact match from training data
        elif ql in train_lkp:
            attrs = train_lkp[ql]
            stats["exact"] += 1
        else:
            # Priority 3: Rule-based extraction
            rule_attrs = extract_attrs(q)
            # Try to supplement from old gold if partial overlap
            if q in old_gold:
                attrs = merge_attrs(old_gold[q], rule_attrs)
            else:
                attrs = rule_attrs
            if attrs:
                stats["rule"] += 1
            else:
                stats["empty"] += 1

        results.append({"query": q, "attributes": attrs})

    with open(OUTPUT, "w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(results)} annotations to {OUTPUT}")
    print(f"  from old_gold  : {stats['old_gold']}")
    print(f"  from train lookup: {stats['exact']}")
    print(f"  from rules     : {stats['rule']}")
    print(f"  empty          : {stats['empty']}")

    # Quick quality check
    non_empty = sum(1 for r in results if r["attributes"])
    print(f"  non-empty      : {non_empty}/{len(results)} ({100*non_empty/len(results):.1f}%)")


if __name__ == "__main__":
    main()
