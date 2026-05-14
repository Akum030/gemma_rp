"""
Gemma-4 E4B fine-tune  V11 PRIORITY BALANCED.

Goal:
  - Preserve the broader recall behavior seen in V7
  - Add only a light clean nested-priority bias
  - Avoid the larger-adapter / heavy-gold / clean-only collapse seen in V8-V10

Design hypothesis:
  - V7 worked best because it kept the broad V6 flat->nested coverage and used the
    smaller LoRA adapter size (r=32, alpha=64)
  - V8-V10 hurt recall by moving too far away from that balance
  - A conservative mixed run should be a better next bet than another aggressive shift

Data recipe:
  1. cat74 nested priority rows, lightly repeated for cleaner schema signal
  2. v6 flat->nested rows, preserved for broad coverage
  3. gold_1k_v2 flat rows converted to nested, added only once (no oversampling)
"""
import os, sys, json, random

sys.path = [p for p in sys.path if "python3.9" not in p]

import importlib.metadata as _md

_real_version = _md.version


def _safe_version(name):
    try:
        return _real_version(name)
    except _md.PackageNotFoundError:
        if name in ("vllm",):
            return "0.0.0"
        raise


_md.version = _safe_version

import unsloth  # noqa: F401
from unsloth import FastModel
from transformers import TrainingArguments, EarlyStoppingCallback
from trl import SFTTrainer
from datasets import Dataset


MODEL_PATH = "/home3/indiamart/gemma_4/models/gemma-4-e4b-it"
OUTPUT_DIR = "/home3/indiamart/gemma_4/isq-gemma4-e4b-v11-priority-balanced"

CAT74_NESTED_TRAIN = "/home3/indiamart/gemma_4/cat74_train_nested.jsonl"
CAT74_NESTED_VAL = "/home3/indiamart/gemma_4/cat74_val_nested.jsonl"
V6_FLAT_TRAIN = "/home3/indiamart/gemma_4/v6_train.jsonl"
V6_FLAT_VAL = "/home3/indiamart/gemma_4/v6_val.jsonl"
GOLD_FLAT = "/home3/indiamart/gemma_4/gold_1k_v2.jsonl"

V11_TRAIN_OUT = "/home3/indiamart/gemma_4/v11_train.jsonl"
V11_VAL_OUT = "/home3/indiamart/gemma_4/v11_val.jsonl"

MAX_LENGTH = 768
NUM_EPOCHS = 2
BATCH_SIZE = 2
GRAD_ACCUMULATION = 16
LEARNING_RATE = 7e-5
WARMUP_STEPS = 80
EVAL_EVERY = 150
SAVE_EVERY = 150
CAT74_REPEAT = 2
GOLD_TRAIN_REPEAT = 1

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

VOCAB = {
    "brand": ["brand", "manufacturer", "company", "make"],
    "part type": ["part_type", "product_type", "type", "product_category", "category"],
    "driven type": ["driven_type", "motor_type", "machine_type", "drive_type"],
    "power": ["power", "wattage", "kilowatt", "horsepower", "hp", "kw", "motor_power", "power_rating", "rated_power"],
    "horsepower": ["horsepower", "hp", "power", "motor_horsepower", "rated_power"],
    "model name/number": ["model_number", "part_number", "model", "model_name", "mpn"],
    "phase": ["phase", "phase_type", "no_of_phase", "number_of_phase"],
    "voltage": ["voltage", "rated_voltage", "operating_voltage", "voltage_rating"],
    "current": ["current", "rated_current", "amperage", "ampere"],
    "frequency": ["frequency", "frequency_hertz", "operating_frequency", "hz"],
    "rpm": ["rpm", "speed", "rotation_speed", "rated_speed", "revolutions_per_minute"],
    "poles": ["poles", "no_of_poles", "number_of_poles", "pole_count"],
    "size": ["size", "dimension", "frame_size", "physical_size"],
    "frame size": ["frame_size", "frame", "size", "frame_designation"],
    "weight": ["weight", "mass", "net_weight", "gross_weight"],
    "mounting type": ["mounting_type", "mounting", "fixing_type", "installation_type"],
    "orientation": ["orientation", "alignment", "mounting_orientation"],
    "shape": ["shape", "geometry", "form"],
    "shaft diameter": ["shaft_diameter", "shaft_size", "shaft"],
    "stroke length": ["stroke_length", "stroke", "stroke_size"],
    "displacement": ["displacement", "swept_volume", "volume_displacement"],
    "torque": ["torque", "rated_torque", "torque_rating", "nm_torque"],
    "capacity": ["capacity", "rated_capacity", "load_capacity", "tank_capacity"],
    "quantity": ["quantity", "qty", "count", "no_of_units"],
    "ip rating": ["ip_rating", "ingress_protection", "ip_class", "protection_rating"],
    "insulation class": ["insulation_class", "insulation", "insulation_grade", "class_of_insulation"],
    "cooling type": ["cooling_type", "cooling", "cooling_method"],
    "efficiency": ["efficiency", "efficiency_class", "ie_class", "energy_efficiency"],
    "grade": ["grade", "quality_grade", "class"],
    "material": ["material", "body_material", "construction_material", "casing_material"],
    "color": ["color", "colour", "shade"],
    "feature": ["feature", "specification", "characteristic", "attribute"],
    "usage": ["usage", "application", "suitable_for", "use_case", "purpose"],
    "application": ["application", "usage", "use_case", "suitable_for"],
    "starter type": ["starter_type", "starter", "starting_method"],
    "power source": ["power_source", "power_supply", "energy_source", "fuel_type"],
    "series": ["series", "product_series", "model_series"],
    "location/city": ["location", "city", "place", "region"],
}

