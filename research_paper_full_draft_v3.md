# Priority-Ordered Attribute Extraction From Industrial Search Queries

## Full Internal Research Draft

Date: 11 May 2026

Authoring status: internal draft for team circulation and research review.

## Record Integrity Note

This draft distinguishes between verified, reproducible evidence and historical project context.

- All quantitative tables in this document are grounded in files that exist in this workspace.
- The preserved quantitative experiment trail is Gemma 4 based.
- A Gemma 3 exploratory setup reference exists in [setup_ollama.sh](setup_ollama.sh), but no archived Gemma 3 training logs, benchmark summaries, or evaluation outputs remain in this repo.
- Therefore, the Gemma 3 to Gemma 4 comparison in this draft is framed as an exploratory-to-reproducible transition, not as a fully audited metric-for-metric benchmark comparison.

That wording is deliberate. It keeps the document publishable and defensible.

## Abstract

Industrial search queries are short, noisy, and dense with intent. Standard extraction systems usually return an unordered set of attribute-value pairs such as brand, product type, phase, power, or rpm. In many downstream search and ranking systems, that is not enough. The system may also need to know which attribute should be treated as the primary intent signal, which constraints are secondary, and which normalized key names should be preferred for each extracted value. This project studies that richer formulation as priority-ordered attribute extraction.

We formulate the task as structured generation with a nested JSON schema in which each extracted value is assigned both an attribute priority and a key-synonym priority list. We fine-tune Gemma 4 E4B with LoRA-based adapters across a sequence of flat-extraction and priority-oriented runs. The earlier flat-extraction Gemma 4 direction already demonstrates business relevance by outperforming qmeans on an older exact key+value benchmark. In the priority-specific phase, V7 establishes the first useful structured model, V8 to V10 show that aggressive scaling or clean-only supervision can damage recall severely, and V11 demonstrates that a conservative rollback toward the successful V7 recipe recovers the best standalone exact key+value quality observed so far. In parallel, a serving-time hybrid of V7 plus qmeans yields the strongest operational key F1.

The main scientific conclusion is that priority-ordered extraction is meaningful and useful, but materially harder than ordinary flat extraction. The key bottleneck is not only extraction coverage. It is the combined problem of extraction, schema obedience, attribute ordering, and key-synonym ordering. This makes the task suitable for a research paper with both positive and negative findings.

## Executive Summary

- The project has moved from ordinary flat extraction to a richer priority-ordered structured extraction task.
- The reproducible quantitative story in this repo begins with Gemma 4, not Gemma 3.
- On the legacy exact key+value benchmark, Gemma 4 V6 outperforms qmeans: 40.7% versus 27.1%.
- On the trusted 1000-query priority benchmark, V11 is now the best standalone priority model.
- V11 key F1 is 45.44%, which is essentially tied with qmeans at 45.50%.
- V11 key+value F1 is 20.26%, which is far above qmeans at 6.00% and above V7 at 15.52%.
- The best current operational system remains the hybrid V7 plus qmeans fallback, with key F1 54.38% and key+value F1 17.22%.
- The research contribution is not only a better model. It is also the formulation, evaluation design, failure analysis, and the discovery that rank-aware structured extraction is substantially harder than flat extraction.

## 1. Problem Statement

The research problem is:

Given an industrial search query, predict not only the extracted attributes and values, but also:

- the relative priority order of attributes in the query
- the preferred key-synonym order for each extracted value

The target output is nested JSON of the form:

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

This is harder than ordinary extraction because the model must solve four coupled problems:

- detect the correct values
- normalize them to the correct canonical key family
- rank the extracted attributes by user intent
- rank the preferred synonym keys for each extracted value

## 2. Why This Problem Matters

Unordered extraction is often sufficient for analytics, but it is incomplete for high-quality retrieval and ranking.

In industrial search, the same query can contain:

- identity signals such as brand or series
- product type signals such as motor, servo motor, starter, actuator
- primary technical constraints such as power, phase, voltage, or rpm
- secondary constraints such as mounting, efficiency, or IP rating

Downstream systems benefit if they know which signal should dominate first.

Examples of business value:

- retrieval can emphasize the top-priority attribute before weaker constraints
- ranking can distinguish between core intent and supporting filters
- normalization can keep the preferred key name instead of arbitrary aliases
- query rewriting can preserve the intended order of importance

## 3. Research Questions

This project answers five practical research questions:

1. Can a fine-tuned Gemma model outperform a production-style baseline on exact attribute extraction quality?
2. Can the extraction task be lifted from flat key-value output to priority-ordered structured output?
3. What data mixture and training strategy best preserve recall while improving structure?
4. Is the best solution a standalone model or a system-level hybrid?
5. What metric stack is actually required to evaluate the full research claim?

## 4. Project Evolution: Gemma 3 To Gemma 4

### 4.1 Gemma 3 Phase: Exploratory Context

The surviving local evidence for Gemma 3 in this workspace is limited to exploratory setup. In [setup_ollama.sh](setup_ollama.sh), the environment explicitly pulls `gemma3:4b` for local use.

What can be said safely:

- Gemma 3 was part of the exploratory tooling context.
- It was suitable for low-cost local probing and setup experiments.
- The current workspace does not preserve Gemma 3 fine-tuning scripts, evaluation outputs, or benchmark summaries for this project.

What cannot be said safely:

- a metric-for-metric Gemma 3 versus Gemma 4 benchmark comparison
- a reproducible claim that Gemma 3 was trained and scored in the same audited way as Gemma 4

For publication, the correct approach is either:

- recover the missing Gemma 3 logs from archived infrastructure, or
- scope the quantitative paper to Gemma 4 and describe Gemma 3 only as an exploratory predecessor

This draft follows the second option because it is supported by the preserved evidence.

### 4.2 Gemma 4 Phase: Reproducible Experimental Program

All preserved training scripts, benchmark summaries, and evaluation results in this repo are Gemma 4 based. The base model used throughout the audited training path is `gemma-4-e4b-it`.

This makes Gemma 4 the real quantitative backbone of the project.

## 5. Gemma 4 Experimental Timeline

### 5.1 Early Gemma 4 Structured Extraction Work

The earliest preserved Gemma 4 training trail includes V3, V5, and V6 style flat extraction efforts.

Key preserved evidence:

- [bee/finetune_v3.py](bee/finetune_v3.py) shows an improved Gemma 4 fine-tuning setup with proper chat formatting, response-side loss focus experiments, LoRA training, and merged model export.
- [bee/compare_v5_results.txt](bee/compare_v5_results.txt) preserves a flat extraction comparison against qmeans_v2.
- [bee/comparison_summary.csv](bee/comparison_summary.csv) and [bee/wide_summary.csv](bee/wide_summary.csv) preserve the strongest flat Gemma 4 versus qmeans summary for the later V6 stage.

### 5.2 Transition To Priority-Ordered Extraction

The project then moved from flat extraction into the ranked structured output formulation.

The preserved priority run sequence is:

- V7: first useful priority-schema restoration run
- V8: larger-capacity priority model plus more gold supervision
- V9: stronger gold weighting and lower learning rate
- V10: clean-schema-only priority training
- V11: conservative rollback toward the V7 recipe with a light clean nested-priority bias

## 6. Training Methodology

### 6.1 Common Training Stack

Across the preserved Gemma 4 training path, the main stack is:

- Base model: Gemma 4 E4B instruction-tuned base
- Fine-tuning style: LoRA/QLoRA-style adapter tuning
- Runtime stack: Unsloth plus Transformers plus TRL
- Hardware context: Tesla T4 GPU environment
- Objective type: structured generation in chat format

### 6.2 Gemma 4 Flat Phase Training

The flat phase focused on canonical attribute extraction before the ranked schema was introduced.

The V6 script in [bee/finetune_gemma4_v6.py](bee/finetune_gemma4_v6.py) shows the main design choices:

- canonical key vocabulary enforcement
- inclusion of cleaned flat training data
- inclusion of gold query data
- inclusion of motor-domain cat74 data for coverage
- strict system prompt restricting the allowed output keys
- LoRA fine-tuning with a coverage-oriented mixture

This phase established the core business signal:

- fine-tuned Gemma 4 could beat qmeans on exact key+value match in the older benchmark

