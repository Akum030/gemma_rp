# Priority-Ordered Attribute Extraction For Industrial Search Queries

## Readable Internal Draft

Date: 12 May 2026

## Executive Summary

This project studies a harder version of product attribute extraction for industrial search queries. Instead of extracting only an unordered list of attributes such as brand, model, power, or phase, the goal is to understand which attribute matters first, which one matters next, and which canonical key name should be preferred for each extracted value.

That difference matters in real search systems. A user query such as `siemens 45 hp 3 phase 1440 rpm motor` is not just a bag of words. It contains a main product identity, supporting technical constraints, and multiple valid interpretations of key names. The project tries to capture that richer intent directly.

The preserved evidence in this repository now supports a complete internal story. Early Gemma 4 experiments started as noisy flat extraction systems with good value recovery but weak canonical key control. Later flat experiments improved that control enough to beat qmeans on exact key+value quality. After that, the work moved to the harder priority-ordered formulation, where V7 became the first useful structured model, V8 through V10 became meaningful negative ablations, and V11 recovered the best standalone priority result through a balanced rollback strategy.

Today, the project has three strong outcomes:

1. Gemma 4 has already beaten qmeans on flat exact key+value extraction in the preserved benchmark.
2. V11 is now the best standalone priority-ordered model in the repository.
3. A hybrid of V7 plus qmeans remains the strongest operational serving path on key F1.

## What Problem We Are Solving

Typical extraction systems answer the question: which attributes are present?

This project answers a harder question:

1. which attributes are present,
2. which attribute is most important for user intent,
3. which key name should be preferred first for that value,
4. which alternate key names are still valid fallbacks.

That means the output is not just flat JSON. It is a ranked structure. A typical target looks like this:

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

This is why the task is harder than ordinary extraction. The model has to recover semantic content, obey structure, rank attributes, and rank key synonyms at the same time.

## Honest Gemma 3 Versus Gemma 4 Position

The user asked for Gemma 3 and Gemma 4 comparison, so the honest position needs to be stated clearly.

Gemma 3 is part of the project history, but not part of the preserved quantitative evidence. The repository still contains exploratory setup context for Gemma 3 in [setup_ollama.sh](setup_ollama.sh), including an `ollama pull gemma3:4b` path. However, this repository does not preserve Gemma 3 fine-tuning scripts, benchmark logs, or evaluation summaries for this task.

Gemma 4 E4B is different. The full auditable experiment trail in this repository is based on Gemma 4 E4B. The training scripts, benchmark artifacts, evaluator, rollups, and final summaries all belong to that model family.

So the correct statement is:

Gemma 3 was exploratory context. Gemma 4 is the quantitative research program preserved in the repository.

That is the defensible way to compare them without inventing missing metrics.

## How The Gemma 4 Training Journey Actually Evolved

### 1. Early Gemma 4 Phase: V3b

The earliest preserved Gemma 4 training script is [bee/finetune_v3.py](bee/finetune_v3.py). It trains Gemma 4 E4B on flat JSON extraction using `product_train_with_keys.jsonl` and `product_val_with_keys.jsonl`. The saved artifact path in that script points to `gemma4-v3b`, so this is best understood as the preserved V3b stage.

This stage was important because it proved the model could already recover many correct values from industrial queries. But it also exposed a major weakness: open-key drift.

The evidence for that is preserved in:

- [bee/compare_v3b_vs_qmeans_vs_gold.txt](bee/compare_v3b_vs_qmeans_vs_gold.txt)
- [bee/compare_v3b_norm.txt](bee/compare_v3b_norm.txt)
- [bee/compare_full_1k.txt](bee/compare_full_1k.txt)

The early V3b story is:

- raw V3b parse rate: 63.5% on the 98-query gold comparison,
- raw V3b unique keys: 273,
- raw V3b canonical-vocabulary share: 59.4%,
- raw V3b key F1: 13.7%,
- raw V3b value exact: 57.2%,
- raw V3b value substring: 90.2%.

That combination is extremely important. It means the early model was not semantically empty. It was often finding the right values, but expressing them through too many inconsistent key names.

After normalization, the same model became much more disciplined:

