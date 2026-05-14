# Priority-Ordered Attribute Extraction From Industrial Search Queries

## Full Internal Research Draft

Date: 12 May 2026

## Abstract

Industrial search queries are compact, noisy, and densely expressive. A short query may combine a brand, a product family, a model identifier, and several technical constraints, yet many extraction systems still reduce such input to an unordered set of attribute-value pairs. That representation is useful, but incomplete. In practical search and catalog systems, it often matters not only which attributes are present, but also which attribute expresses the user's main intent and which canonical key names should be preferred for each extracted value.

This work studies that richer formulation as priority-ordered attribute extraction. We model the task as structured generation with a nested JSON schema in which each extracted value is assigned both an attribute priority and a key-synonym priority list. Using Gemma 4 E4B with LoRA-based fine-tuning, we track the system across a sequence of flat-extraction and priority-oriented runs. The earlier flat-extraction stage already demonstrates business relevance by outperforming qmeans on an older exact key+value benchmark. In the priority phase, V7 establishes the first useful structured model, V8 through V10 show that more aggressive supervision strategies can sharply damage recall, and V11 shows that a conservative rollback toward the successful V7 recipe recovers the strongest standalone exact key+value quality observed so far. In parallel, a serving-time hybrid built from V7 plus qmeans yields the best operational key F1.

The resulting picture is both practical and scientifically useful. Priority-ordered extraction appears valuable, but it is materially harder than ordinary flat extraction because the model must solve extraction, schema obedience, attribute ordering, and key-synonym ordering at the same time. The project therefore supports a credible research paper built on both positive findings and informative negative ablations.

## 1. Introduction

Industrial search queries rarely arrive in clean, canonical form. They are often abbreviated, partially normalized, and packed with more than one kind of signal. A query such as `Siemens 1 kW 3 phase servo motor` contains a brand cue, a product-type cue, and two technical constraints, but it does not present them as separate fields. A standard extractor can recover the underlying attribute-value pairs, yet many downstream systems need more than that. They need to know which attribute should dominate retrieval, which attributes are secondary filters, and which key names should be treated as the preferred normalized interpretation.

This work is motivated by exactly that gap. In production search systems, an unordered list of extracted attributes is often a useful intermediate representation, but it does not fully capture user intent. If the query mixes identity signals, product family cues, and technical constraints, then the relative order of those signals can matter for ranking, normalization, and query rewriting. A representation that preserves this ordering is therefore attractive both as a research problem and as a practical system component.

The project asks whether that richer structure can be learned directly from user queries. The answer is not trivial. Once the task is defined as structured generation, the model must do more than recover the right values. It must also obey a nested output schema, place attributes in a reasonable order of importance, and choose sensible key-synonym orderings for each value. This creates a learning problem that is substantially harder than ordinary flat extraction.

The experimental record preserved in this repository supports four main claims. First, fine-tuned Gemma 4 models can already outperform qmeans on exact key+value quality in a flat extraction setting. Second, the priority-ordered formulation is learnable, but fragile. Third, stronger supervision or cleaner data is not automatically helpful; in fact, several seemingly reasonable design changes reduce recall dramatically. Fourth, the best standalone model and the best operational system are not the same thing: V11 is the strongest standalone priority model, while a V7 plus qmeans hybrid remains the best deployment path on key F1.

## 2. Related Work And Positioning

This project sits at the intersection of several existing research areas: slot filling, structured natural language understanding, product attribute extraction, query understanding in commerce search, and LLM-based normalization. Prior work has already shown that product attributes can be extracted from titles, profiles, and search queries, and that pretrained language models can be effective for joint structured prediction tasks. However, the specific formulation studied here is narrower and more structured than the standard settings in that literature.

The most relevant nearby work includes OpenTag for open attribute-value extraction from product profiles, BERT-based studies of joint intent and slot modeling, work on explicit attribute extraction in e-commerce search, and recent work on LLM-based extraction and normalization of product attributes. Those strands are clearly related, but none of them directly matches the formulation used here. The contribution in this project is not simply attribute extraction, nor only normalization. It is the joint prediction of extracted values, attribute priority order, and key-synonym priority order in a single structured output.

For that reason, the safest positioning claim is also the strongest one: explicit modeling of both attribute order and synonym-key order for industrial search queries appears underexplored. The project should not claim a world-first result without a broader formal literature audit, but it can credibly claim to address a narrowly defined structured prediction problem that is not well represented in the existing extraction literature.

