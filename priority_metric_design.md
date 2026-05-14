# Priority Metric Design

## Why This Note Exists
The current evaluator is useful, but it does not fully measure the research goal.

Right now, the main reported metrics are:
- key-only precision/recall/F1
- key+value precision/recall/F1

These metrics are necessary, but they mostly evaluate flat extraction quality. They do not directly score whether the model got the attribute ranking or key-synonym ranking correct.

## Recommended Metric Stack

### 1. Schema Compliance Rate
Definition:
- percentage of rows that parse into the required nested structure without repair

Why it matters:
- the method is only useful downstream if the output format is reliable

Suggested sub-metrics:
- outer-JSON parse rate
- nested-schema compliance rate
- placeholder-key rate
- deep-wrapper rate

### 2. Attribute Detection Quality
Definition:
- current key-only and key+value precision/recall/F1 over the extracted attribute set

Why it matters:
- this remains the base extraction layer

### 3. Attribute Priority Accuracy
Definition:
- score whether the model assigns the correct relative order among matched attributes

Recommended views:
- exact top-1 attribute accuracy
- exact ordered list accuracy for the first `k` attributes
- pairwise order accuracy
- Kendall tau or Spearman correlation on matched ranked attributes

Example:
- gold order: `brand > product_type > power`
- prediction: `product_type > brand > power`
- set overlap may still be good, but rank quality is wrong

### 4. Key-Synonym Priority Accuracy
Definition:
- for each extracted value, score whether the predicted `key_priority1`, `key_priority2`, etc. match the gold synonym ordering

Recommended views:
- top-1 canonical key accuracy
- mean reciprocal rank over the gold synonym list
- pairwise order accuracy inside the synonym list

Example:
- gold: `power > horsepower`
- prediction: `horsepower > power`
- flat extraction may look acceptable, but preferred key order is still wrong

### 5. End-to-End Exact Structured Match
Definition:
- percentage of rows where the entire nested prediction matches gold exactly up to the evaluation depth

Why it matters:
- this is the strictest downstream-readiness metric

## Suggested Reporting Layout For The Paper

### Table A: Extraction Quality
- key precision, recall, F1
- key+value precision, recall, F1

### Table B: Structural Quality
- parse rate
- schema compliance rate
- placeholder-key rate
- deep-wrapper rate

### Table C: Ranking Quality
- top-1 attribute accuracy
- pairwise attribute order accuracy
- top-1 key-synonym accuracy
- key-synonym MRR

### Table D: End-to-End Quality
- exact structured match rate

## Practical Recommendation
For the next evaluation pass, do not replace the current flat metrics. Add the ranking metrics on top.

That keeps the benchmark comparable with qmeans and older baselines while also measuring the real novelty target: priority-aware structured extraction.

## Short Version
If we only report flat F1, then we are under-measuring the core contribution.

The paper should separate:
- extraction correctness
- schema obedience
- attribute order correctness
- key-synonym order correctness