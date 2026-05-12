"""
Fine-tune Gemma 2 9B for MCAT Classification
=============================================
Optimized for 2x T4 GPUs with 8-bit quantization + LoRA
Training Data: 20k product records (product name → mcat_name + mcat_id)

Output Format:
{"mcat_name": "Three Phase Induction Motor", "mcat_id": 131725}
"""

import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
    BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset

# ============================================================
# CONFIGURATION
# ============================================================
MODEL_PATH = "/home3/indiamart/func_gemma/models/gemma-2-9b-it"
OUTPUT_DIR = "./mcat-gemma2-9b-finetuned"
TRAIN_FILE = "mcat_train.jsonl"
VAL_FILE   = "mcat_val.jsonl"

USE_8BIT = False   # 8-bit LoRA has inplace-view bug with this peft+bnb version
USE_4BIT = True    # 4-bit NF4 avoids the issue and uses less VRAM

# Hyperparameters (same as ISQ script)
NUM_EPOCHS        = 3
BATCH_SIZE        = 1    # Reduced to 1 due to T4 memory constraints
GRAD_ACCUMULATION = 32   # Effective batch size = 32
LEARNING_RATE     = 2e-5
MAX_LENGTH        = 512  # MCAT outputs are short JSON, most samples well under 512
WARMUP_STEPS      = 50

# LoRA config (same as ISQ script)
LORA_R       = 32
LORA_ALPHA   = 64
LORA_DROPOUT = 0.05


def get_latest_checkpoint(output_dir):
    """Find latest checkpoint for resume capability."""
    if not os.path.exists(output_dir):
        return None
    checkpoints = [
        os.path.join(output_dir, d)
        for d in os.listdir(output_dir)
        if d.startswith("checkpoint-")
    ]
    if not checkpoints:
        return None
    checkpoints.sort(key=lambda x: int(x.split("-")[-1]))
    return checkpoints[-1]


def print_gpu_info():
    """Display GPU information."""
    if torch.cuda.is_available():
        print(f"\n{'='*60}")
        print("GPU Information:")
        print(f"{'='*60}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.2f} GB")
        print(f"{'='*60}\n")


def main():
    print("=" * 60)
    print("Gemma 2 9B Fine-tuning - MCAT Classification")
    print("Training Data: 20k product records")
    print("Output: JSON with mcat_name + mcat_id")
    print("=" * 60)

    print_gpu_info()

    # ============================================================
    # TOKENIZER
    # ============================================================
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH, trust_remote_code=True, use_fast=False
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # ============================================================
    # MODEL + QUANTIZATION
    # ============================================================
    if USE_4BIT:
        print("Configuring 4-bit NF4 quantization...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
    else:
        bnb_config = None

    print("Loading Gemma 2 9B model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )

    model.config.use_cache = False
    model.config.pretraining_tp = 1

    if USE_4BIT:
        model = prepare_model_for_kbit_training(model)

    # ============================================================
    # LoRA ADAPTERS
    # ============================================================
    print("Applying LoRA adapters...")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ============================================================
    # DATASET
    # ============================================================
    print("Loading training data...")
    dataset = load_dataset(
        "json", data_files={"train": TRAIN_FILE, "validation": VAL_FILE}
    )
    print(f"Train samples: {len(dataset['train'])}")
    print(f"Validation samples: {len(dataset['validation'])}")

    # Show a sample
    sample = dataset["train"][0]
    print(f"\nSample instruction (first 200 chars):\n  {sample['instruction'][:200]}...")
    print(f"Sample output:\n  {sample['output']}")

    # ============================================================
    # PROMPT FORMAT (Gemma 2 chat template)
    # ============================================================
    def format_prompt(instruction, output):
        return (
            "<bos><start_of_turn>user\n"
            f"{instruction}<end_of_turn>\n"
            "<start_of_turn>model\n"
            f"{output}<end_of_turn><eos>"
        )

    def tokenize_function(examples):
        texts = [
            format_prompt(i, o)
            for i, o in zip(examples["instruction"], examples["output"])
        ]
        tokenized = tokenizer(
            texts,
            truncation=True,
            max_length=MAX_LENGTH,
            padding=False,
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    print("Tokenizing datasets...")
    tokenized_train = dataset["train"].map(
        tokenize_function,
        batched=True,
        remove_columns=dataset["train"].column_names,
    )
    tokenized_val = dataset["validation"].map(
        tokenize_function,
        batched=True,
        remove_columns=dataset["validation"].column_names,
    )

    # Token length stats
    train_lens = [len(x["input_ids"]) for x in tokenized_train]
    print(f"\nToken length stats (train):")
    print(f"  Min: {min(train_lens)}")
    print(f"  Max: {max(train_lens)}")
    print(f"  Avg: {sum(train_lens) / len(train_lens):.0f}")
    print(f"  Records at MAX_LENGTH ({MAX_LENGTH}): {sum(1 for l in train_lens if l >= MAX_LENGTH)}")

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        pad_to_multiple_of=8,
        label_pad_token_id=-100,
        return_tensors="pt",
    )

    # ============================================================
    # TRAINING ARGUMENTS
    # ============================================================
    print("\nTraining Configuration:")
    print(f"  NUM_EPOCHS: {NUM_EPOCHS}")
    print(f"  BATCH_SIZE: {BATCH_SIZE}")
    print(f"  GRAD_ACCUMULATION: {GRAD_ACCUMULATION}")
    print(f"  EFFECTIVE_BATCH: {BATCH_SIZE * GRAD_ACCUMULATION}")
    print(f"  LEARNING_RATE: {LEARNING_RATE}")
    print(f"  MAX_LENGTH: {MAX_LENGTH}")
    print(f"  WARMUP_STEPS: {WARMUP_STEPS}")
    print(f"  Using FP16")
    print(f"  Quantization: 4-bit NF4")
    print(f"  EVAL: Disabled (to avoid CUDA OOM)")

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type="cosine",
        warmup_steps=WARMUP_STEPS,
        weight_decay=0.01,
        max_grad_norm=1.0,
        fp16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        logging_steps=25,
        save_strategy="steps",
        save_steps=200,
        save_total_limit=3,
        eval_strategy="no",  # Disabled to avoid CUDA OOM
        report_to="none",
        optim="adamw_torch",
        group_by_length=True,
        dataloader_pin_memory=False,
        per_device_eval_batch_size=1,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        data_collator=data_collator,
    )

    # ============================================================
    # TRAIN
    # ============================================================
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("\nGPU cache cleared")

    latest_checkpoint = get_latest_checkpoint(OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("Starting Training")
    print("=" * 60)

    if latest_checkpoint:
        print(f"Resuming from {latest_checkpoint}")
        trainer.train(resume_from_checkpoint=latest_checkpoint)
    else:
        print("Starting training from scratch...")
        trainer.train()

    # ============================================================
    # SAVE
    # ============================================================
    print("\n" + "=" * 60)
    print("Saving model...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print("=" * 60)
    print("Training complete!")
    print("=" * 60)
    print(f"\nModel saved to: {OUTPUT_DIR}")
    print(f"\nTo test inference, run:")
    print(f"  python inference_mcat.py --query 'siemens 1.5 kw three phase motor'")


if __name__ == "__main__":
    main()
