# Active Finetuning Session Notes

Date: 15 May 2026

## Current Direction
This session restarts finetuning from the V11 point with a publication-oriented goal.

Primary modeling goal:
- improve priority ordering of attributes
- improve key-priority ordering inside each extracted attribute
- preserve V11-level stability while pushing ranking quality higher

Primary publication goal:
- primary paper framing is Gemma 3 vs Gemma 4 on priority-ordered attribute extraction for industrial search queries
- qmeans should remain only an optional internal reference, not the center of the paper
- focus the external story on how Gemma 4 solves attribute priority order, key-priority order, and structured extraction better on real examples
- collect publication-grade examples for Gemma 3 versus Gemma 4, and also cases where Gemma 4 is logically stronger than incomplete ground truth
- keep a separate bucket for optional internal baseline examples, but do not let them dominate the paper narrative

## This Session's Run Plan
- base point: V11
- next run label: V12
- hypothesis: V11 was strong because it balanced broad coverage and clean structure. The next improvement should not be a more aggressive clean-only push. Instead, it should increase exposure to multi-attribute ranked examples so the model learns ordering better.
- planned change: oversample rows with 2+ and 3+ attributes across the mixed dataset while keeping LoRA size and the broad mixed-data recipe close to V11.

## Tracking Files In This Folder
- version_history.csv: one row per experiment version and its intent
- results_summary.csv: compact metric rollup across runs
- publication_examples.csv: strong real examples for paper and presentation use

## Immediate Deliverables
- create V12 training script and runner
- launch V12 on server
- save logs and outputs under V12 names
- commit and push tracking + V12 config to GitHub

## V12 Launch Status
- launch time: 15 May 2026, 08:03 IST
- server: amit_87483@34.93.58.248
- gpu status before launch: both Tesla T4 GPUs idle
- command style: nohup background run
- active process observed:
	- `bash ./run_v12_train_and_eval.sh`
	- `/home3/indiamart/gemma_4/gemma4_env/bin/python /home3/indiamart/gemma_4/finetune_gemma4_v12_priority_rankfocus.py`
- server logs:
	- `/home3/indiamart/gemma_4/v12_pipeline.nohup`
	- `/home3/indiamart/gemma_4/v12_train.log`
	- `/home3/indiamart/gemma_4/v12_eval.log` (after training phase)
