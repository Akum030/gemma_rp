# Priority-Ordered Attribute Extraction From Industrial Search Queries

## Refined Internal Research Draft

Date: 12 May 2026

This document is intended for internal circulation, research discussion, and paper development. All quantitative claims are based on experiment artifacts preserved in this workspace. As a result, the fully auditable experimental record begins with the Gemma 4 training program. Gemma 3 appears in the surviving materials only as exploratory setup context; no scored Gemma 3 benchmark archive is preserved locally, so the Gemma 3 to Gemma 4 transition is described qualitatively rather than as a formal quantitative comparison.

## Abstract

Industrial search queries are short, noisy, and unusually dense with intent. A single query may mention a brand, a product family, a model number, and several technical constraints, yet many extraction systems still reduce such input to an unordered collection of attribute-value pairs. That representation is useful, but it leaves out a layer of structure that matters in practice: which attribute expresses the user's primary intent, which constraints are secondary, and which normalized key names should be preferred for each extracted value.

This work studies that richer formulation as priority-ordered attribute extraction. We cast the task as structured generation with a nested JSON schema in which each extracted value is assigned both an attribute priority and a key-synonym priority list. Using Gemma 4 E4B with LoRA-based fine-tuning, we track the project across a sequence of flat-extraction and priority-oriented runs. The flat-extraction stage already demonstrates practical value by outperforming qmeans on an older exact key+value benchmark. In the priority phase, V7 establishes the first useful structured model, V8 through V10 show that more aggressive supervision strategies can sharply damage recall, and V11 shows that a conservative rollback toward the successful V7 recipe recovers the strongest standalone exact key+value quality observed so far. In parallel, a serving-time hybrid built from V7 plus qmeans produces the best operational key F1.

Taken together, the results suggest that priority-ordered extraction is both useful and substantially harder than ordinary flat extraction. The central difficulty is not merely identifying the correct values. The model must also satisfy a structured output contract, recover attribute order, and choose preferred key orderings. This makes the task a credible research problem in its own right and gives the project a strong paper narrative built around both positive findings and informative negative results.

## 1. Introduction

Industrial search queries rarely arrive in neat, canonical language. They are often fragmented, abbreviated, and packed with multiple signals at once. A query such as `Siemens 1 kW 3 phase servo motor` is not simply a list of facts. It contains an identity cue, a product-type cue, and a set of technical constraints that may not be equally important for retrieval or ranking. Standard attribute extraction systems are usually designed to recover the underlying attribute-value pairs, but they typically stop there. For many downstream systems, that is an incomplete representation of intent.

In practice, search and catalog systems often benefit from knowing more than whether an attribute is present. They benefit from knowing which attribute should be treated as primary, which ones function as supporting constraints, and which canonical key names should be preferred when multiple synonyms are plausible. A representation that preserves this ordering can help retrieval prioritize the right fields, help ranking distinguish between strong and weak signals, and help normalization retain a consistent vocabulary.

This project studies whether that richer structure can be learned directly from search queries. The resulting task is more demanding than flat extraction because the model must jointly solve extraction, normalization, attribute ranking, and synonym-key ranking. The project also raises a practical evaluation question: if the research claim is fundamentally about ranking and structure, then flat precision and recall are necessary but not sufficient to measure success.

The preserved experimental record in this workspace leads to four main contributions. First, it provides a concrete formulation of priority-ordered attribute extraction for industrial search. Second, it establishes that fine-tuned Gemma 4 models can already outperform qmeans on exact key+value quality in a flat extraction setting. Third, it documents a full sequence of priority-specific ablations from V7 through V11, including both successful and unsuccessful design choices. Fourth, it shows that the best standalone model and the best operational system are not the same thing: V11 is the strongest standalone priority model, while a V7 plus qmeans hybrid remains the strongest deployment path on key F1.

## 2. Task Formulation

The central task in this work is to map a user query to a ranked set of extracted attributes. Each extracted attribute contains three pieces of information:

- the value that was extracted from the query,
- the position of that attribute in the overall intent order,
- and the preferred ordering of valid canonical or synonym key names for that value.

The target output is represented as nested JSON. A minimal example is shown below.

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

This formulation is intentionally stricter than ordinary attribute extraction. A prediction is only fully correct if the model extracts the right value, maps it to the correct key family, places it at the correct relative importance level, and ranks the preferred key names in a sensible order. That added structure is what makes the task scientifically interesting, but it is also what makes the task harder to optimize.

