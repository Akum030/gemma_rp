"""
Gemma-4 E4B fine-tune — V7 PRIORITY-NESTED attribute extraction.

V7 RESTORES the priority objective that V6 dropped:
  Output schema:
    {"attributes":[
       {"attribute_priority1":{"value":"<text>","key_priority1":"<canonical>","key_priority2":"<synonym>",...}},
       {"attribute_priority2":{...}},
       ...
    ]}

Training data is built from TWO sources at startup:
  A) cat74_train_nested.jsonl / cat74_val_nested.jsonl
       — already in priority-nested format (real multi-synonym priority data
         from V4). 1599 train / 400 val rows.
  B) v6_train.jsonl / v6_val.jsonl
       — flat canonical {"key":"value"} format (~6.5K rows). We convert each
         row into priority-nested form using:
           VOCAB[key]   = ordered list of synonyms (key_priority1..N)
           RANK[key]    = base attribute_priority slot for that key
         If two flat keys share the same RANK we re-number sequentially.

LoRA / QLoRA on Gemma-4 E4B (4-bit) via Unsloth.
Output: /home3/indiamart/isq-gemma4-e4b-v7-priority/
"""

import os, sys, json, random, math
sys.path = [p for p in sys.path if "python3.9" not in p]

import unsloth                                   # noqa: F401  (must import first)
from unsloth import FastModel
from transformers import TrainingArguments, EarlyStoppingCallback
from trl import SFTTrainer
from datasets import Dataset

# ============================================================
# PATHS / CONFIG
# ============================================================
MODEL_PATH = "/home3/indiamart/gemma_4/models/gemma-4-e4b-it"
OUTPUT_DIR = "/home3/indiamart/gemma_4/isq-gemma4-e4b-v7-priority"

CAT74_NESTED_TRAIN = "/home3/indiamart/gemma_4/cat74_train_nested.jsonl"
CAT74_NESTED_VAL   = "/home3/indiamart/gemma_4/cat74_val_nested.jsonl"

V6_FLAT_TRAIN = "/home3/indiamart/gemma_4/v6_train.jsonl"
V6_FLAT_VAL   = "/home3/indiamart/gemma_4/v6_val.jsonl"

V7_TRAIN_OUT = "/home3/indiamart/gemma_4/v7_train.jsonl"
V7_VAL_OUT   = "/home3/indiamart/gemma_4/v7_val.jsonl"

