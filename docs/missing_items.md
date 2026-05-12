# Missing Items for Gemma3 vs Gemma4 Paper

Generated: 2026-05-12T14:08:46

## Anchor Files NOT Found in Source (High Priority)

These files were specified as required for the paper but are absent from the workspace.
They may exist on another machine / GPU server.

| Missing File | Family | Likely Location |
|-------------|--------|----------------|
| `priority_benchmark_report.md` | gemma4 | GPU training server |
| `priority_benchmark_report.csv` | gemma4 | GPU training server |
| `priority_project_status.csv` | gemma4 | GPU training server |
| `v11_eval_summary.json` | gemma4 | GPU training server |
| `v10_eval_summary.json` | gemma4 | GPU training server |
| `v9_eval_summary.json` | gemma4 | GPU training server |
| `v8_eval_summary.json` | gemma4 | GPU training server |
| `v7_eval_summary.json` | gemma4 | GPU training server |
| `eval_priority_adapter.py` | gemma4 | GPU training server |
| `watch_v11_and_finalize.py` | gemma4 | GPU training server |
| `finalize_v11_results.py` | gemma4 | GPU training server |
| `finetune_gemma4_v11_priority_balanced.py` | gemma4 | GPU training server |
| `finetune_gemma4_v10_priority_clean.py` | gemma4 | GPU training server |
| `finetune_gemma4_v9_priority.py` | gemma4 | GPU training server |
| `finetune_gemma4_v8_priority.py` | gemma4 | GPU training server |
| `finetune_gemma4_v7_priority.py` | gemma4 | GPU training server |
| `inference_priority_hybrid.py` | gemma4 | GPU training server |
| `research_paper_full_draft_v6.md` | gemma4 | GPU training server |
| `readable_research_draft_may12_2026.md` | gemma4 | GPU training server |
| `priority_attribute_extraction_team_presentation_may12_2026.pptx` | gemma4 | GPU training server |
| `setup_ollama.sh` | gemma4 | GPU training server |

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
