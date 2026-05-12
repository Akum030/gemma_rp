# Comprehensive GPU check and restart with optimized script

Write-Host "=== GPU DIAGNOSTIC & RESTART ===" -ForegroundColor Cyan

Write-Host "`n1. Uploading OPTIMIZED script..." -ForegroundColor Green
scp "c:\Users\IMart.LAPTOP-TSDP3RQJ\Desktop\ashish data\gemma_1000_inference.py" root@func-gemma-gpu-india-1a:~/gemma2_9b/version4/

Write-Host "`n2. Checking GPU status BEFORE killing process..." -ForegroundColor Yellow
ssh root@func-gemma-gpu-india-1a "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv"

Write-Host "`n3. Killing stuck process..." -ForegroundColor Red
ssh root@func-gemma-gpu-india-1a "pkill -f gemma_1000_inference.py"
Start-Sleep -Seconds 3

Write-Host "`n4. Clearing GPU cache..." -ForegroundColor Yellow
ssh root@func-gemma-gpu-india-1a "python3 -c 'import torch; torch.cuda.empty_cache(); print(\"GPU cache cleared\")'"

Write-Host "`n5. GPU status AFTER cleanup..." -ForegroundColor Yellow
ssh root@func-gemma-gpu-india-1a "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv"

Write-Host "`n6. Checking completed queries..." -ForegroundColor Cyan
ssh root@func-gemma-gpu-india-1a "cd ~/gemma2_9b/version4 && wc -l gemma_v4_1000_results.csv 2>/dev/null || echo '0 queries completed'"

Write-Host "`n7. Starting OPTIMIZED inference (256 max tokens, no sampling)..." -ForegroundColor Green
ssh root@func-gemma-gpu-india-1a "cd ~/gemma2_9b/version4 && nohup python -u gemma_1000_inference.py --input 76cat_queries --output gemma_v4_1000_results.csv --start 358 > inference_optimized.log 2>&1 &"

Write-Host "`n8. Waiting for startup..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

Write-Host "`n9. Monitoring log (watch for speed improvement - should be 2-10s per query)..." -ForegroundColor Green
Write-Host "   Press Ctrl+C to stop monitoring`n" -ForegroundColor Gray
ssh root@func-gemma-gpu-india-1a "tail -f ~/gemma2_9b/version4/inference_optimized.log"
