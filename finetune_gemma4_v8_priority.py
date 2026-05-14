"""
Gemma-4 E4B fine-tune  V8 PRIORITY  (overnight push for best attribute quality).

Same nested priority schema as V7. Differences vs V7:
  - Larger LoRA (r=64, alpha=128) for more capacity
  - 5 epochs (vs 3), with cosine LR and longer warmup
  - Adds gold_1k_v2.jsonl to training (1000 high-quality human-labeled rows)
  - Slightly longer max_seq_length (1024) so longer multi-attribute outputs fit
  - Saves every 300 steps with save_total_limit=2 to stay within disk budget

NOTE: Because gold is now in training, the v8 vs gold metric is NOT a clean
benchmark. The clean publishable baseline remains v7-vs-gold (already saved
to /home3/indiamart/gemma_4/v7_eval_summary.json). v8 is the deployable
high-accuracy model.
"""
import os, sys, json, random
sys.path = [p for p in sys.path if "python3.9" not in p]

# stub vllm so unsloth import doesn't fail
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

import unsloth                                   # noqa: F401
from unsloth import FastModel
from transformers import TrainingArguments, EarlyStoppingCallback
from trl import SFTTrainer
from datasets import Dataset

MODEL_PATH = "/home3/indiamart/gemma_4/models/gemma-4-e4b-it"
OUTPUT_DIR = "/home3/indiamart/gemma_4/isq-gemma4-e4b-v8-priority"

CAT74_NESTED_TRAIN = "/home3/indiamart/gemma_4/cat74_train_nested.jsonl"
CAT74_NESTED_VAL   = "/home3/indiamart/gemma_4/cat74_val_nested.jsonl"
V6_FLAT_TRAIN      = "/home3/indiamart/gemma_4/v6_train.jsonl"
V6_FLAT_VAL        = "/home3/indiamart/gemma_4/v6_val.jsonl"
GOLD_FLAT          = "/home3/indiamart/gemma_4/gold_1k_v2.jsonl"

V8_TRAIN_OUT = "/home3/indiamart/gemma_4/v8_train.jsonl"
V8_VAL_OUT   = "/home3/indiamart/gemma_4/v8_val.jsonl"

MAX_LENGTH        = 768
NUM_EPOCHS        = 2
BATCH_SIZE        = 2
GRAD_ACCUMULATION = 16
LEARNING_RATE     = 8e-5
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

