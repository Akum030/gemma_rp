# Research Paper Draft V1

## Working Title
Priority-Ordered Attribute Extraction from Industrial Search Queries

## Draft Status
Internal draft for discussion with a senior reviewer. This is not submission-ready yet.

## Abstract
Search-query understanding systems usually extract attribute-value pairs such as brand, model, phase, or power. However, many industrial and e-commerce search applications need more than unordered extraction. They need to know which attribute matters first for user intent and which normalized key name should be preferred for each value. In this work, we propose a priority-ordered attribute extraction framework that predicts: 1) the extracted attribute value, 2) the relative importance order of attributes in the query, and 3) the preferred key-synonym ordering for each attribute. We formulate the task as structured generation using a nested JSON schema and fine-tune Gemma-based models on a mixture of manually curated and converted training data. Early results show that standard flat extraction can already outperform an internal production-style baseline on exact key+value matching, while the first priority-specific version still struggles with recall. This makes the problem scientifically interesting: the task is useful, but significantly harder than unordered extraction. We describe the task, model design, benchmark structure, early findings, and next steps toward a stronger publishable system.

## 1. Introduction
Search queries in industrial catalogs are short, noisy, and information-dense. A single query may contain:
- brand
- product type
- model number
- power
- phase
- rpm
- usage hints

Most attribute extraction systems try to identify these pieces as an unordered set. That is a useful start, but it misses a critical signal: importance order.

For example, in the query “Siemens 1 kW 3 phase servo motor”, a search engine may benefit from knowing that:
- Siemens is the strongest identity signal
- servo motor is the product-type signal
- 1 kW and 3 phase are supporting technical constraints

This work studies whether a model can learn not only the values, but also the attribute priority order and the preferred synonym-key order for each value.

## 2. Problem Definition
Given a user query, the target system must return a ranked sequence of extracted attributes. Each extracted attribute contains:
- a value
- an attribute priority index
- an ordered list of acceptable key names

