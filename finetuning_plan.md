# Finetuning Plan For Priority-Ordered Attribute Extraction

Date: 15 May 2026

## Purpose Of This File

This file is a future-training index for the project. It is meant to be used as a planning sheet before running a new experiment and as a results sheet after each run finishes.

How to use this file:

1. Pick one training state from the table.
2. Implement that state as a new versioned training script and runner.
3. Run training and evaluation.
4. Come back to this file and fill the blank result block under that state.
5. Add any lessons learned before moving to the next state.

Important:

- The result fields under each state are intentionally blank right now.
- They are meant to be filled later after the run is completed.
- Fill at least: status, adapter path, train log path, eval summary path, key F1, key+value F1, ranking notes, and conclusion.

## Problem We Are Solving

The task is not normal flat attribute extraction. The target is a ranked structured extraction problem for industrial search queries.

For a query like:

`siemens 45 hp 3 phase 1440 rpm motor`

the model should not only identify the attributes, but also:

1. decide which attribute matters most,
2. assign attributes in priority order,
3. assign the preferred key name first for each value,
4. keep alternate valid key names as lower-priority synonyms,
5. return valid nested JSON in the expected schema.

So the model has to learn all of the following together:

- extraction correctness,
- schema obedience,
- attribute priority ordering,
- key-synonym priority ordering.

That is why a simple increase in clean data or a simple increase in LoRA capacity has not always helped. Some earlier runs improved structure at the cost of recall, and some improved precision while collapsing useful extraction behavior.

## Model And Training Context

Current base model family:

- `gemma-4-e4b-it`

Current finetuning style:

- LoRA / QLoRA style training through Unsloth
- 4-bit loading
- TRL `SFTTrainer`
- nested JSON generation task

Current practical lessons from completed runs:

- Smaller LoRA settings with broad mixed data were more stable than aggressive larger-capacity runs.
- Pure clean-only alignment was too restrictive and collapsed extraction.
- Balanced mixtures of nested priority data and flat-to-nested converted data worked better than over-pure training.
- Multi-attribute rows matter because they teach the model real ordering behavior.
- For publication, training should focus more on ground-truth quality, ranking quality, and real examples than on internal baseline comparison.

## Research Paper Framing Lock

This section is the guardrail for the paper direction.

Primary paper topic:

- Gemma 3 versus Gemma 4 for priority-ordered attribute extraction from industrial search queries

Primary claim direction:

- Gemma 4 is being trained to solve the real ranked attribute problem:
	- which attributes are present,
	- which attribute is most important,
	- which key name should be preferred first,
	- how to return a valid nested structure.

What should not become the main paper story:

- the paper should not read like only a qmeans versus Gemma 4 comparison
- qmeans can appear as limited internal context or appendix material, but not as the core scientific narrative

What should become the main paper story:

- Gemma 3 versus Gemma 4
- ground-truth aligned evaluation
- ranked attribute behavior
- key-priority behavior
- real query examples where Gemma 4 captures user intent better
- real query examples where Gemma 4 is more complete or more logically ordered than older outputs

Paper example buckets to actively collect:

1. Gemma 3 versus Gemma 4 on the same query
2. Gemma 4 strong priority-order wins
3. Gemma 4 strong key-priority wins
4. Gemma 4 better-than-incomplete-ground-truth examples
5. optional internal baseline examples kept separate from the main narrative

## Completed Finetuning History

This section is not a future plan. It is the completed or active history so that this file also works as a training ledger.

| Version | Status | Main Idea | What Happened | Key F1 | Key+Value F1 | Practical Takeaway |
|---|---|---|---|---:|---:|---|
| v2 | completed | early nested-priority baseline | first baseline for priority-style training | not standardized | not standardized | useful historically, not the main reference point now |
| v7 | completed | restore nested priority objective | first useful structured priority model | 29.09% | 15.52% | proved the ranked schema is learnable |
| v8 | completed | larger capacity plus stronger supervision | recall regressed badly | 15.88% | 10.72% | more aggressive training was not better |
| v9 | completed | heavier gold weighting | recall collapsed even further | 4.75% | 2.69% | too much gold emphasis narrowed the model |
| v10 | completed | clean-only schema alignment | collapsed to zero extraction | 0.00% | 0.00% | pure clean-only alignment is too restrictive |
| v11 | completed | balanced rollback from failed aggressive runs | best stable standalone run so far | 45.44% | 20.26% | current strongest stable recipe |
| v12 | in progress | ranking-focused continuation from v11 | training active; evaluation not available yet | pending | pending | active run focused on multi-attribute ranking behavior |

