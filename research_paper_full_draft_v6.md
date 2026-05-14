# Priority-Ordered Attribute Extraction From Industrial Search Queries

## Full Internal Research Draft

Date: 12 May 2026

## Abstract

Industrial search queries are short, noisy, and dense with intent. A single query may contain a brand, a product family, a model identifier, and several technical constraints, but many extraction pipelines still reduce that input to an unordered list of attributes. That representation is useful, yet incomplete. In real search systems, it often matters which attribute is primary, which attributes are secondary, and which canonical key names should be preferred for each extracted value.

This draft presents the full internal research story for that problem. The project began with exploratory Gemma 3 setup work, but the preserved quantitative program starts with Gemma 4 E4B and spans three distinct phases: early open-key flat extraction, canonical flat extraction, and finally priority-ordered structured extraction. The earliest preserved Gemma 4 model, V3b, already showed strong value recovery but large key drift. The next flat runs, V5 and V6, progressively tightened canonical key control, and by V6 the fine-tuned Gemma 4 system clearly surpassed qmeans on an exact key+value benchmark. The work then moved to the harder priority-ordered task, where V7 became the first useful structured model, V8 through V10 exposed the fragility of more aggressive supervision strategies, and V11 recovered the best standalone priority result through a conservative rollback toward the successful V7 recipe.

The result is a research narrative that is both practical and scientifically credible. The project has already solved several important problems: it has shown how to move from unordered extraction to intent-aware ranked structure, how to reduce open-key drift, how to recover a strong standalone priority model, and how to combine structured model behavior with qmeans coverage in a stronger hybrid serving path. At the same time, the negative ablations are meaningful. They show that priority-ordered extraction is materially harder than flat extraction because the model must learn semantic recovery, schema obedience, attribute ordering, and key-synonym ordering together.

## 1. Introduction

Industrial B2B search queries rarely arrive in a clean or canonical form. They are often abbreviated, partially normalized, and compressed into a few tokens. A short query such as `Siemens 1 kW 3 phase servo motor` contains brand, product-type, and technical-constraint information, but none of those fields are explicitly separated. Any search system that wants to interpret such a query has to infer structure that the user never wrote down directly.

Traditional attribute extraction addresses part of that problem by recovering a set of key-value pairs. That is already useful, but it is often not sufficient for search, ranking, query rewriting, or catalog normalization. When a user writes `Siemens 45 hp 3 phase 1440 rpm motor`, the system may need to know not just that those fields are present, but that the query is centrally about a motor, that brand is a strong identity cue, and that the technical values should be treated as secondary but still important constraints. The order of those signals matters.

This project studies that richer formulation as priority-ordered attribute extraction. The system does not merely extract values. It must also assign each extracted value a relative position in the intent order and an ordered list of key names that represent the preferred normalized interpretation. That makes the task substantially harder than ordinary flat extraction. The model has to solve semantics and structure at the same time.

The repository now preserves enough evidence to tell a coherent story from beginning to end. The story is not one of smooth monotonic improvement. It begins with noisy open-key outputs, moves through a period of increasingly disciplined canonical flat extraction, and then enters a priority-structured phase where some seemingly reasonable design choices fail badly. That failure pattern turns out to be one of the strongest parts of the research story because it clarifies where the real difficulty lies.

## 2. Research Question And Contribution

The core research question is straightforward: can an LLM-based extractor learn not only which attributes are present in an industrial search query, but also the relative order of those attributes and the preferred order of canonical key names for each extracted value?

The contribution is narrower than a general product extraction paper and more specific than standard slot filling. This work is not just about attribute identification. It is about joint prediction of:

1. extracted attribute values,
2. global attribute priority order,
3. local key-synonym priority order,
4. valid structured JSON under a nested schema.

That combination appears underexplored in the e-commerce and query-understanding literature, especially for industrial queries where product identity and technical constraints are frequently mixed together.

## 3. Honest Scope: Gemma 3 Versus Gemma 4

One of the repeated requirements for this draft was to compare Gemma 3 and Gemma 4 honestly. The preserved repository evidence supports a qualitative comparison, but not a defensible metric-for-metric benchmark table.

