"""Auto-pull v3 inference results from server when ready, run final 3-way compare."""
import os, sys, time, subprocess, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSH = r'C:\Program Files\Git\usr\bin\ssh.exe'
SCP = r'C:\Program Files\Git\usr\bin\scp.exe'
HOST = "amit_87483@34.93.58.248"
REMOTE_CSV = "/home3/indiamart/gemma_4/agent/v3_results.csv"
REMOTE_JSONL = "/home3/indiamart/gemma_4/agent/v3_results.jsonl"
REMOTE_V2_CLEAN = "/home3/indiamart/gemma_4/agent/v2_clean_results.csv"
LOCAL_V3_CSV = os.path.join(ROOT, "bee", "v3_results.csv")
LOCAL_V3_JSONL = os.path.join(ROOT, "bee", "v3_results.jsonl")
LOCAL_V2C_CSV = os.path.join(ROOT, "bee", "v2_clean_results.csv")

def remote(cmd):
    p = subprocess.run([SSH, "-o", "ConnectTimeout=60", HOST, cmd],
                       capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")

def fetch(remote_path, local_path):
    p = subprocess.run([SCP, "-o", "ConnectTimeout=120", f"{HOST}:{remote_path}", local_path],
                       capture_output=True, text=True)
    return p.returncode == 0

def remote_lines(path):
    rc, out = remote(f"wc -l {path} 2>/dev/null || echo 0")
    try: return int(out.strip().split()[0])
    except: return 0

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "v3"  # 'v3' or 'v2_clean'
    if target == "v2_clean":
        remote_csv, local_csv, label = REMOTE_V2_CLEAN, LOCAL_V2C_CSV, "v2_clean"
        report = os.path.join(ROOT, "bee", "compare_v2_clean_vs_qmeans_vs_gold.txt")
    else:
        remote_csv, local_csv, label = REMOTE_CSV, LOCAL_V3_CSV, "v3"
        report = os.path.join(ROOT, "bee", "compare_v3_vs_qmeans_vs_gold.txt")

    print(f"Target: {label} ({remote_csv})")
    while True:
        n = remote_lines(remote_csv)
        print(f"  remote rows: {n}")
        if n >= 1000:
            break
        time.sleep(60)

    print("Fetching ...")
    if not fetch(remote_csv, local_csv):
        print("ERROR fetching csv"); sys.exit(1)
    if target == "v3":
        fetch(REMOTE_JSONL, LOCAL_V3_JSONL)

    print("Running comparison ...")
    cmd = [
        sys.executable, os.path.join(ROOT, "bee", "compare.py"),
        "--gemma", local_csv,
        "--qmeans", os.path.join(ROOT, "bee", "qmeans_results.jsonl"),
        "--gold", os.path.join(ROOT, "bee", "gold_claude_compare.jsonl"),
        "--report", report,
        "--qmeans-alias",
    ]
    subprocess.run(cmd, check=True)
    print(f"\nReport -> {report}")

if __name__ == "__main__":
    main()