- normalized V3b unique keys: 32,
- normalized V3b canonical-vocabulary share: 100.0%,
- normalized V3b key F1: about 20.4% to 20.5%,
- normalized V3b value exact: 50.2% on the 98-query slice and 42.5% on the full 1k view.

So V3b taught the project a foundational lesson: semantic value recovery can appear before canonical key control.

### 2. V5: Flat JSON Became Simpler And More Controlled

The next major preserved flat step is [bee/finetune_gemma4_v5_flat.py](bee/finetune_gemma4_v5_flat.py). This version simplified the task deliberately. Instead of a more complex structure, it asked the model to emit simple flat JSON using IndiaMART-style keys. It also converted cat74 motor-domain data into flat examples to add stronger domain coverage.

The preserved V5 comparison in [bee/compare_v5_results.txt](bee/compare_v5_results.txt) shows that this phase improved the setup, but still did not beat qmeans:

| System | KV strict F1 | Value-only F1 | Token F1 |
|---|---:|---:|---:|
| qmeans_v2 | 37.23 | 46.20 | 79.83 |
| V5_flat | 28.05 | 31.27 | 41.99 |

So V5 was a meaningful transition stage, but not yet a final win.

### 3. V6: Gemma 4 Beat Qmeans On Exact Key+Value Quality

The next major flat step is [bee/finetune_gemma4_v6.py](bee/finetune_gemma4_v6.py). V6 tightened the problem more aggressively by using a strict canonical key set, remapping noisy keys into that set, and incorporating `gold_1k_v2` supervision.

The result, preserved in [bee/comparison_summary.csv](bee/comparison_summary.csv), is one of the most important milestones in the repository:

| System | Exact key+value match rate | Queries with all attributes correct | Queries with zero correct |
|---|---:|---:|---:|
| qmeans | 27.1% | 42 | 415 |
| Gemma V6 | 40.7% | 182 | 332 |

This is where the project stopped being only exploratory. By V6, fine-tuned Gemma 4 had clearly beaten qmeans on the preserved flat exact key+value benchmark.

### 4. V7: The First Useful Priority-Ordered Model

Once flat extraction had become competitive, the project moved to the harder structured task: priority-ordered extraction.

V7 was the first useful model in that new formulation. It proved that the ranked nested output was learnable at all. It did not beat qmeans on every flat metric, but it established a real structured baseline.

On the current trusted priority benchmark, the corrected V7 metrics are:

- key F1: 29.09%
- key+value F1: 15.52%

V7 also exposed structural failure modes such as deep wrappers and placeholder keys. Those errors mattered because they showed that the task difficulty was not only about missing values. It was also about schema obedience.

### 5. V8, V9, V10: Negative Results That Strengthened The Research Story

The next three runs are valuable precisely because they did not improve the system.

- V8 increased capacity and gold supervision, but key F1 fell to 15.88% and key+value F1 fell to 10.72%.
- V9 pushed gold weighting harder, and recall collapsed even further. Key F1 fell to 4.75% and key+value F1 fell to 2.69%.
- V10 pursued clean-schema-only alignment and collapsed completely, reaching 0.00% for both key F1 and key+value F1.

These are not useless failures. They show that more aggressive supervision was not the right answer for this problem. They make the paper stronger because they identify which intuitive design choices were actually harmful.

### 6. V11: The Balanced Rollback That Recovered The Best Standalone Result

The V11 recipe, preserved in [finetune_gemma4_v11_priority_balanced.py](finetune_gemma4_v11_priority_balanced.py), took a different path. Instead of escalating supervision again, it rolled back toward the broad-coverage discipline that had helped V7, but with a lighter clean-schema bias.

The final V11 result is now preserved in [v11_eval_summary.json](v11_eval_summary.json).

V11 metrics:

- key precision: 79.47%
- key recall: 31.82%
- key F1: 45.44%
- key+value precision: 35.43%
- key+value recall: 14.18%
- key+value F1: 20.26%

That makes V11 the best standalone priority model in the repository.

## Current Best Results In One Place

### Flat Extraction Milestone

Gemma V6 beats qmeans on exact key+value match rate:

- qmeans: 27.1%
- Gemma V6: 40.7%

### Priority Extraction Milestone

