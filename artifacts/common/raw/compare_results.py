"""
Compare MCAT predictions: Transformers vs Unsloth vs API
Outputs:
  - mcat_comparison_full.csv  : all 1000 rows side by side
  - mcat_comparison_stats.txt : match rate summary
"""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent

TRANSFORMERS_CSV = HERE / "transformers_mcat_results.csv"
UNSLOTH_CSV      = HERE / "unsloth_mcat_results.csv"
API_CSV          = HERE.parent / "compare" / "api_mcat_results.csv"
OUTPUT_CSV       = HERE / "mcat_comparison_full.csv"
OUTPUT_STATS     = HERE / "mcat_comparison_stats.txt"


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize(val):
    return str(val).strip().lower()


def main():
    trans_rows  = load_csv(TRANSFORMERS_CSV)
    unsloth_rows = load_csv(UNSLOTH_CSV)
    api_rows    = load_csv(API_CSV)

    # Index by keyword for safe join
    def index(rows, key="keyword"):
        return {normalize(r[key]): r for r in rows}

    trans_idx   = index(trans_rows)
    unsloth_idx = index(unsloth_rows)
    api_idx     = index(api_rows)

    # Use API keywords as ground-truth order
    all_keywords = [r["keyword"] for r in api_rows]

    stats = {
        "total": 0,
        # mcat_id matches
        "trans_api_id_match": 0,
        "unsloth_api_id_match": 0,
        "trans_unsloth_id_match": 0,
        # mcat_name matches (case-insensitive)
        "trans_api_name_match": 0,
        "unsloth_api_name_match": 0,
        "all_three_id_match": 0,
    }

    out_rows = []

    for kw in all_keywords:
        nkw = normalize(kw)
        api_r     = api_idx.get(nkw, {})
        trans_r   = trans_idx.get(nkw, {})
        unsloth_r = unsloth_idx.get(nkw, {})

        api_id    = normalize(api_r.get("mcat_id", ""))
        api_name  = normalize(api_r.get("mcat_name", ""))
        api_acc   = api_r.get("mcat_accuracy_level", "")

        trans_id   = normalize(trans_r.get("mcat_id", ""))
        trans_name = normalize(trans_r.get("mcat_name", ""))

        unsloth_id   = normalize(unsloth_r.get("mcat_id", ""))
        unsloth_name = normalize(unsloth_r.get("mcat_name", ""))

        # Match flags
        t_vs_api_id    = (trans_id == api_id and api_id != "")
        u_vs_api_id    = (unsloth_id == api_id and api_id != "")
        t_vs_u_id      = (trans_id == unsloth_id and trans_id != "")
        t_vs_api_name  = (trans_name == api_name and api_name != "")
        u_vs_api_name  = (unsloth_name == api_name and api_name != "")
        all_three_id   = (t_vs_api_id and u_vs_api_id)

        stats["total"] += 1
        if t_vs_api_id:   stats["trans_api_id_match"] += 1
        if u_vs_api_id:   stats["unsloth_api_id_match"] += 1
        if t_vs_u_id:     stats["trans_unsloth_id_match"] += 1
        if t_vs_api_name: stats["trans_api_name_match"] += 1
        if u_vs_api_name: stats["unsloth_api_name_match"] += 1
        if all_three_id:  stats["all_three_id_match"] += 1

        out_rows.append({
            "keyword":            kw,
            # API
            "api_mcat_name":      api_r.get("mcat_name", ""),
            "api_mcat_id":        api_r.get("mcat_id", ""),
            "api_accuracy":       api_acc,
            # Transformers
            "trans_mcat_name":    trans_r.get("mcat_name", ""),
            "trans_mcat_id":      trans_r.get("mcat_id", ""),
            "trans_vs_api_id":    "MATCH" if t_vs_api_id   else "DIFF",
            "trans_vs_api_name":  "MATCH" if t_vs_api_name else "DIFF",
            # Unsloth
            "unsloth_mcat_name":  unsloth_r.get("mcat_name", ""),
            "unsloth_mcat_id":    unsloth_r.get("mcat_id", ""),
            "unsloth_vs_api_id":  "MATCH" if u_vs_api_id   else "DIFF",
            "unsloth_vs_api_name":"MATCH" if u_vs_api_name else "DIFF",
            # Trans vs Unsloth
            "trans_vs_unsloth_id":"MATCH" if t_vs_u_id else "DIFF",
            # All three agree
            "all_three_agree":    "YES" if all_three_id else "NO",
        })

    # Write full comparison CSV
    fieldnames = [
        "keyword",
        "api_mcat_name", "api_mcat_id", "api_accuracy",
        "trans_mcat_name", "trans_mcat_id", "trans_vs_api_id", "trans_vs_api_name",
        "unsloth_mcat_name", "unsloth_mcat_id", "unsloth_vs_api_id", "unsloth_vs_api_name",
        "trans_vs_unsloth_id", "all_three_agree",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    n = stats["total"]

    def pct(x):
        return f"{x}/{n} ({100*x/n:.1f}%)"

    # Write stats
    lines = [
        "=" * 60,
        "  MCAT Prediction Comparison Summary",
        "=" * 60,
        f"Total queries compared : {n}",
        "",
        "── mcat_id match (exact ID) ──────────────────────────────",
        f"  Transformers  vs API    : {pct(stats['trans_api_id_match'])}",
        f"  Unsloth       vs API    : {pct(stats['unsloth_api_id_match'])}",
        f"  Transformers  vs Unsloth: {pct(stats['trans_unsloth_id_match'])}",
        f"  All three agree (ID)    : {pct(stats['all_three_id_match'])}",
        "",
        "── mcat_name match (case-insensitive) ────────────────────",
        f"  Transformers  vs API    : {pct(stats['trans_api_name_match'])}",
        f"  Unsloth       vs API    : {pct(stats['unsloth_api_name_match'])}",
        "=" * 60,
        f"\nFull comparison saved to: {OUTPUT_CSV}",
    ]

    report = "\n".join(lines)
    print(report)

    with open(OUTPUT_STATS, "w", encoding="utf-8") as f:
        f.write(report + "\n")

    print(f"Stats saved to        : {OUTPUT_STATS}")


if __name__ == "__main__":
    main()
