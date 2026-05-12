#!/bin/bash
# Run Gemma fine-tuning in background with nohup
# Logs will be saved to training.log

echo "Starting Gemma 2 9B fine-tuning in background..."
echo "Logs: training.log"
echo "To monitor: tail -f training.log"
echo "To check GPU: nvidia-smi"
echo ""

nohup python -u finetune_gemma_v4.py > training.log 2>&1 &

PID=$!
echo "Training started with PID: $PID"
echo "To stop: kill $PID"
echo ""
echo "Monitoring logs (press Ctrl+C to exit monitoring, training will continue)..."
sleep 2
tail -f training.log