## 3. Project Evolution: From Exploratory Gemma 3 Context To An Auditable Gemma 4 Program

The project history includes an early exploratory phase in which Gemma 3 was part of the local tooling context. The surviving evidence for that phase is limited. The workspace still contains setup references for `gemma3:4b` in [setup_ollama.sh](setup_ollama.sh), but it does not contain preserved Gemma 3 fine-tuning scripts, evaluation summaries, or benchmark logs for this task. Because of that, the present paper draft does not claim a formal metric-for-metric Gemma 3 versus Gemma 4 comparison.

By contrast, the Gemma 4 program is fully visible in the preserved files. The training scripts, evaluation summaries, benchmark reports, and inference utilities all point to the Gemma 4 E4B base model. For the purposes of a reproducible research narrative, Gemma 4 is therefore the correct quantitative foundation for the paper.

Within the Gemma 4 program, the work evolved in two stages. The first stage focused on flat extraction. The second stage introduced the ranked priority schema. The flat stage matters because it established that the broader fine-tuning strategy had business relevance before the structured ranking formulation was introduced. The priority stage matters because it exposed the real research difficulty: it is possible to improve structure and still hurt recall, or to preserve recall and still violate the output schema.

## 4. Training Program And Experimental Setup

### 4.1 Model Family And Training Stack

All preserved quantitative experiments in this workspace use Gemma 4 E4B as the base model. Fine-tuning is performed through LoRA-style adapters using Unsloth, Transformers, and TRL in a Tesla T4 environment. Across the run history, the training objective is framed as chat-style structured generation rather than conventional classification or tagging.

### 4.2 Flat Extraction Phase

The flat extraction phase focused on canonical attribute prediction without explicit attribute ranking. The surviving scripts and comparison files show a progression from earlier flat runs to a stronger V6-style setup that combined cleaned flat supervision, gold query data, and motor-domain coverage data. The V6 script in [bee/finetune_gemma4_v6.py](bee/finetune_gemma4_v6.py) also makes the design intent clear: restrict the key space, preserve canonical names, and broaden coverage over important industrial attributes such as phase, horsepower, power, rpm, and mounting type.

This phase answered the first practical question of the project: can fine-tuned Gemma 4 improve over qmeans on exact extraction quality? By the V6 stage, the answer was clearly yes.

### 4.3 Priority-Oriented Phase

The second phase introduced the nested priority schema. The preserved progression is:

- V7, the first useful priority-schema restoration run,
- V8, a larger-capacity priority model with additional gold supervision,
- V9, a stronger accuracy push with heavier gold weighting and a lower learning rate,
- V10, a clean-schema-only run that removes noisy converted data,
- and V11, a conservative rollback toward the V7 recipe with a light clean nested-priority bias.

This sequence is important because it forms a genuine experimental arc rather than a single successful run. V8 through V10 show that more aggressive changes can make the model worse, not better. V11 then shows that the path out of that regression was not to make the training recipe more forceful, but to rebalance it.

### 4.4 V11 Design

The strongest preserved standalone result comes from V11, and the V11 training script in [finetune_gemma4_v11_priority_balanced.py](finetune_gemma4_v11_priority_balanced.py) captures the logic of that design. The guiding hypothesis was that V7 had worked because it preserved broad coverage while using a relatively modest adapter configuration, and that V8 through V10 had moved too far away from that balance.

V11 therefore uses a mixed data recipe:

- nested cat74 priority rows for cleaner schema signal,
- V6 flat-to-nested rows to preserve broad coverage,
- and gold_1k_v2 rows converted to nested form without aggressive oversampling.

Key V11 configuration values are:

- maximum sequence length: 768,
- epochs: 2,
- batch size: 2,
- gradient accumulation: 16,
- learning rate: 7e-5,
- LoRA configuration: r=32, alpha=64.

The broader lesson from V11 is methodological: the strongest standalone result did not come from a more extreme recipe. It came from a more disciplined one.

## 5. Datasets, Benchmarks, And Metrics

The preserved evaluation program uses two benchmark views. The first is a legacy flat benchmark, which compares exact key+value extraction quality against qmeans. The second is the newer 1000-query priority benchmark, which evaluates the ranked structured formulation against gold and qmeans outputs.

The training and evaluation pipeline draws from three main sources: manually curated nested-priority supervision, flat extraction data converted into nested form, and a trusted 1000-query gold set used for both stronger supervision and final benchmarking.

The current evaluator reports:

- key precision, recall, and F1,
- key+value precision, recall, and F1.

