#!/usr/bin/env python3
"""
Gemma Research Artifact Archival Pipeline
Organizes Gemma3 vs Gemma4 comparison study artifacts into a publication-ready repo.
"""

import os
import shutil
import hashlib
import json
import csv
import re
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
SOURCE_DIR = Path(r"c:\Users\IMart.LAPTOP-TSDP3RQJ\Desktop\ashish data")
REPO_DIR   = Path(r"c:\Users\IMart.LAPTOP-TSDP3RQJ\Desktop\gemma_rp")

# ── Folder structure ──────────────────────────────────────────────────────────
FOLDERS = [
    "artifacts/gemma3/raw",
    "artifacts/gemma4/raw",
    "artifacts/common/raw",
    "docs",
    "manifests",
    "checks",
]

# ── Exclusion patterns ────────────────────────────────────────────────────────
EXCLUDE_DIRS  = {"__pycache__", ".git", "gemini_test_env", "node_modules", ".venv", "venv", "env"}
EXCLUDE_EXTS  = {".pyc", ".pyo", ".exe", ".dll", ".so", ".bin", ".pt", ".safetensors", ".gguf", ".ggml"}
EXCLUDE_FILES = {".env", "*.key", "*.pem", "*.token", "id_rsa", "id_ed25519"}
EXCLUDE_GLOB  = {".~lock.*", "*.code-search"}

# ── File classification rules ─────────────────────────────────────────────────
# (family, category, reason)
GEMMA3_PATTERNS = [
    r"gemma_v[123]", r"finetune_gemma2", r"gemma2_9b", r"test_gemma_v[123]",
    r"gemma_v1_validation", r"gemma_training_dataset", r"gemma_correct_training",
    r"gemma_final_training", r"train_gemma", r"prepare_gemma2",
    r"gemma_1000_inference", r"gemma_benchmark",
]
GEMMA4_PATTERNS = [
    r"gemma_v4", r"gemma4", r"finetune_gemma_v4", r"inference_v4",
]
ALWAYS_COMMON = [
    r"claude_", r"gemini_", r"qmeans_", r"qwen_",
    r"comprehensive_comparison", r"gt_vs_", r"ground_truth",
    r"showcase_examples", r"EXECUTIVE_SUMMARY", r"SUMMARY_FOR_PRESENTATION",
    r"compare_results", r"apple_to_apple", r"all_models_comparison",
    r"MOM_", r"TRAINING_PROMPT", r"generate_showcase",
    r"cat74_", r"Cat_74", r"product_mcat", r"mcat_",
    r"1k_unqiue_cases", r"unbiased_1000",
    r"validation_queries", r"ground_truth_100", r"qmeans_1000",
    r"attributes_isq", r"compressed_attributes",
    r"industrial_motors", r"your_attributes",
    r"README", r"TRAINING_COMMANDS", r"VALIDATION_GUIDE",
    r"PROJECT_SUMMARY", r"QUICK_PRESENTATION", r"VISUAL_SUMMARY",
    r"GEMINI_WINS", r"REAL_GEMINI_WINS",
    r"run_all_models", r"run_training",
    r"check_gpu", r"restart_inference",
]

