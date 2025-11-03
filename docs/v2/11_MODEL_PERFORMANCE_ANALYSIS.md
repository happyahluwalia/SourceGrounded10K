# Model Performance Analysis & Benchmarking

**Date**: November 3, 2025  
**Status**: ✅ Completed  
**Version**: v2.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Testing Methodology](#testing-methodology)
3. [Model Configurations Tested](#model-configurations-tested)
4. [Test Queries](#test-queries)
5. [Results & Analysis](#results--analysis)
6. [Key Findings](#key-findings)
7. [Recommendations](#recommendations)
8. [Technical Details](#technical-details)

---

## Executive Summary

### Objective
Evaluate different LLM configurations to optimize the balance between **response speed** and **answer accuracy** for our financial analysis application.

### Winner: Current Configuration (llama3.1:8b)
- **Speed**: 30.2s average (fastest)
- **Accuracy**: 72.5% (highest)
- **Reliability**: 10/10 success rate
- **Cost**: Lowest memory footprint (~7GB)

### Key Insight
**Larger models ≠ Better performance**. The 72B parameter model was 23x slower with 30% worse accuracy than our baseline 8B model.

---

## Testing Methodology

### Architecture Under Test

Our v2 agentic architecture uses **3 specialized LLM roles**:

```
User Query
    ↓
[1. SupervisorAgent] ← Uses SUPERVISOR_MODEL
    ↓ (routes to FilingQATool)
    ↓
[2. FilingQATool]
    ├─→ Pre-processing (deterministic)
    ├─→ Planning ← Uses PLANNER_MODEL
    ├─→ Execution (deterministic: vector search, data prep)
    └─→ Synthesis ← Uses SYNTHESIZER_MODEL
    ↓
Final Answer
```

### What We Tested

**Variables**:
- Different model sizes (8B, 32B, 72B parameters)
- Different model families (Llama, Qwen, Mixtral)
- Different role assignments (homogeneous vs specialized)

**Constants**:
- Same 10 test queries
- Same production data (SEC filings)
- Same vector database (Qdrant)
- Same prompts and logic

**Metrics Measured**:
1. **Response Time** - Total time from query to answer (seconds)
2. **Accuracy Score** - Keyword matching against expected answers (0-100%)
3. **Success Rate** - Queries completed without errors
4. **Answer Length** - Character count of responses

---

## Model Configurations Tested

### 1. Current (llama3.1:8b) - Baseline ✅
```yaml
Supervisor: llama3.1:8b
Planner: llama3.1:8b
Synthesizer: llama3.1:8b
Memory: ~7GB
Parameters: 8B total
```

### 2. Qwen2.5:72b (All) - Maximum Quality
```yaml
Supervisor: qwen2.5:72b
Planner: qwen2.5:72b
Synthesizer: qwen2.5:72b
Memory: ~41GB
Parameters: 72B total
```

### 3. Qwen2.5:32b (All) - Balanced
```yaml
Supervisor: qwen2.5:32b
Planner: qwen2.5:32b
Synthesizer: qwen2.5:32b
Memory: ~18GB
Parameters: 32B total
```

### 4. Mixtral:8x7b (All) - MoE Architecture ❌
```yaml
Supervisor: mixtral:8x7b
Planner: mixtral:8x7b
Synthesizer: mixtral:8x7b
Memory: ~26GB
Parameters: 47B total (8 experts × 7B, 2 active)
Status: FAILED - All queries errored
```

### 5. Specialized Mix - Role-Optimized
```yaml
Supervisor: qwen2.5:72b  # Best reasoning
Planner: mixtral:8x7b    # Best planning
Synthesizer: llama3.1:8b # Fast synthesis
Memory: ~45GB
Parameters: Mixed
```

### 6. Fast Mix - Speed-Optimized
```yaml
Supervisor: qwen2.5:32b  # Good reasoning
Planner: qwen2.5:32b     # Good planning
Synthesizer: llama3.1:8b # Fast synthesis
Memory: ~20GB
Parameters: Mixed
```

---

## Test Queries

10 queries covering different complexity levels and use cases:

| # | Query | Category | Difficulty | Expected Keywords |
|---|-------|----------|------------|-------------------|
| 1 | Who is the CFO of Apple? | Simple Factual | Easy | Kevan Parekh, CFO |
| 2 | What were Apple's total revenues last fiscal year? | Numerical | Easy | revenue, 416, billion |
| 3 | What are the main risk factors for investing in Amazon? | Analysis | Medium | risk, competition, regulatory |
| 4 | How much did Microsoft spend on R&D last year? | Numerical | Easy | research, development, billion |
| 5 | What is Microsoft's business strategy for cloud computing? | Strategic | Medium | cloud, Azure, strategy |
| 6 | Compare Apple's gross margin to Microsoft's gross margin | Comparison | Hard | gross margin, Apple, Microsoft |
| 7 | What were the key highlights from Pfizer's latest 10-K? | Summarization | Medium | revenue, product, pipeline |
| 8 | Who are the members of Apple's board of directors? | List | Easy | director, board, Tim Cook |
| 9 | What is Amazon's policy on stock-based compensation? | Policy | Medium | stock, compensation, equity |
| 10 | Explain Amazon's revenue recognition policy for AWS | Technical | Hard | revenue recognition, AWS |

**Coverage**:
- 5 companies (AAPL, MSFT, AMZN, PFE, HOOD)
- 3 difficulty levels (Easy: 4, Medium: 4, Hard: 2)
- 7 query types (factual, numerical, analysis, strategic, comparison, summarization, policy)

---

## Results & Analysis

### Summary Table

| Configuration | Avg Time (s) | Avg Accuracy | Success Rate | Speed vs Baseline | Accuracy vs Baseline |
|--------------|-------------|--------------|--------------|-------------------|---------------------|
| **Current (llama3.1:8b)** | **30.2** | **72.5%** | **10/10** | **1.0x** | **100%** |
| Qwen2.5:72b | 692.9 | 50.8% | 10/10 | 0.04x (23x slower) | 70% |
| Qwen2.5:32b | 197.9 | 51.7% | 10/10 | 0.15x (6.5x slower) | 71% |
| Mixtral:8x7b | N/A | N/A | 0/10 | FAILED | FAILED |
| Specialized Mix | 210.5 | 34.2% | 10/10 | 0.14x (7x slower) | 47% |
| Fast Mix | 105.5 | 53.3% | 10/10 | 0.29x (3.5x slower) | 74% |

### Detailed Performance by Configuration

#### 🏆 Winner: Current (llama3.1:8b)

**Performance**:
- Average: 30.2s (range: 16.9s - 46.5s)
- Accuracy: 72.5%
- Memory: ~7GB

**Strengths**:
- ✅ Fastest response time
- ✅ Highest accuracy
- ✅ Most consistent (lowest variance)
- ✅ Lowest resource usage
- ✅ 100% success rate

**Query Breakdown**:
- Best: "Compare margins" (46.5s, 100% accuracy)
- Worst: "Pfizer highlights" (33.4s, 25% accuracy)
- Typical: 25-35s with 66-100% accuracy

**Why It Won**:
- Well-tuned for our prompts
- Fast enough for production
- Reliable and consistent
- Already optimized through usage

---

#### ❌ Worst: Qwen2.5:72b (All)

**Performance**:
- Average: 692.9s (11.5 minutes!)
- Accuracy: 50.8%
- Memory: ~41GB

**Weaknesses**:
- ❌ 23x slower than baseline
- ❌ 30% worse accuracy
- ❌ Extreme variance (399s - 1176s)
- ❌ Unacceptable user experience

**Query Breakdown**:
- Fastest: 399s (6.7 min) - Still too slow
- Slowest: 1176s (19.6 min) - Completely unusable
- Most queries: 600-800s (10-13 min)

**Why It Failed**:
- Model too large for task complexity
- Overthinking simple queries
- Inference time dominates
- No accuracy benefit despite size

**Example**: "Who is the CFO of Apple?"
- llama3.1: 22.8s, 66.7% accuracy
- qwen72b: 424.8s (18.6x slower), 33.3% accuracy (worse!)

---

#### 🤔 Disappointing: Qwen2.5:32b (All)

**Performance**:
- Average: 197.9s (3.3 minutes)
- Accuracy: 51.7%
- Memory: ~18GB

**Analysis**:
- 6.5x slower than baseline
- 29% worse accuracy
- No clear benefit over llama3.1

**Verdict**: Not worth the tradeoff

---

#### 💥 Failed: Mixtral:8x7b (All)

**Status**: Complete failure - 0/10 queries succeeded

**Likely Causes**:
- Model compatibility issues
- Prompt format incompatibility
- Ollama integration problems
- MoE architecture quirks

**Action**: Removed from consideration

---

#### 🎯 Interesting: Fast Mix (Qwen32b + Llama8b)

**Performance**:
- Average: 105.5s (1.8 minutes)
- Accuracy: 53.3%
- Memory: ~20GB

**Analysis**:
- 3.5x slower than baseline
- 26% worse accuracy
- Best of the "larger model" options
- Still not competitive with llama3.1

**Potential**: Could be viable if accuracy improves with prompt tuning

---

#### 🤷 Confused: Specialized Mix

**Performance**:
- Average: 210.5s
- Accuracy: 34.2% (worst!)
- Memory: ~45GB

**Why It Failed**:
- Models may have conflicting output formats
- Handoff between different models problematic
- No synergy benefit
- Worst accuracy despite most resources

**Lesson**: Homogeneous models work better than mixed

---

## Key Findings

### 1. Size Doesn't Equal Performance

**Observation**: Larger models performed significantly worse

| Model Size | Avg Time | Accuracy | Verdict |
|-----------|----------|----------|---------|
| 8B (llama3.1) | 30s | 72.5% | ✅ Best |
| 32B (qwen) | 198s | 51.7% | ❌ Worse |
| 72B (qwen) | 693s | 50.8% | ❌ Much Worse |

**Why?**
- Our task is well-defined (RAG over structured data)
- Smaller models are better tuned for our prompts
- Larger models overthink simple queries
- Inference time dominates total latency

---

### 2. Speed Matters More Than We Thought

**User Experience Thresholds**:
- ✅ **< 30s**: Acceptable (users will wait)
- ⚠️ **30-60s**: Borderline (users get impatient)
- ❌ **> 60s**: Unacceptable (users abandon)

**Results**:
- llama3.1: 30s ✅
- Fast Mix: 106s ❌
- Qwen32b: 198s ❌
- Qwen72b: 693s ❌❌❌

**Conclusion**: Only llama3.1 meets UX requirements

---

### 3. Accuracy Paradox

**Expected**: Larger models → Better accuracy  
**Reality**: Smaller model had highest accuracy

**Possible Explanations**:
1. **Prompt Tuning**: Our prompts optimized for llama3.1
2. **Task Fit**: Simple RAG doesn't need 72B parameters
3. **Overfitting**: Larger models may overthink
4. **Output Format**: llama3.1 follows instructions better

---

### 4. Consistency is Key

**Standard Deviation of Response Times**:
- llama3.1: 8.7s (low variance) ✅
- Qwen72b: 247s (high variance) ❌

**Why It Matters**:
- Predictable UX is better than occasionally fast
- Users prefer consistent 30s over "sometimes 20s, sometimes 120s"

---

### 5. Memory ≠ Bottleneck

**Available RAM**: 49GB  
**Usage**:
- llama3.1: 7GB (14%)
- Qwen72b: 41GB (83%)

**Insight**: We have memory headroom, but it doesn't help performance

---

### 6. Mixed Models Don't Work

**Specialized Mix** (different model per role):
- Worst accuracy (34.2%)
- High latency (210s)
- Most complex setup

**Lesson**: Stick with homogeneous models for consistency

---

## Recommendations

### 🎯 Production Deployment

**Keep Current Configuration**: `llama3.1:8b` for all roles

**Rationale**:
1. ✅ Fastest (30s avg)
2. ✅ Most accurate (72.5%)
3. ✅ Most reliable (10/10)
4. ✅ Lowest cost (memory & compute)
5. ✅ Best UX (consistent, fast)

**No changes needed** - Current setup is optimal.

---

### 🔬 Future Optimization Paths

Since model upgrades didn't help, focus on:

#### 1. Prompt Engineering
- Fine-tune prompts for better accuracy
- Add few-shot examples
- Improve output format instructions

#### 2. Streaming Implementation ✅ (Already Done)
- Reduces perceived latency
- Better UX even at 30s
- Shows progress to users

#### 3. Caching Strategy
- Cache common queries
- Cache vector search results
- Cache LLM responses for identical queries

#### 4. Parallel Processing
- Run vector searches in parallel
- Batch embedding operations
- Optimize database queries

#### 5. Query Preprocessing
- Detect simple vs complex queries
- Route simple queries to faster path
- Skip unnecessary steps

---

### 🚫 What NOT to Do

❌ **Don't upgrade to larger models**
- No accuracy benefit
- Massive speed penalty
- Higher costs

❌ **Don't mix different models**
- Worse accuracy
- Complex debugging
- No synergy benefits

❌ **Don't chase benchmarks**
- Real-world performance matters
- User experience > theoretical quality

---

## Technical Details

### Test Environment

**Hardware**:
- CPU: 8 cores @ 479% peak utilization
- RAM: 49.2GB total
- Disk: SSD (NVMe)

**Software**:
- Ollama: Latest
- LangGraph: v0.2.x
- Python: 3.11
- PostgreSQL: 15
- Qdrant: Latest

**Data**:
- 5 companies (AAPL, MSFT, AMZN, PFE, HOOD)
- Latest 10-K filings
- ~50K chunks in vector DB
- 768-dim embeddings (nomic-embed-text)

---

### Benchmark Script

**Location**: `scripts/benchmark_models.py`

**Features**:
- Async execution
- Automatic checkpointer initialization
- Per-query timing
- Keyword-based accuracy scoring
- JSON + Markdown output
- Error handling and retry logic

**Usage**:
```bash
docker-compose -f docker-compose.prod.yml exec backend \
  python scripts/benchmark_models.py \
  --output /tmp/benchmark_results
```

---

### Accuracy Scoring Methodology

**Method**: Keyword Matching

```python
accuracy = (keywords_found / total_keywords) * 100%
```

**Example**:
- Query: "Who is the CFO of Apple?"
- Expected: ["Kevan Parekh", "Chief Financial Officer", "CFO"]
- Answer: "Kevan Parekh is the CFO of Apple"
- Found: ["Kevan Parekh", "CFO"]
- Score: 2/3 = 66.7%

**Limitations**:
- Doesn't measure semantic correctness
- Doesn't detect hallucinations
- Doesn't evaluate reasoning quality

**Future**: Consider LLM-as-judge for better evaluation

---

### Performance Breakdown by Stage

**llama3.1:8b** (30.2s total):
- Pre-processing: ~0.5s (2%)
- Planning (LLM): ~8s (26%)
- Execution (Vector Search): ~10s (33%)
- Synthesis (LLM): ~12s (39%)

**Qwen2.5:72b** (692.9s total):
- Pre-processing: ~0.5s (<1%)
- Planning (LLM): ~250s (36%)
- Execution (Vector Search): ~10s (1%)
- Synthesis (LLM): ~430s (62%)

**Insight**: LLM inference dominates for large models

---

## Appendix: Raw Data

### Full Results
- **JSON**: `scripts/performance_testing/benchmark_results.json`
- **Markdown**: `scripts/performance_testing/benchmark_results.md`

### Query-by-Query Analysis

Available in detailed results section of benchmark output.

### System Resource Usage

**During llama3.1 inference**:
- Ollama: 6.7GB RAM, 105% CPU
- Backend: 232MB RAM, 0.18% CPU
- Postgres: 28MB RAM, 4.5% CPU
- Qdrant: 59MB RAM, 0.09% CPU

**During qwen72b inference**:
- Ollama: 41GB RAM, 479% CPU (maxed out)
- Backend: 257MB RAM, 0.11% CPU
- Postgres: 32MB RAM, 0% CPU
- Qdrant: 41MB RAM, 0.06% CPU

---

## Conclusion

**The winner is clear**: Our current `llama3.1:8b` configuration outperforms all alternatives across every metric that matters.

**Key Takeaway**: For specialized RAG applications, **task-fit and prompt optimization matter more than model size**.

**Next Steps**: Focus on prompt engineering, caching, and UX improvements rather than model upgrades.

---

**Document Version**: 1.0  
**Last Updated**: November 3, 2025  
**Author**: AI Development Team  
**Status**: Final
