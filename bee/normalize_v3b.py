"""
Post-process v3b raw output: aggressive key normalization + bare-key JSON repair.
Reads bee/v3b_results.csv, writes bee/v3b_norm.csv/.jsonl.
"""
import csv, json, re, sys, os

CANON_KEYS = {
    "frequency","die type","automation grade","power","motor power","weight","process",
    "location/city","usage","operation","place of origin","number of layers","storage material",
    "processing type","shape","country of origin","voltage","types of metal","series","brand",
    "suitable for","size","type of namkeen","name of extract","machine name","technology",
    "machine type","metal","driven type","purity","refining material","power source",
    "screw diameter","blower type","part type","product","botanical name","orientation",
    "power consumption","model name/number","rated speed","material","capacity","color",
    "phase","horsepower","speed","feature","grade","packaging size","model number",
    "voltage rating","current","insulation class","mounting type","frame size","rpm",
    "torque","efficiency","ip rating","duty cycle","cooling type","starter type",
    "shaft diameter","poles","temperature range","application","quantity","dimension","warranty",
}

# Aggressive aliases from v3b audit (case-folded LHS -> canonical RHS)
ALIASES = {
    # "attribute" / "attributes" / "value" — drop, they're meta-noise from model
    "attribute": None, "attributes": None, "value": None, "values": None,
    "key-value attributes": None, "key-value attribute": None,
    "key": None, "key_attributes": None, "query": None,
    # part type variants
    "motor": "part type", "Motor": "part type", "fan": "part type",
    "actuator": "part type", "encoder": "part type", "kit": "part type",
    "control board": "part type", "part": "part type",
    "product_type": "part type", "product type": "part type",
    # brand variants
    "brand_or_name": "brand", "brand_or_series": "brand", "brand_or_model": "brand",
    "brand/series": "brand", "brand/seller": "brand", "brand/make": "brand",
    "manufacturer": "brand", "make": "brand",
    # model number variants
    "model": "model name/number", "model_number": "model name/number",
    "model number": "model name/number", "Model Number": "model name/number",
    "model_no": "model name/number", "model no": "model name/number",
    "part_number": "model name/number", "part number": "model name/number",
    "product_code": "model name/number", "code": "model name/number",
    "product_line": "model name/number",
    # power
    "power_consumption": "power consumption",
    "rated_power": "power", "rated power": "power",
    # power source
    "power_source": "power source",
    # driven type
    "motor_type": "driven type", "motor type": "driven type",
    "drive type": "driven type", "drive_type": "driven type",
    "driven_type": "driven type",
    # speed
    "rated_speed": "rated speed", "speed_rpm": "rpm",
    # voltage
    "voltage_rating": "voltage rating",
    # location
    "location": "location/city", "city": "location/city",
    "country_of_origin": "country of origin",
    "place_of_origin": "place of origin",
    # size
    "size_attribute": "size", "size/weight": "size", "number": "size",
    # function/feature
    "function": "feature", "features": "feature", "functionality": "feature",
    # other
    "no of phase": "phase", "no_of_phase": "phase", "phases": "phase",
    "hp": "horsepower", "horse power": "horsepower",
    "frame_size": "frame size",
    "insulation_class": "insulation class",
    "ip_rating": "ip rating",
    "duty_cycle": "duty cycle",
    "starter_type": "starter type",
    "mounting_type": "mounting type",
    "cooling_type": "cooling type",
    "temperature_range": "temperature range",
    "shaft_diameter": "shaft diameter",
}

def canon_key(k):
    """Return canonical key, or None to drop."""
    if not isinstance(k, str): return None
    kl = k.strip()
    if not kl: return None
    # exact alias hit (case-sensitive)
    if kl in ALIASES: return ALIASES[kl]
    # case-folded alias hit
    klow = kl.lower()
    for ak, av in ALIASES.items():
        if ak.lower() == klow:
            return av
    # canonical exact (case-folded)
    if klow in CANON_KEYS: return klow
    # try common transforms: spaces<->underscore
    alt = klow.replace("_", " ")
    if alt in CANON_KEYS: return alt
    if alt in {a.lower() for a in ALIASES}:
        return ALIASES[next(a for a in ALIASES if a.lower() == alt)]
    # otherwise drop (don't pollute output with junk keys)
    return None


