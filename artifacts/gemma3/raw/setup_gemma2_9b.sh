#!/bin/bash

# Complete setup script for Gemma 2 9B training on GPU server
# Run this on your server: bash setup_gemma2_9b.sh

echo "========================================"
echo "Gemma 2 9B Training Environment Setup"
echo "========================================"

# Step 1: Install dependencies
echo -e "\n[1/5] Installing dependencies..."
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers>=4.38.0
pip install peft>=0.8.0
pip install datasets>=2.16.0
pip install accelerate>=0.26.0
pip install bitsandbytes>=0.42.0
pip install huggingface-hub

# Step 2: Login to HuggingFace
echo -e "\n[2/5] HuggingFace Authentication"
echo "Please login to HuggingFace (need token with Gemma access):"
echo "Get token from: https://huggingface.co/settings/tokens"
huggingface-cli login

# Step 3: Download Gemma 2 9B
echo -e "\n[3/5] Downloading Gemma 2 9B model..."
python download_gemma2_9b.py

# Step 4: Prepare training data
echo -e "\n[4/5] Preparing training data..."
python prepare_gemma2_9b_training_data.py

# Step 5: Verify setup
echo -e "\n[5/5] Verifying setup..."

# Check CUDA
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU Count: {torch.cuda.device_count()}')"

# Check model files
if [ -d "/home3/indiamart/func_gemma/models/gemma-2-9b-it" ]; then
    echo "✓ Model downloaded"
else
    echo "✗ Model not found"
fi

# Check training data
if [ -f "product_train.jsonl" ]; then
    echo "✓ Training data ready"
    wc -l product_train.jsonl
else
    echo "✗ Training data not generated"
fi

echo -e "\n========================================"
echo "Setup complete!"
echo "========================================"
echo -e "\nNext steps:"
echo "  1. Review training config in finetune_gemma2_9b.py"
echo "  2. Start training: python finetune_gemma2_9b.py"
echo "  3. Monitor with: watch -n 1 nvidia-smi"
echo -e "\nEstimated training time: 8-12 hours"
