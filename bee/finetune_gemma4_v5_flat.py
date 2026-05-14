"""
Gemma-4 E4B fine-tune — V5 FLAT attribute extraction.

Key differences from V4:
  - Uses product_train_with_keys.jsonl (10K rows, diverse product categories)
  - OUTPUT is simple flat JSON: {"part type": "motor", "brand": "Siemens", ...}
  - Keys match the IndiaMART gold vocabulary (part type, model name/number, brand, etc.)
  - No complex nested priority format — much easier for the model to learn consistently
  - Also includes cat74 data converted to flat format (extra motors domain coverage)

Steps:
  1. Load product_train_with_keys.jsonl (train+val)  +  cat74 converted to flat
  2. Fine-tune Gemma-4 E4B (Unsloth + 4-bit + LoRA r=16)
  3. Save best checkpoint to OUTPUT_DIR
"""

import os, sys, json, random
sys.path = [p for p in sys.path if "python3.9" not in p]

import unsloth                                   # noqa: F401
from unsloth import FastModel
from transformers import TrainingArguments, EarlyStoppingCallback
from trl import SFTTrainer
from datasets import Dataset

# ============================================================
# PATHS / CONFIG
# ============================================================
MODEL_PATH  = "/home3/indiamart/gemma_4/models/gemma-4-e4b-it"
OUTPUT_DIR  = "/home3/indiamart/isq-gemma4-e4b-v5-flat"

# Primary training data (10K rows, broad vocab matching gold)
PROD_TRAIN  = "/home3/indiamart/gemma_4/product_train_with_keys.jsonl"
PROD_VAL    = "/home3/indiamart/gemma_4/product_val_with_keys.jsonl"

# Optional: cat74 (motors domain) — converted to flat format in-memory
CAT74_TRAIN = "/home3/indiamart/gemma_4/cat74_train.jsonl"
CAT74_VAL   = "/home3/indiamart/gemma_4/cat74_val.jsonl"

MAX_LENGTH        = 512
NUM_EPOCHS        = 5
BATCH_SIZE        = 2
GRAD_ACCUMULATION = 16       # eff batch = 32
LEARNING_RATE     = 2e-4
WARMUP_STEPS      = 100
EVAL_EVERY        = 200
SAVE_EVERY        = 200

SYSTEM_PROMPT = (
    "You are a product attribute extractor for IndiaMART (B2B marketplace). "
    "Given a search query, extract all product attributes and return ONLY a "
    "compact JSON object. Use standard IndiaMART attribute keys such as: "
    "part type, brand, model name/number, power, voltage, phase, speed, usage, "
    "material, size, color, series, driven type, power source, rpm, frequency, "
    "capacity, mounting type, ip rating, insulation class, torque, automation grade, "
    "quantity, dimension, weight, country of origin, horsepower, rated speed, "
    "frame size, shape, orientation, certification, application. "
    "Only include attributes actually present in the query. "
    "Output ONLY the JSON — no explanation, no code fences."
)

# ============================================================
# CAT74 FLAT CONVERSION
# (cat74 format: instruction+output where output is a list of
#  {attribute_key, value, key_priority, attribute_priority})
# We pick key_priority=1 per attribute_priority group → flat dict
# ============================================================
def cat74_flat(output_str: str):
    """Convert cat74 output JSON string to simple flat dict."""
    try:
        obj = json.loads(output_str)
        attrs = obj.get("attributes", [])
    except Exception:
        return {}
    # group by attribute_priority; pick the row with lowest key_priority
    groups = {}
    for a in attrs:
        ap = int(a.get("attribute_priority", 0))
        kp = int(a.get("key_priority", 99))
        if ap < 1:
            continue
        if ap not in groups or kp < groups[ap]["kp"]:
            groups[ap] = {"kp": kp, "key": a.get("attribute_key", ""), "value": a.get("value", "")}
    flat = {}
    for g in groups.values():
        k, v = g["key"].strip(), g["value"].strip()
        if k and v:
            flat[k] = v
    return flat


def extract_query_from_cat74(instruction: str) -> str:
    marker = "Query:"
    idx = instruction.rfind(marker)
    if idx == -1:
        return instruction.strip()
    return instruction[idx + len(marker):].strip()