These metrics are necessary, but they still under-measure the full research claim. They capture extraction quality, but they do not directly score schema compliance, attribute-order correctness, or key-synonym-order correctness. For publication, the final paper will still need a richer metric stack, including schema compliance rate, attribute top-1 accuracy, pairwise order accuracy, key-synonym top-1 accuracy, key-synonym mean reciprocal rank, and exact structured match rate.

## 6. Results

### 6.1 Early Gemma 4 Flat Extraction Results

An intermediate flat comparison is preserved in [bee/compare_v5_results.txt](bee/compare_v5_results.txt).

| System | KV strict F1 | Value-only F1 | Token F1 |
|---|---:|---:|---:|
| qmeans_v2 | 37.23 | 46.20 | 79.83 |
| V5_flat | 28.05 | 31.27 | 41.99 |

This intermediate result is useful negative evidence. It shows that Gemma 4 did not outperform qmeans immediately. The stronger later result was earned through iteration rather than guaranteed by the model family alone.

The later flat benchmark tells a very different story. From [bee/comparison_summary.csv](bee/comparison_summary.csv):

| System | Exact key+value match rate | Queries with all attributes correct | Queries with zero correct |
|---|---:|---:|---:|
| qmeans | 27.1% | 42 | 415 |
| Gemma V6 | 40.7% | 182 | 332 |

By the V6 stage, fine-tuned Gemma 4 clearly surpassed qmeans on exact key+value matching. That result matters for the paper because it established practical value before the ranked formulation was introduced.

### 6.2 Priority Benchmark Results

The preserved priority benchmark summary is reproduced below from [priority_benchmark_report.md](priority_benchmark_report.md).

| Model | Key Precision | Key Recall | Key F1 | Key+Value Precision | Key+Value Recall | Key+Value F1 |
|---|---:|---:|---:|---:|---:|---:|
| qmeans | 95.95% | 29.82% | 45.50% | 12.66% | 3.93% | 6.00% |
| V7 | 60.49% | 19.15% | 29.09% | 32.28% | 10.22% | 15.52% |
| Hybrid (V7 + qmeans fallback) | 75.60% | 42.46% | 54.38% | 23.94% | 13.44% | 17.22% |
| V8 | 61.12% | 9.12% | 15.88% | 41.25% | 6.16% | 10.72% |
| V9 | 77.55% | 2.45% | 4.75% | 43.88% | 1.39% | 2.69% |
| V10 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| V11 | 79.47% | 31.82% | 45.44% | 35.43% | 14.18% | 20.26% |

Several conclusions follow immediately from this table.

First, V11 is now the best standalone priority model in the preserved experimental record. Its key+value F1 of 20.26% is higher than that of V7, V8, V9, V10, and qmeans. Second, qmeans still retains a narrow standalone lead on key F1: 45.50% versus 45.44%. That difference is now very small, but it remains real. Third, the hybrid system remains the best operational path on key F1 at 54.38%, even though its key+value F1 is below V11. In other words, the strongest standalone model and the strongest deployment system are no longer the same entity.

### 6.3 What The Ablation Sequence Teaches

The V7-to-V11 sequence is valuable because each run teaches something different.

V7 is the first clear proof that the priority formulation can work at all. Even with substantial structure problems, it already beats qmeans on key+value F1. V8 shows that increasing adapter capacity and adding more gold supervision is not enough on its own; recall falls sharply. V9 shows that stronger gold weighting can make that recall collapse even worse. V10 shows that clean-only schema alignment can over-correct to the point that extraction nearly disappears. V11 then demonstrates that the project did not need a more aggressive recipe. It needed a more balanced one.

That pattern gives the work a stronger research narrative than a single successful run would have provided. The negative results are not noise. They clarify where the task is fragile.

## 7. Structural Error Analysis

The priority task is not failing in only one way. The V7 structural diagnostics preserved in [priority_error_analysis_notes.md](priority_error_analysis_notes.md) and [v7_priority_analysis.json](v7_priority_analysis.json) show that semantic signal and structural reliability can diverge.

The most important V7 structural numbers are:

- parsed rate: 80.2%,
- deep-wrapper rate: 71.9%,
- placeholder-key rate: 19.9%,
- empty-flat rate after robust unwrapping: 27.2%.

These numbers matter because they show that the model was often close enough to be useful, but still far enough from the target schema to lose credit under a stricter evaluator. In many cases, the model produced the right semantic fragments but nested them one level too deeply or emitted placeholder-like key labels instead of canonical ones. That is why the work should not be described as a simple recall problem. It is equally a schema-obedience problem.