## 3. Task Definition

The goal is to map a user query to a ranked set of extracted attributes. Each attribute must contain three elements:

1. the extracted value,
2. its relative position in the overall intent order,
3. an ordered list of valid canonical or synonym key names.

The target output is represented as nested JSON. A minimal illustration is shown below.

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

This definition is intentionally strict. A prediction is only fully correct if the model extracts the right value, aligns it with the right key family, places it at the right relative level of importance, and ranks the preferred key names in a reasonable order. The difficulty of the task lies precisely in the fact that these decisions are coupled.

## 4. Model History And Experimental Setting

### 4.1 Historical Note On Gemma 3 And Gemma 4

Early exploratory work around this project included Gemma 3 in the local tooling context. The surviving evidence for that phase is limited to setup references such as [setup_ollama.sh](setup_ollama.sh), which includes a local `gemma3:4b` pull path. However, the repository does not preserve Gemma 3 fine-tuning scripts, evaluation summaries, or benchmark logs for this task. Because of that, this draft does not present a metric-for-metric Gemma 3 versus Gemma 4 comparison.

The fully auditable experimental program begins with Gemma 4 E4B. All preserved training scripts, benchmark summaries, and inference utilities in this repository are based on that model. In practical terms, that means the paper's quantitative narrative is a Gemma 4 narrative, even though Gemma 3 remains part of the broader project history.

### 4.2 Training Stack

All preserved quantitative experiments in this repository use Gemma 4 E4B as the base model and fine-tune it through LoRA-style adapters with Unsloth, Transformers, and TRL. The training objective is framed as chat-style structured generation. Across runs, the model is trained either to emit flat attribute JSON or the later nested priority schema, depending on the phase of the project.

### 4.3 Data Sources

The experimental pipeline draws from three main sources:

- manually curated nested-priority supervision,
- flat extraction data converted into nested form,
- and a trusted 1000-query gold set used for stronger supervision and final evaluation.

The flat phase emphasized canonical key control and broad coverage. The later priority phase emphasized structured supervision and ranked output consistency.

### 4.4 Experiment Sequence

The preserved Gemma 4 sequence can be read in two stages. The first stage focuses on flat extraction and leads to a strong V6 system. The second stage introduces priority-ordered extraction and includes the following major runs:

- V7, the first useful priority-schema restoration run,
- V8, a larger-capacity priority model with additional gold supervision,
- V9, a stronger accuracy push with heavier gold weighting and lower learning rate,
- V10, a clean-schema-only priority run,
- V11, a conservative rollback toward the successful V7 recipe with a light clean nested-priority bias.

This sequence matters because it forms a true ablation program rather than a collection of disconnected experiments. Several runs failed in instructive ways, and those failures shaped the final design.

### 4.5 V11 Design

V11 is the strongest standalone priority result in the repository, and its design is important because it did not emerge from a more aggressive recipe. Instead, it emerged from a more balanced one. The working hypothesis behind V11 was that V7 had been successful because it preserved broad coverage while using a relatively modest adapter configuration, whereas V8 through V10 had drifted too far toward either heavier supervision or overly clean structure.

V11 therefore combines nested cat74 priority rows for cleaner schema signal, V6 flat-to-nested rows for coverage, and gold_1k_v2 rows converted into nested form without aggressive oversampling. The configuration preserved in [finetune_gemma4_v11_priority_balanced.py](finetune_gemma4_v11_priority_balanced.py) uses a maximum sequence length of 768, two epochs, batch size 2, gradient accumulation 16, learning rate 7e-5, and a LoRA configuration of r=32 and alpha=64. The broader lesson from V11 is methodological: the best standalone result came from restraint, not escalation.

## 5. Benchmarks And Metrics

The current experimental program uses two benchmark views. The first is a legacy flat benchmark that compares exact key+value quality against qmeans. The second is a newer 1000-query priority benchmark that evaluates ranked structured predictions against gold and qmeans outputs.

The current evaluator reports key precision, recall, and F1 together with key+value precision, recall, and F1. These metrics are indispensable because they preserve comparability with qmeans and with earlier baselines. At the same time, they are not yet sufficient to evaluate the full research claim. A paper centered on priority order and key-synonym order should eventually report schema compliance, attribute-order correctness, key-synonym-order correctness, and exact structured match in addition to flat extraction quality. That richer metric stack remains future work, but the current results are already strong enough to support an internal research narrative.