| Dimension | Gemma 3 | Gemma 4 E4B |
|---|---|---|
| Preserved evidence in repo | Exploratory setup context only | Full training, evaluation, and reporting trail |
| Concrete artifact | [setup_ollama.sh](setup_ollama.sh) with `ollama pull gemma3:4b` | Multiple fine-tuning scripts, evaluation scripts, benchmark summaries, and reports |
| Fine-tuning scripts archived | No | Yes |
| Benchmark logs archived | No | Yes |
| Defensible quantitative comparison today | No | Yes |
| Role in paper | Historical context | Audited experimental platform |

The practical meaning of that table is simple. Gemma 3 belongs to the project history, but Gemma 4 belongs to the project evidence. The final paper can therefore say, without stretching the record, that Gemma 3 was part of the exploratory setup phase while Gemma 4 is the model family on which the preserved quantitative study is based.

That distinction matters because it keeps the paper defensible. The team does not need to invent Gemma 3 numbers to tell a credible story. The honest story is that the audited research program starts with Gemma 4.

## 4. Task Definition

The target task is to map a query to a ranked list of extracted attributes. Each attribute must contain:

1. the extracted value,
2. its relative priority among all attributes in the query,
3. an ordered list of acceptable key names that represent the preferred normalized interpretation.

The target structure is nested JSON. A simplified example is shown below.

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

This definition is intentionally strict. A prediction is not fully correct unless the model extracts the right value, aligns it with the right key family, places it at a reasonable priority level, and orders alternative key names sensibly. That is why flat extraction quality and full task quality are related but not identical.

## 5. Training Stack And Data Sources

All preserved quantitative runs use Gemma 4 E4B as the base model and fine-tune it with LoRA-style adapters through Unsloth, Transformers, and TRL `SFTTrainer`. The training objective is framed as chat-style structured generation. Depending on the phase of the project, the model is trained to emit either flat JSON or the later nested priority schema.

The data story also evolved over time. The main sources visible in the preserved scripts are:

- `product_train_with_keys.jsonl` and `product_val_with_keys.jsonl` for broader flat extraction,
- cat74 motor-domain data, either converted into flat format or converted into nested priority form,
- `gold_1k_v2.jsonl` as stronger ground-truth supervision in the later flat and priority phases,
- qmeans-derived or qmeans-comparable artifacts used to benchmark and sometimes to broaden canonical motor-domain coverage.

The progression of the work can be summarized as a gradual tightening of supervision:

1. early flat extraction allowed noisy or inconsistent keys,
2. later flat extraction forced canonical key discipline,
3. priority extraction introduced nested structure and ranking targets,
4. the strongest standalone priority run balanced clean supervision with broader coverage rather than over-optimizing for purity.

## 6. Full Experimental Chronology

The project history is easiest to understand as a sequence of increasingly constrained learning problems.

