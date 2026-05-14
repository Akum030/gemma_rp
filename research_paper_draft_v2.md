# Research Paper Draft V2

## Working Title
Priority-Ordered Attribute Extraction from Industrial Search Queries

## Draft Status
Internal draft for research review.

This version is the current best local draft. It includes all completed benchmark summaries through V11 and is suitable for internal review and discussion, but not yet for external submission.

## Abstract
Search-query understanding systems typically extract unordered attribute-value pairs such as brand, model number, phase, power, or product type. For industrial and commerce search, this is often not enough. Downstream systems also need to know which attributes matter first for user intent and which normalized key names should be preferred for each extracted value. We study a priority-ordered attribute extraction framework that predicts three things jointly: the extracted value, the relative importance order of attributes in the query, and the preferred synonym-key ordering for each value. We formulate the task as structured generation with a nested JSON schema and fine-tune Gemma-4 E4B with LoRA-based adapters on mixtures of curated nested supervision, converted flat supervision, and gold query data. Across completed standalone results, the first strong priority-specific model V7 achieves stronger exact key+value quality than a qmeans baseline, while qmeans remains stronger on broad key coverage. A serving-time hybrid that preserves V7 structured output and fills missing attributes from qmeans yields the strongest current operational result, improving both key F1 and key+value F1 over either standalone system. Later variants V8, V9, and V10 all underperform V7, while the conservative rollback V11 recovers performance enough to beat V7 on both standalone metrics even though qmeans still leads on broad key coverage. These findings strengthen the research value of the problem: priority-ordered extraction appears useful, expressive, and meaningfully harder than ordinary flat extraction, and naive attempts to improve it can easily damage recall. We also outline the evaluation extensions needed to measure the true research target, including schema obedience and rank-aware correctness.

## 1. Introduction
Short industrial and commerce queries are dense with intent. A query such as `Siemens 1 kW 3 phase servo motor` contains a brand, a product type, and two technical constraints. Many current query-understanding systems convert this into an unordered set of key-value pairs. That is useful, but incomplete.

In real search, ranking, normalization, routing, and retrieval pipelines often benefit from stronger structure:
- which attribute should drive retrieval first
- which attributes are supporting constraints rather than the main intent
- which key name should be preferred when multiple synonyms are valid

This project studies whether a model can learn that richer structure directly from user queries.

The target output is not just a flat set of extracted pairs. It is a ranked sequence of extracted attributes, where each value also carries an ordered list of preferred key names.

## 2. Problem Statement
Given a user query, the system must return a ranked list of extracted attributes. Each extracted attribute includes:
- a value
- an attribute priority index
- an ordered list of preferred canonical or synonym keys

The output schema is represented as nested JSON.

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

This is more demanding than ordinary attribute extraction because the model must jointly learn:
- what to extract
- in what order the extracted attributes should appear
- which key name should be preferred first for each extracted value

## 3. Motivation
The task is motivated by industrial and marketplace use cases where unordered extraction loses useful intent structure.

Potential downstream benefits include:
- retrieval systems that emphasize the top-priority attribute first
- ranking systems that distinguish between identity signals and supporting constraints
- normalization systems that preserve preferred canonical keys instead of arbitrary aliases
- query rewriting pipelines that retain the original importance structure of a query

In short, the goal is not only better extraction. It is better intent structure.

## 4. Related Work
This project sits near several existing research areas:
- slot filling and structured NLU
- product attribute extraction
- query attribute extraction in commerce search
- attribute normalization
- structured generation

Four nearby references are especially relevant.

### 4.1 OpenTag
Zheng et al. (2018) study open attribute value extraction from product profiles. Their work is important because it shows that product attribute extraction itself is a real learning problem and can be framed as sequence tagging. However, it focuses on product titles and descriptions, not short user queries, and it does not model attribute priority order or key-synonym preference order.