RANK = {
    "brand": 1, "part type": 2, "driven type": 2,
    "power": 3, "horsepower": 3, "model name/number": 4,
    "phase": 5, "voltage": 5, "current": 5,
    "frequency": 7, "rpm": 6, "poles": 6,
    "size": 8, "frame size": 8, "weight": 9,
    "mounting type": 8, "orientation": 9, "shape": 9,
    "shaft diameter": 9, "stroke length": 9, "displacement": 9,
    "torque": 7, "capacity": 7, "quantity": 10,
    "ip rating": 8, "insulation class": 9, "cooling type": 9,
    "efficiency": 9, "grade": 10, "material": 10, "color": 10,
    "feature": 10, "usage": 10, "application": 10,
    "starter type": 9, "power source": 6, "series": 10, "location/city": 10,
}


def flat_to_nested(flat):
    items = []
    for key, value in flat.items():
        if not isinstance(value, str) or not value.strip():
            continue
        canon = key.lower().strip()
        rank = RANK.get(canon, 99)
        synonyms = VOCAB.get(canon, [canon.replace(" ", "_")])
        items.append((rank, value.strip(), synonyms))
    items.sort(key=lambda item: item[0])
    nested = []
    for index, (_rank, value, synonyms) in enumerate(items, start=1):
        obj = {"value": value}
        for syn_index, synonym in enumerate(synonyms, start=1):
            obj[f"key_priority{syn_index}"] = synonym
        nested.append({f"attribute_priority{index}": obj})
    return {"attributes": nested}


def load_nested_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("instruction") and row.get("output"):
                rows.append({"instruction": row["instruction"], "output": row["output"]})
    return rows


def load_flat_training_as_nested(path, query_field, output_field):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            query = row.get(query_field, "").strip()
            attrs = row.get(output_field)
            if isinstance(attrs, str):
                try:
                    attrs = json.loads(attrs)
                except Exception:
                    continue
            if not query or not isinstance(attrs, dict) or not attrs:
                continue
            nested = flat_to_nested(attrs)
            if not nested["attributes"]:
                continue
            rows.append({
                "instruction": f"{INSTRUCTION}\n\nQuery: {query}",
                "output": json.dumps(nested, ensure_ascii=False),
            })
    return rows


def write_jsonl(rows, path):
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def get_latest_checkpoint(path):
    if not os.path.exists(path):
        return None
    checkpoints = [os.path.join(path, name) for name in os.listdir(path) if name.startswith("checkpoint-")]
    if not checkpoints:
        return None
    checkpoints.sort(key=lambda item: int(item.split("-")[-1]))
    return checkpoints[-1]


def main():
    print("=" * 70)
    print("GEMMA-4 E4B  V11 PRIORITY BALANCED")
    print("=" * 70)
    random.seed(42)

    print("\n[1/5] Building V11 dataset ...")
    cat_train = load_nested_jsonl(CAT74_NESTED_TRAIN)
    cat_val = load_nested_jsonl(CAT74_NESTED_VAL)
    v6_train = load_flat_training_as_nested(V6_FLAT_TRAIN, "instruction", "output")
    v6_val = load_flat_training_as_nested(V6_FLAT_VAL, "instruction", "output")
    gold_rows = load_flat_training_as_nested(GOLD_FLAT, "query", "attributes")

    random.shuffle(gold_rows)
    gold_split = int(0.9 * len(gold_rows))
    gold_train = gold_rows[:gold_split]
    gold_val = gold_rows[gold_split:]

    boosted_cat_train = cat_train * CAT74_REPEAT
    boosted_gold_train = gold_train * GOLD_TRAIN_REPEAT
    all_train = boosted_cat_train + v6_train + boosted_gold_train
    all_val = cat_val + v6_val + gold_val
    random.shuffle(all_train)

    print(f"   cat74 nested:        train={len(cat_train)} val={len(cat_val)}")
    print(f"   v6 flat->nested:     train={len(v6_train)} val={len(v6_val)}")
    print(f"   gold base split:     train={len(gold_train)} val={len(gold_val)}")
    print(f"   cat74 repeated x{CAT74_REPEAT}: train={len(boosted_cat_train)}")
    print(f"   gold repeated x{GOLD_TRAIN_REPEAT}: train={len(boosted_gold_train)}")
    print(f"   COMBINED:            train={len(all_train)} val={len(all_val)}")

    write_jsonl(all_train, V11_TRAIN_OUT)
    write_jsonl(all_val, V11_VAL_OUT)

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

    print("\n[3/5] Applying LoRA r=32 alpha=64 ...")
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

    print("\n[4/5] Tokenising ...")
    def to_text_ds(rows):
        texts = [
            "<start_of_turn>user\n"
            f"{row['instruction']}<end_of_turn>\n"
            "<start_of_turn>model\n"
            f"{row['output']}<end_of_turn>"
            for row in rows
        ]
        return Dataset.from_dict({"text": texts})

    train_ds = to_text_ds(all_train)
    val_ds = to_text_ds(all_val)

    print("\n[5/5] Trainer ...")
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
        max_grad_norm=1.0,
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
    trainer.model_accepts_loss_kwargs = False

    resume = get_latest_checkpoint(OUTPUT_DIR)
    if resume:
        print(f"   Resuming from: {resume}")

    print("\n>>> STARTING V11 TRAINING <<<\n")
    trainer.train(resume_from_checkpoint=resume)

    print("\nSaving final adapters ...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"DONE. Saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()