| Stage | Main preserved artifact | What changed | Main result | Main lesson |
|---|---|---|---|---|
| Gemma 3 exploratory context | [setup_ollama.sh](setup_ollama.sh) | Local model bring-up via Ollama | No reproducible benchmark preserved | Gemma 3 is part of setup history, not the quantitative paper |
| V3b open-key flat extraction | [bee/finetune_v3.py](bee/finetune_v3.py), [bee/compare_v3b_vs_qmeans_vs_gold.txt](bee/compare_v3b_vs_qmeans_vs_gold.txt), [bee/compare_v3b_norm.txt](bee/compare_v3b_norm.txt), [bee/compare_full_1k.txt](bee/compare_full_1k.txt) | Gemma 4 fine-tuned on flat JSON from product key data | Strong value recovery but severe key drift | Semantics can appear before canonical control |
| V5 canonical flat extraction | [bee/finetune_gemma4_v5_flat.py](bee/finetune_gemma4_v5_flat.py), [bee/compare_v5_results.txt](bee/compare_v5_results.txt) | Simpler flat JSON with IndiaMART-style keys plus cat74 coverage | Still behind qmeans on strict KV F1 | Canonical keys help, but coverage and precision were not yet enough |
| V6 improved canonical flat extraction | [bee/finetune_gemma4_v6.py](bee/finetune_gemma4_v6.py), [bee/comparison_summary.csv](bee/comparison_summary.csv) | Cleaner canonical data, stricter prompt, gold supervision, more motor coverage | Gemma V6 beats qmeans on exact KV match | Gemma 4 can beat the production baseline on flat extraction |
| V7 first useful priority model | [priority_benchmark_report.md](priority_benchmark_report.md) | Nested priority schema restoration | First useful structured result | Ranked extraction is learnable |
| V8 to V10 aggressive priority variants | [priority_benchmark_report.md](priority_benchmark_report.md) | Larger capacity, heavier gold weighting, clean-only alignment | All worse than V7 | Aggressive supervision can collapse recall |
| V11 balanced rollback | [finetune_gemma4_v11_priority_balanced.py](finetune_gemma4_v11_priority_balanced.py), [v11_eval_summary.json](v11_eval_summary.json) | Conservative mix of clean and broad nested data | Best standalone priority result | Balance matters more than escalation |

That chronology is important because it turns the project from a loose collection of experiments into a defensible research program. The evidence now shows not only what worked, but also how the team learned which directions were counterproductive.

## 7. How We Trained Gemma 4 Across Phases

### 7.1 V3b: Early Open-Key Flat Extraction

The earliest preserved Gemma 4 training script is [bee/finetune_v3.py](bee/finetune_v3.py). Despite the filename, the saved artifact path is `gemma4-v3b`, so it is reasonable to treat this as the preserved V3b stage. The script already shows several thoughtful improvements for that time: proper Gemma 4 chat formatting, longer sequence length than the earlier version, light LoRA dropout, step-based evaluation, and merged-model saving for easier inference.

The key configuration points preserved in the script are:

- max sequence length 256,
- 3 epochs,
- batch size 4 with gradient accumulation 8,
- learning rate `1e-4`,
- LoRA `r=32`, `alpha=64`, dropout `0.05`,
- training on `product_train_with_keys.jsonl` and `product_val_with_keys.jsonl`.

The comments in the script are historically useful because they show an early failure mode the team had already discovered: a `train_on_responses_only` variant had broken generation quality by teaching the model template markers instead of clean JSON content. That note matters because it shows the team was already debugging the interaction between format and learnability before the project reached the more visible priority stage.

### 7.2 V5: Simpler Flat JSON With Broader Coverage

The V5 recipe, preserved in [bee/finetune_gemma4_v5_flat.py](bee/finetune_gemma4_v5_flat.py), made a clear strategic simplification. Instead of asking the model to learn a more complex nested structure, it trained the model to emit simple flat JSON with IndiaMART-style keys. The script also expanded motor-domain coverage by converting cat74 nested outputs into flat examples.

The preserved V5 recipe uses:

- max sequence length 512,
- 5 epochs,
- batch size 2 with gradient accumulation 16,
- learning rate `2e-4`,
- flat JSON output only,
- `product_train_with_keys` data plus converted cat74 rows.

This phase is important because it shows an explicit attempt to trade structural ambition for learnability.

### 7.3 V6: Canonical Discipline And Gold Alignment

The V6 recipe, preserved in [bee/finetune_gemma4_v6.py](bee/finetune_gemma4_v6.py), tightened the task further. It forced the model to use only a strict canonical key set, remapped noisy cat74 keys into that set, and incorporated stronger gold supervision through `gold_1k_v2`. The script header also records that qmeans-derived canonicalized examples were included as additional motor-domain examples.

The preserved V6 configuration uses:

- max sequence length 512,
- 6 epochs,
- batch size 2 with gradient accumulation 16,
- learning rate `1e-4`,
- a strict canonical prompt that explicitly bans alternate key names such as `type`, `motor type`, or `speed`,
- cleaned training files `v6_train.jsonl` and `v6_val.jsonl` plus converted cat74 coverage.