## Current Active Item

Current active training:

- actual run: `v12`
- script: `finetune_gemma4_v12_priority_rankfocus.py`
- runner: `run_v12_train_and_eval.sh`
- server: `amit_87483@34.93.58.248`
- adapter target: `/home3/indiamart/gemma_4/isq-gemma4-e4b-v12-priority-rankfocus`
- current state: training still running, no eval summary yet

Latest observed live notes:

- V12 is still training on the server
- no `v12_eval_summary.json` exists yet
- training log shows the run is active and progressing
- V12 is the current ranking-focused branch of work

## Next Selected Item

Because V12 is already the ranking-focused continuation, the next item to prepare after V12 should be:

- `FT-09: v21_hard_example_mix`

Why this is the next best item:

- it directly uses real model failures instead of only changing hyperparameters
- it is the best bridge from raw finetuning to publication-grade examples
- it can improve both results and the final paper story at the same time
- it is especially useful once V12 results are available and we can mine strong failure cases

## Planning Approach

The recommended training strategy is not random search. It should be controlled and grouped into experiment families.

This plan uses the following experiment families:

1. stability-preserving runs
2. ranking-focused runs
3. schema-compliance runs
4. hard-example runs
5. curriculum or staged runs
6. inference-aware training runs

The goal is to improve the final output without repeating the known failure modes from earlier experiments.

What should be measured for every run:

- key precision / recall / F1
- key+value precision / recall / F1
- parse rate
- schema compliance rate
- placeholder-key rate
- deep-wrapper rate
- attribute-order correctness notes
- key-priority correctness notes
- 5 to 10 strong real examples for publication use
- paired Gemma 3 / Gemma 4 example notes wherever available
- explicit note on whether the run improves the actual paper story or only internal metrics

## Future Finetuning States Table

These are suggested future states. They can later become concrete version labels such as `v13`, `v14`, and so on.

