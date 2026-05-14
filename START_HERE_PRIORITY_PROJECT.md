# Priority Attribute Extraction Project

This folder is the current working package for the priority-order attribute extraction project.

## 12 May 2026 Closeout

This repository is now in a documented handoff state rather than an active-only experiment state.

Current closing position:

- the Gemma 4 experiment line from early V3b through V11 is preserved in this repo and in verified archive bundles under `_paper_archives`
- the priority-based attribute extraction paper track is ready to be written from the preserved Gemma 4 evidence
- the second paper track, Gemma 3 versus Gemma 4 benchmarking, should be completed by ingesting the separate Gemma 3 archive prepared from the Ashish data folder on the other machine
- until that Gemma 3 archive is merged, the honest paper framing is: Gemma 3 is historical context with pending archival recovery, while Gemma 4 is the fully audited quantitative program available here

## Read These First
1. [project_brief_for_senior.md](project_brief_for_senior.md)
2. [research_paper_draft_v2.md](research_paper_draft_v2.md)
3. [research_paper_draft_v1.md](research_paper_draft_v1.md)
4. [priority_project_status.csv](priority_project_status.csv)
5. [priority_error_analysis_notes.md](priority_error_analysis_notes.md)
6. [literature_review_notes.md](literature_review_notes.md)
7. [priority_benchmark_report.md](priority_benchmark_report.md)
8. [priority_metric_design.md](priority_metric_design.md)
9. [SERVER_SHUTDOWN_CHECKLIST.md](SERVER_SHUTDOWN_CHECKLIST.md)
10. [senior_status_update_may11.md](senior_status_update_may11.md)
11. [senior_status_update_may11.csv](senior_status_update_may11.csv)

## Useful Supporting Files
- [bee/comparison_summary.csv](bee/comparison_summary.csv)
- [gemma4_results.csv](gemma4_results.csv)
- [gemma4_results.json](gemma4_results.json)
- [finetune_gemma4_v8_priority.py](finetune_gemma4_v8_priority.py)
- [finetune_gemma4_v9_priority.py](finetune_gemma4_v9_priority.py)
- [finetune_gemma4_v11_priority_balanced.py](finetune_gemma4_v11_priority_balanced.py)
- [inference_priority_hybrid.py](inference_priority_hybrid.py)
- [inference_priority_split_hybrid.py](inference_priority_split_hybrid.py)
- [watch_v11_and_finalize.py](watch_v11_and_finalize.py)
- [finalize_v11_results.py](finalize_v11_results.py)
- [v11_live_status.md](v11_live_status.md)
- [eval_priority_adapter.py](eval_priority_adapter.py)
- [priority_error_analysis_notes.md](priority_error_analysis_notes.md)
- [literature_review_notes.md](literature_review_notes.md)
- [priority_benchmark_report.md](priority_benchmark_report.md)
- [priority_benchmark_report.csv](priority_benchmark_report.csv)
- [hybrid_v7_qmeans_eval_summary.json](hybrid_v7_qmeans_eval_summary.json)
- [priority_metric_design.md](priority_metric_design.md)
- [SERVER_SHUTDOWN_CHECKLIST.md](SERVER_SHUTDOWN_CHECKLIST.md)
- [senior_status_update_may11.md](senior_status_update_may11.md)
- [senior_status_update_may11.csv](senior_status_update_may11.csv)
- [v7_priority_analysis.json](v7_priority_analysis.json)

## Current Snapshot
- Verified archive status on 12 May 2026:
  - local repo snapshot saved
  - local zip saved
  - remote Gemma 4 paper-artifact bundle downloaded and hash-verified
  - model metadata bundle saved
  - remote manifest saved
- V6 legacy flat extraction beat qmeans on exact key+value matches in the earlier benchmark.
- V7 restored the nested priority schema. After fixing the evaluator to unwrap malformed nested priority bodies, V7 shows meaningful performance instead of near-zero recall.
- Corrected V7 numbers on the 1000-query benchmark:
  - key F1 = 29.09%
  - key+value F1 = 15.52%
  - qmeans key F1 = 45.50%
  - qmeans key+value F1 = 6.00%
- V8 evaluation is complete:
  - key F1 = 15.88%
  - key+value F1 = 10.72%
- V9 evaluation is complete:
  - key F1 = 4.75%
  - key+value F1 = 2.69%
- V10 clean-schema evaluation is complete:
  - key F1 = 0.00%
  - key+value F1 = 0.00%
- Current conclusion: V7 remains the best priority model so far. Later aggressive recipes made recall and overall F1 worse, not better.
- V11 balanced rollback training was launched on 11 May as the next controlled experiment.
- V11 final preserved result is now available locally:
  - key F1 = 45.44%
  - key+value F1 = 20.26%
- Hybrid remains the best operational serving path on the trusted benchmark:
  - key F1 = 54.38%
  - key+value F1 = 17.22%
- Best current serving path is now `V7 + qmeans missing-key fallback`, which reaches key F1 54.38% and key+value F1 17.22% on the trusted 1k benchmark while still returning priority-ordered output.
- A split-hybrid launcher now exists to recover that best serving path even when the remote server cannot reach qmeans directly.
- A local watcher is now running to monitor V11, pull artifacts, and finalize reports automatically when `v11_eval_summary.json` appears.

## Two Research Threads

The publication work should now be treated as two linked but separate threads:

1. Priority-based attribute extraction
   - main audited evidence is in this repository
   - strongest standalone model is V11
   - strongest operational system is the hybrid path

2. Gemma 3 versus Gemma 4 benchmarking
   - Gemma 4 evidence is already archived here
   - Gemma 3 evidence is expected from the separate archival repo created from the other machine
   - once that repo is available, merge only the reproducible Gemma 3 training, evaluation, and benchmark artifacts into the publication pack

## Why This Matters
The project is not just extracting unordered attributes like brand, power, model, or phase. It is trying to predict:
- which attribute matters first for user intent
- which synonym key should be preferred first for that value

Example target output:

```json
{
  "attributes": [
    {
      "attribute_priority1": {
        "value": "siemens",
        "key_priority1": "brand",
        "key_priority2": "manufacturer",
        "key_priority3": "company"
      }
    },
    {
      "attribute_priority2": {
        "value": "servo motor",
        "key_priority1": "part_type",
        "key_priority2": "product_type"
      }
    },
    {
      "attribute_priority3": {
        "value": "1 kw",
        "key_priority1": "power",
        "key_priority2": "horsepower"
      }
    }
  ]
}
```

## Current Caution
The strongest claim in this project is the idea of priority-ordered query understanding. That claim is promising, but the exact novelty claim still needs a formal literature review before any external paper submission.