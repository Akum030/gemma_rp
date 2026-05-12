"""
Gemma Fine-Tuning Script - VALIDATED TRAINING
Uses TL approved hyperparameters
Training dataset: gemma_final_training_dataset.jsonl (983 examples)
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import load_dataset
import json

# ============================================================================
# HYPERPARAMETERS (from TL)
# ============================================================================
NUM_EPOCHS = 1
LEARNING_RATE = 2e-5
MAX_LENGTH = 128
BATCH_SIZE = 4
FP16 = True
PACKING = False

MODEL_NAME = "google/gemma-2b"  # or your specific Gemma model
OUTPUT_DIR = "./gemma_qmeans_finetuned"

print("="*80)
print("GEMMA FINE-TUNING - VALIDATED TRAINING")
print("="*80)
print(f"\nHyperparameters:")
print(f"  Model: {MODEL_NAME}")
print(f"  Epochs: {NUM_EPOCHS}")
print(f"  Learning Rate: {LEARNING_RATE}")
print(f"  Max Length: {MAX_LENGTH}")
print(f"  Batch Size: {BATCH_SIZE}")
print(f"  FP16: {FP16}")
print(f"  Packing: {PACKING}")
print(f"  Output: {OUTPUT_DIR}")

# ============================================================================
# LOAD DATASET
# ============================================================================
print(f"\nLoading training dataset...")
dataset = load_dataset("json", data_files="gemma_final_training_dataset.jsonl", split="train")
print(f" Loaded {len(dataset)} training examples")

# ============================================================================
# LOAD MODEL & TOKENIZER
# ============================================================================
print(f"\nLoading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if FP16 else torch.float32,
    device_map="auto"
)
print(f" Model loaded")

# Add padding token if not present
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    model.config.pad_token_id = model.config.eos_token_id

# ============================================================================
# PREPROCESSING
# ============================================================================
def preprocess_function(examples):
    """Convert instruction-output pairs to model inputs"""
    prompts = []
    for instruction, output in zip(examples["instruction"], examples["output"]):
        prompt = f"{instruction}\n\nOutput: {output}"
        prompts.append(prompt)
    
    # Tokenize
    model_inputs = tokenizer(
        prompts,
        max_length=MAX_LENGTH,
        truncation=True,
        padding="max_length",
        return_tensors="pt"
    )
    
    # Labels are the same as input_ids for causal LM
    model_inputs["labels"] = model_inputs["input_ids"].clone()
    
    return model_inputs

print(f"\nPreprocessing dataset...")
tokenized_dataset = dataset.map(
    preprocess_function,
    batched=True,
    remove_columns=dataset.column_names
)
print(f" Dataset preprocessed")

# ============================================================================
# TRAINING ARGUMENTS
# ============================================================================
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    learning_rate=LEARNING_RATE,
    fp16=FP16,
    logging_steps=10,
    save_strategy="epoch",
    save_total_limit=2,
    report_to="none",
    dataloader_pin_memory=False,
    gradient_accumulation_steps=1
)

# ============================================================================
# TRAINER
# ============================================================================
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset
)

# ============================================================================
# TRAINING
# ============================================================================
print(f"\n{'='*80}")
print(f"STARTING TRAINING")
print(f"{'='*80}\n")

trainer.train()

print(f"\n{'='*80}")
print(f"TRAINING COMPLETE")
print(f"{'='*80}")

# ============================================================================
# SAVE MODEL
# ============================================================================
print(f"\nSaving fine-tuned model to {OUTPUT_DIR}...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f" Model saved successfully")

print(f"\n{'='*80}")
print(f"FINE-TUNING COMPLETE!")
print(f"{'='*80}")
print(f"\nNext steps:")
print(f"1. Test the model: python test_gemma_finetuned.py")
print(f"2. Run validation: compare with QMeans outputs")
print(f"3. Check key overlap rate (expect 90%+)")