| State | Suggested Version | Starting Point | Main Change | Data Strategy | LoRA / Core Hyperparameters | Why Test It | Fill Later: Result |
|---|---|---|---|---|---|---|---|
| FT-01 | v13_stable_longer | V11 recipe | keep V11 recipe, train slightly longer | cat74 nested + v6 flat->nested + gold once | r=32, alpha=64, dropout=0, seq=768, epochs=3, lr=6e-5, warmup=100, batch=2, grad_acc=16 | tests whether V11 was undertrained rather than underdesigned | pending |
| FT-02 | v14_rank_focus_light | V11 recipe | light multi-attribute oversampling | same as V11 + repeat rows with >=2 attrs | r=32, alpha=64, dropout=0, seq=768, epochs=2, lr=7e-5, warmup=100 | safer ranking push without large distribution shift | pending |
| FT-03 | v15_rank_focus_heavy | FT-02 | stronger oversampling for >=2 and >=3 attrs | mixed data + strong rank-focused repeats | r=32, alpha=64, dropout=0, seq=768, epochs=2, lr=6e-5, warmup=120 | checks whether stronger ordering emphasis helps more than light oversampling | pending |
| FT-04 | v16_long_context | V11 recipe | increase sequence length | same mix as V11 | r=32, alpha=64, dropout=0, seq=1024, epochs=2, lr=7e-5, warmup=100 | useful if longer outputs or longer queries are being truncated | pending |
| FT-05 | v17_small_dropout | V11 recipe | add LoRA dropout | same mix as V11 | r=32, alpha=64, dropout=0.05, seq=768, epochs=2, lr=7e-5 | tests whether mild regularization improves generalization | pending |
| FT-06 | v18_mid_capacity | V11 recipe | moderate LoRA capacity increase only | same mix as V11 | r=48, alpha=96, dropout=0.05, seq=768, epochs=2, lr=6e-5 | tests capacity increase without going all the way to the unstable V8/V9 style | pending |
| FT-07 | v19_gold_light_plus | V11 recipe | slightly more gold, not aggressive | same mix + gold repeat x2 | r=32, alpha=64, dropout=0, seq=768, epochs=2, lr=6e-5 | checks whether a small increase in gold supervision helps without recall collapse | pending |
| FT-08 | v20_schema_repair_balanced | V11 recipe | clean nested boost but keep broad coverage | cat74 nested repeated more + v6 + gold once | r=32, alpha=64, dropout=0, seq=768, epochs=2, lr=5e-5 | attempts schema improvement without repeating V10 clean-only failure | pending |
| FT-09 | v21_hard_example_mix | V11 or FT-02 | add hard examples | mixed data + curated failure cases + malformed outputs repaired into targets | r=32, alpha=64, dropout=0, seq=768, epochs=2, lr=6e-5 | directly attacks observed failure patterns and real bad cases | pending |
| FT-10 | v22_two_stage_curriculum | V11 recipe | stage training: broad then rank-focused | stage 1 broad mixed data, stage 2 multi-attribute + schema-clean subset | r=32, alpha=64, dropout=0, seq=768, epochs=1+1, lr=7e-5 then 5e-5 | tests whether curriculum works better than one-shot mixing | pending |
| FT-11 | v23_topk_synonym_focus | V11 or FT-02 | emphasize key-priority correctness | mixed data + extra weight via repeated rows where synonym ordering matters | r=32, alpha=64, dropout=0, seq=768, epochs=2, lr=6e-5 | targeted run for key-priority1 correctness and synonym ordering | pending |
| FT-12 | v24_inference_style_alignment | best previous run | align train formatting to final inference style more strictly | same data as best run but exact inference prompt and post-processing assumptions | r=32, alpha=64, dropout=0, seq=768, epochs=1 or 2, lr=5e-5 | sometimes training/inference mismatch causes hidden quality loss | pending |

---

## FT-01: v13_stable_longer

### Meaning Of This State

This state keeps the V11 logic almost unchanged and only asks a simple question: was the model still improving and stopped too early?

### Changes Required

- keep the V11 data mix
- keep LoRA at `r=32`, `alpha=64`
- reduce learning rate slightly from `7e-5` to `6e-5`
- increase epochs from `2` to `3`
- keep broad coverage intact

### Why It Should Be Tested

V11 is currently the best stable standalone recipe. Before making larger design changes, it is worth checking whether a longer, gentler run already improves ranking and extraction quality.

### Fill Later After Run

- status:
- version label used:
- adapter path:
- train log path:
- eval summary path:
- key F1:
- key+value F1:
- parse / schema notes:
- ranking notes:
- publication examples collected:
- conclusion:

---

## FT-02: v14_rank_focus_light

### Meaning Of This State

This is the light version of ranking-focused finetuning. It increases the share of examples that contain multiple attributes, but does not push that distribution too hard.

### Changes Required

- start from V11 data recipe
- repeat rows with `>=2` attributes
- keep overall LoRA size unchanged
- keep epochs short

### Why It Should Be Tested

The main publication goal is better ordered extraction, not only better flat extraction. Multi-attribute rows are the best direct supervision for ranking behavior.

### Fill Later After Run

- status:
- version label used:
- adapter path:
- train log path:
- eval summary path:
- key F1:
- key+value F1:
- parse / schema notes:
- ranking notes:
- publication examples collected:
- conclusion:

---

## FT-03: v15_rank_focus_heavy

### Meaning Of This State

This is the stronger version of the ranking-focused idea. It pushes multi-attribute and high-multi-attribute rows much more heavily.

### Changes Required

- repeat rows with `>=2` attributes more heavily
- repeat rows with `>=3` attributes even more
- keep small stable LoRA settings
- lower LR slightly to offset the stronger curriculum bias

### Why It Should Be Tested

If the light version helps, this state checks whether stronger ranking supervision yields further gains. If it hurts recall or diversity, that itself is useful evidence.

### Fill Later After Run

