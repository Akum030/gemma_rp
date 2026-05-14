"""
Gemma-4 E4B fine-tune — V4 priority-nested attribute extraction.

Steps performed inside this single script:
  1. Read /home3/indiamart/gemma_4/cat74_train.jsonl + cat74_val.jsonl
     (flat format: {attribute_key, value, key_priority, attribute_priority}).
  2. Convert each row to NESTED priority format defined in
     TRAINING_PROMPT_PRIORITY_VERSION.txt:
        {"attributes":[{"attribute_priority1":{"value":...,"key_priority1":...,"key_priority2":...}}, ...]}
  3. Replace the long bundled instruction with one concise system prompt that
     teaches the nested schema.
  4. Fine-tune Gemma-4 E4B (Unsloth + 4-bit + LoRA) with eval enabled.
  5. Save best checkpoint at /home3/indiamart/isq-gemma4-e4b-v4-priority.
"""

import os, sys, json, math
sys.path = [p for p in sys.path if "python3.9" not in p]

import unsloth                                  # noqa: F401  (must import first)
from unsloth import FastModel
from transformers import TrainingArguments, EarlyStoppingCallback
from trl import SFTTrainer
from datasets import Dataset

# ============================================================
# PATHS / CONFIG
# ============================================================
MODEL_PATH = "/home3/indiamart/gemma_4/models/gemma-4-e4b-it"
OUTPUT_DIR = "/home3/indiamart/isq-gemma4-e4b-v4-priority"
RAW_TRAIN  = "/home3/indiamart/gemma_4/cat74_train.jsonl"
RAW_VAL    = "/home3/indiamart/gemma_4/cat74_val.jsonl"

NESTED_TRAIN = "/home3/indiamart/gemma_4/cat74_train_nested.jsonl"
NESTED_VAL   = "/home3/indiamart/gemma_4/cat74_val_nested.jsonl"

MAX_LENGTH        = 768      # measured: p99=587 tok on full dataset, comfortable margin
NUM_EPOCHS        = 4
BATCH_SIZE        = 2
GRAD_ACCUMULATION = 16       # eff batch = 32 (matches V2 effective size)
LEARNING_RATE     = 1e-4
WARMUP_STEPS      = 50
EVAL_EVERY        = 100      # steps
SAVE_EVERY        = 100

INSTRUCTION = (
    "Extract product attributes from the search query. Return JSON with key "
    "\"attributes\" = list of objects. Each object has ONE field "
    "\"attribute_priorityN\" (N=1 most important to user intent, N=2 next, ...). "
    "That field is itself an object with \"value\" (extracted text) and "
    "\"key_priority1\", \"key_priority2\", \"key_priority3\", ... ranking "
    "synonym key names from most preferred to least.\n"
    "Rules: extract only what is in the query; lowercase values except "
    "model/part numbers; group every synonym for the same value under one "
    "attribute_priority object; rank attributes by user intent "
    "(brand > product type > primary spec > model > phase/voltage > speed > "
    "frequency > mounting/IP > insulation > others)."
)


# ============================================================
# 1. CONVERT FLAT  →  NESTED
# ============================================================
def extract_query(instruction_text: str) -> str:
    """The original instruction ends with 'Query: <text>'."""
    marker = "Query:"
    idx = instruction_text.rfind(marker)
    if idx == -1:
        return instruction_text.strip()
    return instruction_text[idx + len(marker):].strip()


def flat_to_nested(flat_attrs):
    """
    flat_attrs: list of dicts {attribute_key, value, key_priority, attribute_priority}
    returns:    {"attributes":[{"attribute_priorityN":{value, key_priority1, key_priority2,...}}, ...]}
    """
    # group by attribute_priority
    groups = {}
    for a in flat_attrs:
        ap = int(a.get("attribute_priority", 0))
        if ap < 1:
            continue
        kp = int(a.get("key_priority", 99))
        groups.setdefault(ap, {"value": a.get("value", ""), "keys": []})
        groups[ap]["keys"].append((kp, str(a.get("attribute_key", ""))))
        # value: trust the first one we see (they should all match within a group)

    nested = []
    for ap in sorted(groups):
        g = groups[ap]
        # sort synonyms by their key_priority
        keys_sorted = [k for _, k in sorted(g["keys"], key=lambda x: x[0])]
        # de-dup while preserving order
        seen, ordered = set(), []
        for k in keys_sorted:
            if k and k not in seen:
                ordered.append(k); seen.add(k)
        obj = {"value": g["value"]}
        for i, k in enumerate(ordered, start=1):
            obj[f"key_priority{i}"] = k
        nested.append({f"attribute_priority{ap}": obj})

    return {"attributes": nested}


