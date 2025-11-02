# Model Benchmarking & Deployment Guide

**Purpose**: Test different model configurations in production to find optimal speed/accuracy balance  
**Date**: November 2, 2025  
**Status**: Ready for execution

---

## 📋 Overview

This guide walks you through:
1. Preparing your production server
2. Pulling required models
3. Running benchmark tests
4. Analyzing results
5. Deploying the optimal configuration

**Estimated Time**: 2-4 hours (mostly model download time)

---

## 🎯 What We're Testing

### Model Configurations

| Config Name | Supervisor | Planner | Synthesizer | Total RAM | Speed | Quality |
|------------|------------|---------|-------------|-----------|-------|---------|
| **Current** | llama3.1:8b | llama3.1:8b | llama3.1:8b | ~5GB | Fast | Good |
| **Qwen72b** | qwen2.5:72b | qwen2.5:72b | qwen2.5:72b | ~40GB | Slow | Excellent |
| **Qwen32b** | qwen2.5:32b | qwen2.5:32b | qwen2.5:32b | ~18GB | Medium | Very Good |
| **Mixtral** | mixtral:8x7b | mixtral:8x7b | mixtral:8x7b | ~26GB | Medium | Very Good |
| **Specialized** | qwen2.5:72b | mixtral:8x7b | llama3.1:8b | ~45GB | Medium | Excellent |
| **Fast** | qwen2.5:32b | qwen2.5:32b | llama3.1:8b | ~20GB | Fast | Very Good |

### Test Queries (10 total)

1. **Simple Factual**: "Who is the CFO of Apple?"
2. **Numerical**: "What were Apple's revenues in 2023?"
3. **Risk Analysis**: "What are Tesla's main risk factors?"
4. **R&D Spending**: "How much did Microsoft spend on R&D?"
5. **Strategy**: "What is Nvidia's AI chip strategy?"
6. **Comparison**: "Compare Apple's and Microsoft's gross margins"
7. **Summarization**: "Key highlights from Pfizer's 10-K"
8. **List**: "Who are Apple's board members?"
9. **Policy**: "Amazon's stock-based compensation policy"
10. **Technical**: "Tesla's revenue recognition for vehicles"

---

## 📦 Step 1: Prepare Your Local Environment

### 1.1 Commit Your Changes

```bash
# On your local machine
cd /Users/harpreet/financeagent

# Stage the benchmark script
git add scripts/benchmark_models.py
git add docs/v2/09_MODEL_BENCHMARKING_GUIDE.md

# Commit
git commit -m "Add model benchmarking script and guide"

# Push to main
git push origin main
```

### 1.2 Verify Script Locally (Optional)

```bash
# Test the script syntax
python scripts/benchmark_models.py --help

# Expected output:
# usage: benchmark_models.py [-h] [--output OUTPUT] [--configs CONFIGS [CONFIGS ...]] [--queries QUERIES]
```

---

## 🚀 Step 2: Deploy to Production Server

### 2.1 SSH into Your Server

```bash
ssh your-user@your-server-ip
```

### 2.2 Pull Latest Code

```bash
cd ~/financeagent  # or wherever your project is

# Pull latest changes
git pull origin main

# Verify the script is there
ls -lh scripts/benchmark_models.py
```

### 2.3 Update Dependencies (if needed)

```bash
# Check if psycopg3 is installed (needed for async checkpointing)
docker-compose -f docker-compose.prod.yml exec backend pip list | grep psycopg

# If not installed, rebuild backend
docker-compose -f docker-compose.prod.yml build backend --no-cache
docker-compose -f docker-compose.prod.yml up -d backend
```

---

## 📥 Step 3: Pull Required Models

This is the longest step (30-60 minutes depending on your connection).

### 3.1 Check Current Models

```bash
docker exec -it financeagent-ollama-1 ollama list
```

### 3.2 Pull New Models

```bash
# Qwen2.5:72b (~40GB, ~20-30 min)
echo "Pulling Qwen2.5:72b..."
docker exec -it financeagent-ollama-1 ollama pull qwen2.5:72b

# Qwen2.5:32b (~18GB, ~10-15 min)
echo "Pulling Qwen2.5:32b..."
docker exec -it financeagent-ollama-1 ollama pull qwen2.5:32b

# Mixtral:8x7b (~26GB, ~15-20 min)
echo "Pulling Mixtral:8x7b..."
docker exec -it financeagent-ollama-1 ollama pull mixtral:8x7b-instruct

# Verify all models are downloaded
docker exec -it financeagent-ollama-1 ollama list
```

