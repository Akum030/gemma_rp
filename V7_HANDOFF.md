# V7 Priority Finetuning — Status & Handoff

## ✅ Status: TRAINING LIVE
- **Process**: PID `100759` on `34.93.58.248`
- **Started**: 14:48 IST
- **Progress at 14:58**: step 4/384 (1%) — ~67 sec/step
- **ETA**: ~7 hours total
- **GPU**: 14.7 GB / 15 GB on Tesla T4 (utilization 100%)

## What V7 fixes vs V6
V6 dropped the priority structure that V4 had. V7 restores it:
- **Output schema**: `{"attributes":[{"attribute_priority1":{"value":"...","key_priority1":"...","key_priority2":"...",...}}, ...]}`
- For each query, the model now learns BOTH:
  1. Which attribute matters most → `attribute_priorityN` ranking
  2. The synonym hierarchy for each attribute → `key_priority1..N`

## Dataset (8,149 train / 1,128 val)
Built at startup by `finetune_gemma4_v7_priority.py`:
1. **`cat74_train_nested.jsonl`** (1,600 train / 400 val) — original V4 priority gold (real multi-synonym key rankings from cat74 motor data)
2. **`v6_train.jsonl`** flat → nested (6,549 train / 728 val) — converted using:
   - `VOCAB[canonical_key] = [synonym1, synonym2, ...]` from TRAINING_PROMPT_PRIORITY_VERSION.txt
   - `RANK[canonical_key] = base attribute_priority` (brand=1, part_type=2, power=3, model=4, …)

Saved to `/home3/indiamart/gemma_4/v7_train.jsonl` and `v7_val.jsonl`.

## Files
| Local | Server |
|---|---|
| `finetune_gemma4_v7_priority.py` | `/home/indiamart/gemma_4/finetune_gemma4_v7_priority.py` |
| `inference_v7.py` | `/home/indiamart/gemma_4/inference_v7.py` |
| `inference_priority_hybrid.py` | `/home/indiamart/gemma_4/inference_priority_hybrid.py` |
| `inference_priority_split_hybrid.py` | local launcher only |
| `v7_dryrun.py` | `/home/indiamart/gemma_4/v7_dryrun.py` |
| — | `/home/indiamart/gemma_4/v7_train.log` (training log) |
| — | `/home3/indiamart/gemma_4/isq-gemma4-e4b-v7-priority/` (output dir, LoRA adapters) |

## Hyperparameters
- Base: `gemma-4-e4b-it` (4-bit QLoRA via Unsloth)
- LoRA: r=32, alpha=64, all attention + MLP modules
- 3 epochs × 384 steps (effective batch = 64, lr=1e-4 cosine)
- max_seq_length=768, fp16, adamw_8bit, gradient_checkpointing
- Early stopping patience=3 on eval_loss, eval+save every 200 steps

## Critical fix discovered & applied
SFTTrainer crashed at step 1 with `'int' object has no attribute 'mean'`.
**Fix** (now in script): `trainer.model_accepts_loss_kwargs = False` immediately after creating SFTTrainer. (Saved to user memory.)

## How to monitor
```bash
ssh amit_87483@34.93.58.248
ps -p 100759 -o pid,etime,%mem
tail -50 /home/indiamart/gemma_4/v7_train.log
nvidia-smi
ls /home3/indiamart/gemma_4/isq-gemma4-e4b-v7-priority/    # checkpoints appear every 200 steps
```

## How to run inference (after training completes)
Preferred path for best accuracy:

```bash
ssh amit_87483@34.93.58.248
/home3/indiamart/gemma_4/gemma4_env/bin/python /home/indiamart/gemma_4/inference_priority_hybrid.py --query "siemens 45 hp 3 phase motor"
```

This path keeps the V7 priority-ordered output format and fills missing attributes from qmeans when the qmeans endpoint is reachable.

If the remote server cannot reach qmeans directly, use the local split launcher instead:

```bash
c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/.venv/Scripts/python.exe c:/Users/Imart/CopilotHacksAndPersonal/IM_Repos/finetuning_gemma_4/inference_priority_split_hybrid.py --query "siemens 45 hp 3 phase motor"
```

That path runs V7 on the remote GPU box, calls qmeans locally, and merges the results into the final priority-ordered output.

Fallback path if you want raw V7-only inference:

```bash
ssh amit_87483@34.93.58.248
/home3/indiamart/gemma_4/gemma4_env/bin/python /home/indiamart/gemma_4/inference_v7.py
# Or with custom queries:
/home3/indiamart/gemma_4/gemma4_env/bin/python /home/indiamart/gemma_4/inference_v7.py --query "siemens 45 hp 3 phase motor"
# Or batch:
/home3/indiamart/gemma_4/gemma4_env/bin/python /home/indiamart/gemma_4/inference_v7.py --queries /home3/indiamart/gemma_4/76cat_queries
```

Hybrid output: `/home3/indiamart/gemma_4/hybrid_priority_inference_results.jsonl`

V7-only output: `/home3/indiamart/gemma_4/v7_inference_results.jsonl` (each row: `{query, raw, parsed, secs}`).

## Sample expected output
Query: `"siemens 45 hp 3 phase 1440 rpm motor"` →
```json
{"attributes":[
  {"attribute_priority1":{"value":"siemens","key_priority1":"brand","key_priority2":"manufacturer","key_priority3":"company","key_priority4":"make"}},
  {"attribute_priority2":{"value":"motor","key_priority1":"part_type","key_priority2":"product_type","key_priority3":"category"}},
  {"attribute_priority3":{"value":"45 hp","key_priority1":"power","key_priority2":"horsepower","key_priority3":"hp","key_priority4":"motor_power"}},
  {"attribute_priority4":{"value":"3 phase","key_priority1":"phase","key_priority2":"phase_type"}},
  {"attribute_priority5":{"value":"1440 rpm","key_priority1":"rpm","key_priority2":"speed","key_priority3":"rated_speed"}}
]}
```

## Next steps when training finishes (≈ 22:00 IST)
1. Final adapters saved to `/home3/indiamart/gemma_4/isq-gemma4-e4b-v7-priority/`
2. Run inference_v7.py on a sanity batch
3. Optionally deploy via Ollama: needs GGUF conversion (note: prior conversion attempts OOM'd — would need merged-model conversion on a higher-RAM box, OR just serve via vLLM/Transformers from the LoRA dir directly)