### 4.2 Joint Intent Classification And Slot Filling With BERT
Chen et al. (2019) show that pretrained language models improve joint intent and slot modeling. This is relevant because it supports treating query parsing as structured prediction rather than isolated extraction. However, it does not target industrial product search or ranking over extracted attributes.

### 4.3 Explicit Attribute Extraction In E-Commerce Search
Loughnane et al. (2024) are especially close to the present task. They extract attribute values from search queries using weak labels from customer interactions and show real production value for retrieval and ranking. However, their system focuses on explicit attribute extraction and normalization rather than ordering extracted attributes by importance or ranking preferred key synonyms.

### 4.4 LLM-Based Product Attribute Extraction And Normalization
Brinkmann et al. (2024) study LLMs for extraction and normalization of product attribute values from product offers. This is useful for positioning the present work relative to current LLM-based structured extraction. However, it still focuses on product offers rather than user queries and does not model ranked attribute or key preference structure.

### 4.5 Positioning Claim
The safest current claim is the following:

To our knowledge, explicit modeling of both attribute priority order and synonym-key priority order for industrial search queries is underexplored. Existing work covers attribute extraction, slot filling, and attribute normalization, but we have not yet found a directly matching formulation that jointly predicts values, attribute order, and key preference order in the same structured output.

## 5. Method
We use Gemma-4 E4B as the base model and apply LoRA-based fine-tuning using Unsloth.

### 5.1 Output Design
The model is trained to generate nested JSON where:
- `attribute_priorityN` represents relative importance among extracted attributes
- `key_priority1..N` represent preferred key ordering
- `value` stores the extracted surface form or normalized value

### 5.2 Data Sources
The training mixtures used across versions draw from three main sources:
- manually curated nested priority supervision
- flat extraction supervision converted into the nested schema
- a 1000-query gold dataset used both for stronger supervision and final benchmarking

### 5.3 Model Versions
The current study includes these main versions:
- `V6`: earlier flat extraction baseline
- `V7`: priority-schema restoration model
- `V8`: higher-capacity priority model with added gold supervision
- `V9`: stronger accuracy push with heavier gold weighting and lower learning rate
- `V10`: clean-schema training run that removes noisy flat-to-nested converted data
- `V11`: conservative rollback toward the V7 recipe with a light clean nested-priority bias

## 6. Experimental Setup
Two benchmark views are currently relevant.

### 6.1 Legacy Exact Key+Value Match Benchmark
This older benchmark compares flat extraction quality directly against qmeans and was the first signal that fine-tuned Gemma can have practical value.

### 6.2 Priority Benchmark
The newer 1000-query benchmark evaluates priority-oriented models against gold and qmeans outputs.

The current evaluator reports:
- key precision
- key recall
- key F1
- key+value precision
- key+value recall
- key+value F1

These metrics are necessary, but they do not yet fully measure the intended research contribution.

In addition to standalone model comparisons, we also track a serving-time hybrid system that merges V7 parsed output with qmeans for missing attributes. This is useful for practical deployment analysis, but it should be interpreted separately from standalone finetuned model progress.

## 7. Confirmed Results

### 7.1 Legacy Baseline Signal
On the older exact key+value benchmark:
- qmeans exact key+value match rate: `27.1%`
- Gemma V6 exact key+value match rate: `40.7%`

This is important because it shows that the broader fine-tuning direction already had real business relevance before the ranked priority formulation was introduced.

### 7.2 Confirmed Priority Benchmark Results

| Model | Key Precision | Key Recall | Key F1 | Key+Value Precision | Key+Value Recall | Key+Value F1 |
|---|---:|---:|---:|---:|---:|---:|
| qmeans | 95.95% | 29.82% | 45.50% | 12.66% | 3.93% | 6.00% |
| V7 | 60.49% | 19.15% | 29.09% | 32.28% | 10.22% | 15.52% |
| Hybrid (V7 + qmeans fallback) | 75.60% | 42.46% | 54.38% | 23.94% | 13.44% | 17.22% |
| V8 | 61.12% | 9.12% | 15.88% | 41.25% | 6.16% | 10.72% |
| V9 | 77.55% | 2.45% | 4.75% | 43.88% | 1.39% | 2.69% |
| V10 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| V11 | 79.47% | 31.82% | 45.44% | 35.43% | 14.18% | 20.26% |