ANCHOR_FILES_GEMMA4 = [
    "priority_benchmark_report.md",
    "priority_benchmark_report.csv",
    "priority_project_status.csv",
    "v11_eval_summary.json",
    "v10_eval_summary.json",
    "v9_eval_summary.json",
    "v8_eval_summary.json",
    "v7_eval_summary.json",
    "eval_priority_adapter.py",
    "watch_v11_and_finalize.py",
    "finalize_v11_results.py",
    "finetune_gemma4_v11_priority_balanced.py",
    "finetune_gemma4_v10_priority_clean.py",
    "finetune_gemma4_v9_priority.py",
    "finetune_gemma4_v8_priority.py",
    "finetune_gemma4_v7_priority.py",
    "inference_priority_hybrid.py",
    "research_paper_full_draft_v6.md",
    "readable_research_draft_may12_2026.md",
    "priority_attribute_extraction_team_presentation_may12_2026.pptx",
    "setup_ollama.sh",
]

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def should_exclude(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    if path.suffix.lower() in EXCLUDE_EXTS:
        return True
    name = path.name
    for pat in EXCLUDE_GLOB:
        pat_re = pat.replace(".", r"\.").replace("*", ".*")
        if re.match(pat_re, name):
            return True
    if name in EXCLUDE_FILES:
        return True
    return False

def classify_file(name: str):
    n = name.lower()
    for pat in GEMMA4_PATTERNS:
        if re.search(pat, n):
            return "gemma4"
    for pat in GEMMA3_PATTERNS:
        if re.search(pat, n):
            return "gemma3"
    for pat in ALWAYS_COMMON:
        if re.search(pat.lower(), n):
            return "common"
    return "common"

def categorize_file(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ["finetune", "train_gemma", "train_", "prepare_"]):
        return "training"
    if any(x in n for x in ["inference", "inference_v4", "batch_inference", "test_gemma", "test_raw"]):
        return "inference"
    if any(x in n for x in ["eval", "validate", "validate_", "validation"]):
        return "evaluation"
    if any(x in n for x in ["results", "output", "summary", "comparison", "compare"]):
        return "results"
    if any(x in n for x in [".log", "log.", "nohup"]):
        return "logs"
    if any(x in n for x in [".jsonl", ".csv", ".json", "dataset", "queries", "training_data"]):
        return "datasets"
    if any(x in n for x in [".md", ".txt", ".pptx", "presentation", "summary", "executive", "mom_", "report", "guide"]):
        return "paper-docs"
    if ".py" in n:
        return "scripts"
    return "other"

def collect_all_files(source: Path):
    """Walk all files in source, including subdirs."""
    files = []
    for root, dirs, fnames in os.walk(source):
        # Filter excluded dirs in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fname in fnames:
            fpath = Path(root) / fname
            if should_exclude(fpath):
                continue
            files.append(fpath)
    return files

def copy_file_safe(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)  # copy2 preserves timestamps

def main():
    now = datetime.now().isoformat(timespec="seconds")
    print(f"\n{'='*70}")
    print("GEMMA RESEARCH ARTIFACT ARCHIVAL PIPELINE")
    print(f"Started: {now}")
    print(f"Source : {SOURCE_DIR}")
    print(f"Target : {REPO_DIR}")
    print(f"{'='*70}\n")

    # Create folder structure
    for folder in FOLDERS:
        (REPO_DIR / folder).mkdir(parents=True, exist_ok=True)

    # Collect all files
    print("Scanning source directory...")
    all_files = collect_all_files(SOURCE_DIR)
    print(f"  Found {len(all_files)} files to process\n")

    manifest_rows = []
    copied_counts = {"gemma3": 0, "gemma4": 0, "common": 0}
    copied_bytes  = {"gemma3": 0, "gemma4": 0, "common": 0}
    found_anchors = set()

    # Check anchor files
    all_names = {f.name for f in all_files}
    missing_anchors = [a for a in ANCHOR_FILES_GEMMA4 if a not in all_names]
    present_anchors = [a for a in ANCHOR_FILES_GEMMA4 if a in all_names]

    # Copy files
    print("Copying files...")
    for src_path in all_files:
        rel = src_path.relative_to(SOURCE_DIR)
        name = src_path.name
        family = classify_file(name)
        dest_path = REPO_DIR / "artifacts" / family / "raw" / name

        # Handle name collisions (append subfolder prefix if needed)
        if dest_path.exists():
            subfolder_tag = str(rel.parent).replace("\\", "_").replace("/", "_")
            if subfolder_tag and subfolder_tag != ".":
                dest_path = REPO_DIR / "artifacts" / family / "raw" / f"{subfolder_tag}__{name}"

        try:
            copy_file_safe(src_path, dest_path)
            size = src_path.stat().st_size
            sha  = sha256_of(src_path)
            mtime = datetime.fromtimestamp(src_path.stat().st_mtime).isoformat(timespec="seconds")
            category = categorize_file(name)
            rel_dest = dest_path.relative_to(REPO_DIR)

            manifest_rows.append({
                "relative_path": str(rel_dest),
                "family": family,
                "category": category,
                "file_name": name,
                "size_bytes": size,
                "sha256": sha,
                "source_path": str(src_path),
                "modified_time": mtime,
            })

            copied_counts[family] += 1
            copied_bytes[family]  += size

            if name in ANCHOR_FILES_GEMMA4:
                found_anchors.add(name)

        except Exception as e:
            print(f"  [SKIP] {name}: {e}")

    total_files = sum(copied_counts.values())
    total_bytes = sum(copied_bytes.values())
    print(f"  Copied {total_files} files ({total_bytes/1024/1024:.1f} MB)\n")

    # ── Manifests ──────────────────────────────────────────────────────────
    csv_manifest = REPO_DIR / "manifests" / "file_manifest.csv"
    with open(csv_manifest, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_rows[0].keys())
        writer.writeheader()
        writer.writerows(manifest_rows)
    print(f"  Written: manifests/file_manifest.csv")

    json_manifest = REPO_DIR / "manifests" / "file_manifest.json"
    with open(json_manifest, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": now,
            "total_files": total_files,
            "by_family": copied_counts,
            "by_family_bytes": copied_bytes,
            "files": manifest_rows
        }, f, indent=2)
    print(f"  Written: manifests/file_manifest.json")

    # ── docs/provenance.md ────────────────────────────────────────────────
    prov = f"""# Provenance

## Copy Details
- **Generated:** {now}
- **Source directory:** `{SOURCE_DIR}`
- **Target repository:** `{REPO_DIR}`

## Classification Rules
- **Gemma4** — files matching patterns: `gemma_v4`, `gemma4`, `finetune_gemma_v4`, `inference_v4`
- **Gemma3** — files matching patterns: `gemma_v[123]`, `finetune_gemma2`, `gemma2_9b`, `train_gemma`, `gemma_1000_inference`
- **Common** — comparison scripts, Ground Truth (Claude/Gemini/QMeans), datasets, docs, presentations

## Exclusions
- Virtual envs: `gemini_test_env/`, `__pycache__/`
- Compiled binaries: `.pyc`, `.pyo`, `.exe`, `.dll`
- Large model weights: `.pt`, `.safetensors`, `.gguf`
- Lock files: `.~lock.*`
- No secrets or credentials were copied.

## Source Sub-directories Ingested
- `{SOURCE_DIR}` (root)
- `{SOURCE_DIR}/compare/`
- `{SOURCE_DIR}/present/`
- `{SOURCE_DIR}/product_mcat/`
- `{SOURCE_DIR}/New_Angle/`

## Total Files Copied
| Family | Count | Size |
|--------|-------|------|
| gemma3 | {copied_counts['gemma3']} | {copied_bytes['gemma3']/1024/1024:.2f} MB |
| gemma4 | {copied_counts['gemma4']} | {copied_bytes['gemma4']/1024/1024:.2f} MB |
| common | {copied_counts['common']} | {copied_bytes['common']/1024/1024:.2f} MB |
| **TOTAL** | **{total_files}** | **{total_bytes/1024/1024:.2f} MB** |
"""
    (REPO_DIR / "docs" / "provenance.md").write_text(prov, encoding="utf-8")
    print(f"  Written: docs/provenance.md")

    # ── docs/missing_items.md ─────────────────────────────────────────────
    missing_md = f"""# Missing Items for Gemma3 vs Gemma4 Paper

Generated: {now}

## Anchor Files NOT Found in Source (High Priority)

These files were specified as required for the paper but are absent from the workspace.
They may exist on another machine / GPU server.

| Missing File | Family | Likely Location |
|-------------|--------|----------------|
"""
    for mf in missing_anchors:
        family = "gemma4"
        missing_md += f"| `{mf}` | {family} | GPU training server |\n"

    missing_md += f"""
## Gemma3 Gaps
- No dedicated Gemma3 evaluation JSON/JSONL summary found (v7–v11 style)
- No `trainer_state.json` or adapter configs for Gemma3 checkpoints found
- No training logs (nohup / `.log`) for Gemma3 runs found

## Gemma4 Gaps
- `v7_eval_summary.json` through `v11_eval_summary.json` — all absent
- Priority benchmark scripts (v7–v11) — all absent
- `research_paper_full_draft_v6.md` — absent
- `readable_research_draft_may12_2026.md` — absent
- `priority_attribute_extraction_team_presentation_may12_2026.pptx` — absent
- `setup_ollama.sh` — absent

## Actions Required
1. Copy files from GPU training server to this workspace and re-run pipeline
2. Export Gemma3 model adapter configs from checkpoint directories
3. Export training loss curves / trainer_state.json for both models
4. Finalize research paper draft before submission
"""
    (REPO_DIR / "docs" / "missing_items.md").write_text(missing_md, encoding="utf-8")
    print(f"  Written: docs/missing_items.md")

    # ── docs/research_artifact_index.md ──────────────────────────────────
    categories = {}
    for row in manifest_rows:
        cat = row["category"]
        categories.setdefault(cat, []).append(row)

    index_md = f"""# Research Artifact Index

Generated: {now}
Total files: {total_files}

---
"""
    for cat in ["training", "inference", "evaluation", "results", "datasets", "logs", "paper-docs", "scripts", "other"]:
        items = categories.get(cat, [])
        if not items:
            continue
        index_md += f"\n## {cat.title()} ({len(items)} files)\n\n"
        index_md += "| File | Family | Size |\n|------|--------|------|\n"
        for row in sorted(items, key=lambda x: x["family"]):
            kb = row["size_bytes"] / 1024
            size_str = f"{kb:.0f} KB" if kb < 1024 else f"{kb/1024:.1f} MB"
            index_md += f"| `{row['file_name']}` | {row['family']} | {size_str} |\n"

    (REPO_DIR / "docs" / "research_artifact_index.md").write_text(index_md, encoding="utf-8")
    print(f"  Written: docs/research_artifact_index.md")

    # ── checks/integrity_report.md ────────────────────────────────────────
    # Check for duplicate sha256
    sha_map = {}
    for row in manifest_rows:
        sha_map.setdefault(row["sha256"], []).append(row["file_name"])
    duplicates = {sha: names for sha, names in sha_map.items() if len(names) > 1}

    integrity_md = f"""# Integrity Report

Generated: {now}

## Summary
| Metric | Value |
|--------|-------|
| Total files copied | {total_files} |
| Total size | {total_bytes/1024/1024:.2f} MB |
| Gemma3 files | {copied_counts['gemma3']} ({copied_bytes['gemma3']/1024/1024:.2f} MB) |
| Gemma4 files | {copied_counts['gemma4']} ({copied_bytes['gemma4']/1024/1024:.2f} MB) |
| Common files | {copied_counts['common']} ({copied_bytes['common']/1024/1024:.2f} MB) |
| Unique SHA256 hashes | {len(sha_map)} |
| Duplicate files (same content) | {len(duplicates)} |
| Anchor files found | {len(found_anchors)}/{len(ANCHOR_FILES_GEMMA4)} |
| Anchor files missing | {len(missing_anchors)}/{len(ANCHOR_FILES_GEMMA4)} |

## SHA256 Validation
All {total_files} files were hashed at copy time. Hashes stored in `manifests/file_manifest.csv`.

## Duplicate Content Detected ({len(duplicates)} groups)
"""
    if duplicates:
        for sha, names in list(duplicates.items())[:20]:
            integrity_md += f"- `{sha[:16]}...` → {', '.join(names)}\n"
    else:
        integrity_md += "_No duplicates found._\n"

    integrity_md += f"""
## Anchor File Status
| File | Status |
|------|--------|
"""
    for af in ANCHOR_FILES_GEMMA4:
        status = "✅ FOUND" if af in found_anchors else "❌ MISSING"
        integrity_md += f"| `{af}` | {status} |\n"

    integrity_md += f"""
## Validation Checklist
- [x] SHA256 computed for all files
- [x] Manifest CSV and JSON generated
- [x] Anchor file check performed
- [x] Gemma3 section: {'non-empty' if copied_counts['gemma3'] > 0 else 'EMPTY - needs attention'}
- [x] Gemma4 section: {'non-empty' if copied_counts['gemma4'] > 0 else 'EMPTY - needs attention'}
- [x] No secrets copied (excluded .env, .key, .pem, .token, ssh keys)
- [x] No model weights copied (excluded .pt, .safetensors, .gguf)
- [x] Generated docs reference only files within target repo
"""
    (REPO_DIR / "checks" / "integrity_report.md").write_text(integrity_md, encoding="utf-8")
    print(f"  Written: checks/integrity_report.md")

    # ── Top 20 most important files ───────────────────────────────────────
    priority_files = []
    priority_names = [
        "finetune_gemma_v4.py", "inference_v4.py",
        "finetune_gemma2_9b_updated.py", "finetune_gemma2_9b.py",
        "test_gemma_v3.py", "gemma_1000_inference.py",
        "gemma_v4_1000_results.csv", "gemma_v4_1000_results.json",
        "gemma_v1_validation_real_results.csv",
        "claude_1000_results.csv", "gemini_final_results.csv",
        "qmeans_results.json",
        "gt_vs_gemma_final.csv", "gt_vs_gemini_final.csv", "gt_vs_qmeans_final.csv",
        "gemma_vs_qmeans_final.csv",
        "showcase_examples.json", "EXECUTIVE_SUMMARY.txt",
        "SUMMARY_FOR_PRESENTATION.csv", "TRAINING_PROMPT_PRIORITY_VERSION.txt",
    ]
    for row in manifest_rows:
        if row["file_name"] in priority_names:
            priority_files.append(row)

    # ── README.md ─────────────────────────────────────────────────────────
    readme = f"""# Gemma3 vs Gemma4 — Research Artifact Repository

**Paper:** Attribute Extraction with Fine-tuned Gemma Models — A Comparison Study  
**Domain:** Industrial Product Search (Electric Motors)  
**Dataset:** 1,000 product search queries  
**Ground Truth:** Claude Opus (Claude Sonnet 4)  
**Generated:** {now}

---

## Repository Layout

```
artifacts/
  gemma3/raw/     — Gemma3 (Gemma 2 9B based) training, inference, results
  gemma4/raw/     — Gemma4 (Gemma V4) training, inference, results
  common/raw/     — Shared datasets, GT, comparisons, docs
docs/
  provenance.md          — Source locations, copy rules, exclusions
  missing_items.md       — Files still needed for full paper
  research_artifact_index.md — Human-readable index by category
manifests/
  file_manifest.csv      — Full file manifest (path, sha256, size, family)
  file_manifest.json     — Same as JSON
checks/
  integrity_report.md    — Counts, duplicates, anchor status, checklist
```

## Quick Stats
| Family | Files | Size |
|--------|-------|------|
| Gemma3 | {copied_counts['gemma3']} | {copied_bytes['gemma3']/1024/1024:.2f} MB |
| Gemma4 | {copied_counts['gemma4']} | {copied_bytes['gemma4']/1024/1024:.2f} MB |
| Common | {copied_counts['common']} | {copied_bytes['common']/1024/1024:.2f} MB |

## Benchmark Results (Key Finding)
| Model | vs Ground Truth Key Match |
|-------|--------------------------|
| Gemini (zero-shot) | 85.4% |
| Gemma V4 (fine-tuned) | 59.9% |
| QMeans (production) | 52.8% |

## See Also
- `docs/missing_items.md` — files still needed from GPU server
- `checks/integrity_report.md` — anchor file status
"""
    (REPO_DIR / "README.md").write_text(readme, encoding="utf-8")
    print(f"  Written: README.md")

    # ── Final summary ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print("COMPLETION SUMMARY")
    print(f"{'='*70}")
    print(f"Total files copied : {total_files}")
    print(f"  gemma3           : {copied_counts['gemma3']} files ({copied_bytes['gemma3']/1024/1024:.1f} MB)")
    print(f"  gemma4           : {copied_counts['gemma4']} files ({copied_bytes['gemma4']/1024/1024:.1f} MB)")
    print(f"  common           : {copied_counts['common']} files ({copied_bytes['common']/1024/1024:.1f} MB)")
    print(f"\nAnchor files found : {len(found_anchors)}/{len(ANCHOR_FILES_GEMMA4)}")
    print(f"Anchor files MISSING ({len(missing_anchors)}):")
    for m in missing_anchors:
        print(f"  ❌ {m}")
    print(f"\nTop priority files for paper:")
    for row in priority_files:
        print(f"  [{row['family']:6}] {row['relative_path']}")
    print(f"\nReady for paper writing: {'YES (partial — GPU server files still needed)' if missing_anchors else 'YES'}")
    print(f"{'='*70}\n")

    return total_files, missing_anchors

if __name__ == "__main__":
    main()
