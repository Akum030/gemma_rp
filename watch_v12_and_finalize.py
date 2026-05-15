"""
Watcher for V12 pipeline completion.

What it does:
- polls server for v12_eval_summary.json
- once available, downloads summary/results/logs
- updates tracking CSVs with final V12 metrics

Run locally (optional):
  python watch_v12_and_finalize.py
"""
import json
import os
import csv
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRACKING = ROOT / "tracking"
LOGS = ROOT / "logs"

SSH = [r"C:\Program Files\Git\usr\bin\ssh.exe", "amit_87483@34.93.58.248"]
SCP = r"C:\Program Files\Git\usr\bin\scp.exe"
REMOTE_BASE = "/home3/indiamart/gemma_4"

SUMMARY_REMOTE = f"{REMOTE_BASE}/v12_eval_summary.json"
RESULTS_REMOTE = f"{REMOTE_BASE}/v12_priority_results.jsonl"
TRAIN_LOG_REMOTE = f"{REMOTE_BASE}/v12_train.log"
EVAL_LOG_REMOTE = f"{REMOTE_BASE}/v12_eval.log"

SUMMARY_LOCAL = ROOT / "v12_eval_summary.json"
RESULTS_LOCAL = ROOT / "v12_priority_results.jsonl"
TRAIN_LOG_LOCAL = LOGS / "v12_train.log"
EVAL_LOG_LOCAL = LOGS / "v12_eval.log"

STATUS_FILE = ROOT / "v12_watch_state.json"
POLL_SECONDS = 120


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def remote_exists(path):
    cmd = SSH + [f"test -f {path} && echo yes || echo no"]
    result = run(cmd)
    return "yes" in result.stdout


def scp_down(remote, local_path):
    local_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [SCP, f"amit_87483@34.93.58.248:{remote}", str(local_path)]
    result = run(cmd)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def write_status(data):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_results_summary(summary_json):
    path = TRACKING / "results_summary.csv"
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    v12 = None
    for row in rows:
        if row.get("version") == "v12":
            v12 = row
            break
    if not v12:
        return

    metrics = summary_json.get("v12_vs_gold", {})
    key = metrics.get("key_only", {})
    kv = metrics.get("key_value", {})

    v12["status"] = "completed"
    v12["key_precision"] = f"{key.get('precision', 0):.4f}"
    v12["key_recall"] = f"{key.get('recall', 0):.4f}"
    v12["key_f1"] = f"{key.get('f1', 0):.4f}"
    v12["key_value_precision"] = f"{kv.get('precision', 0):.4f}"
    v12["key_value_recall"] = f"{kv.get('recall', 0):.4f}"
    v12["key_value_f1"] = f"{kv.get('f1', 0):.4f}"
    v12["notes"] = "completed by watcher"

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def update_version_history_completed():
    path = TRACKING / "version_history.csv"
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    for row in rows:
        if row.get("version") == "v12":
            row["status"] = "completed"
            row["notes"] = "completed by watcher"
            break

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    write_status({"status": "watching", "started_at": time.time()})

    while True:
        if remote_exists(SUMMARY_REMOTE):
            scp_down(SUMMARY_REMOTE, SUMMARY_LOCAL)
            if remote_exists(RESULTS_REMOTE):
                scp_down(RESULTS_REMOTE, RESULTS_LOCAL)
            if remote_exists(TRAIN_LOG_REMOTE):
                scp_down(TRAIN_LOG_REMOTE, TRAIN_LOG_LOCAL)
            if remote_exists(EVAL_LOG_REMOTE):
                scp_down(EVAL_LOG_REMOTE, EVAL_LOG_LOCAL)

            with open(SUMMARY_LOCAL, "r", encoding="utf-8") as f:
                summary = json.load(f)
            update_results_summary(summary)
            update_version_history_completed()
            write_status({"status": "completed", "completed_at": time.time()})
            print("V12 completed and tracking files updated.")
            return

        write_status({"status": "watching", "last_check": time.time()})
        print("V12 not completed yet; waiting...")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