The main confirmed conclusion from these local results is:
- among standalone systems, qmeans remains strongest on broad key recovery
- among standalone priority models, V7 remains strongest on exact key+value quality
- the best current practical system is the hybrid serving path, which beats both standalone qmeans and standalone V7 on the trusted benchmark

### 7.3 V7 Structural Quality
For V7, the structural analysis shows that flat F1 alone is not enough to describe behavior:
- parsed rate: `80.2%`
- deep-wrapper rate: `71.9%`
- placeholder-key rate: `19.9%`
- empty-flat rate after robust unwrapping: `27.2%`

These numbers show that V7 has real semantic signal but still suffers from substantial schema-obedience failures.

### 7.4 What V8 Taught Us
V8 is an important negative result.

Compared with V7:
- precision stayed reasonably high when V8 emitted a match
- recall dropped materially
- exact key+value F1 also dropped below V7

This means that increasing LoRA capacity and adding more gold supervision did not automatically solve the main problem. The bottleneck is not only model scale. Schema quality and data mixture quality still appear central.

### 7.5 What V9 And V10 Taught Us
V9 and V10 are also informative, but in a negative direction.

V9 shows that stronger gold weighting can sharply reduce recall instead of improving it. Its precision is high when it predicts, but it predicts far too little to be competitive.

V10 shows that clean-schema-only alignment from this setup can over-correct so aggressively that extraction nearly disappears entirely on the trusted benchmark.

Together, these two runs suggest that the best next step is not another aggressive shift. The next step should be a controlled rollback toward the V7 recipe with only a light clean-schema bias.

That controlled rollback experiment, `V11`, has now completed. V11 beats V7 on both standalone metrics, but qmeans still leads on key F1. V11 also beats qmeans on key+value F1.

### 7.6 What The Hybrid Serving Result Changes
The hybrid serving result changes the practical deployment picture, but not the standalone research ranking.

By taking V7's parsed priority output and filling only missing attributes from qmeans, the current system reaches:
- key F1: `54.38%`
- key+value F1: `17.22%`

This is the strongest current operational result in the project. It shows that V7 already contributes useful structured signal even though it still underperforms qmeans on standalone recall.

However, this should not be misreported as a pure model improvement. It is a system-level serving combination, not a new standalone finetuned adapter.

### 7.7 What V11 Taught Us
V11 completed with key F1 45.44% and key+value F1 20.26%. V11 beats V7 on both standalone metrics, but qmeans still leads on key F1. V11 also beats qmeans on key+value F1.

This result is useful because it directly tests whether a conservative rollback toward the V7 recipe can recover standalone quality better than the aggressive changes used in V8-V10.

## 8. Interpretation
The current evidence supports four important conclusions.

### 8.1 The Task Is Real
Priority-ordered attribute extraction is not a trivial extension of flat extraction. The difficulty of V7 and V8 suggests that adding ranking and structured generation creates a genuinely harder learning problem.

### 8.2 Exact Quality And Broad Coverage Can Diverge
qmeans is better at covering more keys overall, but V7 is better at exact key+value quality. This matters because different downstream systems may care about different parts of that tradeoff.

The hybrid result shows that these two strengths can be combined operationally even before the standalone model problem is fully solved.

### 8.3 Capacity Alone Is Not Enough
V8 is evidence that simply scaling adapter capacity and injecting more supervision does not guarantee better ranked extraction performance.

