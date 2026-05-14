# Priority-Ordered Attribute Extraction from Industrial Search Queries
### Fine-tuning Gemma 4 E4B with LoRA — Full Research Record

> **Status:** Research Complete (V11 is final run) | Archived: 12 May 2026  
> **Base Model:** `gemma-4-e4b-it`  
> **Task:** Extract product attributes from B2B search queries, ranked by importance  

---

## What This Project Does — In Plain English

When a buyer types a search query like `Siemens 1 kW 3 phase servo motor`, a smart search system needs to understand:

1. **What** attributes are in that query (brand, power, motor type, etc.)
2. **Which attribute matters most** — brand identity? product type? technical spec?
3. **What are the right canonical names** for each attribute (e.g., "brand" vs "manufacturer" vs "company" — which is preferred?)

Standard attribute extractors give you an unordered list. **This project builds a model that outputs a ranked, structured list** — most important attribute first, with preferred key names ordered too.

This is harder than regular extraction, and that difficulty is the research story.

---

## The Output Format (What the Model Learns to Produce)

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

The model must get the **value right**, the **priority slot right**, and the **key name order right** — all at once.

---

## Repository Structure

```
finetuning_gemma_4/
│
├── README.md                          ← You are here
│
│── RESULTS & REPORTS ──────────────────────────────────────
├── priority_benchmark_report.md       ← Main metrics table (all models)
├── priority_benchmark_report.csv      ← Same table, machine-readable
├── v11_eval_summary.json              ← V11 detailed eval results (raw)
├── hybrid_v7_qmeans_eval_summary.json ← Hybrid system eval results (raw)
├── v7_eval_summary.json               ← V7 detailed eval results
├── v8_eval_summary.json               ← V8 detailed eval results
├── v9_eval_summary.json               ← V9 detailed eval results
├── v10_eval_summary.json              ← V10 detailed eval results
├── gemma4_results.csv                 ← Earlier flat-extraction results
│
│── RESEARCH PAPER ─────────────────────────────────────────
├── research_paper_full_draft_v6.md    ← Full paper draft (latest, most complete)
├── readable_research_draft_may12_2026.md ← Clean readable version for sharing
├── literature_review_notes.md         ← Prior work references with analysis
├── priority_metric_design.md          ← What metrics to use and why
├── priority_error_analysis_notes.md   ← Error breakdown for V7 (evaluator fix story)
│
│── TRAINING SCRIPTS ───────────────────────────────────────
├── finetune_gemma4_v7_priority.py     ← V7: first useful priority model
├── finetune_gemma4_v8_priority.py     ← V8: aggressive variant (regressed)
├── finetune_gemma4_v9_priority.py     ← V9: heavier gold weighting (collapsed)
├── finetune_gemma4_v10_priority_clean.py ← V10: clean-only (0% recall)
├── finetune_gemma4_v11_priority_balanced.py ← V11: best standalone model ✓
│
│── INFERENCE & EVAL ───────────────────────────────────────
├── inference_priority_hybrid.py       ← Deployed serving: V7 + qmeans fallback
├── inference_priority_split_hybrid.py ← Alt hybrid launcher
├── eval_priority_adapter.py           ← Evaluator script (F1 computation)
│
│── EARLY FLAT EXTRACTION (bee/) ───────────────────────────
├── bee/finetune_v3.py                 ← V3b: first Gemma 4 run, open keys
├── bee/finetune_gemma4_v5_flat.py     ← V5: simpler flat JSON, more coverage
├── bee/finetune_gemma4_v6.py          ← V6: canonical keys, beat qmeans baseline
├── bee/comparison_summary.csv         ← V6 vs qmeans flat benchmark
│
│── TEAM DOCS ──────────────────────────────────────────────
├── project_brief_for_senior.md        ← Non-technical senior brief
├── senior_status_update_may11.md      ← Latest status update (MD)
├── senior_status_update_may11.csv     ← Latest status update (CSV)
├── priority_project_status.csv        ← Full experiment log, all runs
├── START_HERE_PRIORITY_PROJECT.md     ← Project master index
├── TASK_CLOSEOUT_MAY12_2026.md        ← Closeout handoff document
│
│── DATA ───────────────────────────────────────────────────
├── gold_1k_v2.jsonl                   ← 1000-query gold evaluation set
├── product_train_with_keys.jsonl      ← Training data (flat extraction phase)
├── product_val_with_keys.jsonl        ← Validation data (flat extraction phase)
├── v6_train.jsonl / v6_val.jsonl      ← V6 cleaned canonical training data
├── v7_priority_results.jsonl          ← V7 raw predictions (1000 queries)
```

---

## All Experiment Results — The Numbers

> **Primary source file:** [`priority_benchmark_report.md`](priority_benchmark_report.md)  
> **Evaluation set:** 1000 industrial B2B search queries (`gold_1k_v2.jsonl`)