## 8. Case Study

One preserved example in [split_hybrid_sample.jsonl](split_hybrid_sample.jsonl) captures the promise and the remaining difficulty of the system.

The query is:

`siemens 45 hp 3 phase 1440 rpm motor`

The final hybrid output recovers a clean ranked structure with brand, product type, power, phase, and rpm in sensible order. Its flattened output is:

- brand = siemens
- part type = motor
- power = 45 hp
- phase = 3 phase
- rpm = 1440 rpm

The corresponding preserved raw V7 output is revealing. After parsing, V7 contains essentially the same semantic content, but the raw structure still carries extra nested wrappers under `attribute_priorityN`. qmeans, on the other hand, retrieves most of the relevant values very quickly, but weakens the product-type interpretation in this example by assigning `part type = 3 phase`.

This case study is useful because it illustrates the exact pattern that recurs throughout the project. The structured model contains value. The value is not always visible unless the evaluator and serving path are robust enough to recover it cleanly.

## 9. What The Project Has Already Solved

The work has already resolved several important questions.

First, it has defined a clear formulation of priority-ordered attribute extraction for industrial search queries. That formulation is specific enough to train, evaluate, and analyze, yet general enough to matter beyond this single dataset.

Second, it has answered the feasibility question for fine-tuned Gemma 4 models. The flat benchmark shows that the model family can outperform qmeans on exact key+value quality in a meaningful setting.

Third, it has established a strong standalone priority model. V11 is no longer only a recovery run; it is the best standalone priority result preserved in the repo.

Fourth, it has identified the strongest practical system. The hybrid serving path demonstrates that the structured signal from V7 can be combined with qmeans coverage to outperform either standalone system on key F1.

Finally, it has built the supporting research infrastructure: evaluator repairs, benchmark rollups, structural diagnostics, reporting artifacts, and example inference paths. That infrastructure is part of the contribution because it makes the project analyzable rather than anecdotal.

## 10. What Remains Open

The project is in a strong internal state, but it is not yet fully publication-ready.

The most immediate limitation is evaluation. The current metric stack still measures extraction more directly than it measures ranking. For a paper built around priority order and synonym-key order, that is a material gap.

The second limitation is archival completeness. A formal Gemma 3 versus Gemma 4 table cannot yet be defended from the preserved evidence, because the workspace does not contain audited Gemma 3 benchmark artifacts.

The third limitation is that qmeans still retains a slight standalone lead on key F1, even though V11 has moved much closer than the earlier priority runs and clearly surpasses qmeans on key+value F1.

None of these limitations undermine the research direction. They simply define the remaining work needed for external submission.

## 11. Publication Readiness

If this work is to move from an internal draft to a publishable paper, the next steps should be precise.

The final paper should add four evaluation layers that are still missing or incomplete in the current benchmark:

- schema compliance,
- attribute-order correctness,
- key-synonym-order correctness,
- and exact structured match.

It should also either recover the missing Gemma 3 benchmark archive or explicitly scope the paper as a Gemma 4 study with Gemma 3 treated only as exploratory context. The second option is already defensible today; the first would only strengthen the historical framing.

## 12. Conclusion

The preserved evidence now supports a coherent and credible research story. The project begins with flat extraction, where fine-tuned Gemma 4 eventually surpasses qmeans on exact key+value matching. It then moves into the harder problem of priority-ordered structured extraction, where early success in V7 is followed by a sequence of negative ablations that expose the fragility of the task. V11 closes that arc by showing that a conservative rollback strategy can recover the strongest standalone result in the project, while the hybrid serving path continues to offer the strongest operational key F1.

That combination of results is scientifically useful. It shows that the task is real, that the task is hard, and that progress depends on balancing coverage, schema obedience, and ranking behavior rather than maximizing any one of them in isolation. With a richer metric stack and a cleaner archival position on the early Gemma 3 phase, this work is well positioned to become a publishable paper.

## Appendix A. Metric Snapshot

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

## Appendix B. Internal Summary In Plain Language

The project started by asking whether fine-tuned Gemma could beat qmeans on extraction quality at all. By the V6 stage, the answer was yes. It then moved to the harder problem of priority-ordered extraction, where the first usable structured model was V7. The next three priority runs made it clear that simply increasing capacity or forcing cleaner supervision was not enough and could easily damage recall. V11 showed that the recovery path was to return to a better-balanced recipe. Today, V11 is the best standalone priority model in the workspace, while the hybrid system remains the best operational path overall.