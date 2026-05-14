# Priority Error Analysis Notes

## Why This Note Exists
The first V7 summary looked almost unusably bad. After inspecting the raw saved outputs, the main issue was not only the model itself, but also how malformed nested outputs were being flattened by the evaluator.

Once the evaluator was fixed to recursively unwrap nested priority bodies, the V7 benchmark changed substantially.

## Corrected V7 Result
- key precision: 60.49%
- key recall: 19.15%
- key F1: 29.09%
- key+value precision: 32.28%
- key+value recall: 10.22%
- key+value F1: 15.52%

This is still weaker than qmeans on key coverage, but stronger than qmeans on exact key+value F1 under the current priority evaluator.

The saved structural analysis report for the same 1000-query run adds the following V7 diagnostics:
- parsed rate: 80.2%
- deep-wrapper rate: 71.9%
- changed-flat rate: 72.5%
- placeholder-key rate: 19.9%
- empty-flat rate after robust unwrapping: 27.2%

Interpretation:
- most rows still look structurally close enough to parse at the outer JSON level
- a large majority contain extra inner wrapper nesting that a naive evaluator would under-read
- many rows change materially when flattened correctly from the saved `parsed` output instead of trusting the stored `flat` field
- placeholder key emissions remain a real schema-obedience problem even after evaluator repair

## Observed Failure Modes In Raw V7 Outputs
### 1. Extra nested wrapper inside a valid priority slot
Observed pattern:

```json
{
  "attribute_priority1": {
    "attribute_priorityN": {
      "value": "siemens",
      "key_priority1": "brand"
    }
  }
}
```

Expected pattern:

```json
{
  "attribute_priority1": {
    "value": "siemens",
    "key_priority1": "brand"
  }
}
```

Impact:
- the old evaluator treated many of these rows as empty
- the model is showing schema confusion, not pure extraction failure
- this is now quantified: deep wrapper nesting appears in 71.9% of V7 rows

### 2. Placeholder keys instead of real canonical keys
Observed examples:
- `attribute_priorityN`
- `attribute_priority1`
- `attribute_priority2`

Impact:
- extraction may contain a usable value, but key normalization fails
- this hurts recall and exact key+value quality
- placeholder keys still appear in 19.9% of V7 rows

### 3. Generic invented key labels
Observed examples:
- `main_type`
- `secondary_type`
- `family`
- `subtype`

Impact:
- these are semantically plausible, but do not align with the canonical key vocabulary used by evaluation and downstream systems

### 4. Value collapse across multiple attributes
Observed examples where the model packs too much text into one value:
- `ap fan motor & fresh air moter`
- `Positioner Model 6dr5`

Impact:
- correct intent fragments may be present, but not disentangled into separate ranked attributes

### 5. Structural overfitting to prompt words
Observed patterns suggest the model sometimes learns the scaffolding tokens more strongly than the intended attribute semantics.

Impact:
- output appears JSON-like
- but schema obedience is partial and brittle

## What This Means
The priority task is not failing in only one way.

There are two simultaneous gaps:
1. schema obedience gap
2. attribute coverage gap

V9 is aimed mainly at improving coverage through stronger supervision.

V10 is aimed mainly at improving schema obedience by training only on cleaner nested supervision.

## Why V10 Uses Clean Data Only
The converted flat-to-nested V6 data is useful for volume, but it may also teach weak structural habits because its priority structure is synthetic rather than manually authored.

So V10 intentionally removes that noisy source and trains only on:
- cat74 nested priority gold
- gold_1k_v2 converted to the exact nested priority schema

## Practical Hypothesis
If V9 improves recall and V10 improves schema obedience, then a later version can combine both strengths more effectively than V7.