# Dataset 2 Ground Truth Generation & Metrics Calculation

## Step 1: Set Up API Key

You need an OpenAI API key (or compatible API) to generate ground truth.

### Windows PowerShell:
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

### Alternative: Use Anthropic Claude API
```powershell
$env:ANTHROPIC_API_KEY="your-anthropic-key"
$env:API_BASE_URL="https://api.anthropic.com/v1"
```

---

## Step 2: Generate Ground Truth

Run the ground truth generation script:

```powershell
python generate_groundtruth_dataset2.py
```

**Options available:**
1. Full dataset (1198 queries) - ~4-6 hours, high cost
2. **300 query sample - RECOMMENDED** - ~1 hour, medium cost
3. 200 query sample - ~40 mins, low cost  
4. Test with 10 queries first

**Recommendation:** Start with option 4 (10 queries) to test, then run option 2 (300 queries)

---

## Step 3: Calculate Metrics

Once ground truth is generated, calculate metrics:

```powershell
python calculate_dataset2_metrics.py
```

This will output:
- Key Found Rate for each model
- Value Match Rate for each model
- Average attributes per query
- Ranking table (same format as Dataset 1)

---

## Expected Output Format

```
| Rank | Model | Key Found | Value Match | Avg Attrs/Query | Verdict |
|------|-------|-----------|-------------|-----------------|---------|
| 🥇 | **Gemini** | 68% | 90% | 3.17 | Best accuracy |
| 🥈 | **QMeans** | 62% | 82% | 1.31 | Good baseline |
| 🥉 | **Gemma** | 13% | 80% | 2.04 | Needs improvement |
```

---

## Cost Estimates (using GPT-4-turbo)

| Sample Size | API Calls | Est. Cost | Time |
|-------------|-----------|-----------|------|
| 10 queries | 10 | $0.10 | 30 sec |
| 200 queries | 200 | $2-3 | 40 min |
| 300 queries | 300 | $3-5 | 1 hour |
| 1198 queries | 1198 | $12-20 | 4-6 hours |

---

## Troubleshooting

### Error: "OPENAI_API_KEY not set"
Set your API key as shown in Step 1

### Error: "Rate limit exceeded"
The script includes 0.5s delay between calls. If you hit rate limits:
- Use a lower tier model (gpt-3.5-turbo)
- Increase sleep time in generate_groundtruth_dataset2.py

### Error: "ground_truth_dataset2.csv not found"
You need to run Step 2 before Step 3

---

## Files Generated

1. `ground_truth_dataset2.csv` - Ground truth attributes
2. `ground_truth_dataset2.csv.temp` - Checkpoint file (saved every 50 queries)

---

## Quick Start (Recommended Workflow)

```powershell
# 1. Set API key
$env:OPENAI_API_KEY="your-key"

# 2. Test with 10 queries first
python generate_groundtruth_dataset2.py
# Select option 4

# 3. If test looks good, run 300 query sample
python generate_groundtruth_dataset2.py
# Select option 2

# 4. Calculate metrics
python calculate_dataset2_metrics.py
```

This will give you statistically significant results for your team presentation in about 1 hour!