MAX_LENGTH        = 768
NUM_EPOCHS        = 3
BATCH_SIZE        = 2
GRAD_ACCUMULATION = 16       # effective batch = 32
LEARNING_RATE     = 1e-4
WARMUP_STEPS      = 80
EVAL_EVERY        = 200
SAVE_EVERY        = 200

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
# VOCAB & RANK for flat -> nested conversion
#   Derived from TRAINING_PROMPT_PRIORITY_VERSION.txt
#   VOCAB[canonical_key] = [synonym1, synonym2, ...]
#       (canonical key is always synonym1)
#   RANK[canonical_key]  = base attribute_priority slot
# ============================================================
VOCAB = {
    # ---- highest priority: identity ----
    "brand":              ["brand", "manufacturer", "company", "make"],
    "part type":          ["part_type", "product_type", "type", "product_category", "category"],
    "driven type":        ["driven_type", "motor_type", "machine_type", "drive_type"],
    # ---- primary specs ----
    "power":              ["power", "wattage", "kilowatt", "horsepower", "hp", "kw",
                           "motor_power", "power_rating", "rated_power"],
    "horsepower":         ["horsepower", "hp", "power", "motor_horsepower", "rated_power"],
    "model name/number":  ["model_number", "part_number", "model", "model_name", "mpn"],
    # ---- electrical ----
    "phase":              ["phase", "phase_type", "no_of_phase", "number_of_phase"],
    "voltage":            ["voltage", "rated_voltage", "operating_voltage", "voltage_rating"],
    "current":            ["current", "rated_current", "amperage", "ampere"],
    "frequency":          ["frequency", "frequency_hertz", "operating_frequency", "hz"],
    "rpm":                ["rpm", "speed", "rotation_speed", "rated_speed", "revolutions_per_minute"],
    "poles":              ["poles", "no_of_poles", "number_of_poles", "pole_count"],
    # ---- physical / mech ----
    "size":               ["size", "dimension", "frame_size", "physical_size"],
    "frame size":         ["frame_size", "frame", "size", "frame_designation"],
    "weight":             ["weight", "mass", "net_weight", "gross_weight"],
    "mounting type":      ["mounting_type", "mounting", "fixing_type", "installation_type"],
    "orientation":        ["orientation", "alignment", "mounting_orientation"],
    "shape":              ["shape", "geometry", "form"],
    "shaft diameter":     ["shaft_diameter", "shaft_size", "shaft"],
    "stroke length":      ["stroke_length", "stroke", "stroke_size"],
    "displacement":       ["displacement", "swept_volume", "volume_displacement"],
    "torque":             ["torque", "rated_torque", "torque_rating", "nm_torque"],
    "capacity":           ["capacity", "rated_capacity", "load_capacity", "tank_capacity"],
    "quantity":           ["quantity", "qty", "count", "no_of_units"],
    # ---- protection / class ----
    "ip rating":          ["ip_rating", "ingress_protection", "ip_class", "protection_rating"],
    "insulation class":   ["insulation_class", "insulation", "insulation_grade", "class_of_insulation"],
    "cooling type":       ["cooling_type", "cooling", "cooling_method"],
    "efficiency":         ["efficiency", "efficiency_class", "ie_class", "energy_efficiency"],
    "grade":              ["grade", "quality_grade", "class"],
    # ---- material / appearance ----
    "material":           ["material", "body_material", "construction_material", "casing_material"],
    "color":              ["color", "colour", "shade"],
    # ---- meta ----
    "feature":            ["feature", "specification", "characteristic", "attribute"],
    "usage":              ["usage", "application", "suitable_for", "use_case", "purpose"],
    "application":        ["application", "usage", "use_case", "suitable_for"],
    "starter type":       ["starter_type", "starter", "starting_method"],
    "power source":       ["power_source", "power_supply", "energy_source", "fuel_type"],
    "series":             ["series", "product_series", "model_series"],
    "location/city":      ["location", "city", "place", "region"],
}

# attribute_priority rank slot per canonical key
# (lower slot = more important to user intent)
RANK = {
    "brand":             1,
    "part type":         2,
    "driven type":       2,
    "power":             3,
    "horsepower":        3,
    "model name/number": 4,
    "phase":             5,
    "voltage":           5,
    "current":           5,
    "frequency":         7,
    "rpm":               6,
    "poles":             6,
    "size":              8,
    "frame size":        8,
    "weight":            9,
    "mounting type":     8,
    "orientation":       9,
    "shape":             9,
    "shaft diameter":    9,
    "stroke length":     9,
    "displacement":      9,
    "torque":            7,
    "capacity":          7,
    "quantity":          10,
    "ip rating":         8,
    "insulation class":  9,
    "cooling type":      9,
    "efficiency":        9,
    "grade":             10,
    "material":          10,
    "color":             10,
    "feature":           10,
    "usage":             10,
    "application":       10,
    "starter type":      9,
    "power source":      6,
    "series":            10,
    "location/city":     10,
}


def flat_to_nested(flat: dict) -> dict:
    """
    flat: {"power": "45 hp", "brand": "siemens", ...}
    returns nested priority schema. Re-numbers attribute_priority sequentially
    after sorting by RANK (stable on insertion order for same rank).
    """
    items = []
    for k, v in flat.items():
        if not isinstance(v, str) or not v.strip():
            continue
        kk = k.lower().strip()
        rank = RANK.get(kk, 99)
        synonyms = VOCAB.get(kk, [kk.replace(" ", "_")])
        items.append((rank, kk, v.strip(), synonyms))
    # stable sort by rank
    items.sort(key=lambda x: x[0])
    nested = []
    for i, (_rank, _k, value, synonyms) in enumerate(items, start=1):
        obj = {"value": value}
        for j, syn in enumerate(synonyms, start=1):
            obj[f"key_priority{j}"] = syn
        nested.append({f"attribute_priority{i}": obj})
    return {"attributes": nested}