V6 marks the point where canonical control stopped being a side goal and became a first-class part of the model design.

### 7.4 V7 Through V11: Priority-Ordered Structured Extraction

The priority phase introduced the nested target structure with `attribute_priorityN` and `key_priorityN` fields. This was the phase that turned the project into a real ranking-and-structure problem instead of a standard flat extraction problem.

The broad historical arc is:

- V7 established the first useful priority model,
- V8 increased model and data aggressiveness but lost recall,
- V9 pushed gold weighting more heavily and collapsed recall further,
- V10 emphasized clean-only alignment so strongly that extraction disappeared,
- V11 rolled back toward the balanced V7 recipe and became the best standalone priority model.

The preserved V11 script and summary show that the recovery recipe mattered more than scale. V11 uses a moderate configuration rather than an extreme one: sequence length 768, 2 epochs, batch size 2 with gradient accumulation 16, learning rate `7e-5`, and LoRA `r=32`, `alpha=64`, trained on a balanced mix of nested cat74 rows, V6 flat-to-nested rows, and converted `gold_1k_v2` rows. The lesson is clear: the best result came from restoring balance between clean structure and broad coverage.

## 8. Benchmark Views And Metric Caveats

The project now contains several benchmark views, and they do not all measure exactly the same thing. That is important to state explicitly because some of the early numbers are historically meaningful without being directly interchangeable with the final priority metrics.

The preserved benchmark views include:

1. an early 98-query gold comparison used in [bee/compare_v3b_vs_qmeans_vs_gold.txt](bee/compare_v3b_vs_qmeans_vs_gold.txt) and [bee/compare_v3b_norm.txt](bee/compare_v3b_norm.txt),
2. a full 1000-query comparison in [bee/compare_full_1k.txt](bee/compare_full_1k.txt),
3. a later flat exact-match benchmark summarized in [bee/comparison_summary.csv](bee/comparison_summary.csv),
4. the current priority evaluator summarized in [priority_benchmark_report.md](priority_benchmark_report.md).

The safest way to read those numbers is stage by stage. The early V3b reports are useful for understanding how the model evolved from open-key behavior to canonical behavior. The V5 and V6 results show whether the flat extractor became practically competitive. The V7 to V11 results show how well the project handled the harder structured priority problem.

For publication, the evaluator still needs to grow beyond flat key and key+value F1. A proper priority paper should also report parse rate, schema compliance, placeholder-key rate, deep-wrapper rate, attribute-order correctness, key-synonym-order correctness, and exact structured match.

## 9. Results

### 9.1 Early V3b Results: Strong Semantics, Weak Key Discipline

The first newly recovered part of the story is the early V3b evidence. The raw comparison in [bee/compare_v3b_vs_qmeans_vs_gold.txt](bee/compare_v3b_vs_qmeans_vs_gold.txt) shows that V3b was already extracting meaningful values, but it had not yet learned a disciplined canonical key vocabulary.

| System view | Gold set | Parse rate | Unique keys | Canonical-vocab share | Key F1 | Value exact | Value substring |
|---|---:|---:|---:|---:|---:|---:|---:|
| V3b raw | 98-query subset | 63.5% | 273 | 59.4% | 13.7% | 57.2% | 90.2% |
| V3b normalized | 98-query subset | 52.6% | 32 | 100.0% | 20.4% | 50.2% | 87.1% |
| V3b normalized | 1000-query full view | 52.6% | 32 | 100.0% | 20.5% | 42.5% | 87.7% |
| qmeans | 98-query subset | 94.6% | 18 | 98.5% | 45.0% | 19.4% | 80.0% |
| qmeans | 1000-query full view | 94.6% | 18 | 98.5% | 48.4% | 11.9% | 80.5% |

This table tells an important story. V3b raw had much stronger semantic value recovery than its key F1 suggested. Its value-exact score on the 98-query view was 57.2%, far above qmeans at 19.4%, and its value-substring score was above 90%. But the model was producing far too many uncontrolled key names, with 273 unique keys and only 59.4% of them landing in the canonical vocabulary. After normalization, the key F1 improved from 13.7% to 20.4%, and the key space collapsed from 273 unique keys to 32. That is the first preserved sign that canonical control was becoming a central issue.

