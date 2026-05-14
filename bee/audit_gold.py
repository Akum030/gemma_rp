"""
Audit Opus gold (bee/gold_1k.jsonl) for Makita-class brand confusion.

Patterns where the apparent OEM is NOT the brand of the part being sold:
  "X Component By Y"          -> Y is the brand
  "X Component for Y"          -> Y is the compatibility, X is brand of accessory
  "X Component compatible with Y"
  "replacement for Y"
  "fits Y"
  "to suit Y"

For each match we re-judge brand using rule:
  - if pattern = "<part> By <Brand>"           -> brand = <Brand>
  - if pattern = "for/compatible/fits/to suit/replacement for <equip>"
                                               -> brand stays as the leading word IF it looks like a brand
                                                  else mark as 'unknown_brand' (drop brand key)

Outputs:
  bee/gold_audit_log.txt     -- every flip with reasoning
  bee/gold_1k_v2.jsonl       -- corrected gold
"""
import json, re, sys
from pathlib import Path

GOLD_IN  = Path("bee/gold_1k.jsonl")
GOLD_OUT = Path("bee/gold_1k_v2.jsonl")
LOG_OUT  = Path("bee/gold_audit_log.txt")

# regex patterns (case insensitive). group 'tail' is what comes after the marker.
PATTERNS = [
    ("by",                  re.compile(r"\bby\s+([A-Za-z][\w\-\.& ]{1,40})", re.I)),
    ("for",                 re.compile(r"\bfor\s+([A-Za-z][\w\-\.& ]{1,40})", re.I)),
    ("compatible_with",     re.compile(r"\bcompatible\s+with\s+([A-Za-z][\w\-\.& ]{1,40})", re.I)),
    ("replacement_for",     re.compile(r"\breplacement\s+for\s+([A-Za-z][\w\-\.& ]{1,40})", re.I)),
    ("fits",                re.compile(r"\bfits\s+([A-Za-z][\w\-\.& ]{1,40})", re.I)),
    ("to_suit",             re.compile(r"\bto\s+suit\s+([A-Za-z][\w\-\.& ]{1,40})", re.I)),
    ("suitable_for",        re.compile(r"\bsuitable\s+for\s+([A-Za-z][\w\-\.& ]{1,40})", re.I)),
    ("use_in",              re.compile(r"\buse\s+in\s+([A-Za-z][\w\-\.& ]{1,40})", re.I)),
]

# words to strip from a captured "brand-like" tail
STOP_TAIL = {"the", "and", "with", "in", "of", "a", "an"}

def clean_tail(t: str) -> str:
    t = t.strip().rstrip(",.;:")
    # take only first 1-3 word brand-looking token sequence
    parts = [p for p in re.split(r"\s+", t) if p]
    keep = []
    for p in parts[:3]:
        if p.lower() in STOP_TAIL:
            break
        keep.append(p)
    return " ".join(keep).strip()


def find_brand_value(attrs: dict) -> str:
    """Return the value stored under any brand-like key, else ''."""
    for k, v in attrs.items():
        if k.lower() in ("brand", "manufacturer", "company", "make"):
            if isinstance(v, str):
                return v
    return ""


def main():
    if not GOLD_IN.exists():
        print(f"missing {GOLD_IN}", file=sys.stderr); sys.exit(1)

    rows = [json.loads(l) for l in open(GOLD_IN, encoding="utf-8-sig") if l.strip()]
    print(f"loaded {len(rows)} gold rows")

    flips = []
    for row in rows:
        q = row.get("query", "")
        attrs = row.get("attributes", {}) or {}
        for marker, pat in PATTERNS:
            m = pat.search(q)
            if not m:
                continue
            tail = clean_tail(m.group(1))
            if not tail:
                continue
            current_brand = find_brand_value(attrs)

            if marker == "by":
                # Y after "By" IS the brand (Makita / PowerSpeed lesson)
                new_brand = tail.lower()
                if new_brand and new_brand != (current_brand or "").lower():
                    flips.append({
                        "query": q,
                        "marker": marker,
                        "tail": tail,
                        "old_brand": current_brand,
                        "new_brand": new_brand,
                        "action": "set_brand",
                    })
            else:
                # for / compatible with / replacement for / fits / etc:
                # the trailing word is COMPATIBILITY, not brand.
                # If current_brand happens to equal this trailing word -> flag.
                if current_brand and current_brand.lower() == tail.lower():
                    flips.append({
                        "query": q,
                        "marker": marker,
                        "tail": tail,
                        "old_brand": current_brand,
                        "new_brand": None,
                        "action": "drop_brand_keep_compat",
                    })

    # apply
    flip_index = {f["query"]: f for f in flips}
    with open(GOLD_OUT, "w", encoding="utf-8") as fout, \
         open(LOG_OUT,  "w", encoding="utf-8") as flog:
        flog.write(f"GOLD AUDIT — {len(flips)} flips out of {len(rows)} rows\n")
        flog.write("=" * 70 + "\n")
        for row in rows:
            q = row.get("query", "")
            new_attrs = dict(row.get("attributes", {}) or {})
            f = flip_index.get(q)
            if f:
                if f["action"] == "set_brand":
                    new_attrs["brand"] = f["new_brand"]
                    flog.write(f"\nFLIP set_brand | {q}\n  old brand: {f['old_brand']!r}  new brand: {f['new_brand']!r}\n")
                elif f["action"] == "drop_brand_keep_compat":
                    # remove brand keys; add compatibility key
                    for k in list(new_attrs.keys()):
                        if k.lower() in ("brand", "manufacturer", "company", "make"):
                            new_attrs.pop(k, None)
                    new_attrs["compatibility"] = f["tail"].lower()
                    flog.write(f"\nFLIP drop_brand | {q}\n  was brand: {f['old_brand']!r}  now compatibility: {f['tail']!r}\n")
            new_row = {"query": q, "attributes": new_attrs}
            fout.write(json.dumps(new_row, ensure_ascii=False) + "\n")

        flog.write("\n" + "=" * 70 + "\n")
        flog.write("SUMMARY:\n")
        from collections import Counter
        c = Counter(f["action"] for f in flips)
        for k, v in c.most_common():
            flog.write(f"  {k}: {v}\n")

    print(f"flips: {len(flips)}")
    print(f"wrote {GOLD_OUT} and {LOG_OUT}")


if __name__ == "__main__":
    main()