### 6.3 Gemma 4 Priority Phase Training

The V11 script in [finetune_gemma4_v11_priority_balanced.py](finetune_gemma4_v11_priority_balanced.py) captures the final successful standalone design hypothesis.

Core V11 idea:

- preserve the broader recall behavior seen in V7
- add only a light clean nested-priority bias
- avoid the recall collapse patterns seen in V8 to V10

V11 data mixture:

- cat74 nested priority rows with light repetition
- V6 flat-to-nested rows for broad coverage
- gold_1k_v2 flat rows converted to nested with no aggressive oversampling

Key V11 training configuration:

- max sequence length: 768
- epochs: 2
- batch size: 2
- gradient accumulation: 16
- learning rate: 7e-5
- LoRA size: r=32, alpha=64

This is important because V11 did not win by making the model more aggressive. It won by becoming more conservative and better balanced.

## 7. Datasets And Benchmarks

### 7.1 Main Data Sources

The preserved training and evaluation path draws from three major sources:

- manually curated nested priority supervision
- flat extraction supervision converted into nested priority form
- a trusted 1000-query gold benchmark

### 7.2 Legacy Flat Benchmark

This benchmark measures exact key+value quality in a flat setting.

It is useful because it establishes whether the fine-tuning direction has business relevance at all.

### 7.3 Priority Benchmark

This benchmark evaluates the newer priority formulation on 1000 trusted queries.

Current evaluator outputs:

- key precision, recall, F1
- key+value precision, recall, F1

Important limitation:

These are necessary metrics, but they are still not enough to fully measure the novelty claim, because they do not directly score attribute ranking or key-synonym ranking.

## 8. Results

### 8.1 Early Flat Gemma 4 Results

#### V5 Flat Comparison

From [bee/compare_v5_results.txt](bee/compare_v5_results.txt):

| System | KV strict F1 | Value-only F1 | Token F1 |
|---|---:|---:|---:|
| qmeans_v2 | 37.23 | 46.20 | 79.83 |
| V5_flat | 28.05 | 31.27 | 41.99 |

Interpretation:

- early Gemma 4 flat extraction was not yet better than qmeans_v2 on this intermediate benchmark
- this is useful negative evidence because it shows that the strong later result was not automatic

#### V6 Flat Comparison

From [bee/comparison_summary.csv](bee/comparison_summary.csv):

| System | Exact key+value match rate | All attributes correct | Zero correct |
|---|---:|---:|---:|
| qmeans | 27.1% | 42 | 415 |
| Gemma V6 | 40.7% | 182 | 332 |

Interpretation:

- by the V6 stage, Gemma 4 clearly outperformed qmeans on exact key+value matching
- this validated the fine-tuning direction before the priority formulation was introduced

### 8.2 Priority Benchmark Results

From [priority_benchmark_report.md](priority_benchmark_report.md):

| Model | Key Precision | Key Recall | Key F1 | Key+Value Precision | Key+Value Recall | Key+Value F1 |
|---|---:|---:|---:|---:|---:|---:|
| qmeans | 95.95% | 29.82% | 45.50% | 12.66% | 3.93% | 6.00% |
| V7 | 60.49% | 19.15% | 29.09% | 32.28% | 10.22% | 15.52% |
| Hybrid (V7 + qmeans fallback) | 75.60% | 42.46% | 54.38% | 23.94% | 13.44% | 17.22% |
| V8 | 61.12% | 9.12% | 15.88% | 41.25% | 6.16% | 10.72% |
| V9 | 77.55% | 2.45% | 4.75% | 43.88% | 1.39% | 2.69% |
| V10 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| V11 | 79.47% | 31.82% | 45.44% | 35.43% | 14.18% | 20.26% |

### 8.3 Main Quantitative Findings

1. V11 is the best standalone priority model in the repo.
2. V11 key+value F1 is 20.26%, which is higher than V7, V8, V9, V10, and qmeans.
3. qmeans still leads standalone key F1 by a very small margin: 45.50% versus 45.44%.
4. The hybrid system remains the best overall key F1 system at 54.38%.
5. The strongest practical deployment result and the strongest standalone model are not the same thing.

### 8.4 Structural Diagnostics From V7

