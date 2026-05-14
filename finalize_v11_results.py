import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--v11-summary", required=True)
    parser.add_argument("--v11-results", default="")
    parser.add_argument("--skip-report-rebuild", action="store_true")
    return parser.parse_args()


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def percent(value):
    return f"{value * 100:.2f}%"


def metric_tuple(summary, key):
    block = summary[key]
    return {
        "key_precision": block["key_only"]["precision"],
        "key_recall": block["key_only"]["recall"],
        "key_f1": block["key_only"]["f1"],
        "key_value_precision": block["key_value"]["precision"],
        "key_value_recall": block["key_value"]["recall"],
        "key_value_f1": block["key_value"]["f1"],
    }


def verdict(v11, v7, qmeans):
    beats_v7_key = v11["key_f1"] > v7["key_f1"]
    beats_v7_kv = v11["key_value_f1"] > v7["key_value_f1"]
    beats_qmeans_key = v11["key_f1"] > qmeans["key_f1"]
    beats_qmeans_kv = v11["key_value_f1"] > qmeans["key_value_f1"]

    if beats_v7_key and beats_v7_kv and beats_qmeans_key:
        short = "V11 beats V7 on both standalone metrics and also beats qmeans on key F1."
        abstract = "Later variants V8, V9, and V10 all underperform V7, while the conservative rollback V11 recovers performance strongly enough to beat V7 on both standalone metrics and surpass qmeans on key F1."
    elif beats_v7_key and beats_v7_kv:
        short = "V11 beats V7 on both standalone metrics, but qmeans still leads on key F1."
        abstract = "Later variants V8, V9, and V10 all underperform V7, while the conservative rollback V11 recovers performance enough to beat V7 on both standalone metrics even though qmeans still leads on broad key coverage."
    elif beats_v7_key and not beats_v7_kv:
        short = "V11 improves key recovery over V7 but does not beat V7 on exact key+value quality."
        abstract = "Later variants V8, V9, and V10 all underperform V7, while the conservative rollback V11 partially recovers standalone performance by improving key recovery without surpassing V7 on exact key+value quality."
    elif not beats_v7_key and beats_v7_kv:
        short = "V11 improves exact key+value quality over V7 but does not beat V7 on key recovery."
        abstract = "Later variants V8, V9, and V10 all underperform V7, while the conservative rollback V11 partially recovers standalone performance by improving exact key+value quality without surpassing V7 on key recovery."
    else:
        short = "V11 does not beat V7 on the trusted standalone benchmark."
        abstract = "Later variants V8, V9, V10, and V11 all underperform V7 on the trusted standalone benchmark, with the rollback V11 failing to fully recover standalone quality."

    if beats_qmeans_kv:
        short += " V11 also beats qmeans on key+value F1."

    return short, abstract


def sanitize_rows(rows, fieldnames):
    return [{field: row.get(field, "") for field in fieldnames} for row in rows]


def upsert_csv_row(path, key_field, key_value, new_row):
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = sanitize_rows(list(reader), fieldnames)

    found = False
    for index, row in enumerate(rows):
        if row[key_field] == key_value:
            rows[index] = new_row
            found = True
            break
    if not found:
        rows.append(new_row)

    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def upsert_senior_csv(path, standalone_row, training_note):
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = sanitize_rows(list(reader), fieldnames)

    standalone_found = False
    training_found = False
    insert_at = len(rows)
    for index, row in enumerate(rows):
        if row["section"] == "standalone_priority_model" and row["item"] == "gemma_v10_priority_clean":
            insert_at = index + 1
        if row["section"] == "standalone_priority_model" and row["item"] == "gemma_v11_priority_balanced":
            rows[index] = standalone_row
            standalone_found = True
        if row["section"] == "training_status" and row["item"] == "gemma_v11_priority_balanced":
            row["status"] = "completed"
            row["notes"] = training_note
            training_found = True

    if not standalone_found:
        rows.insert(insert_at, standalone_row)

    if not training_found:
        rows.append({
            "section": "training_status",
            "item": "gemma_v11_priority_balanced",
            "status": "completed",
            "key_precision": "",
            "key_recall": "",
            "key_f1": "",
            "key_value_precision": "",
            "key_value_recall": "",
            "key_value_f1": "",
            "notes": training_note,
        })

    for row in rows:
        if row["section"] == "paper_status" and row["item"] == "research_paper_draft_v2":
            row["notes"] = "Internal paper updated through V11 plus hybrid serving result; ready for senior review but not yet external submission"

    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def replace_once(text, old, new):
    if old in text:
        return text.replace(old, new, 1)
    return text


