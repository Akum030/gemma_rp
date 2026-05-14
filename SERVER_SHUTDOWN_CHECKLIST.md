# Server Shutdown Checklist

This note is the minimum safe checklist to complete before the remote server is shut down.

## Status On 12 May 2026

This checklist has now been executed to a safe stopping point for the Gemma 4 workstream.

Verified local archival copies now exist at:

- `c:\Users\Imart\CopilotHacksAndPersonal\IM_Repos\_paper_archives\finetuning_gemma_4_snapshot_20260512_130307`
- `c:\Users\Imart\CopilotHacksAndPersonal\IM_Repos\_paper_archives\finetuning_gemma_4_snapshot_20260512_130308.zip`
- `c:\Users\Imart\CopilotHacksAndPersonal\IM_Repos\_paper_archives\gemma4_manifest_20260512_130615.txt`
- `c:\Users\Imart\CopilotHacksAndPersonal\IM_Repos\_paper_archives\gemma4_model_metadata_20260512_130615.tar.gz`
- `c:\Users\Imart\CopilotHacksAndPersonal\IM_Repos\_paper_archives\gemma4_paper_artifacts_20260512_130615.tar.gz`

The large remote archive was re-downloaded and hash-verified against the server before shutdown approval.

## Publication Scope Now Locked

The publication effort is now explicitly split into two connected research problems:

- priority-based attribute extraction
- Gemma 3 versus Gemma 4 benchmarking and historical comparison

For the current repository, the Gemma 4 side is archived and defensible.
The Gemma 3 side is expected to be completed from the separate external archival repo populated from the Ashish data folder on the other machine.

## 1. Verify Final Remote Artifacts Exist
Expected remote paths:

- `/home3/indiamart/gemma_4/v7_eval_summary.json`
- `/home3/indiamart/gemma_4/v8_eval_summary.json`
- `/home3/indiamart/gemma_4/v9_eval_summary.json`
- `/home3/indiamart/gemma_4/v10_eval_summary.json`
- `/home3/indiamart/gemma_4/v7_priority_results.jsonl`
- `/home3/indiamart/gemma_4/v8_priority_results.jsonl`
- `/home3/indiamart/gemma_4/v9_priority_results.jsonl`
- `/home3/indiamart/gemma_4/v10_priority_results.jsonl`
- `/home3/indiamart/gemma_4/isq-gemma4-e4b-v8-priority/`
- `/home3/indiamart/gemma_4/isq-gemma4-e4b-v9-priority/`
- `/home3/indiamart/gemma_4/isq-gemma4-e4b-v10-priority-clean/`
- `/home3/indiamart/gemma_4/v9_train.log`
- `/home3/indiamart/gemma_4/v10_train.log`

## 2. Copy Final Summaries And Result Files Locally
Minimum local copies to keep:

- `v9_eval_summary.json`
- `v10_eval_summary.json`
- `v9_priority_results.jsonl`
- `v10_priority_results.jsonl`

## 3. Rebuild The Local Benchmark Rollup
Run:

```powershell
c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/.venv/Scripts/python.exe c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/build_priority_benchmark_report.py --v7 c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/v7_eval_summary.json --v8 c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/v8_eval_summary.json --v9 c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/v9_eval_summary.json --v10 c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/v10_eval_summary.json --out-md c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/priority_benchmark_report.md --out-csv c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/priority_benchmark_report.csv
```

## 4. Refresh The Paper Pack
After final V9 and V10 metrics are available, update:

- `START_HERE_PRIORITY_PROJECT.md`
- `project_brief_for_senior.md`
- `research_paper_draft_v1.md`
- `priority_project_status.csv`

## 5. Minimum Final Comparison To Capture
Before shutdown, the project should retain one final comparison table covering:

- `qmeans`
- `v7`
- `v8`
- `v9`
- `v10`

With at least these metrics:

- key precision
- key recall
- key F1
- key+value precision
- key+value recall
- key+value F1

## 6. Research-Side Conclusion To Preserve
Even if V9 or V10 do not beat V7 on every metric, the following outcomes are still scientifically useful:

- V7 established that the priority formulation can beat qmeans on exact key+value quality.
- V8 showed that higher-capacity training alone does not automatically fix recall.
- V9 tests whether stronger gold weighting improves coverage.
- V10 tests whether clean-schema training improves structure obedience.

That is enough to support an internal research narrative even before rank-aware metrics are fully implemented.

## 7. Final Handoff Position

The final handoff position for this repo is:

- Gemma 4 research history is preserved locally and in `_paper_archives`.
- V11 is the strongest standalone priority-model checkpoint in the preserved Gemma 4 line.
- Hybrid remains the strongest serving-time operational system.
- Gemma 3 should no longer be described as missing forever; it should be described as pending ingestion from the separate archival repo prepared from the other machine.
- Until that Gemma 3 archive is merged into the paper pack, any strict metric-for-metric Gemma 3 versus Gemma 4 table remains provisional.