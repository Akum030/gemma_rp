"""
Build a consolidated markdown and CSV benchmark report from available priority summary JSON files.
"""
import argparse
import csv
import json
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--v7", required=True)
    parser.add_argument("--hybrid", default="")
    parser.add_argument("--v8", required=True)
    parser.add_argument("--v9", required=True)
    parser.add_argument("--v10", default="")
    parser.add_argument("--v11", default="")
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-csv", required=True)
    return parser.parse_args()


def load_summary(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def extract_row(label, summary):
    if not summary:
        return {
            "label": label,
            "status": "missing",
            "n": "",
            "key_precision": "",
            "key_recall": "",
            "key_f1": "",
            "key_value_precision": "",
            "key_value_recall": "",
            "key_value_f1": "",
        }

    key_name = next((key for key in summary.keys() if key.endswith("_vs_gold") and key != "qmeans_vs_gold"), None)
    if not key_name:
        return {
            "label": label,
            "status": "invalid",
            "n": summary.get("n", ""),
            "key_precision": "",
            "key_recall": "",
            "key_f1": "",
            "key_value_precision": "",
            "key_value_recall": "",
            "key_value_f1": "",
        }

    key_only = summary[key_name]["key_only"]
    key_value = summary[key_name]["key_value"]
    return {
        "label": label,
        "status": "completed",
        "n": summary.get("n", ""),
        "key_precision": key_only["precision"],
        "key_recall": key_only["recall"],
        "key_f1": key_only["f1"],
        "key_value_precision": key_value["precision"],
        "key_value_recall": key_value["recall"],
        "key_value_f1": key_value["f1"],
    }


def extract_qmeans(summary):
    if not summary or "qmeans_vs_gold" not in summary:
        return None
    key_only = summary["qmeans_vs_gold"]["key_only"]
    key_value = summary["qmeans_vs_gold"]["key_value"]
    return {
        "label": "qmeans",
        "status": "completed",
        "n": summary.get("n", ""),
        "key_precision": key_only["precision"],
        "key_recall": key_only["recall"],
        "key_f1": key_only["f1"],
        "key_value_precision": key_value["precision"],
        "key_value_recall": key_value["recall"],
        "key_value_f1": key_value["f1"],
    }


def write_csv(path, rows):
    fieldnames = [
        "label",
        "status",
        "n",
        "key_precision",
        "key_recall",
        "key_f1",
        "key_value_precision",
        "key_value_recall",
        "key_value_f1",
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path, rows, source_paths):
    lines = []
    lines.append("# Priority Benchmark Report")
    lines.append("")
    lines.append("## Source Files")
    for label, source_path in source_paths.items():
        lines.append(f"- {label}: `{source_path}`")
    lines.append("")
    lines.append("## Summary Table")
    lines.append("")
    lines.append("| Model | Status | N | Key P | Key R | Key F1 | Key+Value P | Key+Value R | Key+Value F1 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['label']} | {row['status']} | {row['n']} | {row['key_precision']} | {row['key_recall']} | {row['key_f1']} | {row['key_value_precision']} | {row['key_value_recall']} | {row['key_value_f1']} |"
        )

    completed = [row for row in rows if row["status"] == "completed"]
    lines.append("")
    lines.append("## Notes")
    if not completed:
        lines.append("- No completed summaries were available when this report was generated.")
    else:
        best_key = max(completed, key=lambda row: float(row["key_f1"]))
        best_key_value = max(completed, key=lambda row: float(row["key_value_f1"]))
        lines.append(f"- Best current key F1: {best_key['label']} ({best_key['key_f1']})")
        lines.append(f"- Best current key+value F1: {best_key_value['label']} ({best_key_value['key_value_f1']})")
        standalone_priority = [row for row in completed if row["label"].startswith("v")]
        if standalone_priority:
            best_priority = max(standalone_priority, key=lambda row: float(row["key_value_f1"]))
            lines.append(f"- Best standalone priority model: {best_priority['label']} (key+value F1 {best_priority['key_value_f1']})")
        if any(row["label"] == "hybrid_v7_plus_qmeans_fallback" for row in completed):
            lines.append("- The hybrid row is a serving-time combination, not a new standalone finetuned model.")
        lines.append("- This report is purely a metric rollup. It does not replace structural error analysis.")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    args = parse_args()
    v7 = load_summary(args.v7)
    hybrid = load_summary(args.hybrid)
    v8 = load_summary(args.v8)
    v9 = load_summary(args.v9)
    v10 = load_summary(args.v10)
    v11 = load_summary(args.v11)

    rows = []
    qmeans = extract_qmeans(v7 or hybrid or v8 or v9 or v10 or v11)
    if qmeans:
        rows.append(qmeans)
    rows.append(extract_row("v7", v7))
    if args.hybrid:
        rows.append(extract_row("hybrid_v7_plus_qmeans_fallback", hybrid))
    rows.append(extract_row("v8", v8))
    rows.append(extract_row("v9", v9))
    rows.append(extract_row("v10", v10))
    if args.v11:
        rows.append(extract_row("v11", v11))

    write_csv(args.out_csv, rows)
    write_markdown(args.out_md, rows, {
        "v7": args.v7,
        "hybrid serving": args.hybrid,
        "v8": args.v8,
        "v9": args.v9,
        "v10": args.v10,
        "v11": args.v11,
    })


if __name__ == "__main__":
    main()