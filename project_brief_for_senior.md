# Senior Review Brief

## Project Name
Priority-Ordered Attribute Extraction from Search Queries

## One-Line Goal
Build a model that does not only extract attributes from a search query, but also predicts the priority order of those attributes and the preferred synonym key order for each extracted value.

## Business Problem
Most query-understanding systems return unordered key-value pairs.

Example:
- brand = Siemens
- part type = Servo Motor
- power = 1 kW

That is useful, but it does not answer which attribute matters most for user intent.

For industrial search, marketplace search, catalog matching, and ad routing, this missing order matters because:
- the top attribute often drives retrieval quality
- different downstream systems prefer different key names for the same value
- ranking, filtering, matching, and catalog expansion benefit from knowing intent priority

## What We Are Trying to Do Differently
For a single query, we want the model to output:
1. the extracted values
2. the order of importance among those values
3. the synonym ranking for each attribute key

Example query:
- Siemens 1 kW 3 phase servo motor

Target structure:

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
    },
    {
      "attribute_priority4": {
        "value": "3 phase",
        "key_priority1": "phase",
        "key_priority2": "phase_type"
      }
    }
  ]
}
```

## Why This May Be Important
This can help systems like IndiaMART, Amazon-like product search, Google Shopping-like query understanding, or internal catalog search in three ways:
- better retrieval because the most important attribute is known first
- better normalization because synonym-key preference is explicit
- better downstream ranking because intent structure is richer than flat extraction

## Current Experiment Story
### Earlier baseline
- Legacy Gemma V6 flat extraction beat qmeans on exact key+value match rate in the older benchmark.
- Evidence: [bee/comparison_summary.csv](bee/comparison_summary.csv)

### V7
- V7 restored the priority schema.
- After correcting the evaluator to unwrap malformed nested priority wrappers, V7 is no longer near-zero.
- Current V7 numbers on the 1000-query gold benchmark:
  - key precision: 60.49%
  - key recall: 19.15%
  - key F1: 29.09%
  - key+value precision: 32.28%
  - key+value recall: 10.22%
  - key+value F1: 15.52%
- This means V7 is still behind qmeans on key coverage, but ahead of qmeans on exact key+value quality under the current priority evaluator.

### V8
- V8 increased LoRA capacity and added gold supervision.
- Evaluation is complete on the 1000-query benchmark.
- V8 metrics:
  - key F1: 15.88%
  - key+value F1: 10.72%
- This underperformed V7, so higher capacity plus added gold supervision did not solve the recall problem by itself.

### V9
- V9 training completed successfully.
- It uses stronger gold weighting and a lower learning rate for a more stable accuracy push.
- Evaluation is complete on the same 1000-query benchmark.
- V9 metrics:
  - key F1: 4.75%
  - key+value F1: 2.69%
- This performed materially worse than V7 and even worse than V8 on the trusted benchmark.

### V10
- V10 training completed successfully after V9.
- It is a short clean-schema alignment run that removes the noisy flat-to-nested conversion data and trains only on high-quality nested supervision.
- The goal is to improve schema obedience, especially correct `attribute_priorityN` and `key_priorityN` structure.
- Evaluation is complete on the same 1000-query benchmark.
- V10 metrics:
  - key F1: 0.00%
  - key+value F1: 0.00%
- This means clean-schema-only alignment from this setup collapsed extraction almost completely.

### V11
- V11 training and evaluation are now complete.
- key F1: 45.44%
- key+value F1: 20.26%
- V11 beats V7 on both standalone metrics, but qmeans still leads on key F1. V11 also beats qmeans on key+value F1.

### Current Best Serving Path
- The best current overall benchmark result is not a standalone finetuned model. It is a serving-time hybrid.
- The hybrid keeps V7 for priority-ordered structured output and fills missing attributes from qmeans when that endpoint is reachable.
- Hybrid benchmark metrics on the trusted 1000-query set:
  - key precision: 75.60%
  - key recall: 42.46%
  - key F1: 54.38%
  - key+value precision: 23.94%
  - key+value recall: 13.44%
  - key+value F1: 17.22%
- This is the strongest current practical result, but it depends on qmeans endpoint availability and does not replace the need for a stronger standalone priority model.

## Current Status
- Summary table: [priority_project_status.csv](priority_project_status.csv)
- Senior CSV snapshot: [senior_status_update_may11.csv](senior_status_update_may11.csv)
- Paper draft: [research_paper_draft_v2.md](research_paper_draft_v2.md)
- Senior-ready note: [senior_status_update_may11.md](senior_status_update_may11.md)

## Honest Assessment Right Now
The idea is strong and potentially publishable, but the current priority version is not yet strong enough for submission. The best immediate signal is:
- the flat extraction family already showed business value
- the priority schema is conceptually promising
- V7 priority is already competitive on exact key+value quality but still weak on total key recall
- V8 did not improve over V7, which is useful negative evidence and increases confidence that the problem is genuinely hard rather than under-trained only once
- V9 and V10 further confirm that more aggressive supervision changes can make the model much worse, so the next step should be a controlled rollback toward the V7 recipe rather than another aggressive jump
- The new hybrid serving path already gives the strongest practical benchmark result while still preserving the priority-ordered output format
- V11 is now complete: V11 beats V7 on both standalone metrics, but qmeans still leads on key F1. V11 also beats qmeans on key+value F1.
- iteration is still needed, especially to improve coverage without losing precision

## What I Need Review On
1. Is the problem statement strong enough for an internal research direction?
2. Is the novelty claim acceptable if stated carefully as a hypothesis rather than a guaranteed first-in-world claim?
3. Should the next paper version focus on industry impact first, or on model architecture first?
4. What is the best internal benchmark definition for “priority correctness”?

## Recommended Positioning for Now
Do not claim “world first” externally yet.

Safer language:
- We propose a priority-ordered attribute extraction framework for search queries.
- Our literature scan found adjacent work on slot filling, product attribute extraction, query-time attribute extraction, and attribute normalization, but we have not yet found a directly matching formulation that jointly predicts values, attribute importance order, and synonym-key order in one structured output.
- To our knowledge, explicit prediction of both attribute importance order and synonym-key order for industrial search queries is underexplored.
- We are building a benchmark and a model family for this problem.

Evaluation should also be framed carefully:
- flat key and key+value F1 are necessary baseline metrics
- but the final benchmark should separately measure schema obedience, attribute-order correctness, and key-synonym-order correctness