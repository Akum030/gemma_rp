"""
Fine-tune Gemma 2 9B for ISQ Extraction
Optimized for 2x T4 GPUs with 8-bit quantization + LoRA
Updated with TL's hyperparameter suggestions
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

MODEL_PATH = "/home3/indiamart/func_gemma/models/gemma-2-9b-it"
OUTPUT_DIR = "./isq-gemma2-9b-finetuned-v3"
TRAIN_FILE = "product_train_with_keys.jsonl"
VAL_FILE = "product_val_with_keys.jsonl"

USE_8BIT = True

# TL's Optimized Hyperparameters
NUM_EPOCHS = 1          # TL: Reduced from 3 to 1
BATCH_SIZE = 4          # TL: Increased from 1 to 4
GRAD_ACCUMULATION = 8   # Kept at 8
LEARNING_RATE = 2e-5    # TL: Reduced from 1e-4 to 2e-5
MAX_LENGTH = 128        # TL: Reduced from 512 to 128

LORA_R = 32
LORA_ALPHA = 64
LORA_DROPOUT = 0.05

def get_latest_checkpoint(output_dir):
    if not os.path.exists(output_dir):
        return None
    checkpoints = [os.path.join(output_dir, d) for d in os.listdir(output_dir) if d.startswith("checkpoint-")]
    if not checkpoints:
        return None
    checkpoints.sort(key=lambda x: int(x.split("-")[-1]))
    return checkpoints[-1]

def print_gpu_info():
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
    print("Gemma 2 9B Fine-tuning for ISQ Extraction")
    print("Updated with TL's Hyperparameters")
    print("=" * 60)

    print_gpu_info()

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True, use_fast=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    if USE_8BIT:
        print("Configuring 8-bit quantization...")
        bnb_config = BitsAndBytesConfig(
            load_in_8bit=True,
            bnb_8bit_compute_dtype=torch.float16,  # TL: Using FP16 instead of BF16
            bnb_8bit_use_double_quant=True,
        )
    else:
        bnb_config = None

    print("Loading Gemma 2 9B model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        torch_dtype=torch.float16,  # TL: Using FP16 instead of BF16
        device_map="auto",
        trust_remote_code=True
    )

    model.config.use_cache = False
    model.config.pretraining_tp = 1

    if USE_8BIT:
        model = prepare_model_for_kbit_training(model)

    print("Applying LoRA adapters...")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("Loading training data...")
    dataset = load_dataset("json", data_files={"train": TRAIN_FILE, "validation": VAL_FILE})
    print(f"Train samples: {len(dataset['train'])}")
    print(f"Validation samples: {len(dataset['validation'])}")

    def format_prompt(instruction, output):
        return (
            "<bos><start_of_turn>user\n"
            f"{instruction}<end_of_turn>\n"
            "<start_of_turn>model\n"
            f"{output}<end_of_turn><eos>"
        )

    def tokenize_function(examples):
        texts = [format_prompt(i, o) for i, o in zip(examples["instruction"], examples["output"])]
        tokenized = tokenizer(texts, truncation=True, max_length=MAX_LENGTH, padding=False)
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    print("Tokenizing datasets...")
    tokenized_train = dataset["train"].map(tokenize_function, batched=True, remove_columns=dataset["train"].column_names)
    tokenized_val = dataset["validation"].map(tokenize_function, batched=True, remove_columns=dataset["validation"].column_names)

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        pad_to_multiple_of=8,
        label_pad_token_id=-100,
        return_tensors="pt"
    )

    print("Setting up training configuration...")
    print("\nTL's Optimized Hyperparameters:")
    print(f"  NUM_EPOCHS: {NUM_EPOCHS} (was 3)")
    print(f"  BATCH_SIZE: {BATCH_SIZE} (was 1)")
    print(f"  LEARNING_RATE: {LEARNING_RATE} (was 1e-4)")
    print(f"  MAX_LENGTH: {MAX_LENGTH} (was 512)")
    print(f"  Using FP16 (was BF16)")
    
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type="cosine",
        warmup_steps=100,
        weight_decay=0.01,
        max_grad_norm=1.0,
        fp16=True,  # TL: Using FP16 instead of BF16
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        logging_steps=50,
        save_strategy="steps",
        save_steps=500,
        save_total_limit=3,
        eval_strategy="no",
        report_to="none",
        optim="adamw_torch",
        group_by_length=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        data_collator=data_collator
    )

    latest_checkpoint = get_latest_checkpoint(OUTPUT_DIR)

    print("\n" + "=" * 60)
    print("🚀 Starting Training")
    print("=" * 60)

    if latest_checkpoint:
        print(f"Resuming from {latest_checkpoint}")
        trainer.train(resume_from_checkpoint=latest_checkpoint)
    else:
        print("Starting training from scratch...")
        trainer.train()

    print("\n" + "=" * 60)
    print("💾 Saving model...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print("=" * 60)
    print("✓ Training complete!")
    print("=" * 60)
    print(f"\nModel saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
