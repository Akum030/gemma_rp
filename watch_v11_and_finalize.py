import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_SSH_BIN = r"C:\Program Files\Git\usr\bin\ssh.exe"
DEFAULT_SCP_BIN = r"C:\Program Files\Git\usr\bin\scp.exe"
DEFAULT_REMOTE_HOST = "amit_87483@34.93.58.248"
REMOTE_RESULT_DIR = "/home3/indiamart/gemma_4"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ssh-bin", default=DEFAULT_SSH_BIN)
    parser.add_argument("--scp-bin", default=DEFAULT_SCP_BIN)
    parser.add_argument("--remote-host", default=DEFAULT_REMOTE_HOST)
    parser.add_argument("--poll-seconds", type=int, default=120)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--status-json", default=str(ROOT / "v11_live_status.json"))
    parser.add_argument("--status-md", default=str(ROOT / "v11_live_status.md"))
    parser.add_argument("--watch-log", default=str(ROOT / "v11_watch.log"))
    parser.add_argument("--state-file", default=str(ROOT / "v11_watch_state.json"))
    parser.add_argument("--finalizer", default=str(ROOT / "finalize_v11_results.py"))
    return parser.parse_args()


def run_command(argv, label):
    completed = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        raise RuntimeError(f"{label} failed with code {completed.returncode}: {completed.stderr or completed.stdout}")
    return completed.stdout


