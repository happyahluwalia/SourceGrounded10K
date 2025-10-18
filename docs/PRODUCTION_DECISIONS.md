# Production Deployment Decisions & Trade-offs

**Last Updated:** October 2025  
**Target Environment:** Digital Ocean 8GB Droplet  
**Status:** Production-Ready

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Hardware Constraints](#hardware-constraints)
3. [Model Selection](#model-selection)
4. [Architecture Decisions](#architecture-decisions)
5. [Configuration Choices](#configuration-choices)
6. [Trade-offs Summary](#trade-offs-summary)
7. [Alternative Configurations](#alternative-configurations)

---

## Executive Summary

### Final Configuration

| Component | Choice | Key Metric |
|-----------|--------|------------|
| **LLM** | phi3:mini-instruct | 3.8B params, 3GB RAM |
| **Embeddings** | nomic-embed-text-v1.5 | 768-dim, 8K context |
| **Chunk Size** | 1024 characters | 31% of context window |
| **Top-K** | 5 chunks | 1,280 tokens total |
| **Memory Usage** | ~4.5GB peak | 3.5GB buffer remaining |

### Key Principle

**Optimize for stability and simplicity over maximum performance.**

Production systems need to be:
- ✅ Reliable (won't crash under load)
- ✅ Maintainable (easy to debug and update)
- ✅ Predictable (consistent performance)

---

## Hardware Constraints

### Target: Digital Ocean 8GB Droplet

**Available Resources:**
```
Total RAM: 8GB
CPU: 4 vCPUs (shared)
Disk: 160GB SSD
Network: 5TB transfer
Cost: $48/month
```

**Memory Budget:**
```
Component               Memory      % of Total
────────────────────────────────────────────────
System/OS               500 MB      6.25%
PostgreSQL              300 MB      3.75%
Qdrant (10K vectors)    500 MB      6.25%
Redis                   100 MB      1.25%
Nginx                    50 MB      0.63%
────────────────────────────────────────────────
Infrastructure         1,450 MB     18.13%

Available for AI       6,550 MB     81.87%
────────────────────────────────────────────────
Phi-3 (model)          2,500 MB     31.25%
Phi-3 (inference)        500 MB      6.25%
────────────────────────────────────────────────
Total Used             4,450 MB     55.63%
Safety Buffer          3,550 MB     44.37% ✅
```

**Why This Matters:**
- Linux OOM killer activates at ~95% memory usage
- Need buffer for traffic spikes
- Concurrent requests increase memory
- **Target: Stay under 75% utilization**

---

## Model Selection

### Decision 1: LLM Model

#### Options Evaluated

| Model | Params | RAM | Context | Quality | Stability |
|-------|--------|-----|---------|---------|-----------|
| gemma:1b | 1B | 1.5GB | 2K | Basic | High |
| **phi3:mini-instruct** | **3.8B** | **3GB** | **4K** | **Good** | **High** ✅ |
| llama3.1:8b-instruct | 8B | 6GB | 8K | Excellent | Medium ⚠️ |
| llama3.1:70b-instruct | 70B | 40GB+ | 8K | Best | N/A ❌ |

#### Decision: phi3:mini-instruct

**Reasons:**

1. **Memory Safety**
   - Uses 3GB (37.5% of available)
   - Leaves 3.5GB buffer (43.75%)
   - Safe for concurrent requests
   - Won't trigger OOM killer

2. **Quality Upgrade**
   - 3.8x more parameters than gemma:1b
   - Better instruction following
   - More accurate financial analysis
   - Fewer hallucinations

3. **Proven Stability**
   - Microsoft production-grade model
   - Widely deployed
   - Well-tested on 8GB systems
   - Active community support

4. **Context Window**
   - 4K tokens sufficient for RAG
   - Fits 5 chunks + prompt + answer
   - Balanced for our use case

**Trade-offs:**

| Aspect | vs Gemma 1B | vs Llama 3.1 8B |
|--------|-------------|-----------------|
| **Speed** | 50% slower | 40% faster |
| **Quality** | Much better | Slightly worse |
| **Memory** | +1.5GB | -3GB |
| **Stability** | Same | Much safer |
| **Cost** | Same | Same |

**Why Not Llama 3.1 8B?**
- Only 0.5GB buffer (6.25% safety margin)
- Risk of OOM under load
- Concurrent requests would crash
- Not worth the quality gain for the risk

**Verdict:** ✅ **Phi-3 is the sweet spot for 8GB RAM**

---

### Decision 2: Embedding Model

#### Options Evaluated

| Model | Dimensions | Context | RAM (10K vecs) | Source |
|-------|------------|---------|----------------|--------|
| all-MiniLM-L6-v2 | 384 | 256 | 15 MB | HuggingFace |
| BGE-large-en-v1.5 | 1024 | 512 | 41 MB | HuggingFace |
| **nomic-embed-text-v1.5** | **768** | **8K** | **31 MB** | **Ollama** ✅ |
| text-embedding-3-large | 3072 | 8K | 123 MB | OpenAI API |

#### Decision: nomic-embed-text-v1.5

**Reasons:**

1. **Context Window: 8K tokens**
   - **Critical for financial documents**
   - 10-K filings have long tables (often >512 tokens)
   - Item 7 MD&A sections are lengthy
   - Can embed full context without truncation

2. **Optimal Dimensions: 768**
   - 25% less memory than BGE (1024-dim)
   - 2x more expressive than MiniLM (384-dim)
   - Sweet spot for quality vs. memory

3. **Unified Architecture**
   - Same Ollama system as LLM
   - Single model management interface
   - Simpler deployment
   - Consistent API

4. **Production-Ready**
   - Actively maintained
   - Good performance
   - Stable API
   - Easy to switch if needed

**Trade-offs:**

| Aspect | vs BGE-large | vs MiniLM | vs OpenAI |
|--------|--------------|-----------|-----------|
| **Context** | 16x larger | 32x larger | Same |
| **Memory** | 25% less | 2x more | 75% less |
| **Quality** | Comparable | Better | Slightly worse |
| **Speed** | 33% slower | Similar | Much faster |
| **Cost** | Free | Free | $0.13/1M tokens |
| **Privacy** | Local | Local | Cloud ❌ |

**Why Not BGE-large?**
- Only 512 token context (too small)
- 25% more memory for vectors
- Requires sentence-transformers library
- More complex deployment

**Why Not OpenAI?**
- Costs add up ($13 per 100M tokens)
- Data leaves your infrastructure
- API dependency (latency, downtime)
- Privacy concerns with financial data

**Verdict:** ✅ **Nomic's 8K context is game-changing for financial docs**

---

### Decision 3: Why Ollama for Embeddings?

#### Architecture Comparison

**Option A: SentenceTransformers (Old)**
```
┌─────────────────────────────────────┐
│  Python App                          │
│  ├─ sentence-transformers (BGE)     │  ← Separate system
│  │  └─ Downloads models to disk     │
│  ├─ ollama (LLM)                    │  ← Different system
│  │  └─ Manages own models           │
│  └─ qdrant-client                   │
└─────────────────────────────────────┘

Deployment:
1. pip install sentence-transformers
2. Download BGE model (1.3GB)
3. ollama pull phi3
4. Configure both systems
```

**Option B: Ollama (New)**
```
┌─────────────────────────────────────┐
│  Python App                          │
│  ├─ ollama (Embeddings + LLM)       │  ← Unified!
│  │  └─ Single model management      │
│  └─ qdrant-client                   │
└─────────────────────────────────────┘

Deployment:
1. ollama pull nomic-embed-text
2. ollama pull phi3
3. Done!
```

#### Decision: Ollama

**Reasons:**

1. **Unified Model Management**
   - One command: `ollama pull <model>`
   - One API: `ollama.embeddings()` and `ollama.generate()`
   - One configuration system
   - One monitoring interface

2. **Simpler Deployment**
   - No Python package conflicts
   - No model download scripts
   - No separate model directories
   - Easier to switch models

3. **Better for Production**
   - Centralized model serving
   - Consistent error handling
   - Easier to monitor
   - Simpler rollback

4. **Operational Benefits**
   - Switch models via env var (no code changes)
   - Same health checks for both
   - Unified logging
   - Single point of failure (easier to debug)

**Trade-offs:**

| Aspect | SentenceTransformers | Ollama |
|--------|---------------------|---------|
| **Speed** | ✅ Batched (faster) | ❌ Sequential (slower) |
| **Memory** | ✅ In-process | ❌ Separate service |
| **Deployment** | ❌ Complex | ✅ Simple |
| **Switching** | ❌ Code changes | ✅ Env var |
| **Monitoring** | ❌ Two systems | ✅ One system |

**Performance Impact:**
```
Embedding 500 chunks:
- SentenceTransformers: ~30 seconds (batched)
- Ollama: ~40-50 seconds (sequential)
- Difference: +33% slower
```

**Why We Accept the Slowdown:**
- Embedding is one-time per filing
- 40-50s is acceptable for batch processing
- Simplicity > speed in production
- Easier to debug and maintain

**Verdict:** ✅ **33% slower is worth the operational simplicity**

---

## Configuration Choices

### Decision 4: Chunk Size

#### Context Window Analysis

**Phi-3 Context Window: 4,096 tokens**

#### Options Evaluated

| Chunk Size | Chars | Tokens (5 chunks) | Context Used | Buffer | Status |
|------------|-------|-------------------|--------------|--------|--------|
| 512 | 2,560 | 640 | 16% | 3,456 | ✅ Safe, but small |
| 768 | 3,840 | 960 | 23% | 3,136 | ✅ Conservative |
| **1024** | **5,120** | **1,280** | **31%** | **2,816** | ✅ **Balanced** |
| 1536 | 7,680 | 1,920 | 47% | 2,176 | ✅ Good for Llama |
| 2048 | 10,240 | 2,560 | 63% | 1,536 | ⚠️ Tight |
| 3072 | 15,360 | 3,840 | 94% | 256 | ❌ Too tight |

**Calculation:**
```
5 chunks × 1,024 chars/chunk = 5,120 chars
5,120 chars ÷ 4 chars/token ≈ 1,280 tokens

Context breakdown:
- Retrieved chunks: 1,280 tokens (31%)
- Prompt template: ~200 tokens (5%)
- Answer: 500 tokens (12%)
─────────────────────────────────────
Total: 1,980 tokens (48%)
Buffer: 2,116 tokens (52%) ✅
```

#### Decision: 1024 characters

**Reasons:**

1. **Balanced Utilization**
   - Uses 48% of context (not too tight)
   - Leaves 52% buffer (comfortable)
   - Room to increase MAX_TOKENS if needed

2. **Financial Document Fit**
   - Tables often 800-1200 chars
   - Paragraphs typically 600-1000 chars
   - Keeps semantic units together

3. **Leverages Nomic's Strength**
   - 1024 chars fits well in 8K context
   - 2x larger than old 512 chunks
   - Better context without overwhelming LLM

4. **Flexibility**
   - Can retrieve 5-7 chunks safely
   - Can increase to 1536 for Llama 3.1
   - Can decrease to 768 if needed

**Trade-offs:**

| Aspect | vs 512 | vs 2048 |
|--------|--------|---------|
| **Context per chunk** | 2x better | 50% worse |
| **Safety margin** | Less efficient | Safer |
| **Semantic coherence** | Better | Slightly worse |
| **Retrieval quality** | More chunks needed | Fewer chunks |

**Why Not 2048?**
- Only 1,536 token buffer (37%)
- Risk of truncation with longer prompts
- Less room for answer expansion
- Not worth the risk

**Verdict:** ✅ **1024 is the sweet spot for phi3**

---

### Decision 5: Retrieval Parameters (Top-K)

#### Options Evaluated

| Top-K | Total Tokens | Context % | Pros | Cons |
|-------|--------------|-----------|------|------|
| 3 | 768 | 19% | Fast, focused | May miss context |
| **5** | **1,280** | **31%** | **Balanced** | **Good coverage** ✅ |
| 7 | 1,792 | 44% | More context | Slower, noise |
| 10 | 2,560 | 63% | Maximum context | Too much noise |

#### Decision: Top-K = 5

**Reasons:**

1. **Sufficient Coverage**
   - 5 chunks typically cover the topic
   - Captures different perspectives
   - Includes related context

2. **Quality vs. Noise**
   - More chunks = more noise
   - LLM gets confused with too much context
   - 5 is empirically optimal for RAG

3. **Performance**
   - Vector search scales with K
   - 5 is fast enough (<100ms)
   - Reasonable LLM processing time

4. **Context Budget**
   - Uses 31% of context (comfortable)
   - Leaves room for prompt and answer
   - Can increase to 7 if needed

**Trade-offs:**

| Aspect | Top-K=3 | Top-K=5 | Top-K=7 |
|--------|---------|---------|---------|
| **Coverage** | May miss info | Good | Better |
| **Noise** | Low | Balanced | Higher |
| **Speed** | Fastest | Fast | Slower |
| **Context** | 19% | 31% | 44% |

**Verdict:** ✅ **5 chunks is the RAG sweet spot**

---

### Decision 6: Score Threshold

#### Options Evaluated

| Threshold | Behavior | Use Case |
|-----------|----------|----------|
| 0.3 | Very permissive | Exploratory queries |
| **0.5** | **Balanced** | **General use** ✅ |
| 0.7 | Strict | Precise queries |
| 0.9 | Very strict | Exact matches only |

#### Decision: 0.5

**Reasons:**

1. **Balanced Precision/Recall**
   - Not too strict (won't miss relevant docs)
   - Not too loose (won't include noise)
   - Works for most queries

2. **User Experience**
   - Better to return something than nothing
   - Users can refine queries if needed
   - Avoids "no results" frustration

3. **Configurable**
   - Can be overridden per query
   - Users can set stricter if needed
   - Good default for exploration

**Trade-offs:**

| Threshold | Precision | Recall | User Experience |
|-----------|-----------|--------|-----------------|
| 0.3 | Lower | Higher | More results, more noise |
| **0.5** | **Balanced** | **Balanced** | **Good default** ✅ |
| 0.7 | Higher | Lower | Fewer results, more relevant |

**Verdict:** ✅ **0.5 is a safe default**

---

## Architecture Decisions

### Decision 7: No Reranking

#### Options

**Option A: Retrieval + Reranking**
```
Query → Embed → Qdrant (top-20) → Reranker → LLM (top-5)
```

**Option B: Retrieval Only (Current)**
```
Query → Embed → Qdrant (top-5) → LLM
```

#### Decision: No Reranking

**Reasons:**

1. **Simplicity**
   - One less component to manage
   - Fewer failure points
   - Easier to debug

2. **Memory Constraints**
   - Reranker models: 300-500MB
   - Would reduce buffer to 3GB
   - Not worth the memory cost

3. **Diminishing Returns**
   - Nomic embeddings are already good
   - Reranking improves by ~5-10%
   - Not critical for our use case

4. **Latency**
   - Reranking adds 200-500ms
   - Users prefer faster responses
   - Can add later if needed

**When to Reconsider:**
- Upgrade to 16GB RAM
- Quality issues with retrieval
- Users complain about relevance

**Verdict:** ✅ **Skip reranking for now**

---

### Decision 8: No Streaming Responses

#### Options

**Option A: Streaming**
```python
for chunk in llm.stream(prompt):
    yield chunk  # Real-time output
```

**Option B: Blocking (Current)**
```python
response = llm.generate(prompt)
return response  # Wait for complete answer
```

#### Decision: Blocking Responses

**Reasons:**

1. **Simpler Implementation**
   - No WebSocket complexity
   - Standard REST API
   - Easier error handling

2. **Better for Citations**
   - Need full response to extract sources
   - Hard to stream with metadata
   - Cleaner UX with complete answer

3. **Acceptable Latency**
   - Phi-3 generates in 3-5 seconds
   - Not long enough to need streaming
   - Users can wait

4. **Caching Benefits**
   - Can cache complete responses
   - Hard to cache streams
   - Better for repeated queries

**When to Reconsider:**
- Upgrade to Llama 3.1 (slower)
- Users complain about wait time
- Need real-time feedback

**Verdict:** ✅ **Blocking is fine for 3-5s responses**

---

## Trade-offs Summary

### What We Optimized For

1. **Stability** > Performance
   - 3.5GB memory buffer
   - Won't crash under load
   - Predictable behavior

2. **Simplicity** > Features
   - Unified Ollama architecture
   - No reranking complexity
   - Standard REST API

3. **Quality** > Speed
   - Phi-3 vs Gemma (50% slower, much better)
   - Nomic vs MiniLM (similar speed, better quality)
   - 1024 chunks vs 512 (better context)

4. **Privacy** > Convenience
   - Local models vs OpenAI
   - No data leaves infrastructure
   - Full control

### What We Sacrificed

1. **Speed**
   - Ollama embeddings: 33% slower than batched
   - Phi-3: 50% slower than Gemma
   - Acceptable for batch processing

2. **Maximum Quality**
   - Phi-3 vs Llama 3.1: Slightly worse
   - No reranking: 5-10% less relevant
   - Worth it for stability

3. **Features**
   - No streaming responses
   - No multi-modal (images)
   - No real-time updates
   - Can add later if needed

4. **Cost Optimization**
   - Could use smaller models
   - Could use OpenAI (cheaper at low volume)
   - Chose stability over cost

---

## Alternative Configurations

### For 4GB RAM (Budget)

```bash
OLLAMA_MODEL=gemma:1b           # 1.5GB
EMBEDDING_MODEL=all-MiniLM-L6-v2  # 384-dim
CHUNK_SIZE=512
TOP_K=3
```

**Trade-offs:**
- ✅ Fits in 4GB
- ❌ Lower quality
- ❌ Smaller context

---

### For 16GB RAM (Premium)

```bash
OLLAMA_MODEL=llama3.1:8b-instruct  # 6GB
EMBEDDING_MODEL=nomic-embed-text-v1.5
CHUNK_SIZE=1536
TOP_K=7
MAX_TOKENS=800
```

**Trade-offs:**
- ✅ Best quality
- ✅ More context
- ⚠️ Needs monitoring

---

### For Maximum Speed (Development)

```bash
OLLAMA_MODEL=gemma:1b
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=512
TOP_K=3
EMBEDDING_BATCH_SIZE=64
```

**Trade-offs:**
- ✅ Fastest iteration
- ✅ Lowest memory
- ❌ Lower quality

---

### For Maximum Quality (32GB+ RAM)

```bash
OLLAMA_MODEL=llama3.1:70b-instruct
EMBEDDING_MODEL=nomic-embed-text-v1.5
CHUNK_SIZE=2048
TOP_K=10
MAX_TOKENS=1000
```

**Trade-offs:**
- ✅ Best possible quality
- ✅ Maximum context
- ❌ Requires 32GB+ RAM
- ❌ Much slower

---

## Decision Matrix

### Quick Reference

| Constraint | Recommended Config |
|------------|-------------------|
| **8GB RAM** | phi3 + nomic + 1024 chunks ✅ |
| **4GB RAM** | gemma + MiniLM + 512 chunks |
| **16GB RAM** | llama3.1 + nomic + 1536 chunks |
| **Speed Priority** | gemma + MiniLM + 512 chunks |
| **Quality Priority** | llama3.1 + nomic + 1536 chunks |
| **Privacy Priority** | Any local model (no OpenAI) |
| **Cost Priority** | gemma + MiniLM (smallest) |

---

## Validation Checklist

Before deploying, verify these decisions still hold:

- [ ] Memory usage stays under 6GB (75% of 8GB)
- [ ] Response time under 10 seconds
- [ ] Answer quality acceptable to users
- [ ] No OOM crashes under load
- [ ] Embedding generation completes
- [ ] Context window not exceeded
- [ ] Models available in Ollama

---

## When to Revisit

Reconsider these decisions if:

1. **Memory Issues**
   - OOM crashes occur
   - Usage consistently >7GB
   - → Downgrade to gemma:1b

2. **Quality Issues**
   - Users complain about answers
   - Hallucinations increase
   - → Upgrade to llama3.1:8b

3. **Speed Issues**
   - Queries take >10 seconds
   - Users abandon requests
   - → Reduce chunk_size or top_k

4. **Scale Issues**
   - Concurrent users increase
   - Need faster responses
   - → Upgrade to 16GB droplet

---

## References

- [Model Selection Analysis](MODEL_SELECTION_ANALYSIS.md)
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [Production Deployment Guide](PRODUCTION_DEPLOYMENT.md)
- [Phi-3 Technical Report](https://arxiv.org/abs/2404.14219)
- [Nomic Embed Documentation](https://ollama.ai/library/nomic-embed-text)

---

**Document Owner:** Engineering Team  
**Review Frequency:** Quarterly or after major changes  
**Last Review:** October 2025