- status: concept validated and currently running in a close real form as `v12`
- version label used: actual live run is `v12_priority_rankfocus`
- adapter path: `/home3/indiamart/gemma_4/isq-gemma4-e4b-v12-priority-rankfocus`
- train log path: `/home3/indiamart/gemma_4/v12_train.log`
- eval summary path: `/home3/indiamart/gemma_4/v12_eval_summary.json`
- key F1: pending
- key+value F1: pending
- parse / schema notes: pending
- ranking notes: pending
- publication examples collected: pending
- conclusion: pending until V12 finishes

---

## FT-04: v16_long_context

### Meaning Of This State

This state tests whether longer output or longer query contexts are being clipped by the present sequence length.

### Changes Required

- increase max sequence length to `1024`
- keep the V11 recipe otherwise very close
- verify GPU memory remains safe on the T4

### Why It Should Be Tested

Some multi-attribute outputs may need more space, especially when several key synonyms are emitted per attribute. If truncation is happening, ranking quality can degrade silently.

### Fill Later After Run

- status:
- version label used:
- adapter path:
- train log path:
- eval summary path:
- key F1:
- key+value F1:
- parse / schema notes:
- ranking notes:
- publication examples collected:
- conclusion:

---

## FT-05: v17_small_dropout

### Meaning Of This State

This state adds small LoRA dropout while keeping the rest of the stable recipe close to V11.

### Changes Required

- use `lora_dropout=0.05`
- keep `r=32`, `alpha=64`
- keep data mix similar to V11

### Why It Should Be Tested

If the model is becoming too confident on frequent patterns, mild dropout may improve generalization to unseen or noisier queries.

### Fill Later After Run

- status:
- version label used:
- adapter path:
- train log path:
- eval summary path:
- key F1:
- key+value F1:
- parse / schema notes:
- ranking notes:
- publication examples collected:
- conclusion:

---

## FT-06: v18_mid_capacity

### Meaning Of This State

This state tries a moderate capacity increase instead of the more aggressive jump seen in earlier larger-capacity experiments.

### Changes Required

- use `r=48`, `alpha=96`
- add small dropout
- slightly lower LR than V11
- keep broad mixed data

### Why It Should Be Tested

It is still possible that some extra capacity helps ranking and schema fidelity, but the earlier aggressive setting may simply have been too much. This is a controlled middle-ground test.

### Fill Later After Run

- status:
- version label used:
- adapter path:
- train log path:
- eval summary path:
- key F1:
- key+value F1:
- parse / schema notes:
- ranking notes:
- publication examples collected:
- conclusion:

---

## FT-07: v19_gold_light_plus

### Meaning Of This State

This state tests a mild increase in ground-truth supervision without repeating the overly aggressive gold-heavy behavior that hurt recall before.

### Changes Required

- keep mixed broad data
- increase gold repeat from `x1` to `x2`
- lower LR slightly

### Why It Should Be Tested

Ground-truth examples are valuable for publication-quality behavior, but too much gold emphasis can narrow the model. This test checks whether a small increase is the right compromise.

### Fill Later After Run

- status:
- version label used:
- adapter path:
- train log path:
- eval summary path:
- key F1:
- key+value F1:
- parse / schema notes:
- ranking notes:
- publication examples collected:
- conclusion:

---

## FT-08: v20_schema_repair_balanced

### Meaning Of This State

This state focuses on schema correctness, but it does not remove the broad-coverage data entirely.

### Changes Required

- repeat cat74 nested data more strongly
- keep v6 flat->nested data in the mix
- keep gold once
- lower LR to encourage cleaner alignment

### Why It Should Be Tested

The clean-only attempt failed earlier. This state keeps the useful broad data while still nudging the model toward better nested structure and key naming.

### Fill Later After Run

- status:
- version label used:
- adapter path:
- train log path:
- eval summary path:
- key F1:
- key+value F1:
- parse / schema notes:
- ranking notes:
- publication examples collected:
- conclusion:

---

## FT-09: v21_hard_example_mix

### Meaning Of This State

This state uses a curated hard-example set built from real model failures.

### Changes Required

- collect bad cases from current eval outputs
- collect cases with deep wrappers, placeholder keys, wrong product type ordering, wrong brand/type ordering
- repair them into clean targets
- add them into training as a focused subset

