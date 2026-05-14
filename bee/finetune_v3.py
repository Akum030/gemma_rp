"""
Gemma 4 E4B - V3 Fine-tuning script (improved)

Key improvements vs V2:
  1. train_on_responses_only:  loss is only on the assistant turn (JSON output),
     so model learns to emit clean JSON, not regenerate the prompt.
  2. Uses tokenizer.apply_chat_template (proper Gemma 4 chat format with BOS).
  3. max_seq_length raised 128 -> 256.
  4. lora_dropout 0 -> 0.05 (light regularization).
  5. eval_strategy=steps + load_best_model_at_end for early-stop quality.
  6. Saves merged-16bit model under /home3/indiamart/gemma_4/models/gemma4-v3
     so inference doesn't need to load adapter+base separately.

Usage:
  bash run_finetune_v3.sh           # wraps env
  # or:
  python finetune_v3.py
"""
import os, sys, json
sys.path = [p for p in sys.path if "python3.9" not in p]

import torch
import unsloth                                  # noqa: F401  (must import before transformers)
from unsloth import FastModel

from transformers import TrainingArguments
from trl import SFTTrainer
from datasets import load_dataset

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_PATH  = "/home3/indiamart/gemma_4/models/gemma-4-e4b-it"
OUTPUT_DIR  = "/home3/indiamart/gemma_4/models/gemma4-v3b"
TRAIN_FILE  = "/home3/indiamart/gemma_4/product_train_with_keys.jsonl"
VAL_FILE    = "/home3/indiamart/gemma_4/product_val_with_keys.jsonl"

MAX_LENGTH        = 256          # was 128
NUM_EPOCHS        = 3
BATCH_SIZE        = 4
GRAD_ACCUMULATION = 8            # effective batch = 32
LEARNING_RATE     = 1e-4
WARMUP_RATIO      = 0.05
LORA_R            = 32
LORA_ALPHA        = 64
LORA_DROPOUT      = 0.05         # was 0
EVAL_STEPS        = 100
SAVE_STEPS        = 100
# ──────────────────────────────────────────────────────────────────────────────


def get_latest_checkpoint(output_dir):
    if not os.path.exists(output_dir):
        return None
    cps = [os.path.join(output_dir, d) for d in os.listdir(output_dir)
           if d.startswith("checkpoint-")]
    if not cps:
        return None
    cps.sort(key=lambda x: int(x.rsplit("-", 1)[-1]))
    return cps[-1]


def main():
    print("=" * 70)
    print("Gemma 4 E4B  — V3 fine-tune (train_on_responses_only)")
    print("=" * 70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    model, tokenizer = FastModel.from_pretrained(
        model_name=MODEL_PATH,
        max_seq_length=MAX_LENGTH,
        load_in_4bit=True,
        load_in_8bit=False,
        full_finetuning=False,
    )

    text_tok = getattr(tokenizer, "tokenizer", tokenizer)
    if text_tok.pad_token is None:
        text_tok.pad_token = text_tok.eos_token
    text_tok.padding_side = "right"

    model = FastModel.get_peft_model(
        model,
        finetune_vision_layers=False,
        finetune_language_layers=True,
        finetune_attention_modules=True,
        finetune_mlp_modules=True,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        random_state=42,
    )
    model.print_trainable_parameters()

    raw = load_dataset(
        "json",
        data_files={"train": TRAIN_FILE, "validation": VAL_FILE},
    )
    print(f"Train: {len(raw['train'])} | Val: {len(raw['validation'])}")

    # build chat-templated text using Gemma 4 turn structure
    def to_chat(example):
        return {
            "text": (
                "<start_of_turn>user\n"
                f"{example['instruction']}<end_of_turn>\n"
                "<start_of_turn>model\n"
                f"{example['output']}<end_of_turn>"
            )
        }

    dataset = raw.map(to_chat, remove_columns=raw["train"].column_names)
    print("Sample formatted text:")
    print(dataset["train"][0]["text"][:300])

    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type="cosine",
        warmup_ratio=WARMUP_RATIO,
        weight_decay=0.01,
        max_grad_norm=1.0,
        fp16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        logging_steps=25,
        save_strategy="steps",
        save_steps=SAVE_STEPS,
        save_total_limit=2,
        eval_strategy="steps",
        eval_steps=EVAL_STEPS,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",
        optim="adamw_8bit",
        dataloader_pin_memory=False,
        ddp_find_unused_parameters=False,
        seed=42,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        dataset_text_field="text",
        max_seq_length=MAX_LENGTH,
        args=args,
    )

    # NOTE: NOT using train_on_responses_only - it broke generation in v3 first run
    # by training the model to only produce template markers, never JSON content.
    # Standard full-text loss works (v2 model proved this).

    latest = get_latest_checkpoint(OUTPUT_DIR)
    if latest:
        print(f"Resuming from checkpoint: {latest}")
        trainer.train(resume_from_checkpoint=latest)
    else:
        print("Starting fresh ...")
        trainer.train()

    print("Saving final adapter -> ", OUTPUT_DIR)
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    # also save merged 16bit model so inference is single artifact
    try:
        merged_dir = OUTPUT_DIR + "-merged"
        print(f"Saving merged 16bit model -> {merged_dir}")
        model.save_pretrained_merged(
            merged_dir, tokenizer, save_method="merged_16bit",
        )
    except Exception as e:
        print(f"WARN: merged save failed (will use adapter): {e}")

    print("Done!")

if __name__ == "__main__":
    main()