def load_cat74_as_flat(path: str):
    """Load cat74 file, convert each row to {instruction, output} with flat JSON output."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            query = extract_query_from_cat74(row.get("instruction", ""))
            flat = cat74_flat(row.get("output", "{}"))
            if not flat or not query:
                continue
            rows.append({
                "query": query,
                "output": json.dumps(flat, ensure_ascii=False),
            })
    return rows

# ============================================================
# HELPERS
# ============================================================
def get_latest_checkpoint(output_dir):
    if not os.path.isdir(output_dir):
        return None
    ckpts = [
        os.path.join(output_dir, d) for d in os.listdir(output_dir)
        if d.startswith("checkpoint-") and os.path.isdir(os.path.join(output_dir, d))
    ]
    if not ckpts:
        return None
    return sorted(ckpts, key=lambda x: int(x.rsplit("-", 1)[-1]))[-1]


def format_prompt(query: str, output: str) -> str:
    """Gemma-4 chat format for SFT."""
    return (
        "<start_of_turn>user\n"
        f"{SYSTEM_PROMPT}\n\n"
        f"Query: {query}<end_of_turn>\n"
        "<start_of_turn>model\n"
        f"{output}<end_of_turn>"
    )


def load_prod_file(path: str):
    """Load product_train_with_keys rows, extract query from instruction."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            instr = row.get("instruction", "")
            # instruction = "Extract key-value attributes from this query: <query>"
            marker = "this query:"
            idx = instr.find(marker)
            query = instr[idx + len(marker):].strip() if idx != -1 else instr.strip()
            out = row.get("output", "{}")
            # validate output is valid JSON dict
            try:
                d = json.loads(out)
                if not isinstance(d, dict):
                    continue
                out = json.dumps(d, ensure_ascii=False)  # normalise
            except Exception:
                continue
            if query:
                rows.append({"query": query, "output": out})
    return rows


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    random.seed(42)

    # ---- 1. Load & combine datasets ----
    print("[1/5] Loading datasets ...")
    prod_train_rows = load_prod_file(PROD_TRAIN)
    prod_val_rows   = load_prod_file(PROD_VAL)
    print(f"   product_train: {len(prod_train_rows)}  product_val: {len(prod_val_rows)}")

    cat74_train_rows = []
    cat74_val_rows   = []
    if os.path.exists(CAT74_TRAIN):
        cat74_train_rows = load_cat74_as_flat(CAT74_TRAIN)
        print(f"   cat74_train (converted): {len(cat74_train_rows)}")
    if os.path.exists(CAT74_VAL):
        cat74_val_rows = load_cat74_as_flat(CAT74_VAL)
        print(f"   cat74_val (converted):   {len(cat74_val_rows)}")

    all_train = prod_train_rows + cat74_train_rows
    all_val   = prod_val_rows   + cat74_val_rows
    random.shuffle(all_train)
    print(f"   TOTAL train: {len(all_train)}  val: {len(all_val)}")

    def rows_to_dataset(rows):
        texts = [format_prompt(r["query"], r["output"]) for r in rows]
        return Dataset.from_dict({"text": texts})

    train_ds = rows_to_dataset(all_train)
    val_ds   = rows_to_dataset(all_val)

    # ---- 2. Model + tokenizer ----
    print("\n[2/5] Loading Gemma-4 E4B (4-bit) ...")
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

    # ---- 3. LoRA ----
    print("\n[3/5] Applying LoRA ...")
    model = FastModel.get_peft_model(
        model,
        finetune_vision_layers=False,
        finetune_language_layers=True,
        finetune_attention_modules=True,
        finetune_mlp_modules=True,
        r=16,
        lora_alpha=32,
        lora_dropout=0,
        bias="none",
        random_state=42,
    )
    model.print_trainable_parameters()

    # ---- 4. Trainer ----
    print("\n[4/5] Configuring trainer ...")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type="cosine",
        warmup_steps=WARMUP_STEPS,
        weight_decay=0.01,
        max_grad_norm=1.0,
        fp16=True,
        gradient_checkpointing=True,
        logging_steps=10,
        save_strategy="steps",
        save_steps=SAVE_EVERY,
        save_total_limit=3,
        eval_strategy="steps",
        eval_steps=EVAL_EVERY,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",
        optim="adamw_8bit",
        dataloader_pin_memory=False,
        ddp_find_unused_parameters=False,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        dataset_text_field="text",
        max_seq_length=MAX_LENGTH,
        args=training_args,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )
    # Fix for transformers 5.5 + trl SFTTrainer loss kwargs
    trainer.model_accepts_loss_kwargs = False

    # ---- 5. Train ----
    print("\n[5/5] Training ...")
    latest = get_latest_checkpoint(OUTPUT_DIR)
    if latest:
        print(f"Resuming from {latest}")
        trainer.train(resume_from_checkpoint=latest)
    else:
        print("Training from scratch ...")
        trainer.train()

    print("\nSaving model ...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\nDone! Saved to {OUTPUT_DIR}")
