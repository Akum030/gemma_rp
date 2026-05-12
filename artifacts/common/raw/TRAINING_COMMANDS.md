# Gemma V4 Fine-tuning - Quick Commands

## Upload files to server
```bash
scp cat74_train.jsonl cat74_val.jsonl finetune_gemma_v4.py inference_v4.py run_training.sh \
    root@func-gemma-gpu-india-1a:~/gemma2_9b/
```

## On the server

### Option 1: Using the run script (recommended)
```bash
cd ~/gemma2_9b
chmod +x run_training.sh
./run_training.sh
```
This will start training in background and show live logs (Ctrl+C to exit monitoring, training continues).

### Option 2: Manual nohup command
```bash
cd ~/gemma2_9b
nohup python -u finetune_gemma_v4.py > training.log 2>&1 &
tail -f training.log  # Monitor logs
```

## Monitor training

### View live logs
```bash
tail -f training.log
```

### View last 50 lines
```bash
tail -n 50 training.log
```

### Search for specific info
```bash
grep "Epoch" training.log           # See epoch progress
grep "loss" training.log            # See loss values
grep "GPU" training.log             # GPU info
grep "Saving" training.log          # Checkpoint saves
```

### Check GPU usage
```bash
nvidia-smi
watch -n 1 nvidia-smi  # Auto-refresh every second
```

### Check if training is running
```bash
ps aux | grep finetune_gemma_v4.py
```

### Stop training
```bash
# Find PID first
ps aux | grep finetune_gemma_v4.py

# Kill by PID
kill <PID>

# Or force kill
pkill -f finetune_gemma_v4.py
```

## After training completes

### Test inference
```bash
python inference_v4.py --query "siemens 1.5 kw 415v three phase motor"
python inference_v4.py --query "abb 3 hp single phase 230v foot mounted motor"
python inference_v4.py --query "crompton 2.2 kw bldc servo motor ip55"
```

### Check model size
```bash
du -sh isq-gemma2-9b-finetuned-v4-priority/
```

### List checkpoints
```bash
ls -lh isq-gemma2-9b-finetuned-v4-priority/
```

## Estimated timeline
- Training: ~6-8 hours (2 epochs, 1600 samples)
- Checkpoints saved every 200 steps
- Can resume from checkpoint if interrupted

## Troubleshooting

### Out of memory
If CUDA OOM occurs:
1. Check current settings in finetune_gemma_v4.py:
   - BATCH_SIZE=2 (reduce to 1 if needed)
   - MAX_LENGTH=768 (reduce to 512 if needed)
   - eval_strategy="no" (already disabled)

### Training too slow
Expected: ~2-3 minutes per training step with 2 T4 GPUs

### Loss not decreasing
Check logs for:
- Initial loss should be ~2-4
- Should decrease to <1.0 by end of epoch 1
- Final loss should be ~0.3-0.6