The tradeoff is visible as well. Normalization improved key discipline but reduced parse rate and some value metrics, because poorly aligned or noisy outputs were now being dropped or collapsed more aggressively. That tradeoff set up the next phase of the project.

### 9.2 What Early Example Rows Reveal

The preserved row-level comparison in [bee/wide_comparison.csv](bee/wide_comparison.csv) helps explain why early V3b looked both promising and unstable. For example, on the query `SIEMENS SIMOTICS S-1FK2 SERVO MOTOR 1FK2104-6AF01-1MB0 1 kW`, the early Gemma output recovers brand, part type, model-family information, and power with substantial semantic fidelity. But it also compresses `SIMOTICS S-1FK2` and `1FK2104-6AF01-1MB0` into a single model field rather than separating series and model cleanly. In other rows, V3b predicts the right general concept but uses key families such as `feature`, `product`, or non-canonical variants that later stages explicitly removed.

This matters for the paper because it shows the early model was not merely bad. It was semantically active but structurally undisciplined. That is a different and much more useful failure mode.

### 9.3 V5 And V6: Flat Extraction Becomes Competitive

The preserved V5 comparison in [bee/compare_v5_results.txt](bee/compare_v5_results.txt) shows a system that was improving but still not strong enough.

| System | KV strict F1 | Value-only F1 | Token F1 |
|---|---:|---:|---:|
| qmeans_v2 | 37.23 | 46.20 | 79.83 |
| V5_flat | 28.05 | 31.27 | 41.99 |

V5 is therefore important historically, but not yet a headline win. It shows that moving to simpler flat JSON and better key control did not immediately produce a stronger system than qmeans.

The later flat benchmark in [bee/comparison_summary.csv](bee/comparison_summary.csv) does show a clear win.

| System | Exact key+value match rate | Queries with all attributes correct | Queries with zero correct |
|---|---:|---:|---:|
| qmeans | 27.1% | 42 | 415 |
| Gemma V6 | 40.7% | 182 | 332 |

V6 is the stage at which fine-tuned Gemma 4 clearly demonstrates business value over qmeans in flat extraction. That matters because it means the later priority work was not being attempted from a weak base. The team had already established that Gemma 4 could win on an operationally meaningful flat benchmark.

### 9.4 Priority Benchmark Results

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

Two facts define the current state of the project.

First, V11 is the best standalone priority model in the repository. It reaches 45.44% key F1 and 20.26% key+value F1, essentially tying qmeans on key F1 and surpassing qmeans clearly on key+value F1.

Second, the hybrid system remains the best operational path on key F1 at 54.38%. That distinction matters. The strongest standalone research model and the strongest deployment system are not yet the same thing.

### 9.5 What The Full Sequence Shows

The complete sequence from V3b through V11 is scientifically useful because it shows three different kinds of progress.

1. semantic progress: V3b already recovers useful values,
2. canonicalization progress: V5 and V6 progressively discipline the key space,
3. structured-ranking progress: V7 through V11 show that ranked extraction is learnable but fragile.

That is a much stronger internal narrative than a single best-model result would have provided.

## 10. Priority-Order Attribute Problems The Project Has Solved

One of the clearest ways to summarize the project is to list the specific problems that are now solved or substantially de-risked.

### 10.1 Recovering The Main Intent Instead Of An Unordered Bag

The project has shown that it is possible to represent a query not just as a set of attributes, but as an ordered structure in which primary product identity and secondary constraints can be separated. That is the conceptual foundation of the entire paper.

### 10.2 Handling Multiple Possible Key Names For The Same Value

The work has made key-synonym ranking explicit. Rather than pretending there is always only one valid key name, the system can represent a preferred normalized key and alternate plausible key families. This is especially useful in industrial data, where `motor type`, `driven type`, `type`, and `part type` can overlap or conflict.

### 10.3 Reducing Open-Key Drift