We represent this using the following structure:

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
    }
  ]
}
```

This is different from ordinary attribute extraction because the model must jointly learn:
- what to extract
- which extracted attribute should appear first
- which canonical or synonym key should be preferred first

## 3. Motivation
The task is motivated by real search behavior in industrial and commerce platforms such as:
- large B2B marketplaces
- parts catalogs
- e-commerce search engines
- catalog-matching pipelines
- product recommendation or routing systems

In practice, downstream systems often need a stronger structure than flat extraction. For example:
- retrieval can emphasize top-priority attributes first
- ranking can distinguish between essential and supporting constraints
- normalization can use the preferred key name instead of arbitrary synonyms
- query rewriting can preserve intent more reliably

## 4. Related-Work Positioning
There is existing work on:
- slot filling
- named entity recognition
- product attribute extraction
- query understanding
- facet prediction
- structured generation

Representative nearby references include:
- Zheng et al. (2018), OpenTag: open attribute value extraction from product profiles
- Chen et al. (2019), BERT for joint intent classification and slot filling
- Loughnane et al. (2024), Explicit Attribute Extraction in e-Commerce Search
- Brinkmann et al. (2024), Using LLMs for the Extraction and Normalization of Product Attribute Values

These works support the importance of structured attribute extraction, product normalization, and query understanding. However, the exact combination studied here appears more specific: explicit extraction of attribute values together with both attribute priority order and synonym-key priority order.

Important caution:
we should not externally claim “first in the world” until a formal literature review is completed. The correct current wording is:

“To our knowledge, priority-ordered attribute extraction for industrial search queries is underexplored.”

A more precise formulation after the current literature scan is:

“Existing work covers slot filling, product attribute extraction, and attribute normalization, but we have not yet found prior work that jointly predicts extracted values, attribute priority order, and synonym-key priority order in a single structured output for industrial search queries.”

## 5. Method
### 5.1 Model family
We use Gemma-4 E4B as the base model and apply LoRA-based fine-tuning with Unsloth.

### 5.2 Output design
The model is trained to generate nested JSON where:
- attribute_priorityN encodes relative importance
- key_priority1..N encode synonym preference order
- value stores the extracted surface form or normalized value

### 5.3 Data sources
The current data mixture includes:
- original nested priority data from a curated category dataset
- flat extraction data converted into the nested priority schema
- a 1000-query gold dataset used for improved supervision in later versions

### 5.4 Versions
The project currently includes:
- legacy flat extraction baseline
- V7 priority schema restoration
- V8 higher-capacity priority model with gold supervision
- V9 stronger accuracy push with heavier gold weighting and lower learning rate

## 6. Experimental Setup
### 6.1 Benchmarks
We currently use two useful comparisons:
- a legacy exact key+value match benchmark
- a newer priority-aware benchmark against gold and qmeans outputs

### 6.2 Baselines
The main baselines are:
- qmeans production-style extractor
- earlier Gemma flat extraction system
- later Gemma priority variants

### 6.3 Metrics
Current metrics include:
- key precision
- key recall
- key F1
- key+value precision
- key+value recall
- key+value F1
- exact pair match rate in the legacy benchmark

These metrics are necessary, but they do not fully measure the intended contribution. The final paper should separate four evaluation layers:
- extraction correctness
- schema obedience
- attribute priority correctness
- key-synonym priority correctness

So a stronger final benchmark section should also report:
- schema compliance rate
- placeholder-key rate
- deep-wrapper rate
- top-1 attribute priority accuracy
- pairwise attribute order accuracy
- top-1 key-synonym accuracy
- key-synonym mean reciprocal rank
- exact structured match rate

## 7. Early Results
### 7.1 Legacy benchmark
On the earlier benchmark, flat fine-tuned Gemma outperformed qmeans on exact key+value matching.

From [bee/comparison_summary.csv](bee/comparison_summary.csv):
- qmeans exact key+value match rate: 27.1%
- Gemma V6 exact key+value match rate: 40.7%

This is important because it shows the general fine-tuning direction has real promise.

### 7.2 V7 priority benchmark
On the newer 1000-query gold benchmark, V7 achieved:
- key precision: 60.49%
- key recall: 19.15%
- key F1: 29.09%
- key+value precision: 32.28%
- key+value recall: 10.22%
- key+value F1: 15.52%

For the same benchmark under the current corrected evaluator, qmeans achieved:
- key F1: 45.50%
- key+value F1: 6.00%

This means V7 is weaker than qmeans on key coverage, but stronger on exact key+value matching.

The structural analysis of V7 also shows why flat F1 alone is not enough to describe behavior:
- parsed rate: 80.2%
- deep-wrapper rate: 71.9%
- placeholder-key rate: 19.9%
- empty-flat rate after robust unwrapping: 27.2%

So the current benchmark already suggests that V7 has partial semantic ability, but still suffers from major schema-obedience failures.

### 7.3 V8 priority benchmark
On the same 1000-query gold benchmark, V8 achieved:
- key precision: 61.12%
- key recall: 9.12%
- key F1: 15.88%
- key+value precision: 41.25%
- key+value recall: 6.16%
- key+value F1: 10.72%

Relative to V7, this is a negative but useful result:
- precision stayed reasonably high when V8 emitted matches
- recall dropped sharply
- exact key+value F1 also dropped below V7

So increasing LoRA capacity and adding more gold supervision did not automatically solve the priority problem. The current evidence suggests the bottleneck is not only model capacity. Data mixture quality and schema obedience still matter.

### 7.4 Interpretation
The priority task appears meaningfully harder than flat extraction. That is actually a useful research finding:
- the task is non-trivial
- the schema is rich and expressive
- stronger supervision and better optimization are required

A more precise current interpretation is:
- qmeans is still stronger at broad key recovery
- V7 priority is already better at exact value-grounded matches once a key is predicted
- V8 shows that a larger training recipe can still fail if it does not improve structured recall
- the main gap to close is recall and schema obedience, not only precision

## 8. Current Engineering Status
At the time of this draft:
- V8 evaluation is complete
- V9 fine-tuning is complete and evaluation is running
- V10 clean-schema fine-tuning is complete and evaluation is running

This means the remaining blocker before a fuller paper rewrite is benchmark completion for V9 and V10, not additional training launches.

## 9. Main Hypothesis
Our central hypothesis is:

If a model can learn both attribute order and key-synonym order, then downstream search systems can perform better query understanding than with unordered extraction alone.

## 10. Expected Contributions
The paper can eventually claim four contributions if results become strong enough:
1. A new task formulation for priority-ordered attribute extraction from search queries.
2. A structured JSON output schema that jointly models values, attribute order, and key preference order.
3. A benchmark setup for evaluating both extraction accuracy and priority-aware behavior.
4. An empirical study showing where priority extraction helps and where it currently fails.

## 11. Limitations
This draft should state the current limitations clearly:
- novelty is promising but not yet validated through a formal literature survey
- V7 priority recall is weak
- the current benchmark for priority correctness can be improved
- the system has been tested mainly in an industrial-query setting, not yet across broad domains

## 12. Practical Value if Successful
If the approach succeeds, it can support:
- industrial product search
- marketplace query routing
- product normalization pipelines
- faceted search generation
- catalog mapping and enrichment

## 13. Next Steps
1. Finish V9 and V10 evaluation on the same 1000-query benchmark.
2. Compare V7, V8, V9, V10, and qmeans in one table.
3. Perform error analysis for missing attributes, wrong priority rank, and wrong key synonym order.
4. Define a clearer metric for priority-order correctness.
5. Add rank-aware metrics on top of the current flat evaluator.
6. Rewrite the paper after V9 and V10 metrics are available.

## 14. Simple Explanation for Non-Researchers
This project is trying to teach a model not only to understand what is in a search query, but also what matters first.

That makes it useful for real search systems where the same query can have multiple attributes, but not all attributes are equally important.

## 15. Suggested Message to Senior Reviewer
Suggested cover note:

“This is an early internal draft for a research direction we are exploring. The core idea is priority-ordered attribute extraction from search queries, where the model predicts both the extracted values and their relative importance order. We already see promise from earlier fine-tuning results, but the first priority-specific model still has recall issues. We are running stronger follow-up experiments now and want feedback on the problem framing, novelty positioning, and evaluation strategy.”