def append_log(path, message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def fetch_remote_state(args):
    remote_cmd = r'''python3 - <<'PY'
import json
import os
import re
import subprocess


def list_processes():
    ps = subprocess.run(
        ["ps", "-eo", "pid=,ppid=,args="],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=True,
    )
    processes = []
    for raw_line in ps.stdout.splitlines():
        parts = raw_line.strip().split(None, 2)
        if len(parts) < 3:
            continue
        processes.append({"pid": int(parts[0]), "ppid": int(parts[1]), "command": parts[2]})
    return processes


def descendants(processes, root_pid):
    children_by_parent = {}
    for process in processes:
        children_by_parent.setdefault(process["ppid"], []).append(process)

    found = []
    stack = [root_pid]
    while stack:
        current = stack.pop()
        for child in children_by_parent.get(current, []):
            found.append(child)
            stack.append(child["pid"])
    return found

train_log = "/home3/indiamart/gemma_4/v11_train.log"
eval_log = "/home3/indiamart/gemma_4/v11_eval.log"
summary_path = "/home3/indiamart/gemma_4/v11_eval_summary.json"
results_path = "/home3/indiamart/gemma_4/v11_priority_results.jsonl"

processes = list_processes()
pipeline_matches = [
    process for process in processes
    if process["command"] == "bash /home/indiamart/gemma_4/run_v11_train_and_eval.sh"
]

pipeline_descendants = []
for pipeline in pipeline_matches:
    pipeline_descendants.extend(descendants(processes, pipeline["pid"]))

train_matches = [
    process for process in pipeline_descendants
    if "/home/indiamart/gemma_4/finetune_gemma4_v11_priority_balanced.py" in process["command"]
]
eval_matches = [
    process for process in pipeline_descendants
    if "/home/indiamart/gemma_4/eval_priority_adapter.py" in process["command"] and "--label v11" in process["command"]
]

state = {
    "train_log_exists": os.path.exists(train_log),
    "eval_log_exists": os.path.exists(eval_log),
    "summary_exists": os.path.exists(summary_path),
    "results_exists": os.path.exists(results_path),
    "training_running": bool(train_matches),
    "pipeline_running": bool(pipeline_matches),
    "eval_running": bool(eval_matches),
}

if state["train_log_exists"]:
    text = open(train_log, encoding="utf-8", errors="ignore").read()
    matches = re.findall(r"(\d+)%\|[^\n\r]*?(\d+)/(\d+)", text)
    if matches:
        progress_pct, current_step, total_steps = matches[-1]
        state["progress_percent"] = int(progress_pct)
        state["current_step"] = int(current_step)
        state["total_steps"] = int(total_steps)
    state["train_log_size"] = os.path.getsize(train_log)

if state["eval_log_exists"]:
    state["eval_log_size"] = os.path.getsize(eval_log)

if state["summary_exists"]:
    state["summary_mtime"] = int(os.path.getmtime(summary_path))

if state["results_exists"]:
    state["results_mtime"] = int(os.path.getmtime(results_path))
    with open(results_path, encoding="utf-8", errors="ignore") as handle:
        state["results_line_count"] = sum(1 for _ in handle)

gpu = subprocess.run(
    ["nvidia-smi", "--query-gpu=index,name,memory.used,utilization.gpu", "--format=csv,noheader"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="ignore",
)
state["gpu"] = gpu.stdout.strip().splitlines()

print(json.dumps(state))
PY'''
    output = run_command([args.ssh_bin, args.remote_host, remote_cmd], "fetch remote state")
    return json.loads(output)


def write_status_files(status_json_path, status_md_path, state):
    with open(status_json_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)

    lines = [
        "# V11 Live Status",
        "",
        f"- observed_at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- pipeline_running: {state.get('pipeline_running')}",
        f"- training_running: {state.get('training_running')}",
        f"- eval_running: {state.get('eval_running')}",
        f"- summary_exists: {state.get('summary_exists')}",
    ]
    if state.get("current_step") is not None and state.get("total_steps"):
        lines.append(f"- progress: {state.get('current_step')}/{state.get('total_steps')} ({state.get('progress_percent', 0)}%)")
    if state.get("results_line_count") is not None:
        lines.append(f"- eval_results_written: {state.get('results_line_count')}")
    if state.get("gpu"):
        lines.append("- gpu:")
        for item in state["gpu"]:
            lines.append(f"  - {item}")

    with open(status_md_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def load_watch_state(path):
    state_path = Path(path)
    if not state_path.exists():
        return {"finalized": False}
    with open(state_path, encoding="utf-8") as handle:
        return json.load(handle)


def save_watch_state(path, state):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def copy_remote_file(args, remote_name, local_name):
    remote_path = f"{args.remote_host}:{REMOTE_RESULT_DIR}/{remote_name}"
    local_path = str(ROOT / local_name)
    run_command([args.scp_bin, remote_path, local_path], f"scp {remote_name}")
    return local_path


def maybe_finalize(args, remote_state, watch_state):
    if not remote_state.get("summary_exists"):
        return False

    summary_mtime = remote_state.get("summary_mtime")
    if watch_state.get("finalized") and watch_state.get("summary_mtime") == summary_mtime:
        return True

    summary_path = copy_remote_file(args, "v11_eval_summary.json", "v11_eval_summary.json")
    if remote_state.get("results_exists"):
        copy_remote_file(args, "v11_priority_results.jsonl", "v11_priority_results.jsonl")
    if remote_state.get("eval_log_exists"):
        copy_remote_file(args, "v11_eval.log", "v11_eval.log")
    if remote_state.get("train_log_exists"):
        copy_remote_file(args, "v11_train.log", "v11_train.log")

    run_command([
        sys.executable,
        args.finalizer,
        "--root",
        str(ROOT),
        "--v11-summary",
        summary_path,
        "--v11-results",
        str(ROOT / "v11_priority_results.jsonl"),
    ], "finalize v11")

    watch_state["finalized"] = True
    watch_state["summary_mtime"] = summary_mtime
    return True


def main():
    args = parse_args()
    watch_state = load_watch_state(args.state_file)

    while True:
        try:
            remote_state = fetch_remote_state(args)
            write_status_files(args.status_json, args.status_md, remote_state)
            finalized = maybe_finalize(args, remote_state, watch_state)
            save_watch_state(args.state_file, watch_state)
            append_log(
                args.watch_log,
                " ".join(
                    [
                        f"progress={remote_state.get('current_step')}/{remote_state.get('total_steps')}",
                        f"eval_running={remote_state.get('eval_running')}",
                        f"results_lines={remote_state.get('results_line_count')}",
                        f"summary_exists={remote_state.get('summary_exists')}",
                        f"finalized={finalized}",
                    ]
                ),
            )
        except Exception as exc:
            append_log(args.watch_log, f"error={exc}")

        if args.once:
            break

        if watch_state.get("finalized"):
            append_log(args.watch_log, "finalized=true; stopping watcher")
            break

        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()