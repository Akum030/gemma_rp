# Senior Status Update — 11 May 2026

## Current Position
The research direction is valid, but the problem is not solved yet.

The strongest confirmed priority model is still `V7`.

The senior CSV snapshot is here: [senior_status_update_may11.csv](senior_status_update_may11.csv)

No standalone finetuned priority model has yet beaten qmeans on key F1.

However, the best current serving path is now a hybrid:
- keep `V7` for priority-ordered structured extraction
- fill missing attributes from qmeans when that endpoint is reachable

On the trusted 1k benchmark, that hybrid serving path reaches:
- key F1: 54.38%
- key+value F1: 17.22%

That is better than both standalone qmeans and standalone V7.

## Confirmed Benchmark Summary

| Model | Key F1 | Key+Value F1 | Main takeaway |
|---|---:|---:|---|
| qmeans | 45.50% | 6.00% | Best broad key coverage baseline |
| V7 | 29.09% | 15.52% | Best exact key+value quality among priority models |
| V8 | 15.88% | 10.72% | Higher capacity plus added gold supervision did not help |
| V9 | 4.75% | 2.69% | Stronger gold weighting sharply reduced recall |
| V10 | 0.00% | 0.00% | Clean-schema-only alignment collapsed extraction |

Hybrid serving note:
- `V7 + qmeans-missing-key fallback` = key F1 54.38%, key+value F1 17.22%

## What We Have Learned
- Priority-ordered extraction is a real and difficult problem, not a trivial extension of flat extraction.
- The first strong priority model `V7` already beats qmeans on exact key+value quality.
- Later aggressive changes made the model worse, not better.
- This is useful research evidence because it shows the real bottleneck is recall plus schema obedience, not just raw model capacity.

## Paper Status
- Internal paper draft is ready for senior review: [research_paper_draft_v2.md](research_paper_draft_v2.md)
- The draft now includes the full completed comparison through `V11`.
- The draft also now distinguishes standalone model results from the best current hybrid serving result.
- The current claim is framed safely as an underexplored structured prediction problem, not a world-first claim.

## Current Action
V11 training and evaluation are now complete.

V11 metrics on the trusted 1k benchmark:
- key F1: 45.44%
- key+value F1: 20.26%
- V11 beats V7 on both standalone metrics, but qmeans still leads on key F1. V11 also beats qmeans on key+value F1.

For live inference, the preferred script is now [inference_priority_hybrid.py](inference_priority_hybrid.py).

If the remote server still cannot reach qmeans directly, use [inference_priority_split_hybrid.py](inference_priority_split_hybrid.py). That path runs V7 on the remote GPU box, queries qmeans locally, and then merges the two into the final priority-ordered output.

Monitoring automation note:
- [watch_v11_and_finalize.py](watch_v11_and_finalize.py) is now set up to keep polling V11, pull the final artifacts, and trigger report finalization automatically when the remote `v11_eval_summary.json` appears.
- The latest polled snapshot is written to [v11_live_status.md](v11_live_status.md).

qmeans availability note:
- local machine check succeeded on 11 May
- remote training server check timed out, so the current deployment caveat is network reachability from that server rather than a dead endpoint

V11 hypothesis:
- return closer to the successful `V7` recipe
- keep the smaller LoRA adapter size
- preserve broad V6-derived coverage data
- add only a light clean nested-priority bias

The goal is to recover recall without repeating the aggressive failure pattern seen in `V8`, `V9`, and `V10`.

## Recommendation
This work is ready for internal review as a serious research direction.

It is not yet ready for external publication because:
- qmeans still wins on broad recall
- rank-aware metrics are not fully implemented
- V11 is now complete: V11 beats V7 on both standalone metrics, but qmeans still leads on key F1. V11 also beats qmeans on key+value F1.