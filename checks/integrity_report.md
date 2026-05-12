# Integrity Report

Generated: 2026-05-12T14:08:46

## Summary
| Metric | Value |
|--------|-------|
| Total files copied | 223 |
| Total size | 96.97 MB |
| Gemma3 files | 15 (1.57 MB) |
| Gemma4 files | 4 (3.61 MB) |
| Common files | 204 (91.79 MB) |
| Unique SHA256 hashes | 219 |
| Duplicate files (same content) | 2 |
| Anchor files found | 0/21 |
| Anchor files missing | 21/21 |

## SHA256 Validation
All 223 files were hashed at copy time. Hashes stored in `manifests/file_manifest.csv`.

## Duplicate Content Detected (2 groups)
- `c8dc80ae845fb667...` → unique_key_val_96_cat.csv, your_attributes.csv
- `e3b0c44298fc1c14...` → gemini_error.log, gemini_output.log, gemini_run.log, finetune_script.py

## Anchor File Status
| File | Status |
|------|--------|
| `priority_benchmark_report.md` | ❌ MISSING |
| `priority_benchmark_report.csv` | ❌ MISSING |
| `priority_project_status.csv` | ❌ MISSING |
| `v11_eval_summary.json` | ❌ MISSING |
| `v10_eval_summary.json` | ❌ MISSING |
| `v9_eval_summary.json` | ❌ MISSING |
| `v8_eval_summary.json` | ❌ MISSING |
| `v7_eval_summary.json` | ❌ MISSING |
| `eval_priority_adapter.py` | ❌ MISSING |
| `watch_v11_and_finalize.py` | ❌ MISSING |
| `finalize_v11_results.py` | ❌ MISSING |
| `finetune_gemma4_v11_priority_balanced.py` | ❌ MISSING |
| `finetune_gemma4_v10_priority_clean.py` | ❌ MISSING |
| `finetune_gemma4_v9_priority.py` | ❌ MISSING |
| `finetune_gemma4_v8_priority.py` | ❌ MISSING |
| `finetune_gemma4_v7_priority.py` | ❌ MISSING |
| `inference_priority_hybrid.py` | ❌ MISSING |
| `research_paper_full_draft_v6.md` | ❌ MISSING |
| `readable_research_draft_may12_2026.md` | ❌ MISSING |
| `priority_attribute_extraction_team_presentation_may12_2026.pptx` | ❌ MISSING |
| `setup_ollama.sh` | ❌ MISSING |

## Validation Checklist
- [x] SHA256 computed for all files
- [x] Manifest CSV and JSON generated
- [x] Anchor file check performed
- [x] Gemma3 section: non-empty
- [x] Gemma4 section: non-empty
- [x] No secrets copied (excluded .env, .key, .pem, .token, ssh keys)
- [x] No model weights copied (excluded .pt, .safetensors, .gguf)
- [x] Generated docs reference only files within target repo