## 6. Results

### 6.1 Early Gemma 4 Flat Extraction Results

An intermediate flat comparison is preserved in [bee/compare_v5_results.txt](bee/compare_v5_results.txt).

| System | KV strict F1 | Value-only F1 | Token F1 |
|---|---:|---:|---:|
| qmeans_v2 | 37.23 | 46.20 | 79.83 |
| V5_flat | 28.05 | 31.27 | 41.99 |

This intermediate result is important because it shows that Gemma 4 did not begin with a clear lead. The later gains were achieved through iteration rather than inherited automatically from the model family.

The later flat benchmark, preserved in [bee/comparison_summary.csv](bee/comparison_summary.csv), tells a different story.

| System | Exact key+value match rate | Queries with all attributes correct | Queries with zero correct |
|---|---:|---:|---:|
| qmeans | 27.1% | 42 | 415 |
| Gemma V6 | 40.7% | 182 | 332 |

By the V6 stage, fine-tuned Gemma 4 clearly surpassed qmeans on exact key+value matching. This result matters because it established practical value before the ranked priority formulation was introduced.

### 6.2 Priority Benchmark Results

The current priority benchmark summary from [priority_benchmark_report.md](priority_benchmark_report.md) is reproduced below.

| Model | Key Precision | Key Recall | Key F1 | Key+Value Precision | Key+Value Recall | Key+Value F1 |
|---|---:|---:|---:|---:|---:|---:|
| qmeans | 95.95% | 29.82% | 45.50% | 12.66% | 3.93% | 6.00% |
| V7 | 60.49% | 19.15% | 29.09% | 32.28% | 10.22% | 15.52% |
| Hybrid (V7 + qmeans fallback) | 75.60% | 42.46% | 54.38% | 23.94% | 13.44% | 17.22% |
| V8 | 61.12% | 9.12% | 15.88% | 41.25% | 6.16% | 10.72% |
| V9 | 77.55% | 2.45% | 4.75% | 43.88% | 1.39% | 2.69% |
| V10 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| V11 | 79.47% | 31.82% | 45.44% | 35.43% | 14.18% | 20.26% |

Two results define the current state of the project. The first is that V11 is now the best standalone priority model in the repository. Its key+value F1 of 20.26% is better than that of V7, V8, V9, V10, and qmeans. The second is that the hybrid V7 plus qmeans system remains the strongest operational path on key F1 at 54.38%. In other words, the strongest standalone model and the strongest deployment system are not the same thing.

It is also worth noting how narrow the remaining standalone gap has become. qmeans still holds a slight lead on key F1, at 45.50% versus 45.44% for V11, but the gap is now marginal. On exact key+value quality, however, V11 is clearly ahead.

### 6.3 What The Ablation Sequence Shows

The V7-to-V11 sequence is useful precisely because it includes unsuccessful runs. V7 establishes that the priority formulation can work at all. V8 shows that increasing capacity and injecting more gold supervision does not automatically improve the model. V9 shows that pushing gold weighting more aggressively can collapse recall even further. V10 shows that clean-only alignment can over-correct so strongly that extraction nearly disappears. V11 then shows that the correct response to those failures was not a more forceful recipe, but a better-balanced one.

This sequence gives the work a much stronger research character than a single winning model would have provided. It demonstrates not only where the model succeeds, but also which intuitively reasonable choices turn out to be counterproductive.

## 7. Structural Error Analysis

The project’s most important qualitative insight is that the priority problem is not only a coverage problem. It is also a structure problem. The V7 diagnostics preserved in [priority_error_analysis_notes.md](priority_error_analysis_notes.md) and [v7_priority_analysis.json](v7_priority_analysis.json) show that semantic signal and structural reliability can diverge sharply.

The most informative V7 structural numbers are:

- parsed rate: 80.2%,
- deep-wrapper rate: 71.9%,
- placeholder-key rate: 19.9%,
- empty-flat rate after robust unwrapping: 27.2%.