From [priority_error_analysis_notes.md](priority_error_analysis_notes.md) and [v7_priority_analysis.json](v7_priority_analysis.json):

- parsed rate: 80.2%
- deep-wrapper rate: 71.9%
- placeholder-key rate: 19.9%
- empty-flat rate after robust unwrapping: 27.2%

These diagnostics are essential because they show that the priority problem is not only a recall problem. It is also a schema-obedience problem.

## 9. Example Case Study

The following example is preserved in [split_hybrid_sample.jsonl](split_hybrid_sample.jsonl).

### Query

`siemens 45 hp 3 phase 1440 rpm motor`

### Hybrid Final Structured Output

```json
{
  "attributes": [
    {
      "attribute_priority1": {
        "value": "siemens",
        "key_priority1": "brand",
        "key_priority2": "manufacturer",
        "key_priority3": "company",
        "key_priority4": "make"
      }
    },
    {
      "attribute_priority2": {
        "value": "motor",
        "key_priority1": "part_type",
        "key_priority2": "product_type",
        "key_priority3": "type"
      }
    },
    {
      "attribute_priority3": {
        "value": "45 hp",
        "key_priority1": "power",
        "key_priority2": "wattage",
        "key_priority3": "kilowatt"
      }
    },
    {
      "attribute_priority4": {
        "value": "3 phase",
        "key_priority1": "phase",
        "key_priority2": "phase_type"
      }
    },
    {
      "attribute_priority5": {
        "value": "1440 rpm",
        "key_priority1": "rpm",
        "key_priority2": "speed"
      }
    }
  ]
}
```

### Flattened Comparison

| System | Flat output |
|---|---|
| Hybrid | brand=siemens, part type=motor, power=45 hp, phase=3 phase, rpm=1440 rpm |
| V7 parsed | brand=siemens, part type=motor, power=45 hp, phase=3 phase, rpm=1440 rpm |
| qmeans | rpm=1440 rpm, phase=3 phase, power=45 hp, brand=siemens, part type=3 phase |

### Why This Example Matters

- The query contains a clear brand, product type, and two primary technical constraints.
- The hybrid output correctly preserves priority order and produces a clean final nested structure.
- The preserved raw V7 output still shows the schema-obedience issue: extra nested wrappers under `attribute_priorityN`.
- qmeans recovers most values quickly, but its part-type assignment is weaker in this example.

This example is useful in the paper because it shows both the promise and the remaining challenge:

- semantic extraction is strong
- final structure is useful
- the model needed evaluator repair and serving-time handling to expose its value cleanly

## 10. What Problems We Solved

The project solved several concrete research and engineering problems.

### 10.1 We Solved The Task Formulation Problem

The project defines a clear and reusable formulation for priority-ordered attribute extraction from industrial search queries.

This includes:

- attribute ranking
- key-synonym ranking
- structured nested output

### 10.2 We Solved The Basic Feasibility Question

The flat Gemma 4 direction proved that the model family can outperform qmeans on exact key+value quality in a meaningful benchmark.

### 10.3 We Solved The First Standalone Priority Model Problem

V7 showed that a model can learn a useful priority-oriented representation, even if it still has structure issues.

### 10.4 We Solved The Conservative Recovery Problem

V11 demonstrated that the regression from V8 to V10 was not a dead end. A rollback toward the V7 recipe with a lighter clean-schema bias recovered the strongest standalone result in the project.

### 10.5 We Solved The Best Practical System Problem

The hybrid serving path established the best current operational system by combining V7 structure with qmeans recall.

### 10.6 We Solved Benchmarking And Failure Analysis Infrastructure

The project now has:

- a trusted priority evaluator
- benchmark rollups
- structural diagnostics
- senior-facing CSV and markdown status artifacts
- example inference paths for live use

## 11. What Remains Unsolved

The project is not fully solved yet, and the paper should be honest about that.

### 11.1 qmeans Still Slightly Leads Standalone Key F1

The difference is now tiny, but it still exists:

- qmeans key F1: 45.50%
- V11 key F1: 45.44%

### 11.2 The Evaluation Stack Is Still Incomplete For Publication

Current benchmark tables are strong but not yet complete relative to the novelty claim.