# ============================================================
# DATASET BUILD
# ============================================================
def load_nested_jsonl(path: str):
    """Load already-nested rows ({instruction, output} format)."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            instr = row.get("instruction", "")
            out   = row.get("output", "")
            if not instr or not out:
                continue
            # normalize instruction to use our INSTRUCTION header
            # (cat74 nested already uses same INSTRUCTION text)
            rows.append({"instruction": instr, "output": out})
    return rows


def load_flat_v6_as_nested(path: str):
    """Load v6 flat rows and convert each to nested priority format."""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            query = row.get("instruction", "").strip()
            try:
                flat = json.loads(row.get("output", "{}"))
                if not isinstance(flat, dict) or not flat:
                    continue
            except Exception:
                continue
            if not query:
                continue
            nested = flat_to_nested(flat)
            if not nested["attributes"]:
                continue
            new_row = {
                "instruction": f"{INSTRUCTION}\n\nQuery: {query}",
                "output": json.dumps(nested, ensure_ascii=False),
            }
            rows.append(new_row)
    return rows


def write_jsonl(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


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
    print("GEMMA-4 E4B  —  V7 PRIORITY-NESTED FINE-TUNE")
    print("=" * 70)
    random.seed(42)

    # ---- 1. Build combined dataset ----
    print("\n[1/5] Building V7 priority dataset ...")
    cat_train = load_nested_jsonl(CAT74_NESTED_TRAIN)
    cat_val   = load_nested_jsonl(CAT74_NESTED_VAL)
    print(f"   cat74 nested:   train={len(cat_train)}   val={len(cat_val)}")

    v6_train_n = load_flat_v6_as_nested(V6_FLAT_TRAIN)
    v6_val_n   = load_flat_v6_as_nested(V6_FLAT_VAL)
    print(f"   v6 flat->nested: train={len(v6_train_n)}   val={len(v6_val_n)}")

    all_train = cat_train + v6_train_n
    all_val   = cat_val   + v6_val_n
    random.shuffle(all_train)
    print(f"   COMBINED:        train={len(all_train)}   val={len(all_val)}")

    write_jsonl(all_train, V7_TRAIN_OUT)
    write_jsonl(all_val,   V7_VAL_OUT)
    print(f"   wrote {V7_TRAIN_OUT}")
    print(f"   wrote {V7_VAL_OUT}")

    # show sample
    print("\n   sample (converted from v6 flat):")
    print("   instruction:", v6_train_n[0]["instruction"][:120], "...")
    print("   output:     ", v6_train_n[0]["output"][:300])

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

    # ---- 4. Tokenise ----
    print("\n[4/5] Preparing datasets ...")
    def to_text_ds(rows):
        texts = []
        for r in rows:
            text = (
                "<start_of_turn>user\n"
                f"{r['instruction']}<end_of_turn>\n"
                "<start_of_turn>model\n"
                f"{r['output']}<end_of_turn>"
            )
            texts.append(text)
        return Dataset.from_dict({"text": texts})

    train_ds = to_text_ds(all_train)
    val_ds   = to_text_ds(all_val)
    print(f"   train rows: {len(train_ds)}   val rows: {len(val_ds)}")

    # ---- 5. Trainer ----
    print("\n[5/5] Setting up SFTTrainer ...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        logging_steps=20,
        eval_strategy="steps",
        eval_steps=EVAL_EVERY,
        save_strategy="steps",
        save_steps=SAVE_EVERY,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        bf16=False,
        fp16=True,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=42,
        report_to="none",
        dataloader_num_workers=2,
        gradient_checkpointing=True,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        dataset_text_field="text",
        max_seq_length=MAX_LENGTH,
        packing=False,
        args=args,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )
    # CRITICAL fix for transformers 5.5 + trl SFTTrainer loss kwargs:
    # without this, training crashes at step 1 with
    #   AttributeError: 'int' object has no attribute 'mean'
    trainer.model_accepts_loss_kwargs = False

    resume = get_latest_checkpoint(OUTPUT_DIR)
    if resume:
        print(f"   Resuming from checkpoint: {resume}")
    print("\n>>> STARTING TRAINING <<<\n")
    trainer.train(resume_from_checkpoint=resume)

    # ---- save ----
    print("\nSaving final adapters + tokenizer ...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"DONE. Saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