These numbers show that the model was often close enough to be useful while still far enough from the target schema to lose credit under a stricter evaluator. In many cases, the right semantic fragments were present, but they were wrapped too deeply, attached to placeholder-like key labels, or flattened incorrectly unless the evaluator handled them carefully. That is why it is misleading to describe the task as merely one of recall. Schema obedience is a first-class challenge in its own right.

## 8. Case Study

The example preserved in [split_hybrid_sample.jsonl](split_hybrid_sample.jsonl) offers a concrete illustration of both the promise and the remaining difficulty of the system. The query is:

`siemens 45 hp 3 phase 1440 rpm motor`

The final hybrid output recovers a clean ranked structure with brand, product type, power, phase, and rpm in sensible order. When flattened, the output becomes:

- brand = siemens,
- part type = motor,
- power = 45 hp,
- phase = 3 phase,
- rpm = 1440 rpm.

The preserved raw V7 output for the same query contains essentially the same semantic content, but it also includes the extra nested wrappers that became one of the project’s recurring structural failure modes. qmeans, by contrast, recovers most of the relevant values quickly, but weakens the part-type interpretation in this example by assigning `part type = 3 phase`.

This example captures the central pattern of the project. The structured model often contains valuable signal, but that signal is not always visible unless the evaluator and serving path are designed to recover it faithfully.

## 9. What The Project Has Already Solved

The work has already answered several important questions. It has defined a concrete formulation of priority-ordered attribute extraction for industrial search queries. It has shown that fine-tuned Gemma 4 models can outperform qmeans on exact key+value quality in a flat extraction setting. It has established a strong standalone priority model in V11. It has also identified a stronger system-level deployment path in the V7 plus qmeans hybrid.

Just as importantly, the project has built the surrounding research infrastructure needed to make those claims meaningful: a repaired evaluator, consolidated benchmark rollups, structural diagnostics, senior-facing reporting artifacts, and live inference utilities. Those artifacts matter because they transform the project from a set of promising runs into a coherent experimental program.

## 10. What Remains Open

The project is in a strong internal state, but it is not yet ready to be presented as a finished external paper.

The first limitation is evaluation. The current metric stack still measures extraction quality more directly than it measures ranking behavior. For a paper centered on priority order and key-synonym order, that is the most important remaining technical gap.

The second limitation is archival completeness. A formal Gemma 3 versus Gemma 4 results table cannot yet be defended from the evidence preserved in this repository. If the team wants that comparison in the final paper, the missing Gemma 3 benchmark artifacts will need to be recovered.

The third limitation is that qmeans still holds a slight standalone lead on key F1, even though V11 has moved very close and clearly surpasses qmeans on key+value F1.

None of these limitations invalidate the work. They simply mark the boundary between a strong internal draft and a submission-ready paper.

## 11. Publication Readiness

The remaining path to publication is clear. The final paper should add formal structure metrics, direct ranking metrics, and exact structured match. It should also take one of two archival positions on the model history: either recover the missing Gemma 3 benchmark trail, or state explicitly that the quantitative paper is a Gemma 4 study with Gemma 3 treated as exploratory context. The second option is already defensible today; the first would make the historical arc stronger.

## 12. Conclusion

The evidence preserved in this repository now supports a coherent research story. The project begins with flat extraction, where fine-tuned Gemma 4 eventually surpasses qmeans on exact key+value matching. It then moves into the harder problem of priority-ordered structured extraction, where early success in V7 is followed by a sequence of negative ablations that expose the fragility of the task. V11 closes that arc by showing that a conservative rollback strategy can recover the strongest standalone result in the project, while the hybrid serving path continues to provide the strongest operational key F1.

That combination of results is scientifically useful. It shows that the task is real, that the task is difficult, and that progress depends on balancing coverage, structure, and ranking behavior rather than maximizing any one of them in isolation. With a richer metric stack and a cleaner archival position on the early Gemma 3 phase, this work is well positioned to become a publishable paper.

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

The project began by asking whether fine-tuned Gemma 4 could beat qmeans on extraction quality at all. By the V6 stage, the answer was yes. The work then moved to the harder problem of priority-ordered extraction, where V7 became the first useful structured model. The next three priority runs made it clear that simply increasing capacity or forcing cleaner supervision could easily damage recall. V11 showed that the recovery path was to return to a better-balanced recipe. Today, V11 is the strongest standalone priority model in the repository, while the hybrid system remains the strongest operational path overall.