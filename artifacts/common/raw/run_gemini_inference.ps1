# Run Gemini 3 Pro Inference in Background with Live Logging
# Process 1000 queries with $10 budget limit

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Starting Gemini 3 Pro Inference on 1000 queries" -ForegroundColor Green
Write-Host "Budget: $10 | Model: google/gemini-3-pro-preview" -ForegroundColor Yellow
Write-Host "=" * 80 -ForegroundColor Cyan

# Change to compare directory
Set-Location "c:\Users\IMart.LAPTOP-TSDP3RQJ\Desktop\ashish data\compare"

# Start background job
Write-Host "`nStarting inference in background..." -ForegroundColor Yellow
$job = Start-Job -ScriptBlock {
    Set-Location "c:\Users\IMart.LAPTOP-TSDP3RQJ\Desktop\ashish data\compare"
    python gemini_1000_inference.py --input 76cat_queries --output gemini_1000_results.csv *>&1
}

Write-Host "✓ Job started (ID: $($job.Id))" -ForegroundColor Green
Write-Host "`nMonitoring output (Press Ctrl+C to stop watching, job continues)..." -ForegroundColor Cyan
Write-Host "-" * 80 -ForegroundColor Gray

# Monitor job output in real-time
while ($job.State -eq 'Running') {
    $output = Receive-Job $job
    if ($output) {
        Write-Host $output
    }
    Start-Sleep -Milliseconds 500
}

# Get final output
$finalOutput = Receive-Job $job
if ($finalOutput) {
    Write-Host $finalOutput
}

# Show completion status
Write-Host "`n" + ("=" * 80) -ForegroundColor Cyan
if ($job.State -eq 'Completed') {
    Write-Host "✓ INFERENCE COMPLETED SUCCESSFULLY" -ForegroundColor Green
} else {
    Write-Host "⚠ Job finished with state: $($job.State)" -ForegroundColor Yellow
}
Write-Host ("=" * 80) -ForegroundColor Cyan

# Clean up job
Remove-Job $job

Write-Host "`nOutput saved to: gemini_1000_results.csv" -ForegroundColor Green
Write-Host "Check results: Get-Content gemini_1000_results.csv | Select-Object -Last 5" -ForegroundColor Gray