### 8.4 Aggressive Supervision Changes Can Be Harmful
V9 and V10 show that stronger gold emphasis or clean-only schema alignment can damage recall so severely that overall benchmark quality collapses.

### 8.5 Schema Obedience Is A First-Class Research Problem
The structural failures in V7 show that a model can contain useful semantics while still violating output structure often enough to hurt downstream use. This makes schema obedience a meaningful evaluation target rather than a cosmetic formatting issue.

## 9. What The Results Now Mean For The Next Model
The completed V7-V11 sequence suggests a clear next-model design rule:

- keep the smaller V7 adapter scale
- keep broad V6-derived coverage data
- add only a light clean nested-priority bias
- avoid heavy gold oversampling and avoid clean-only alignment as a standalone recipe

## 10. What The Final Benchmark Still Needs
The current flat evaluator is useful but incomplete. The final paper should report at least four layers of evaluation:
- extraction correctness
- schema obedience
- attribute-order correctness
- key-synonym-order correctness

Recommended additions include:
- schema compliance rate
- top-1 attribute priority accuracy
- pairwise attribute order accuracy
- top-1 key-synonym accuracy
- key-synonym mean reciprocal rank
- end-to-end exact structured match rate

## 11. Limitations
This draft should be explicit about current limitations.

- The literature positioning is promising but not yet fully exhaustive.
- V7 recall remains weak relative to qmeans.
- The current best serving result depends on qmeans endpoint availability and therefore is not yet a fully self-contained model-only solution.
- V8 did not improve over V7.
- V9 and V10 both underperformed V7 substantially.
- Rank-aware evaluation metrics are still designed conceptually rather than fully implemented.
- Results are currently scoped to the industrial-query setting rather than broad general-domain query understanding.

## 12. Practical Value
If the method succeeds, it could support:
- industrial product search
- marketplace query routing
- retrieval and ranking systems that use top-priority intent explicitly
- product normalization pipelines
- faceted search generation
- catalog mapping and enrichment

## 13. Research Contribution Narrative
Even before V9 and V10 are fully collected, the project already supports a coherent internal research narrative:

1. Fine-tuned generative models can outperform a production-style baseline on exact key+value quality in this domain.
2. Extending the task to ranked structured output creates a harder and more interesting problem than flat extraction.
3. The first strong priority model V7 beats qmeans on exact key+value F1 but still loses on broad recall.
4. A simple serving-time hybrid can already combine V7 structured signal with qmeans coverage to produce the best current practical benchmark result.
5. Later variants V8, V9, and V10 do not solve the standalone model problem and in fact perform worse, which strengthens the claim that the task is fundamentally difficult and not only under-trained once.
6. The next clear scientific question is whether a more conservative rollback toward the V7 recipe can recover recall while improving structure only slightly, rather than aggressively.

## 14. Conclusion
The current evidence supports priority-ordered attribute extraction as a credible internal research direction. It is not yet a solved engineering problem, and it is not yet ready for an external paper submission. However, the combination of positive exact key+value results, clear structural failure modes, and informative negative V8-V10 evidence gives the project real research value.

The most defensible current conclusion is not that the problem is solved, but that it is worth studying: the task is useful, structurally richer than flat extraction, and empirically hard enough to justify a dedicated research effort.

## 15. Suggested Cover Note For Internal Review
Suggested cover note:

"This draft summarizes an internal research direction on priority-ordered attribute extraction from industrial search queries. The goal is to predict not only extracted values, but also attribute importance order and preferred key-synonym ordering. Confirmed local results show that our V7 priority model already beats qmeans on exact key+value quality, while qmeans remains stronger on broad standalone recall. A serving-time hybrid that combines V7 with qmeans fallback currently gives the best practical benchmark result. Later variants V8, V9, and V10 all performed worse than V7, suggesting that the remaining difficulty lies in recall and schema obedience rather than capacity alone. We are treating this as a serious structured prediction problem rather than a small extension of flat extraction." 