**Expected output:**
```
NAME                          ID              SIZE      MODIFIED
qwen2.5:72b                   abc123def       40 GB     2 minutes ago
qwen2.5:32b                   def456ghi       18 GB     5 minutes ago
mixtral:8x7b-instruct         ghi789jkl       26 GB     8 minutes ago
llama3.1:latest               jkl012mno       4.9 GB    7 days ago
nomic-embed-text:latest       mno345pqr       274 MB    7 days ago
```

### 3.3 Check Available Memory

```bash
# Check you have enough RAM
free -h

# Check disk space (models take ~90GB total)
df -h

# Expected: At least 100GB free disk space
```

---

## 🧪 Step 4: Run Benchmark Tests

### 4.1 Create Results Directory

```bash
cd ~/financeagent

# Create directory for results
mkdir -p benchmark_results
cd benchmark_results
```

### 4.2 Run Full Benchmark (All Configs)

```bash
# Run all 6 configurations × 10 queries = 60 tests
# Estimated time: 30-60 minutes
docker-compose -f ../docker-compose.prod.yml exec backend \
  python scripts/benchmark_models.py \
  --output /app/benchmark_results/full_benchmark_$(date +%Y%m%d_%H%M%S)
```

**What happens:**
- Tests each configuration sequentially
- Logs progress to console
- Saves results to JSON + Markdown files
- Shows real-time metrics

**Expected console output:**
```
================================================================================
MODEL BENCHMARK STARTING
================================================================================
Configurations to test: 6
Queries per configuration: 10
Total tests: 60
================================================================================

================================================================================
Testing Configuration: Current (llama3.1:8b)
================================================================================
Models: Supervisor=llama3.1, Planner=llama3.1, Synthesizer=llama3.1

[1/10] Testing: Who is the CFO of Apple?...
  ✓ Response time: 12.34s
  ✓ Accuracy score: 100.0%
  ✓ Answer length: 245 chars

[2/10] Testing: What were Apple's total revenues in fiscal year 2023?...
  ✓ Response time: 15.67s
  ✓ Accuracy score: 75.0%
  ✓ Answer length: 312 chars

...
```

### 4.3 Run Quick Test (Single Config)

If you want to test just one configuration first:

```bash
# Test only Qwen2.5:72b
docker-compose -f ../docker-compose.prod.yml exec backend \
  python scripts/benchmark_models.py \
  --output /app/benchmark_results/qwen72b_test \
  --configs "Qwen2.5:72b (All)"

# Test only first 3 queries
docker-compose -f ../docker-compose.prod.yml exec backend \
  python scripts/benchmark_models.py \
  --output /app/benchmark_results/quick_test \
  --queries 3
```

### 4.4 Monitor Progress

```bash
# In another terminal, watch the logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Watch memory usage
watch -n 5 'docker stats --no-stream'
```

---

## 📊 Step 5: Retrieve and Analyze Results

### 5.1 Copy Results to Local Machine

```bash
# On your LOCAL machine (new terminal)
cd ~/Downloads

# Copy results from server
scp -r your-user@your-server:/home/your-user/financeagent/benchmark_results .

# View the markdown report
cd benchmark_results
cat full_benchmark_*.md
```

### 5.2 Share Results with Me

You can share the results in two ways:

**Option A: Share the Markdown file**
```bash
# Just paste the contents of the .md file in chat
cat full_benchmark_*.md
```

**Option B: Share the JSON file**
```bash
# For detailed analysis, share the .json file
cat full_benchmark_*.json
```

### 5.3 Quick Analysis (On Server)

```bash
# View summary on server
cd ~/financeagent/benchmark_results
cat full_benchmark_*.md | head -50

# Or use grep to find key metrics
grep "Avg Time" full_benchmark_*.md
grep "Avg Accuracy" full_benchmark_*.md
```

---

## 🎯 Step 6: Deploy Optimal Configuration

After analyzing results, deploy the best configuration.

### 6.1 Update Production Config

```bash
# Edit .env on server
cd ~/financeagent
nano .env

# Update these lines based on benchmark results:
SUPERVISOR_MODEL=qwen2.5:72b      # Replace with optimal choice
PLANNER_MODEL=qwen2.5:72b         # Replace with optimal choice
SYNTHESIZER_MODEL=qwen2.5:72b     # Replace with optimal choice
```

