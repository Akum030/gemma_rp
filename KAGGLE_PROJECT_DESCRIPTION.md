## The Problem

Industrial B2B marketplaces process millions of unstructured search queries like "siemens 45 hp 3 phase 1440 rpm motor". Existing extraction systems return an unordered bag of attributes. They cannot tell you which attribute most defines the buyer's intent, nor which canonical key name should be used to represent it. This wastes search relevance, hurts small sellers, and limits AI agents downstream.

## Our Solution

We fine-tuned Gemma 4 E4B using Unsloth + LoRA to perform priority-ordered structured attribute extraction. The model outputs nested JSON ranking attributes by user intent AND ranking canonical key-name synonyms:

```
{
  "attributes": [
    { "attribute_priority1": { "value": "siemens", "key_priority1": "brand",     "key_priority2": "manufacturer" } },
    { "attribute_priority2": { "value": "motor",   "key_priority1": "part_type", "key_priority2": "product_type" } },
    { "attribute_priority3": { "value": "45 hp",   "key_priority1": "power",     "key_priority2": "horsepower" } }
  ]
}
```

This is harder than normal extraction — the model must learn extraction + schema obedience + attribute ranking + synonym ranking jointly, in a single generation pass.

## Why Gemma 4 E4B over Gemma 3

Gemma 3 served as our exploratory baseline (Ollama deployment, early prompting). The full quantitative program was conducted on Gemma 4 E4B because it offers:

- Native function calling and superior nested-JSON schema control
- First-class LoRA fine-tuning via Unsloth
- 4-bit QLoRA deployable on a single Tesla T4 (15 GB) — edge-ready

## Technical Execution

- **Base model:** gemma-4-e4b-it
- **Framework:** Unsloth + TRL SFTTrainer + PEFT LoRA (4-bit QLoRA)
- **Adapter:** r=32, alpha=64, dropout=0
- **Training:** fp16, AdamW 8-bit, cosine LR with 80-step warmup
- **Sequence length:** 768
- **Hardware:** 1× Tesla T4 (15 GB)
- **Learning rate:** 7e-5, 2 epochs, effective batch size 32

## The 12-Version Training Program

| Stage | Outcome |
|---|---|
| V3b | Open-key flat extraction — strong values, noisy keys |
| V5 | Canonical flat — still behind production baseline AttrExt |
| V6 | Canonical flat — **beats AttrExt on exact KV match** (40.7% vs 27.1%) |
| V7 | First priority-ordered model — Key F1 29.09% |
| V8 / V9 / V10 | Aggressive ablations — all collapsed (preserved honestly) |
| V11 | **Best standalone priority** — Key F1 45.44%, K+V F1 20.26% |
| Hybrid V7 + AttrExt | **Best operational** — Key F1 54.38% |

## Results

| System | Key F1 | Key+Value F1 |
|---|---|---|
| AttrExt (production baseline) | 45.50% | 6.00% |
| Our V11 (standalone) | **45.44%** | **20.26%** |
| Hybrid V7 + AttrExt | **54.38%** | 17.22% |

V11 matches the production baseline on Key F1 while outperforming it by **3.4× on Key+Value F1**. The hybrid path provides the strongest operational system.

## Why the Negative Results Strengthen the Work

V8, V9, V10 are preserved ablations, not hidden failures:

- **V8:** larger capacity + aggressive supervision → recall regressed
- **V9:** heavy ground-truth weighting → recall collapsed to 2.45%
- **V10:** clean-only data → total collapse (0% F1)
- **V11:** balanced rollback → strongest standalone result

This sequence demonstrates real research discipline: aggressive supervision can break ranked extraction, balance recovers it.

## Impact & Why It Matters

- **Edge-deployable:** runs on a single Tesla T4 GPU — no expensive cloud LLM APIs
- **Privacy-preserving:** enterprise queries never leave the cluster
- **Democratizes structured search AI** for small industrial sellers in markets like India
- **Fully open:** training scripts, V11 adapter, and 1000-query benchmark are public

## Reproducibility

- Training: `python finetune_gemma4_v11_priority_balanced.py`
- Evaluation: `python eval_priority_adapter.py --adapter <path>`
- All on a single T4 GPU in under a day

## What's in the Repository

- All 12 training scripts (V1 → V12)
- Reusable evaluator with key-alias canonicalization
- 1000-query ground-truth benchmark
- V11 eval summary JSON
- Full research paper (PDF attached)
- Living planning document with 12 future experiment states

**Repository:** https://github.com/Akum030/gemma_rp