| Model | What it is | Key F1 | Key+Value F1 | Notes |
|---|---|---|---|---|
| **qmeans** | Production baseline (rule-based) | 45.50% | 6.00% | High precision (96%), very low recall — misses most values |
| **V3b** | First Gemma 4 run, open keys | *(early benchmark only)* | — | Strong values, severe key drift |
| **V5** | Flat JSON, broader coverage | *(early benchmark only)* | — | Still behind qmeans on strict match |
| **V6** | Canonical flat, gold supervision | *(flat benchmark)* | — | **First model to beat qmeans** on exact flat match |
| **V7** | First priority-ordered model | 29.09% | 15.52% | First useful structured output |
| **V8** | Aggressive training variant | 15.88% | 10.72% | Regression — more training hurt it |
| **V9** | Heavy gold weighting | 4.75% | 2.69% | Recall collapsed |
| **V10** | Clean-only alignment | 0.00% | 0.00% | Complete failure |
| **V11** ⭐ | Balanced rollback (best standalone) | **45.44%** | **20.26%** | Best standalone model |
| **Hybrid V7 + qmeans** ⭐ | Serving-time combination | **54.38%** | 17.22% | Best deployed system |

### How to read these numbers

- **Key F1**: Did the model extract the right attribute names? (e.g., did it output "brand" when gold says "brand")
- **Key+Value F1**: Did it extract both the right name AND the right value? (stricter — "brand: siemens" vs just "brand")
- **qmeans** is the production baseline — any fine-tuned model needs to beat or complement it to be useful
- **V11 vs qmeans on Key+Value F1**: 20.26% vs 6.00% — **3.4× improvement** on exact attribute extraction
- **Hybrid system** gets the best key recall (54.38%) by using V7's ranked output + qmeans to fill in gaps

### Raw numbers for V11 (from `v11_eval_summary.json`)

```
Key-only:   Precision=79.47%  Recall=31.82%  F1=45.44%   (TP=987, FP=255, FN=2115)
Key+Value:  Precision=35.43%  Recall=14.18%  F1=20.26%   (TP=440, FP=802, FN=2662)
```

---

## How We Got Here — The Training Journey

### Phase 1: Flat Extraction (V3b → V6)
The project started by training Gemma 4 to extract attributes as a **flat, unordered JSON** — simpler than the final goal but necessary to establish that the model can learn canonical key names at all.

- **V3b**: Open key names, good value recovery, bad key canonicalization
- **V5**: Switched to IndiaMART-style canonical keys, added motor-domain data
- **V6**: Strict canonical key list, cleaned training data, gold supervision → **beat qmeans on exact flat match**

### Phase 2: Priority-Ordered Extraction (V7 → V11)
Harder: the model now has to emit a **nested ranked structure** (not flat), order attributes by importance, and order key synonyms within each attribute.

| Run | Why it was tried | What happened |
|---|---|---|
| V7 | Introduced nested priority schema | First useful result; 29% key F1, 15.5% key+value F1 |
| V8 | Larger model capacity + more aggressive loss | Recall dropped from 19% → 9% |
| V9 | Even heavier gold weighting | Recall dropped to 2.5% — model became over-conservative |
| V10 | Clean-only training, no noisy examples | 0% recall — complete failure |
| V11 | Rolled back to V7 recipe, balanced data mix | Recovered to 45.4% key F1, 20.3% key+value F1 |

**The key lesson:** More aggressive training made things worse. The V11 recovery came from going *back* to a simpler, more balanced approach.

### Phase 3: Hybrid Serving
Rather than choosing between the fine-tuned model and qmeans, we combine them:
- **V7 generates priority-ranked output** (structured, ranked)
- **qmeans fills in any keys V7 missed** (high-precision fallback)
- Result: **54.38% key F1** — best overall system

---

## Training Configuration (V11 — Best Standalone Model)

| Parameter | Value |
|---|---|
| Base model | `gemma-4-e4b-it` |
| Framework | Unsloth + TRL SFTTrainer |
| Adapter type | LoRA |
| LoRA rank (r) | 32 |
| LoRA alpha | 64 |
| Max sequence length | 768 tokens |
| Epochs | 2 |
| Batch size | 2 (+ grad accumulation 16) |
| Learning rate | 7e-5 |
| Training data | Balanced mix: nested cat74 + V6 flat-to-nested + gold_1k_v2 |
| Adapter path (server) | `/home3/indiamart/gemma_4/isq-gemma4-e4b-v11-priority-balanced` |

---

## Evaluation Method

**Script:** [`eval_priority_adapter.py`](eval_priority_adapter.py)

The evaluator:
1. Runs the model on all 1000 gold queries
2. Parses the nested JSON output (handles malformed nesting)
3. Flattens prediction and gold to `{key: value}` sets
4. Computes precision, recall, F1 for key-only and key+value matches