# vocabulary copied from v7 (kept identical so labels are consistent)
VOCAB = {
    "brand":              ["brand", "manufacturer", "company", "make"],
    "part type":          ["part_type", "product_type", "type", "product_category", "category"],
    "driven type":        ["driven_type", "motor_type", "machine_type", "drive_type"],
    "power":              ["power", "wattage", "kilowatt", "horsepower", "hp", "kw",
                           "motor_power", "power_rating", "rated_power"],
    "horsepower":         ["horsepower", "hp", "power", "motor_horsepower", "rated_power"],
    "model name/number":  ["model_number", "part_number", "model", "model_name", "mpn"],
    "phase":              ["phase", "phase_type", "no_of_phase", "number_of_phase"],
    "voltage":            ["voltage", "rated_voltage", "operating_voltage", "voltage_rating"],
    "current":            ["current", "rated_current", "amperage", "ampere"],
    "frequency":          ["frequency", "frequency_hertz", "operating_frequency", "hz"],
    "rpm":                ["rpm", "speed", "rotation_speed", "rated_speed", "revolutions_per_minute"],
    "poles":              ["poles", "no_of_poles", "number_of_poles", "pole_count"],
    "size":               ["size", "dimension", "frame_size", "physical_size"],
    "frame size":         ["frame_size", "frame", "size", "frame_designation"],
    "weight":             ["weight", "mass", "net_weight", "gross_weight"],
    "mounting type":      ["mounting_type", "mounting", "fixing_type", "installation_type"],
    "orientation":        ["orientation", "alignment", "mounting_orientation"],
    "shape":               ["shape", "geometry", "form"],
    "shaft diameter":     ["shaft_diameter", "shaft_size", "shaft"],
    "stroke length":      ["stroke_length", "stroke", "stroke_size"],
    "displacement":       ["displacement", "swept_volume", "volume_displacement"],
    "torque":             ["torque", "rated_torque", "torque_rating", "nm_torque"],
    "capacity":           ["capacity", "rated_capacity", "load_capacity", "tank_capacity"],
    "quantity":           ["quantity", "qty", "count", "no_of_units"],
    "ip rating":          ["ip_rating", "ingress_protection", "ip_class", "protection_rating"],
    "insulation class":   ["insulation_class", "insulation", "insulation_grade", "class_of_insulation"],
    "cooling type":       ["cooling_type", "cooling", "cooling_method"],
    "efficiency":         ["efficiency", "efficiency_class", "ie_class", "energy_efficiency"],
    "grade":              ["grade", "quality_grade", "class"],
    "material":           ["material", "body_material", "construction_material", "casing_material"],
    "color":              ["color", "colour", "shade"],
    "feature":            ["feature", "specification", "characteristic", "attribute"],
    "usage":              ["usage", "application", "suitable_for", "use_case", "purpose"],
    "application":        ["application", "usage", "use_case", "suitable_for"],
    "starter type":       ["starter_type", "starter", "starting_method"],
    "power source":       ["power_source", "power_supply", "energy_source", "fuel_type"],
    "series":             ["series", "product_series", "model_series"],
    "location/city":      ["location", "city", "place", "region"],
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
    for k, v in flat.items():
        if not isinstance(v, str) or not v.strip():
            continue
        kk = k.lower().strip()
        rank = RANK.get(kk, 99)
        synonyms = VOCAB.get(kk, [kk.replace(" ", "_")])
        items.append((rank, kk, v.strip(), synonyms))
    items.sort(key=lambda x: x[0])
    nested = []
    for i, (_r, _k, value, synonyms) in enumerate(items, start=1):
        obj = {"value": value}
        for j, syn in enumerate(synonyms, start=1):
            obj[f"key_priority{j}"] = syn
        nested.append({f"attribute_priority{i}": obj})
    return {"attributes": nested}


def load_nested_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            r = json.loads(line)
            if r.get("instruction") and r.get("output"):
                rows.append({"instruction": r["instruction"], "output": r["output"]})
    return rows


def load_flat_v6_as_nested(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            r = json.loads(line)
            q = r.get("instruction", "").strip()
            try:
                d = json.loads(r.get("output", "{}"))
                if not isinstance(d, dict) or not d:
                    continue
            except Exception:
                continue
            if not q: continue
            nested = flat_to_nested(d)
            if not nested["attributes"]:
                continue
            rows.append({
                "instruction": f"{INSTRUCTION}\n\nQuery: {q}",
                "output": json.dumps(nested, ensure_ascii=False),
            })
    return rows


def load_gold_as_nested(path):
    """gold_1k_v2.jsonl: {query, attributes:{k:v}}"""
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            r = json.loads(line)
            q = r.get("query", "").strip()
            d = r.get("attributes") or {}
            if not q or not d: continue
            nested = flat_to_nested(d)
            if not nested["attributes"]: continue
            rows.append({
                "instruction": f"{INSTRUCTION}\n\nQuery: {q}",
                "output": json.dumps(nested, ensure_ascii=False),
            })
    return rows


def write_jsonl(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def get_latest_checkpoint(d):
    if not os.path.exists(d): return None
    cps = [os.path.join(d, x) for x in os.listdir(d) if x.startswith("checkpoint-")]
    if not cps: return None
    cps.sort(key=lambda x: int(x.split("-")[-1]))
    return cps[-1]


def main():
    print("=" * 70)
    print("GEMMA-4 E4B  V8 PRIORITY  overnight push")
    print("=" * 70)
    random.seed(42)

    print("\n[1/5] Building V8 dataset ...")
    cat_train = load_nested_jsonl(CAT74_NESTED_TRAIN)
    cat_val   = load_nested_jsonl(CAT74_NESTED_VAL)
    v6_train  = load_flat_v6_as_nested(V6_FLAT_TRAIN)
    v6_val    = load_flat_v6_as_nested(V6_FLAT_VAL)
    gold_rows = load_gold_as_nested(GOLD_FLAT)

    # split gold 90/10 for internal eval signal
    random.shuffle(gold_rows)
    gold_split = int(0.9 * len(gold_rows))
    gold_train = gold_rows[:gold_split]
    gold_val   = gold_rows[gold_split:]

    all_train = cat_train + v6_train + gold_train
    all_val   = cat_val + v6_val + gold_val
    random.shuffle(all_train)

    print(f"   cat74 nested:    train={len(cat_train)}  val={len(cat_val)}")
    print(f"   v6 flat->nest:   train={len(v6_train)}  val={len(v6_val)}")
    print(f"   gold flat->nest: train={len(gold_train)} val={len(gold_val)}")
    print(f"   COMBINED:        train={len(all_train)} val={len(all_val)}")

    write_jsonl(all_train, V8_TRAIN_OUT)
    write_jsonl(all_val,   V8_VAL_OUT)

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

    print("\n[3/5] Applying LoRA r=64 alpha=128 ...")
    model = FastModel.get_peft_model(
        model,
        finetune_vision_layers=False,
        finetune_language_layers=True,
        finetune_attention_modules=True,
        finetune_mlp_modules=True,
        r=64,
        lora_alpha=128,
        lora_dropout=0,
        bias="none",
        random_state=42,
    )
    model.print_trainable_parameters()

    print("\n[4/5] Tokenising ...")
    def to_text_ds(rows):
        texts = [
            "<start_of_turn>user\n"
            f"{r['instruction']}<end_of_turn>\n"
            "<start_of_turn>model\n"
            f"{r['output']}<end_of_turn>"
            for r in rows
        ]
        return Dataset.from_dict({"text": texts})

    train_ds = to_text_ds(all_train)
    val_ds   = to_text_ds(all_val)

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
    # critical fix for transformers 5.5 + trl loss kwargs
    trainer.model_accepts_loss_kwargs = False

    resume = get_latest_checkpoint(OUTPUT_DIR)
    if resume:
        print(f"   Resuming from: {resume}")
    print("\n>>> STARTING V8 TRAINING <<<\n")
    trainer.train(resume_from_checkpoint=resume)

    print("\nSaving final adapters ...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"DONE. Saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
