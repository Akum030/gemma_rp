import sys, re, json
# Inline the parser to avoid torch import
def extract_json(raw):
    for stop in ("<start_of_turn>", "<end_of_turn>", "</start_of_turn>"):
        idx = raw.find(stop)
        if idx >= 0: raw = raw[:idx]
    raw = raw.strip()
    start = raw.find("{")
    if start < 0: return None
    depth = 0; end = -1
    for i, ch in enumerate(raw[start:], start):
        if ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0: end = i + 1; break
    candidate = raw[start:end] if end > 0 else raw[start:] + "}"
    try: return json.loads(candidate)
    except Exception: pass
    pairs = re.findall(r'"([^"]+)"\s*:\s*("[^"]*"|\[[^\]]*\]|true|false|null|-?\d+(?:\.\d+)?)', candidate)
    if not pairs:
        pairs2 = re.findall(
            r'([A-Za-z_][\w \-/]*?)\s*:\s*(?:"([^"]*)"|([A-Za-z0-9_.\-/ ]+?))(?=[,}])',
            candidate,
        )
        if pairs2:
            out = {}
            for k, qv, bv in pairs2:
                k = k.strip().lstrip("{").strip()
                v = (qv if qv else bv).strip()
                if not k or not v: continue
                out.setdefault(k, v)
            return out if out else None
        return None
    rebuilt = "{" + ",".join(f'"{k}":{v}' for k, v in pairs) + "}"
    try: return json.loads(rebuilt)
    except Exception: return None

cases = [
    '{attribute: "Cooler Motor"}',
    '{size_attribute: "130", shape: "Flat", power_source: "Motor"}',
    '{power_source}:a.c',
    '{product_line}:ms s3',
    '{   "feature": "ap fan motor" }',
    '{feature: "Ac", "Part": "Outdoor Fan Motor"}',
    '{   "Model": "Positioner Model 6dr5",   "Brand": "Siemens Sipart Ps2" }',
    '{model_number: ABC-123, power: 1 kW}',
]
for c in cases:
    print(repr(c), "->", extract_json(c))