def norm_value(v):
    if v is None: return ""
    if isinstance(v, list):
        return "; ".join(str(x).strip() for x in v if str(x).strip())
    return str(v).strip()


def normalize(d):
    if not isinstance(d, dict): return {}
    out = {}
    for k, v in d.items():
        ck = canon_key(k)
        if ck is None:
            continue
        v = norm_value(v)
        if not v:
            continue
        if ck not in out:
            out[ck] = v
    return out


def parse_loose_json(raw):
    """Parse JSON, tolerating bare keys, single quotes, trailing junk."""
    if not raw: return None
    # cut chat markers
    for stop in ("<start_of_turn>", "<end_of_turn>", "</start_of_turn>", "<turn|>"):
        i = raw.find(stop)
        if i >= 0: raw = raw[:i]
    raw = raw.strip()
    if "{" not in raw: return None
    s = raw.find("{")
    depth = 0; e = -1
    for i, ch in enumerate(raw[s:], s):
        if ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0: e = i + 1; break
    cand = raw[s:e] if e > 0 else raw[s:] + "}"
    # try strict
    try: return json.loads(cand)
    except Exception: pass
    # try replacing single->double quotes for values
    try: return json.loads(cand.replace("'", '"'))
    except Exception: pass
    # quoted-key pairs
    pairs = re.findall(r'"([^"]+)"\s*:\s*("[^"]*"|\[[^\]]*\]|true|false|null|-?\d+(?:\.\d+)?)', cand)
    if pairs:
        try:
            return json.loads("{" + ",".join(f'"{k}":{v}' for k, v in pairs) + "}")
        except Exception:
            pass
    # bare-key  key: "value"  or  key: bareword
    pairs2 = re.findall(
        r'([A-Za-z_][\w \-/]*?)\s*:\s*(?:"([^"]*)"|([A-Za-z0-9_.\-/]+(?:[ /\-][A-Za-z0-9_.\-/]+)*))(?=[,}])',
        cand,
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


def main():
    src_csv = "bee/v3b_results.csv"
    out_csv = "bee/v3b_norm.csv"
    out_jsonl = "bee/v3b_norm.jsonl"
    n_total = 0; n_parse = 0; n_keys = 0
    with open(src_csv, encoding="utf-8") as f, \
         open(out_csv, "w", encoding="utf-8", newline="") as fc, \
         open(out_jsonl, "w", encoding="utf-8") as fj:
        rdr = csv.DictReader(f)
        w = csv.writer(fc)
        w.writerow(["query", "ok", "key_count", "raw_output", "attributes_json", "norm_attributes_json"])
        for r in rdr:
            n_total += 1
            q = r["query"]
            raw = r.get("raw_output", "")
            # try original parse first
            attrs = None
            try:
                attrs = json.loads(r.get("attributes_json", "") or "null")
            except Exception:
                attrs = None
            if not attrs:
                attrs = parse_loose_json(raw)
            norm = normalize(attrs or {})
            ok = bool(norm)
            if ok: n_parse += 1
            n_keys += len(norm)
            w.writerow([q, ok, len(norm), raw, json.dumps(attrs or {}), json.dumps(norm)])
            fj.write(json.dumps({"query": q, "ok": ok, "attributes": attrs or {}, "norm_attributes": norm}, ensure_ascii=False) + "\n")
    print(f"Total: {n_total}  parsed-with-canonical-keys: {n_parse} ({100*n_parse/n_total:.1f}%)  mean keys/q: {n_keys/n_total:.2f}")
    print(f"-> {out_csv}\n-> {out_jsonl}")

if __name__ == "__main__":
    main()
