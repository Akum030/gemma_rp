import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from datasets import load_dataset
import json
import os

print("=" * 60)
print("GEMMA TRAINING - CORRECT ISQ DATASET (3rd Attempt)")
print("=" * 60)

# TL-approved hyperparameters
NUM_EPOCHS = 1
LEARNING_RATE = 2e-5
MAX_LENGTH = 128
BATCH_SIZE = 4
USE_FP16 = True
PACKING = False

MODEL_NAME = "google/gemma-2b"
TRAINING_FILE = "gemma_correct_training_dataset.jsonl"
OUTPUT_DIR = "gemma_isq_finetuned_correct"

print(f"\nHyperparameters:")
print(f"  Epochs: {NUM_EPOCHS}")
print(f"  Learning Rate: {LEARNING_RATE}")
print(f"  Max Length: {MAX_LENGTH}")
print(f"  Batch Size: {BATCH_SIZE}")
print(f"  FP16: {USE_FP16}")
print(f"  Packing: {PACKING}")

# Load training data
print(f"\nLoading training data from {TRAINING_FILE}...")
dataset = load_dataset('json', data_files=TRAINING_FILE)
print(f"✓ Loaded {len(dataset['train'])} training examples")

# Load tokenizer and model
print(f"\nLoading model: {MODEL_NAME}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16 if USE_FP16 else torch.float32,
    device_map="auto"
)

print(f"✓ Model loaded")

# Tokenization function
def tokenize_function(examples):
    prompts = [
        f"{inst}\n{out}" 
        for inst, out in zip(examples['instruction'], examples['output'])
    ]
    
    tokenized = tokenizer(
        prompts,
        truncation=True,
        max_length=MAX_LENGTH,
        padding='max_length',
        return_tensors='pt'
    )
    
    tokenized['labels'] = tokenized['input_ids'].clone()
    return tokenized

print("\nTokenizing dataset...")
tokenized_dataset = dataset['train'].map(
    tokenize_function,
    batched=True,
    remove_columns=['instruction', 'output']
)
print(f"✓ Tokenization complete")

# Training arguments
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    learning_rate=LEARNING_RATE,
    fp16=USE_FP16,
    logging_steps=50,
    save_strategy="epoch",
    report_to="none",
    dataloader_pin_memory=False
)

# Create trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

# Train
print("\n" + "=" * 60)
print("STARTING TRAINING")
print("=" * 60)

trainer.train()

# Save model
print(f"\nSaving model to {OUTPUT_DIR}")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("\n" + "=" * 60)
print("✓ TRAINING COMPLETE")
print("=" * 60)
print(f"Model saved to: {OUTPUT_DIR}")