### 6.2 Restart Backend

```bash
# Restart to apply new config
docker-compose -f docker-compose.prod.yml restart backend

# Verify it's using the new models
docker-compose -f docker-compose.prod.yml logs backend | grep "model"
```

### 6.3 Test in Production

```bash
# Test a query with the new configuration
curl -X POST https://yourdomain.com/api/v2/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Who is the CFO of Apple?"}'

# Measure response time
time curl -X POST https://yourdomain.com/api/v2/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What were Apple'\''s revenues in 2023?"}'
```

---

## 🔍 Step 7: Interpret Results

### Key Metrics to Compare

1. **Average Response Time** - Lower is better
   - Fast: <15s
   - Medium: 15-30s
   - Slow: >30s

2. **Average Accuracy** - Higher is better
   - Excellent: >85%
   - Good: 70-85%
   - Poor: <70%

3. **Success Rate** - Should be 100%
   - Any failures indicate model compatibility issues

4. **Balance Score** - Speed × Accuracy
   - Highest score = best overall choice

### Example Decision Matrix

```
If you prioritize SPEED:
  → Choose "Fast (Qwen32b + Llama8b)"
  → Expected: 10-15s response, 75-80% accuracy

If you prioritize ACCURACY:
  → Choose "Qwen2.5:72b (All)"
  → Expected: 25-35s response, 85-90% accuracy

If you want BALANCE:
  → Choose "Specialized (Qwen72b + Mixtral + Llama8b)"
  → Expected: 18-25s response, 80-85% accuracy
```

---

## 🚨 Troubleshooting

### Issue: Model Not Found

```bash
# Error: "model 'qwen2.5:72b' not found"
# Solution: Pull the model
docker exec -it financeagent-ollama-1 ollama pull qwen2.5:72b
```

### Issue: Out of Memory

```bash
# Error: "OOM" or container crashes
# Solution: Test smaller models first
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/benchmark_models.py \
  --configs "Current (llama3.1:8b)" "Qwen2.5:32b (All)"
```

### Issue: Script Fails to Import

```bash
# Error: "ModuleNotFoundError"
# Solution: Run inside the backend container
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/benchmark_models.py --output /app/results
```

### Issue: Benchmark Takes Too Long

```bash
# Solution: Test fewer queries
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/benchmark_models.py \
  --queries 3 \
  --output /app/quick_test
```

---

## 📝 Checklist

Before starting:
- [ ] Code committed and pushed to main
- [ ] SSH access to production server verified
- [ ] At least 100GB free disk space
- [ ] At least 45GB free RAM
- [ ] Backup of current .env file

During benchmark:
- [ ] All models downloaded successfully
- [ ] Benchmark script running without errors
- [ ] Monitoring memory usage
- [ ] Results being saved to files

After benchmark:
- [ ] Results copied to local machine
- [ ] Markdown report reviewed
- [ ] Optimal configuration identified
- [ ] Production .env updated
- [ ] Backend restarted
- [ ] New configuration tested

---

## 🎯 Expected Timeline

| Step | Duration | Notes |
|------|----------|-------|
| 1. Prepare local | 5 min | Commit and push |
| 2. Deploy to prod | 5 min | Pull code |
| 3. Pull models | 30-60 min | Depends on connection |
| 4. Run benchmark | 30-60 min | 6 configs × 10 queries |
| 5. Analyze results | 10 min | Review reports |
| 6. Deploy optimal | 5 min | Update config |
| **Total** | **1.5-2.5 hours** | Mostly waiting |

---

## 📧 Next Steps

1. **Run the benchmark** following this guide
2. **Share the results** (paste the .md file contents)
3. **I'll analyze** and recommend the optimal configuration
4. **Deploy** the recommended config
5. **Monitor** performance in production

**Questions?** Just ask! I'm here to help interpret the results and make the best decision.

---

## 💡 Pro Tips

1. **Run during low traffic** - Benchmark uses significant resources
2. **Test incrementally** - Start with 1-2 configs, then expand
3. **Monitor memory** - Use `docker stats` to watch RAM usage
4. **Keep current config** - Don't change production until analysis complete
5. **Document findings** - Add notes to the benchmark results

Good luck! 🚀