def replace_section(text, pattern, replacement):
    if re.search(pattern, text, flags=re.DOTALL):
        return re.sub(pattern, replacement, text, count=1, flags=re.DOTALL)
    return text


def update_text_file(path, updater):
    text = path.read_text(encoding="utf-8")
    updated = updater(text)
    path.write_text(updated, encoding="utf-8")


def rebuild_reports(root, v11_summary_path):
    command = [
        sys.executable,
        str(root / "build_priority_benchmark_report.py"),
        "--v7",
        str(root / "v7_eval_summary.json"),
        "--hybrid",
        str(root / "hybrid_v7_qmeans_eval_summary.json"),
        "--v8",
        str(root / "v8_eval_summary.json"),
        "--v9",
        str(root / "v9_eval_summary.json"),
        "--v10",
        str(root / "v10_eval_summary.json"),
        "--v11",
        str(v11_summary_path),
        "--out-md",
        str(root / "priority_benchmark_report.md"),
        "--out-csv",
        str(root / "priority_benchmark_report.csv"),
    ]
    subprocess.run(command, check=True, cwd=root)


def write_completion_note(path, metrics, short_verdict):
    lines = [
        "# V11 Completion Update",
        "",
        "## Standalone V11 Metrics",
        f"- key precision: {percent(metrics['key_precision'])}",
        f"- key recall: {percent(metrics['key_recall'])}",
        f"- key F1: {percent(metrics['key_f1'])}",
        f"- key+value precision: {percent(metrics['key_value_precision'])}",
        f"- key+value recall: {percent(metrics['key_value_recall'])}",
        f"- key+value F1: {percent(metrics['key_value_f1'])}",
        "",
        "## Verdict",
        f"- {short_verdict}",
        "",
        "## Related Files",
        "- priority_benchmark_report.md",
        "- priority_project_status.csv",
        "- senior_status_update_may11.csv",
        "- senior_status_update_may11.md",
        "- project_brief_for_senior.md",
        "- research_paper_draft_v2.md",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    args = parse_args()
    root = Path(args.root)
    v11_summary_path = Path(args.v11_summary)

    v11_summary = load_json(v11_summary_path)
    v7_summary = load_json(root / "v7_eval_summary.json")

    v11_metrics = metric_tuple(v11_summary, "v11_vs_gold")
    v7_metrics = metric_tuple(v7_summary, "v7_vs_gold")
    qmeans_metrics = metric_tuple(v7_summary, "qmeans_vs_gold")

    short_verdict, abstract_sentence = verdict(v11_metrics, v7_metrics, qmeans_metrics)

    if not args.skip_report_rebuild:
        rebuild_reports(root, v11_summary_path)

    upsert_csv_row(
        root / "priority_project_status.csv",
        "experiment",
        "gemma_v11_priority_balanced",
        {
            "experiment": "gemma_v11_priority_balanced",
            "benchmark_set": "gold_1k_v2",
            "metric_family": "current_priority_evaluator",
            "status": "completed",
            "key_precision": f"{v11_metrics['key_precision']:.4f}",
            "key_recall": f"{v11_metrics['key_recall']:.4f}",
            "key_f1": f"{v11_metrics['key_f1']:.4f}",
            "key_value_precision": f"{v11_metrics['key_value_precision']:.4f}",
            "key_value_recall": f"{v11_metrics['key_value_recall']:.4f}",
            "key_value_f1": f"{v11_metrics['key_value_f1']:.4f}",
            "exact_pair_match_rate": "",
            "all_attributes_correct": "",
            "zero_correct": "",
            "notes": f"Completed on 11 May; {short_verdict}",
        },
    )

    upsert_senior_csv(
        root / "senior_status_update_may11.csv",
        {
            "section": "standalone_priority_model",
            "item": "gemma_v11_priority_balanced",
            "status": "completed",
            "key_precision": f"{v11_metrics['key_precision']:.4f}",
            "key_recall": f"{v11_metrics['key_recall']:.4f}",
            "key_f1": f"{v11_metrics['key_f1']:.4f}",
            "key_value_precision": f"{v11_metrics['key_value_precision']:.4f}",
            "key_value_recall": f"{v11_metrics['key_value_recall']:.4f}",
            "key_value_f1": f"{v11_metrics['key_value_f1']:.4f}",
            "notes": short_verdict,
        },
        f"Pipeline completed on 11 May; final standalone metrics recorded in the gemma_v11_priority_balanced row. {short_verdict}",
    )

    def update_senior_md(text):
        text = replace_once(text, "through `V10`.", "through `V11`.")
        text = replace_section(
            text,
            r"A new conservative rollback experiment, `V11`, has now been launched\..*?For live inference, the preferred script is now \[inference_priority_hybrid\.py\]\(inference_priority_hybrid\.py\)\.",
            (
                "V11 training and evaluation are now complete.\n\n"
                "V11 metrics on the trusted 1k benchmark:\n"
                f"- key F1: {percent(v11_metrics['key_f1'])}\n"
                f"- key+value F1: {percent(v11_metrics['key_value_f1'])}\n"
                f"- {short_verdict}\n\n"
                "For live inference, the preferred script is now [inference_priority_hybrid.py](inference_priority_hybrid.py)."
            ),
        )
        text = replace_once(text, "- we still need to see whether `V11` can improve over `V7`", f"- V11 is now complete: {short_verdict}")
        return text

    def update_project_brief(text):
        replacement = (
            "### V11\n"
            "- V11 training and evaluation are now complete.\n"
            f"- key F1: {percent(v11_metrics['key_f1'])}\n"
            f"- key+value F1: {percent(v11_metrics['key_value_f1'])}\n"
            f"- {short_verdict}\n\n"
            "### Current Best Serving Path"
        )
        text = replace_section(text, r"### V11\n.*?### Current Best Serving Path", replacement)
        text = replace_once(text, "- V11 is that controlled rollback and is now running", f"- V11 is now complete: {short_verdict}")
        return text

    def update_research_paper(text):
        text = replace_once(text, "through V10", "through V11")
        text = replace_once(
            text,
            "Later variants V8, V9, and V10 all underperform V7, with the clean-schema-only V10 run collapsing almost completely on the trusted benchmark.",
            abstract_sentence,
        )
        text = replace_once(
            text,
            "- `V10`: clean-schema training run that removes noisy flat-to-nested converted data",
            "- `V10`: clean-schema training run that removes noisy flat-to-nested converted data\n- `V11`: conservative rollback toward the V7 recipe with a light clean nested-priority bias",
        )
        if "| V11 |" not in text:
            text = replace_once(
                text,
                "| V10 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |",
                "| V10 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |\n"
                f"| V11 | {percent(v11_metrics['key_precision'])} | {percent(v11_metrics['key_recall'])} | {percent(v11_metrics['key_f1'])} | {percent(v11_metrics['key_value_precision'])} | {percent(v11_metrics['key_value_recall'])} | {percent(v11_metrics['key_value_f1'])} |",
            )
        text = replace_once(
            text,
            "That controlled rollback experiment, `V11`, has now been launched.",
            f"That controlled rollback experiment, `V11`, has now completed. {short_verdict}",
        )
        v11_section = (
            "### 7.7 What V11 Taught Us\n"
            f"V11 completed with key F1 {percent(v11_metrics['key_f1'])} and key+value F1 {percent(v11_metrics['key_value_f1'])}. {short_verdict}\n\n"
            "This result is useful because it directly tests whether a conservative rollback toward the V7 recipe can recover standalone quality better than the aggressive changes used in V8-V10."
        )
        if "### 7.7 What V11 Taught Us" in text:
            text = replace_section(text, r"### 7\.7 What V11 Taught Us\n.*?(?=\n## 8\. Interpretation)", v11_section + "\n\n")
        else:
            text = replace_once(text, "## 8. Interpretation", v11_section + "\n\n## 8. Interpretation")
        text = replace_once(text, "The completed V7-V10 sequence suggests a clear next-model design rule:", "The completed V7-V11 sequence suggests a clear next-model design rule:")
        return text

    update_text_file(root / "senior_status_update_may11.md", update_senior_md)
    update_text_file(root / "project_brief_for_senior.md", update_project_brief)
    update_text_file(root / "research_paper_draft_v2.md", update_research_paper)

    write_completion_note(root / "v11_completion_update.md", v11_metrics, short_verdict)

    print(json.dumps({
        "status": "ok",
        "key_f1": round(v11_metrics["key_f1"], 4),
        "key_value_f1": round(v11_metrics["key_value_f1"], 4),
        "verdict": short_verdict,
    }, indent=2))


if __name__ == "__main__":
    main()