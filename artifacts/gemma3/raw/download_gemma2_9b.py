"""
Download Gemma 2 9B Model
Requires HuggingFace token with Gemma access
"""

from huggingface_hub import snapshot_download
import os

# Configuration
MODEL_ID = "google/gemma-2-9b-it"  # Instruction-tuned version
LOCAL_DIR = "/home3/indiamart/func_gemma/models/gemma-2-9b-it"

print("=" * 60)
print("Gemma 2 9B Model Download")
print("=" * 60)
print(f"\nModel: {MODEL_ID}")
print(f"Target: {LOCAL_DIR}")
print("\nNote: You need HuggingFace token with Gemma access")
print("Get token: https://huggingface.co/settings/tokens")
print("Accept Gemma license: https://huggingface.co/google/gemma-2-9b-it")
print("=" * 60)

# Create directory
os.makedirs(LOCAL_DIR, exist_ok=True)

# Download model
print("\n🔽 Downloading Gemma 2 9B (this will take time - ~18GB)...")
print("Progress:")

try:
    snapshot_download(
        repo_id=MODEL_ID,
        local_dir=LOCAL_DIR,
        local_dir_use_symlinks=False,
        resume_download=True
    )
    
    print("\n✓ Download complete!")
    print(f"Model saved to: {LOCAL_DIR}")
    
    # Verify files
    files = os.listdir(LOCAL_DIR)
    print(f"\nDownloaded files ({len(files)} files):")
    key_files = ['config.json', 'tokenizer.json', 'tokenizer_config.json']
    safetensor_files = [f for f in files if f.endswith('.safetensors')]
    
    for f in key_files:
        status = "✓" if f in files else "✗"
        print(f"  {status} {f}")
    
    print(f"  ✓ {len(safetensor_files)} model shard(s)")
    
    print("\n" + "=" * 60)
    print("✓ Model ready for training!")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ Download failed: {e}")
    print("\nTroubleshooting:")
    print("  1. Login first: huggingface-cli login")
    print("  2. Accept Gemma license at: https://huggingface.co/google/gemma-2-9b-it")
    print("  3. Check internet connection")
    print("  4. Ensure sufficient disk space (~20GB)")