### Why It Should Be Tested

This is one of the highest-value experiment types because it directly targets real observed failures instead of generic hyperparameter guessing.

### Fill Later After Run

- status:
- version label used:
- adapter path:
- train log path:
- eval summary path:
- key F1:
- key+value F1:
- parse / schema notes:
- ranking notes:
- publication examples collected:
- conclusion:

---

## FT-10: v22_two_stage_curriculum

### Meaning Of This State

This state splits training into two phases instead of forcing one data mix to do everything.

### Changes Required

- stage 1: broad mixed training like V11
- stage 2: shorter refinement on multi-attribute and cleaner nested rows
- use lower LR in stage 2

### Why It Should Be Tested

The model may need broad exposure first and ranking emphasis second. Curriculum often works when one objective depends on another simpler objective.

### Fill Later After Run

- status:
- version label used:
- adapter path:
- train log path:
- eval summary path:
- key F1:
- key+value F1:
- parse / schema notes:
- ranking notes:
- publication examples collected:
- conclusion:

---

## FT-11: v23_topk_synonym_focus

### Meaning Of This State

This state is aimed specifically at improving `key_priority1` correctness and the ordering of alternative key names.

### Changes Required

- identify rows where synonym ordering truly matters
- repeat those rows in training
- keep attribute ordering mix reasonably broad
- keep LoRA small and stable

### Why It Should Be Tested

The publication story is stronger if the model does not just extract the right value, but also expresses the most meaningful canonical key first. This state targets that claim directly.

### Fill Later After Run

- status:
- version label used:
- adapter path:
- train log path:
- eval summary path:
- key F1:
- key+value F1:
- parse / schema notes:
- ranking notes:
- publication examples collected:
- conclusion:

---

## FT-12: v24_inference_style_alignment

### Meaning Of This State

This state tries to reduce the gap between training-time format and real inference-time format.

### Changes Required

- keep the best data mix from earlier successful states
- match prompt formatting exactly to final inference
- keep output formatting aligned with post-processing assumptions
- use a short low-LR alignment run

### Why It Should Be Tested

Some quality loss comes not from weak supervision, but from mismatch between how the model is trained and how it is actually prompted and parsed in inference.

### Fill Later After Run

- status:
- version label used:
- adapter path:
- train log path:
- eval summary path:
- key F1:
- key+value F1:
- parse / schema notes:
- ranking notes:
- publication examples collected:
- conclusion:

---

## Recommended Run Order

If only a few runs can be afforded, the best order is:

1. FT-01
2. FT-02
3. FT-08
4. FT-09
5. FT-10
6. FT-11

Why this order:

- FT-01 checks whether simple stable training is enough.
- FT-02 tests the most direct ranking-improvement idea.
- FT-08 tests schema repair without clean-only collapse.
- FT-09 tests real failure-driven improvement.
- FT-10 tests curriculum, which may be stronger than one-shot mixing.
- FT-11 isolates key-priority quality for publication claims.

Updated execution note:

- FT-03 equivalent is already active now as `v12`
- once `v12` finishes, the next best real item is `FT-09`
- after that, `FT-10` should be considered if ranking quality improves but structure is still unstable

## What Else Can Improve Results Beyond Hyperparameters

These are additional high-value suggestions beyond the table.

### 1. Build A Hard-Example Training Set

Create a curated file of difficult real queries from failed predictions:

- wrong product type chosen as top priority
- brand missed when present
- technical spec outranking product identity incorrectly
- placeholder keys like `attribute_priorityN`
- deep wrapper nesting
- duplicate or conflicting keys

This is likely one of the best ways to improve publication-quality examples.

### 2. Add Ranking-Aware Evaluation

The current flat extraction metrics are not enough. Add:

- top-1 attribute correctness
- pairwise attribute order accuracy
- top-1 key synonym accuracy
- key-synonym MRR
- exact structured match

Without these, the model may improve on the real task but not show it clearly in results.

### 3. Maintain A Publication Examples Sheet During Training

After each run, capture at least:

- 5 cases where Gemma is clearly better than an internal baseline
- 5 cases where Gemma output is logically stronger than imperfect ground truth
- 5 failure cases still remaining

