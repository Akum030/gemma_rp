"""
Fine-tune Gemma 2 9B for ISQ Extraction
Optimized for 2x T4 GPUs (32GB VRAM total) with 8-bit quantization + LoRA

Requirements:
- bitsandbytes
- transformers
- peft
- accelerate
- datasets
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
import bitsandbytes as bnb

# ==================== CONFIGURATION ====================

MODEL_PATH = "/home3/indiamart/func_gemma/models/gemma-2-9b-it"
OUTPUT_DIR = "./isq-gemma2-9b-finetuned"
TRAIN_FILE = "product_train.jsonl"
VAL_FILE = "product_val.jsonl"

# 8-bit quantization config (reduces VRAM from ~18GB to ~12GB)
USE_8BIT = True  # Set to False for full precision if you have enough VRAM

# Training hyperparameters (optimized for 9B model)
NUM_EPOCHS = 3
BATCH_SIZE = 1  # Per device
GRAD_ACCUMULATION = 8  # Effective batch size = 8
LEARNING_RATE = 1e-4  # Lower LR for larger model
MAX_LENGTH = 512

# LoRA configuration (less aggressive for 9B model)
LORA_R = 32  # Increased from 16
LORA_ALPHA = 64  # Increased from 32
LORA_DROPOUT = 0.05

# ==================== HELPER FUNCTIONS ====================

def get_latest_checkpoint(output_dir):
    """Resume from latest checkpoint if exists"""
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
    """Display GPU information"""
    if torch.cuda.is_available():
        print(f"\n{'='*60}")
        print("GPU Information:")
        print(f"{'='*60}")
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.2f} GB")
        print(f"{'='*60}\n")
    else:
        print("⚠️  WARNING: No GPU detected! Training will be extremely slow.")

# ==================== MAIN TRAINING ====================

def main():
    print("=" * 60)
    print("Gemma 2 9B Fine-tuning for ISQ Extraction")
    print("=" * 60)
    
    print_gpu_info()
    
    # Load tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH,
        trust_remote_code=True,
        use_fast=False
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Quantization config (8-bit)
    if USE_8BIT:
        print("Configuring 8-bit quantization...")
        bnb_config = BitsAndBytesConfig(
            load_in_8bit=True,
            bnb_8bit_compute_dtype=torch.bfloat16,
            bnb_8bit_use_double_quant=True,  # Extra compression
        )
    else:
        bnb_config = None
        print("Using full precision (bf16)...")
    
    # Load model
    print("Loading Gemma 2 9B model...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        quantization_config=bnb_config,
        torch_dtype=torch.bfloat16,
        device_map="auto",  # Automatically distribute across GPUs
        trust_remote_code=True
    )
    
    model.config.use_cache = False
    model.config.pretraining_tp = 1  # Tensor parallelism
    
    # Prepare model for k-bit training
    if USE_8BIT:
        model = prepare_model_for_kbit_training(model)
    
    # LoRA configuration
    print("Applying LoRA adapters...")
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj"
        ],
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Load datasets
    print("Loading training data...")
    dataset = load_dataset(
        "json",
        data_files={"train": TRAIN_FILE, "validation": VAL_FILE}
    )
    
    print(f"Train samples: {len(dataset['train'])}")
    print(f"Validation samples: {len(dataset['validation'])}")
    
    # Tokenization function
    def format_prompt(instruction, output):
        """Format in Gemma 2 chat template"""
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
            padding=False
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized
    
    # Tokenize datasets
    print("Tokenizing datasets...")
    tokenized_train = dataset["train"].map(
        tokenize_function,
        batched=True,
        remove_columns=dataset["train"].column_names,
        desc="Tokenizing train"
    )
    
    tokenized_val = dataset["validation"].map(
        tokenize_function,
        batched=True,
        remove_columns=dataset["validation"].column_names,
        desc="Tokenizing validation"
    )
    
    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        pad_to_multiple_of=8,
        label_pad_token_id=-100,
        return_tensors="pt"
    )
    
    # Training arguments
    print("Setting up training configuration...")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        
        # Training schedule
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        
        # Optimization
        learning_rate=LEARNING_RATE,
        lr_scheduler_type="cosine",
        warmup_steps=100,
        weight_decay=0.01,
        max_grad_norm=1.0,
        
        # Precision & performance
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        
        # Logging & saving
        logging_steps=50,
        save_strategy="steps",
        save_steps=500,
        save_total_limit=3,
        
        # Evaluation
        eval_strategy="steps",
        eval_steps=500,
        
        # Multi-GPU
        ddp_find_unused_parameters=False,
        
        # Misc
        report_to="none",
        optim="adamw_torch",  # Use PyTorch AdamW
        group_by_length=True,  # Efficiency boost
    )
    
    # Trainer
    print("Initializing trainer...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        data_collator=data_collator
    )
    
    # Check for checkpoint
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
    
    # Save final model
    print("\n" + "=" * 60)
    print("💾 Saving model...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    
    print("=" * 60)
    print("✓ Training complete!")
    print("=" * 60)
    print(f"\nModel saved to: {OUTPUT_DIR}")
    print(f"\nNext steps:")
    print(f"  1. Test the model with inference script")
    print(f"  2. Evaluate on test set")
    print(f"  3. Deploy for production")

if __name__ == "__main__":
    main()