The newly recovered V3b evidence makes this especially clear. Early Gemma 4 outputs contained meaningful values but uncontrolled key naming. The later flat and priority recipes progressively reduced that drift through prompt constraints, data remapping, and canonical supervision.

### 10.4 Beating Qmeans On Exact Key+Value Quality

By V6, the Gemma 4 flat extractor clearly surpassed qmeans on the preserved exact key+value benchmark. That is one of the most important practical achievements in the repository because it proves the fine-tuned model family can outperform the production baseline on exact extraction quality.

### 10.5 Producing A Strong Standalone Priority Model

V11 demonstrates that the ranked structured task is not only theoretically interesting but practically learnable. The model now reaches qmeans-level key F1 while outperforming qmeans clearly on key+value F1.

### 10.6 Producing A Better System-Level Serving Path

The hybrid V7 plus qmeans path solves a different problem: it gives the team a stronger deployment option even before the standalone research problem is completely finished. That is a valuable engineering result in its own right.

### 10.7 Building The Research Infrastructure Around The Model

The project is no longer just a folder of checkpoints. It now includes evaluators, structural diagnostics, live monitoring, benchmark rollups, senior-facing updates, and internal paper drafts. That surrounding infrastructure is one of the reasons the work is now describable as a coherent experimental program.

## 11. Structural Error Analysis

The priority problem is not only about missing values. It is also about malformed structure. The V7 diagnostics preserved in [priority_error_analysis_notes.md](priority_error_analysis_notes.md) and [v7_priority_analysis.json](v7_priority_analysis.json) show how semantic signal and structural compliance can diverge.

The most informative V7 structural numbers are:

- parsed rate: 80.2%,
- deep-wrapper rate: 71.9%,
- placeholder-key rate: 19.9%,
- empty-flat rate after robust unwrapping: 27.2%.

Those numbers explain why the project cannot be judged only by flat F1. In many cases the semantic content was present but hidden behind extra nesting, placeholder labels, or schema deviations. That is why the later evaluator work and hybrid serving logic mattered so much. They helped recover real signal that a brittle parser would have thrown away.

## 12. Case Study: Why Structure Matters In Practice

The example preserved in [split_hybrid_sample.jsonl](split_hybrid_sample.jsonl) remains one of the cleanest illustrations of the project’s value. The query is:

`siemens 45 hp 3 phase 1440 rpm motor`

The final hybrid output recovers a clean ranked structure whose flattened interpretation is:

- brand = siemens,
- part type = motor,
- power = 45 hp,
- phase = 3 phase,
- rpm = 1440 rpm.

The preserved raw V7 output for the same query contains much of the same semantic content, but with extra nested wrappers that made robust parsing necessary. qmeans recovers many of the values, but weakens the part-type interpretation in this example. This single case reflects the broader project pattern: the structured model often contains better intent organization, while the baseline retains stronger broad coverage. The hybrid path benefits from both.

## 13. Why The Negative Results Strengthen The Paper

V8, V9, and V10 are not embarrassing dead ends. They are valuable ablations.

- V8 shows that more capacity and more aggressive supervision do not automatically help.
- V9 shows that heavier gold weighting can damage recall severely.
- V10 shows that forcing clean-only structure can erase extraction behavior entirely.
- V11 shows that the correct recovery path was a better balance of clean structure and broad coverage, not more force.

That sequence gives the final paper genuine research character. It identifies which intuitively appealing decisions turned out to be wrong, and it explains why the eventual recovery worked.

## 14. What Remains Open

The project is strong internally, but a few important gaps remain before the work is ready as a polished external submission.

### 14.1 Rank-Aware Evaluation Is Still Incomplete

The current evaluator measures extraction quality better than it measures ranking quality. A submission-ready paper should add attribute top-1 correctness, pairwise order accuracy, key-synonym top-1 accuracy, key-synonym MRR, and exact structured match.

### 14.2 Structural Metrics Should Be Promoted To First-Class Headline Results

Parse rate, schema compliance, placeholder-key rate, and deep-wrapper rate should move from diagnostic notes into the main results section, because they directly measure whether the model is solving the actual structured task.

