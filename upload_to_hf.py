"""
Upload V11 LoRA adapter to Hugging Face Hub.

Run this script ON THE REMOTE SERVER where the adapter lives:
  python upload_to_hf.py --repo_id YOUR_HF_USERNAME/gemma4-e4b-priority-attr-v11

Requires:
  pip install huggingface_hub
  export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
"""

import argparse
import os
import sys
from pathlib import Path

# ── Default paths (edit if different on your server) ──────────────────────────
DEFAULT_ADAPTER_DIR = "/home3/indiamart/gemma_4/isq-gemma4-e4b-v11-priority-balanced"
BASE_MODEL_ID = "google/gemma-4-e4b-it"

# ── Required files that confirm this is a valid PEFT adapter ──────────────────
REQUIRED_FILES = ["adapter_config.json", "adapter_model.safetensors"]
FALLBACK_FILES = ["adapter_model.bin"]          # older PEFT format

README_CONTENT = """\
---
language: en
license: gemma
base_model: google/gemma-4-e4b-it
tags:
  - gemma
  - gemma-4
  - peft
  - lora
  - unsloth
  - attribute-extraction
  - information-extraction
  - b2b
  - industrial
library_name: peft
---

# Gemma 4 E4B — Priority-Ordered Attribute Extraction (V11)

Fine-tuned LoRA adapter on top of `google/gemma-4-e4b-it` for **priority-ordered structured attribute extraction** from industrial B2B search queries.

Given a raw search query like `"siemens 45 hp 3 phase 1440 rpm motor"`, the model outputs nested JSON that:
- **Ranks attributes by user intent** (brand > product type > primary spec > model > ...)
- **Ranks canonical key synonyms** for each attribute

```json
{
  "attributes": [
    { "attribute_priority1": { "value": "siemens",  "key_priority1": "brand",     "key_priority2": "manufacturer" } },
    { "attribute_priority2": { "value": "motor",    "key_priority1": "part_type", "key_priority2": "product_type" } },
    { "attribute_priority3": { "value": "45 hp",    "key_priority1": "power",     "key_priority2": "horsepower"   } },
    { "attribute_priority4": { "value": "3 phase",  "key_priority1": "phase",     "key_priority2": "phase_type"   } },
    { "attribute_priority5": { "value": "1440 rpm", "key_priority1": "rpm",       "key_priority2": "speed"        } }
  ]
}
```

## Evaluation (1,000-query ground-truth benchmark)

| Metric | AttrExt (production baseline) | **This model (V11)** |
|---|---|---|
| Key Precision | 95.95% | 79.47% |
| Key Recall | 29.82% | 31.82% |
| **Key F1** | 45.50% | **45.44%** |
| K+V Precision | 12.66% | 35.43% |
| K+V Recall | 3.93% | 14.18% |
| **Key+Value F1** | 6.00% | **20.26%** (3.4× better) |

## Training details

| Parameter | Value |
|---|---|
| Base model | `google/gemma-4-e4b-it` |
| Framework | Unsloth + TRL SFTTrainer + PEFT LoRA |
| LoRA r / alpha | 32 / 64 |
| LoRA dropout | 0.0 |
| Max sequence length | 768 |
| Epochs | 2 |
| Batch size (effective) | 32 (bs=2, grad_acc=16) |
| Learning rate | 7e-5 (cosine + 80-step warmup) |
| Optimizer | AdamW 8-bit |
| Precision | fp16 (4-bit QLoRA) |
| Hardware | 1× Tesla T4 (15 GB) |

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE_MODEL_ID = "google/gemma-4-e4b-it"
ADAPTER_ID    = "YOUR_HF_USERNAME/gemma4-e4b-priority-attr-v11"  # ← change this

tokenizer  = AutoTokenizer.from_pretrained(BASE_MODEL_ID)
base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID, device_map="auto")
model      = PeftModel.from_pretrained(base_model, ADAPTER_ID)

INSTRUCTION = (
    "Extract product attributes from the search query. Return JSON with key "
    "\\"attributes\\" = list of objects. Each object has ONE field "
    "\\"attribute_priorityN\\" (N=1 most important to user intent, N=2 next, ...). "
    "That field is itself an object with \\"value\\" (extracted text) and "
    "\\"key_priority1\\", \\"key_priority2\\", ... ranking synonym key names."
)

query = "siemens 45 hp 3 phase 1440 rpm motor"
prompt = f"{INSTRUCTION}\\n\\nQuery: {query}\\nOutput:"

inputs  = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=256, temperature=0.1)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Repository

Training scripts, evaluation code, and benchmark: https://github.com/Akum030/gemma_rp

## License

This adapter inherits the [Gemma Terms of Use](https://ai.google.dev/gemma/terms).
"""