The final paper still needs:

- schema compliance rate
- attribute top-1 accuracy
- pairwise attribute order accuracy
- key-synonym top-1 accuracy
- key-synonym mean reciprocal rank
- exact structured match rate

### 11.3 Gemma 3 Quantitative Comparison Is Not Yet Archived

If the team wants a formal Gemma 3 versus Gemma 4 table in the final paper, the missing Gemma 3 experiment records must be recovered.

Without that, the publishable wording should remain:

- Gemma 3 was part of early exploration
- Gemma 4 is the audited experimental platform in this repo

## 12. Scientific Findings

The project yields five strong research findings.

### Finding 1

Priority-ordered extraction is a real and harder problem than flat extraction.

### Finding 2

Higher capacity or stronger supervision is not automatically better. V8 to V10 demonstrate that aggressive design changes can destroy recall.

### Finding 3

Schema obedience is a first-class failure mode, not only a formatting issue.

### Finding 4

Exact key+value quality and broad key coverage can diverge sharply. That is why qmeans and priority-tuned Gemma can each look strong on different metrics.

### Finding 5

System-level hybrids can outperform standalone models before the standalone research problem is fully solved.

## 13. Recommended Paper Claim

The safest and strongest current claim is:

To our knowledge, explicit modeling of both attribute priority order and synonym-key priority order for industrial search queries is underexplored. In a preserved Gemma 4 experimental program, we show that flat fine-tuning already has strong business relevance, that priority-aware structured extraction is substantially harder than flat extraction, that aggressive optimization can easily damage recall, and that a conservative rollback strategy recovers the best standalone exact key+value quality observed so far.

## 14. Recommended Publication Tables

The final paper should include at least these four tables:

### Table A: Legacy Flat Benchmark

- qmeans exact key+value match rate
- Gemma V6 exact key+value match rate

### Table B: Priority Benchmark

- qmeans
- V7
- V8
- V9
- V10
- V11
- hybrid system, clearly labeled as serving-time combination

### Table C: Structural Quality

- parse rate
- schema compliance rate
- deep-wrapper rate
- placeholder-key rate

### Table D: Rank-Aware Quality

- attribute top-1 accuracy
- pairwise attribute order accuracy
- key-synonym top-1 accuracy
- key-synonym MRR
- exact structured match rate

## 15. Conclusion

This project is now in a good research position.

The repo preserves a credible Gemma 4 experimental story that begins with flat extraction, transitions into priority-ordered structured extraction, documents both positive and negative ablations, and ends with a strong standalone result in V11 together with an even stronger operational hybrid system.

The paper is not yet fully publication-ready because the metric stack still under-measures the ranking claim and because a fully reproducible Gemma 3 benchmark trail is not preserved locally. But the core research story is already strong:

- the task is useful
- the task is hard
- the model can learn it partially
- the best standalone result now comes from V11
- the best deployment result comes from the hybrid system

That is enough to circulate internally as a serious research draft and enough to convert into a publishable paper once the rank-aware metrics and archival cleanup are finished.

## Appendix A: Metric Snapshot

### Legacy Flat Benchmark

| System | Exact key+value match rate |
|---|---:|
| qmeans | 27.1% |
| Gemma V6 | 40.7% |

### Priority Benchmark

| System | Key F1 | Key+Value F1 |
|---|---:|---:|
| qmeans | 45.50% | 6.00% |
| V7 | 29.09% | 15.52% |
| V8 | 15.88% | 10.72% |
| V9 | 4.75% | 2.69% |
| V10 | 0.00% | 0.00% |
| V11 | 45.44% | 20.26% |
| Hybrid V7 + qmeans | 54.38% | 17.22% |

## Appendix B: Team Takeaway In Plain Language

- We started with ordinary extraction and proved Gemma 4 can beat qmeans on exact matches.
- We then moved to the harder problem of priority-ordered extraction.
- The first useful priority model was V7.
- Aggressive changes in V8, V9, and V10 hurt performance.
- The balanced rollback V11 is now the best standalone priority model.
- The hybrid system is still the best operational system overall.
- The paper story is strong, but the final publication still needs rank-aware metrics and a clean archival position on Gemma 3.