**Important:** The evaluator was fixed mid-project when we discovered V7 was being scored near-zero due to extra nesting levels in outputs. The corrected evaluator recursively unwraps nested priority bodies. See [`priority_error_analysis_notes.md`](priority_error_analysis_notes.md) for full details.

---

## What Makes This Research Novel

From the literature review ([`literature_review_notes.md`](literature_review_notes.md)):

| What prior work does | This project adds |
|---|---|
| Extract attribute values from product text | ✓ Done, plus... |
| Normalize to canonical key names | ✓ Done, plus... |
| Model intent from short search queries | ✓ Done, plus... |
| **Rank attributes by importance** | ← NEW: priority-ordered output |
| **Rank key synonyms within each attribute** | ← NEW: key-synonym preference order |
| **Jointly predict all three in one nested schema** | ← NEW: structured joint generation |

Closest references:
- OpenTag (KDD 2018) — product attribute extraction via BiLSTM-CRF, no priority
- Loughnane et al. (ECNLP 2024) — query attribute extraction, no ranking
- Brinkmann et al. (2024) — LLM extraction + normalization, product offers, no ranking

---

## What Is Still Pending

These are the items not yet complete for a full external publication:

| Item | Status | Notes |
|---|---|---|
| Rank-aware metrics | ❌ Not computed | Pairwise order accuracy, top-1 attribute accuracy, MRR |
| Exact structured match | ❌ Not computed | Strict all-or-nothing per-query match |
| Gemma3 comparison | ❌ Pending | Gemma3 was exploratory only (Ollama), no fine-tuning artifacts preserved |
| Broader literature sweep | ⚠️ Partial | Entity salience, facet ranking, keyphrase ranking still to review |
| Schema compliance metrics | ❌ Not computed | Parse rate, placeholder-key rate per model |

See [`priority_metric_design.md`](priority_metric_design.md) for the full recommended metric stack.

---

## Archived Artifacts

All server files were archived locally on 12 May 2026 before server shutdown.

| Archive | Location | Contents |
|---|---|---|
| Folder snapshot | `_paper_archives/finetuning_gemma_4_snapshot_20260512_130307/` | 179 files, 191 MB |
| Zip archive | `_paper_archives/finetuning_gemma_4_snapshot_20260512_130308.zip` | 162 MB |
| Full server archive | `_paper_archives/gemma4_paper_artifacts_20260512_130615.tar.gz` | 2.1 GB (hash verified) |
| Model metadata | `_paper_archives/gemma4_model_metadata_20260512_130615.tar.gz` | 21 KB adapter/tokenizer configs |
| File manifest | `_paper_archives/gemma4_manifest_20260512_130615.txt` | 4.9 MB file list |

Zip SHA256: `1BB9416324A1A4F6F32CF350B8F66C9962E127A2A902D5189A73CCDE9CDDCBEF`

---

## Key Files Quick Reference

| If you want to... | Go to |
|---|---|
| See all metrics in one place | [`priority_benchmark_report.md`](priority_benchmark_report.md) |
| Read the full research paper draft | [`research_paper_full_draft_v6.md`](research_paper_full_draft_v6.md) |
| Read a clean shareable version | [`readable_research_draft_may12_2026.md`](readable_research_draft_may12_2026.md) |
| See the V11 raw eval numbers | [`v11_eval_summary.json`](v11_eval_summary.json) |
| Understand the error analysis | [`priority_error_analysis_notes.md`](priority_error_analysis_notes.md) |
| Understand the metric design | [`priority_metric_design.md`](priority_metric_design.md) |
| Look at prior work | [`literature_review_notes.md`](literature_review_notes.md) |
| Send to a senior/manager | [`senior_status_update_may11.md`](senior_status_update_may11.md) |
| Run the best serving system | [`inference_priority_hybrid.py`](inference_priority_hybrid.py) |
| Re-train V11 | [`finetune_gemma4_v11_priority_balanced.py`](finetune_gemma4_v11_priority_balanced.py) |
| Re-run evaluation | [`eval_priority_adapter.py`](eval_priority_adapter.py) |

---

## Team / Authors

| Role | Person |
|---|---|
| Project lead / experiments | IndiaMART ML Team |
| Server infrastructure | `amit_87483` on `34.123.131.255` (shut down post-archival) |
| Gemma 3 exploratory setup | Referenced in [`setup_ollama.sh`](setup_ollama.sh) |

---

## How to Cite (Internal Draft)

```
Priority-Ordered Attribute Extraction from Industrial B2B Search Queries
Using Fine-tuned Gemma 4 E4B with LoRA Adapters.
IndiaMART ML Team, May 2026.
```

---

*Last updated: 14 May 2026. Server is offline. All artifacts archived locally.*
