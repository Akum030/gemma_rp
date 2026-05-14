import os, sys, torch
sys.path = [p for p in sys.path if 'python3.9' not in p]

import unsloth
from unsloth import FastModel
from transformers import TrainingArguments
from trl import SFTTrainer
from datasets import load_dataset

MODEL_PATH  = "/home3/indiamart/gemma_4/models/gemma-4-e4b-it"
OUTPUT_DIR  = "/home3/indiamart/isq-gemma4-e4b-v2"
TRAIN_FILE  = "/home3/indiamart/gemma_4/product_train_with_keys.jsonl"
VAL_FILE    = "/home3/indiamart/gemma_4/product_val_with_keys.jsonl"

MAX_LENGTH        = 128
NUM_EPOCHS        = 3       # was 1
BATCH_SIZE        = 4
GRAD_ACCUMULATION = 8
LEARNING_RATE     = 1e-4    # higher LR works better with more epochs
WARMUP_STEPS      = 100

def get_latest_checkpoint(output_dir):
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

def main():
    print("=" * 60)
    print("Gemma 4 E4B — V2 Retraining (3 epochs)")
    print("=" * 60)

    model, tokenizer = FastModel.from_pretrained(
        model_name=MODEL_PATH,
        max_seq_length=MAX_LENGTH,
        load_in_4bit=True,
        load_in_8bit=False,
        full_finetuning=False,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = FastModel.get_peft_model(
        model,
        finetune_vision_layers=False,
        finetune_language_layers=True,
        finetune_attention_modules=True,
        finetune_mlp_modules=True,
        r=32,
        lora_alpha=64,
        lora_dropout=0,        # 0 for fast patching
        bias="none",
        random_state=42,
    )
    model.print_trainable_parameters()

    dataset = load_dataset(
        "json",
        data_files={"train": TRAIN_FILE, "validation": VAL_FILE},
    )
    print(f"Train: {len(dataset['train'])} | Val: {len(dataset['validation'])}")

    def format_prompt(instruction, output):
        return (
            "<start_of_turn>user\n"
            f"{instruction}<end_of_turn>\n"
            "<start_of_turn>model\n"
            f"{output}<end_of_turn>"
        )

    def format_dataset(examples):
        return {"text": [
            format_prompt(i, o)
            for i, o in zip(examples["instruction"], examples["output"])
        ]}

    dataset = dataset.map(format_dataset, batched=True)

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
        logging_steps=50,
        save_strategy="steps",
        save_steps=200,
        save_total_limit=2,
        eval_strategy="no",
        report_to="none",
        optim="adamw_8bit",
        dataloader_pin_memory=False,
        ddp_find_unused_parameters=False,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        dataset_text_field="text",
        max_seq_length=MAX_LENGTH,
        args=training_args,
    )

    latest_checkpoint = get_latest_checkpoint(OUTPUT_DIR)
    if latest_checkpoint:
        print(f"Resuming from: {latest_checkpoint}")
        trainer.train(resume_from_checkpoint=latest_checkpoint)
    else:
        print("Starting fresh...")
        trainer.train()

    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Done! Model saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
