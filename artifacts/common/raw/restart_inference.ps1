# Restart inference with memory leak fixes

Write-Host "1. Uploading fixed script..." -ForegroundColor Cyan
scp "c:\Users\IMart.LAPTOP-TSDP3RQJ\Desktop\ashish data\gemma_1000_inference.py" root@func-gemma-gpu-india-1a:~/gemma2_9b/version4/

Write-Host "`n2. Killing stuck process..." -ForegroundColor Yellow
ssh root@func-gemma-gpu-india-1a "pkill -f gemma_1000_inference.py"

Start-Sleep -Seconds 2

Write-Host "`n3. Checking existing progress..." -ForegroundColor Cyan
ssh root@func-gemma-gpu-india-1a "cd ~/gemma2_9b/version4 && wc -l gemma_v4_1000_results.csv"

Write-Host "`n4. Restarting with memory leak fixes (resume from query 356)..." -ForegroundColor Green
ssh root@func-gemma-gpu-india-1a "cd ~/gemma2_9b/version4 && nohup python -u gemma_1000_inference.py --input 76cat_queries --output gemma_v4_1000_results.csv --start 356 > inference_log_resume.txt 2>&1 &"

Write-Host "`n5. Monitoring log (Ctrl+C to stop viewing)..." -ForegroundColor Cyan
Start-Sleep -Seconds 3
ssh root@func-gemma-gpu-india-1a "tail -f ~/gemma2_9b/version4/inference_log_resume.txt"