### 14.3 The Gemma 3 Archive Is Still Missing

If the team wants a true Gemma 3 versus Gemma 4 quantitative comparison in the final paper, the missing Gemma 3 fine-tuning and evaluation trail will have to be recovered. If not, the paper should explicitly state that Gemma 3 is historical context and Gemma 4 is the audited study.

### 14.4 Qmeans Still Has The Best Standalone Coverage Profile On Key Recall

V11 is now essentially tied with qmeans on key F1 and well ahead on key+value F1, but qmeans still represents the strongest broad-coverage baseline in some respects. That is exactly why the hybrid remains the best operational system.

## 15. Publication-Ready Framing

If the team wants to circulate this work internally right now, the safest framing is:

1. Gemma 3 belongs to exploratory history.
2. Gemma 4 is the audited quantitative program.
3. V6 established practical superiority over qmeans on flat exact key+value matching.
4. V11 established the best standalone priority model.
5. The hybrid established the best operational deployment path.
6. The main remaining gap is rank-aware and structure-aware evaluation, not the absence of a research story.

That framing is complete, defensible, and faithful to the repository evidence.

## 16. Conclusion

The repository now supports a much fuller and more human research narrative than the earlier summaries suggested. The project did not begin with a clean win. It began with Gemma 4 models that already understood many attribute values but expressed them through noisy and inconsistent key spaces. It then moved through a phase of increasingly disciplined flat extraction, where V6 became the first clear business-quality win over qmeans. Only after that foundation was in place did the work move into the harder priority-ordered setting.

That second phase is where the project becomes especially interesting. V7 proved that ranked structured extraction was possible. V8 through V10 proved that more aggressive supervision could easily break it. V11 proved that the recovery path was not further escalation, but balance. The hybrid system then showed how the research model and the baseline system could be combined into a stronger operational path.

Taken together, those results support a strong internal paper and a credible external research direction. The project has already solved important product and modeling problems. What remains is to formalize the ranking metrics, promote the structural diagnostics into the main evaluation stack, and decide whether to recover the Gemma 3 archive or to scope the final publication explicitly as a Gemma 4 study.

## Appendix A. Consolidated Metric Snapshot

### A.1 Early V3b Indicators

| System view | Key F1 | Value exact | Main interpretation |
|---|---:|---:|---|
| V3b raw, 98-query view | 13.7% | 57.2% | Good semantic values, very noisy keys |
| V3b normalized, 98-query view | 20.4% | 50.2% | Better canonical control, still weak coverage |
| V3b normalized, full 1k view | 20.5% | 42.5% | Same pattern holds at larger scale |

### A.2 Flat Extraction Milestones

| System | Headline metric | Value |
|---|---|---:|
| V5_flat | KV strict F1 | 28.05 |
| qmeans_v2 | KV strict F1 | 37.23 |
| Gemma V6 | Exact key+value match rate | 40.7% |
| qmeans | Exact key+value match rate | 27.1% |

### A.3 Priority Extraction Milestones

| System | Key F1 | Key+Value F1 |
|---|---:|---:|
| qmeans | 45.50% | 6.00% |
| V7 | 29.09% | 15.52% |
| V8 | 15.88% | 10.72% |
| V9 | 4.75% | 2.69% |
| V10 | 0.00% | 0.00% |
| V11 | 45.44% | 20.26% |
| Hybrid V7 + qmeans | 54.38% | 17.22% |

## Appendix B. Plain-Language Summary

The full story is now straightforward. Gemma 3 appears in the preserved repo only as exploratory setup context. The real auditable work starts with Gemma 4. The earliest Gemma 4 model, V3b, already understood many of the right values but used too many inconsistent key names. V5 simplified the task into flat canonical JSON, and V6 turned that into a clear win over qmeans on exact key+value matching. The project then moved to the harder priority-ordered task, where V7 became the first useful structured model, V8 to V10 failed in informative ways, and V11 recovered the best standalone priority result. Today, V11 is the strongest standalone priority model, while the hybrid remains the strongest overall operational system.