def check_adapter_dir(adapter_dir: Path) -> None:
    """Verify the adapter directory contains expected files."""
    if not adapter_dir.exists():
        print(f"ERROR: adapter directory not found: {adapter_dir}")
        sys.exit(1)

    found = list(adapter_dir.iterdir())
    print(f"\n[CHECK] Files in {adapter_dir}:")
    for f in sorted(found):
        print(f"        {f.name}  ({f.stat().st_size:,} bytes)")

    # Must have adapter_config.json
    if not (adapter_dir / "adapter_config.json").exists():
        print("\nERROR: adapter_config.json not found — this may not be a PEFT adapter folder.")
        sys.exit(1)

    # Must have weights (safetensors or bin)
    has_weights = (
        (adapter_dir / "adapter_model.safetensors").exists()
        or (adapter_dir / "adapter_model.bin").exists()
        or any(f.suffix == ".safetensors" for f in found)
    )
    if not has_weights:
        print("\nERROR: No adapter weight file found (adapter_model.safetensors / .bin).")
        sys.exit(1)

    print("\n[OK] Adapter directory validated.")


def write_readme(adapter_dir: Path) -> None:
    readme_path = adapter_dir / "README.md"
    readme_path.write_text(README_CONTENT, encoding="utf-8")
    print(f"[OK] README.md written to {readme_path}")


def upload(adapter_dir: Path, repo_id: str, token: str, private: bool) -> None:
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("ERROR: huggingface_hub not installed. Run:  pip install huggingface_hub")
        sys.exit(1)

    api = HfApi(token=token)

    # Create repo if it doesn't exist
    print(f"\n[HF] Creating / verifying repo: {repo_id}  (private={private})")
    try:
        api.create_repo(
            repo_id=repo_id,
            repo_type="model",
            private=private,
            exist_ok=True,
        )
        print(f"[HF] Repo ready: https://huggingface.co/{repo_id}")
    except Exception as e:
        print(f"ERROR creating repo: {e}")
        sys.exit(1)

    # Upload folder
    print(f"\n[HF] Uploading {adapter_dir}  →  {repo_id} ...")
    print("     This may take a few minutes depending on file sizes.\n")
    try:
        api.upload_folder(
            folder_path=str(adapter_dir),
            repo_id=repo_id,
            repo_type="model",
            commit_message="Upload V11 priority-ordered attribute extraction adapter",
        )
    except Exception as e:
        print(f"ERROR during upload: {e}")
        sys.exit(1)

    print(f"\n[DONE] Model uploaded successfully!")
    print(f"       View at: https://huggingface.co/{repo_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Upload Gemma 4 V11 LoRA adapter to Hugging Face Hub"
    )
    parser.add_argument(
        "--model_dir",
        default=DEFAULT_ADAPTER_DIR,
        help=f"Local path to adapter folder (default: {DEFAULT_ADAPTER_DIR})",
    )
    parser.add_argument(
        "--repo_id",
        required=True,
        help="Hugging Face repo id, e.g.  YOUR_HF_USERNAME/gemma4-e4b-priority-attr-v11",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        default=False,
        help="Make the HF repo private (default: public)",
    )
    args = parser.parse_args()

    # Get token
    token = os.environ.get("HF_TOKEN", "")
    if not token:
        print("ERROR: HF_TOKEN environment variable is not set.")
        print("       Run:  export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx")
        sys.exit(1)

    adapter_dir = Path(args.model_dir)

    print("=" * 60)
    print("  Gemma 4 V11 Adapter → Hugging Face Hub Uploader")
    print("=" * 60)
    print(f"  Adapter dir : {adapter_dir}")
    print(f"  Repo id     : {args.repo_id}")
    print(f"  Private     : {args.private}")
    print("=" * 60)

    check_adapter_dir(adapter_dir)
    write_readme(adapter_dir)
    upload(adapter_dir, args.repo_id, token, args.private)


if __name__ == "__main__":
    main()