Current priority benchmark summary:

| Model | Key F1 | Key+Value F1 |
|---|---:|---:|
| qmeans | 45.50% | 6.00% |
| V7 | 29.09% | 15.52% |
| Hybrid V7 + qmeans | 54.38% | 17.22% |
| V8 | 15.88% | 10.72% |
| V9 | 4.75% | 2.69% |
| V10 | 0.00% | 0.00% |
| V11 | 45.44% | 20.26% |

These numbers support two different conclusions:

1. V11 is the best standalone priority model.
2. The hybrid V7 plus qmeans path is still the best operational system on key F1.

That distinction is important and should be stated clearly in any team presentation.

## Priority-Order Attribute Problems We Have Already Solved

The user asked specifically for the problems solved in this project, so they are listed directly here.

### 1. We Defined A Clear Priority-Ordered Extraction Problem

The work moved beyond ordinary flat extraction and defined a structured problem where attribute importance and key-synonym preference are both explicit outputs.

### 2. We Showed That Query Intent Can Be Represented As Ordered Structure

The system is no longer forced to treat all extracted attributes as equally important. That is a meaningful advance for industrial search understanding.

### 3. We Reduced Open-Key Drift

The V3b evidence makes this especially clear. Early Gemma 4 outputs had strong semantic value recovery but weak key control. Later stages progressively forced the model into a more stable canonical vocabulary.

### 4. We Proved Gemma 4 Can Beat Qmeans On Exact Key+Value Quality

This happened by the V6 stage and is one of the strongest practical outcomes in the repository.

### 5. We Built A Real Standalone Priority Model

V11 now proves that priority-ordered extraction is not only an idea. It is a working standalone system with meaningful performance.

### 6. We Built A Stronger Serving Path Through Hybrid Inference

The hybrid V7 plus qmeans path shows that the project can deliver better operational performance even before every part of the standalone research problem is fully complete.

### 7. We Built The Research Infrastructure Around The Modeling Work

The project now has evaluator logic, structural diagnostics, benchmark rollups, senior-facing updates, live monitoring, and research drafts. That makes it a coherent research program rather than a loose folder of experiments.

## What Still Remains Open

The work is strong internally, but three things still remain before it is fully publication-ready.

### 1. Rank-Aware Metrics Are Still Missing

The current evaluator reports flat key and key+value quality well, but it does not yet fully measure whether attribute order and key-synonym order are correct. A publication-ready paper should add:

- attribute top-1 correctness
- pairwise order accuracy
- key-synonym top-1 accuracy
- key-synonym MRR
- exact structured match

### 2. Structural Metrics Need To Become Headline Results

The current structural diagnostics are meaningful, but they still live more as supporting evidence than as primary reported metrics. That should change.

### 3. The Gemma 3 Archive Is Still Missing

If the team wants a scored Gemma 3 versus Gemma 4 comparison in the final paper, those older benchmark artifacts must be recovered. Otherwise the honest paper should explicitly state that Gemma 3 is project history and Gemma 4 is the audited study.

## Recommended Internal Team Wording

If this needs to be explained simply to the team, the clearest wording is:

This project began with exploratory Gemma 3 setup work, but the preserved quantitative study starts with Gemma 4 E4B. Early Gemma 4 runs showed strong value understanding but noisy key naming. Later flat runs progressively improved canonical control, and by V6 Gemma 4 had already beaten qmeans on exact key+value extraction. The work then moved to the harder priority-ordered task, where V7 became the first useful structured model, V8 through V10 showed that aggressive supervision could hurt performance badly, and V11 recovered the best standalone result through a more balanced recipe. Today, V11 is the strongest standalone priority model, while the hybrid V7 plus qmeans system remains the strongest operational path.

## Final Team Takeaway

The most important message is that the project now has a complete and believable story.

It is not a story where the model simply improved every week in a straight line. It is a story where:

- the early model understood values before it understood canonical control,
- flat extraction became strong enough to beat qmeans,
- structured priority extraction became possible but fragile,
- aggressive changes caused negative ablations,
- a balanced rollback finally produced the best standalone model.

That is exactly the kind of experimental history that supports a credible research paper and a strong internal presentation.