These examples are often more persuasive than one more decimal point of F1.

### 4. Separate Training Data By Role

Keep training data grouped by purpose:

- broad coverage data
- schema-clean data
- ranking-rich multi-attribute data
- hard-example repair data
- synonym-order-critical data

This makes future ablation experiments much easier and far more scientific.

### 5. Consider Two-Phase Training As A Standard Pattern

Instead of one mixed recipe for everything, use:

- phase 1 for broad extraction learning
- phase 2 for ranking and schema refinement

That may fit this problem better than a single all-purpose distribution.

### 6. Check Truncation Explicitly

Log token lengths for:

- query length
- expected output length
- generated output length

If longer ranking-rich examples are being clipped, improvements in data quality may not show up in final results.

### 7. Keep The Prompt Stable When Testing Data Ideas

If both prompt and data change together, it becomes hard to know what caused improvement. Prefer controlled changes:

- first vary data mix
- then vary capacity
- then vary prompt wording

### 8. Build A Small Manual Ranking Validation Set

Create a small hand-verified set of maybe 100 queries where the attribute order is trusted and reviewed carefully. This can become the cleanest publication validation slice for priority-order claims.

### 9. Save More Intermediate Examples During Evaluation

For each run, save:

- raw output
- parsed output
- flattened output
- matched / missed attributes

This makes post-run analysis far easier and helps build the examples section for the paper.

### 10. Track Results In One CSV And One Narrative File

Use:

- a CSV for metrics and hyperparameters
- a markdown note for qualitative lessons

That keeps experiment management clear and reduces repeated confusion later.

## End Report: What Each Finetuning Says

This section is the short report view of the training history so far.

### v2

Meaning:

- early nested-priority baseline
- historically important, but not the best reference for current modeling choices

What was achieved:

- established an initial priority-style training path

### v7

Meaning:

- first working priority-ordered model after the stronger flat extraction stage

What was achieved:

- showed that the nested ranked schema is actually learnable
- gave the first useful structured baseline for all later comparison

### v8

Meaning:

- tried to improve performance using more aggressive capacity and supervision

What was achieved:

- showed clearly that larger or stronger is not automatically better
- produced an important negative result for future planning

### v9

Meaning:

- tested heavier gold weighting as a refinement strategy

What was achieved:

- showed that too much gold emphasis can destroy recall
- prevented future wasted cycles on the same idea

### v10

Meaning:

- tested whether clean-only data could repair schema behavior

What was achieved:

- showed the limit of over-clean alignment
- confirmed that broad-coverage data is necessary for useful extraction behavior

### v11

Meaning:

- recovery run after the aggressive failures

What was achieved:

- best stable standalone performance so far
- restored confidence in the training direction
- became the main base recipe for future continuation

### v12

Meaning:

- current active continuation focused on ranking-rich multi-attribute supervision

What has been achieved so far:

- training has been launched and is actively running
- the experiment path has shifted toward publication-relevant ranking quality
- this run is expected to teach stronger attribute-order behavior than a pure V11-style repeat

### Overall Short Summary

The finetuning history says the following in simple terms:

- the model can learn the priority schema,
- aggressive tuning alone was not the answer,
- stable mixed-data recipes work better,
- ranking-rich data is the next logical direction,
- the best next improvement after the current run should come from hard examples, not just another random hyperparameter change.

## Questions That Would Improve The Next Planning Pass

These questions do not block this plan, but your answers would make the next revision stronger.

1. Do you want future version labels to continue as `v13`, `v14`, `v15`, or do you want a different naming scheme for publication-oriented runs?
2. Which matters more for the next month: better attribute order, better key-priority order, or stronger exact key+value extraction?
3. Do you want to keep using the same `gold_1k_v2` split for all experiments, or should we create a smaller untouched publication validation slice?
4. Should we create a dedicated hard-example JSONL file next and make that a first-class training asset?
5. Do you want me to turn the top 3 states from this file into ready-to-run scripts immediately after this?

## Final Note

This file is intentionally written as both a planning document and an experiment record template. Do not rewrite it after every run. Instead, keep appending real outcomes into the blank result areas so it becomes the long-term index for the full finetuning journey.