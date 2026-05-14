"""
Split hybrid priority inference.

This script works around the remote qmeans timeout by:
1. running V7 inference on the remote GPU box over SSH
2. querying qmeans locally
3. merging the two into the final priority-ordered output

Use this when the best hybrid benchmark result is desired but the remote server
cannot reach the qmeans endpoint directly.
"""

import argparse
import json
import os
import subprocess
import tempfile
import uuid

from inference_priority_hybrid import (
    DEFAULT_QMEANS_SOURCE,
    DEFAULT_QMEANS_URL,
    flat_to_nested,
    flatten_priority_output,
    merge_priority_outputs,
    parse_json_loose,
    query_qmeans,
)


DEFAULT_SSH_BIN = r"C:\Program Files\Git\usr\bin\ssh.exe"
DEFAULT_SCP_BIN = r"C:\Program Files\Git\usr\bin\scp.exe"
DEFAULT_REMOTE_HOST = "amit_87483@34.93.58.248"
DEFAULT_REMOTE_SCRIPT = "/home/indiamart/gemma_4/inference_v7.py"
DEFAULT_REMOTE_PYTHON = "/home3/indiamart/gemma_4/gemma4_env/bin/python"
DEFAULT_OUT = r"c:\Users\Imart\CopilotHacksAndPersonal\IM_Repos\finetuning_gemma_4\split_hybrid_priority_results.jsonl"

SAMPLES = [
    "siemens 45 hp 3 phase 1440 rpm motor",
    "crompton greaves 5 kw single phase 50hz induction motor",
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--queries", type=str, default=None, help="JSONL with one {'query': ...} per line, or plain text one query per line")
    parser.add_argument("--out", type=str, default=DEFAULT_OUT)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    parser.add_argument("--qmeans-url", type=str, default=DEFAULT_QMEANS_URL)
    parser.add_argument("--qmeans-source", type=str, default=DEFAULT_QMEANS_SOURCE)
    parser.add_argument("--ssh-bin", type=str, default=DEFAULT_SSH_BIN)
    parser.add_argument("--scp-bin", type=str, default=DEFAULT_SCP_BIN)
    parser.add_argument("--remote-host", type=str, default=DEFAULT_REMOTE_HOST)
    parser.add_argument("--remote-script", type=str, default=DEFAULT_REMOTE_SCRIPT)
    parser.add_argument("--remote-python", type=str, default=DEFAULT_REMOTE_PYTHON)
    parser.add_argument("--keep-remote-files", action="store_true")
    return parser.parse_args()


def collect_queries(args):
    if args.query:
        return [args.query]
    if args.queries:
        queries = []
        with open(args.queries, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    query = row.get("query") or row.get("instruction") or row.get("text")
                    if query:
                        queries.append(query)
                except json.JSONDecodeError:
                    queries.append(line)
        return queries
    return list(SAMPLES)


def run_command(argv, label):
    completed = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        raise RuntimeError(f"{label} failed with code {completed.returncode}: {completed.stderr or completed.stdout}")
    return completed.stdout


def write_queries_file(path, queries):
    with open(path, "w", encoding="utf-8") as handle:
        for query in queries:
            handle.write(query + "\n")


def run_remote_v7(args, queries):
    token = uuid.uuid4().hex
    remote_in = f"/tmp/split_hybrid_queries_{token}.txt"
    remote_out = f"/tmp/split_hybrid_results_{token}.jsonl"

    with tempfile.TemporaryDirectory() as temp_dir:
        local_in = os.path.join(temp_dir, "queries.txt")
        local_out = os.path.join(temp_dir, "remote_results.jsonl")
        write_queries_file(local_in, queries)

        run_command([
            args.scp_bin,
            local_in,
            f"{args.remote_host}:{remote_in}",
        ], "scp upload")

        remote_cmd = (
            f"{args.remote_python} {args.remote_script} "
            f"--queries {remote_in} --out {remote_out} --max_new_tokens {args.max_new_tokens}"
        )
        run_command([
            args.ssh_bin,
            args.remote_host,
            remote_cmd,
        ], "remote v7 inference")

        run_command([
            args.scp_bin,
            f"{args.remote_host}:{remote_out}",
            local_out,
        ], "scp download")

        if not args.keep_remote_files:
            cleanup_cmd = f"rm -f {remote_in} {remote_out}"
            run_command([
                args.ssh_bin,
                args.remote_host,
                cleanup_cmd,
            ], "remote cleanup")

        rows = []
        with open(local_out, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows


def merge_rows(remote_rows, args):
    records = []
    for row in remote_rows:
        query = row.get("query", "")
        parsed = row.get("parsed")
        if not isinstance(parsed, dict):
            parsed = parse_json_loose(row.get("raw", "") or "")
        v7_flat = flatten_priority_output(parsed)
        qmeans_result = query_qmeans(query, args.qmeans_url, args.qmeans_source)
        hybrid_flat = merge_priority_outputs(v7_flat, qmeans_result["attrs"])
        record = {
            "query": query,
            "result": flat_to_nested(hybrid_flat),
            "hybrid_flat": hybrid_flat,
            "v7_flat": v7_flat,
            "qmeans_flat": qmeans_result["attrs"],
            "v7_raw": row.get("raw"),
            "v7_parsed": parsed,
            "v7_secs": row.get("secs"),
            "qmeans_secs": qmeans_result["secs"],
            "qmeans_ok": qmeans_result["ok"],
        }
        if not qmeans_result["ok"]:
            record["qmeans_error"] = qmeans_result.get("error")
        records.append(record)
    return records


def main():
    args = parse_args()
    queries = collect_queries(args)

    print(f"Running remote V7 inference for {len(queries)} queries ...")
    remote_rows = run_remote_v7(args, queries)

    print("Merging with local qmeans results ...")
    records = merge_rows(remote_rows, args)

    with open(args.out, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    for index, record in enumerate(records, start=1):
        print(f"[{index}/{len(records)}] {record['query']}")
        print(json.dumps(record["result"], ensure_ascii=False, indent=2))
        if not record["qmeans_ok"]:
            print(f"qmeans fallback unavailable locally: {record.get('qmeans_error')}")
        print()

    print(f"Done. Results -> {args.out}")


if __name__ == "__main__":
    main()