def convert_file(src_path: str, dst_path: str) -> int:
    n_in = n_out = 0
    with open(src_path, "r", encoding="utf-8") as fin, \
         open(dst_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            n_in += 1
            row = json.loads(line)
            try:
                output_obj = json.loads(row["output"])
                flat_attrs = output_obj.get("attributes", [])
                nested = flat_to_nested(flat_attrs)
            except Exception as e:
                continue  # skip malformed
            query = extract_query(row.get("instruction", ""))
            new_row = {
                "instruction": f"{INSTRUCTION}\n\nQuery: {query}",
                "output": json.dumps(nested, ensure_ascii=False),
            }
            fout.write(json.dumps(new_row, ensure_ascii=False) + "\n")
            n_out += 1
    return n_in, n_out


def get_latest_checkpoint(output_dir):
    if not os.path.exists(output_dir):
        return None
    cps = [os.path.join(output_dir, d) for d in os.listdir(output_dir)
           if d.startswith("checkpoint-")]
    if not cps:
        return None
    cps.sort(key=lambda x: int(x.split("-")[-1]))
    return cps[-1]


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 70)
    print("GEMMA-4 E4B  —  V4 PRIORITY-NESTED FINE-TUNE")
    print("=" * 70)

    # ---- 1. data conversion ----
    print("\n[1/5] Converting cat74 flat -> nested ...")
    n1_in, n1_out = convert_file(RAW_TRAIN, NESTED_TRAIN)
    n2_in, n2_out = convert_file(RAW_VAL,   NESTED_VAL)
    print(f"   train: {n1_in} -> {n1_out}   val: {n2_in} -> {n2_out}")
    print(f"   wrote: {NESTED_TRAIN}")
    print(f"   wrote: {NESTED_VAL}")

    # show one sample for sanity
    with open(NESTED_TRAIN) as f:
        smp = json.loads(f.readline())
    print("\n   sample instruction (head):")
    print("   " + smp["instruction"][:160].replace("\n", " ") + " ...")
    print("\n   sample output (head):")
    print("   " + smp["output"][:300] + " ...")

    # ---- 2. model + tokenizer ----
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
    print("\n[3/5] Applying LoRA adapters ...")
    model = FastModel.get_peft_model(
        model,
        finetune_vision_layers=False,
        finetune_language_layers=True,
        finetune_attention_modules=True,
        finetune_mlp_modules=True,
        r=32,
        lora_alpha=64,
        lora_dropout=0,
        bias="none",
        random_state=42,
    )
    model.print_trainable_parameters()

    # ---- 4. dataset prep ----
    print("\n[4/5] Tokenising ...")
    def load_jsonl(path):
        rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
        return Dataset.from_list(rows)

    train_ds = load_jsonl(NESTED_TRAIN)
    val_ds   = load_jsonl(NESTED_VAL)
    print(f"   train: {len(train_ds)}  val: {len(val_ds)}")

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

    train_ds = train_ds.map(format_dataset, batched=True,
                            remove_columns=train_ds.column_names)
    val_ds   = val_ds.map(format_dataset,   batched=True,
                            remove_columns=val_ds.column_names)

    # ---- 5. trainer ----
    print("\n[5/5] Configuring trainer ...")
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

    # Compatibility: transformers 5.5 + unsloth + trl passes num_items_in_batch
    # as int; SFTTrainer tries .mean() on it.  Disabling stops the forwarding.
    trainer.model_accepts_loss_kwargs = False

    latest = get_latest_checkpoint(OUTPUT_DIR)
    print("\n" + "=" * 70)
    if latest:
        print(f"Resuming from {latest}")
        trainer.train(resume_from_checkpoint=latest)
    else:
        print("Training from scratch ...")
        trainer.train()

    print("\nSaving final model + tokenizer ...")
    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"DONE -> {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
