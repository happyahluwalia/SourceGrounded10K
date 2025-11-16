# Inference Improvement Strategy

**Date**: November 16, 2025  
**Status**: Planning Phase  
**Goal**: Optimize LLM serving performance for finance agent RAG system

---

## Executive Summary

After analyzing modern LLM serving infrastructure (vLLM, LMCache, vLLM Production Stack, llm-d, KServe), we've identified a phased approach to improve inference performance while maintaining simplicity and production stability.

**Key Decision**: Migrate from Ollama to vLLM with LMCache for 3-10x performance improvement in our RAG workload.

---

## Phase 1: Immediate Implementation (Week 1-2)

### 🎯 Migrate to vLLM

#### Why vLLM?
- **Performance**: 2-3x throughput improvement over Ollama via PagedAttention and continuous batching
- **Zero code changes**: OpenAI-compatible API (our LangChain code stays unchanged)
- **Production-ready**: 1,822+ contributors, PyTorch Foundation project
- **Market adoption**: Used by AWS, Google, NVIDIA, Databricks, Replicate
- **Built-in optimizations**: Prefix caching, quantization (GPTQ, AWQ, FP8), speculative decoding

#### What to Implement

**1. Update docker-compose.prod.yml**
```yaml
# Replace ollama service
vllm:
  image: vllm/vllm-openai:latest
  command: |
    --model llama3.1
    --gpu-memory-utilization 0.9
    --enable-prefix-caching
    --max-model-len 8192
    --dtype auto
  ports:
    - "11434:8000"  # Keep same port for backward compatibility
  volumes:
    - vllm_models:/root/.cache/huggingface
  environment:
    HUGGING_FACE_HUB_TOKEN: ${HF_TOKEN}
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
  restart: unless-stopped
```

**2. Update Backend Environment Variables**
```yaml
# In docker-compose.prod.yml backend service
environment:
  OLLAMA_BASE_URL: http://vllm:8000/v1  # Add /v1 for OpenAI compatibility
```

**3. Verify LangChain Integration**
No code changes needed - `ChatOllama` uses OpenAI-compatible endpoint.

**4. Benchmark Performance**
```bash
# Create benchmark script
python scripts/benchmark_vllm.py --queries 100 --concurrent 5
```

Measure:
- Time-to-first-token (TTFT)
- Tokens per second (throughput)
- End-to-end latency
- GPU memory usage

#### What to Study

**Core Concepts** (2-3 hours):
1. **PagedAttention**: How vLLM manages KV cache memory efficiently
   - Read: [vLLM blog post](https://blog.vllm.ai/2023/06/20/vllm.html)
   - Key insight: Treats KV cache like OS virtual memory (paging)

2. **Continuous Batching**: Dynamic batching of requests
   - Traditional: Wait for batch to fill → process → wait again
   - vLLM: Add/remove requests dynamically as they arrive/complete
   - Result: Higher GPU utilization, lower latency

3. **Prefix Caching**: Reuse KV cache for common prefixes
   - Example: System prompt + RAG context cached across queries
   - Reduces redundant computation

**Interview Prep** (1 hour):
- Read vLLM paper: [Efficient Memory Management for LLM Serving](https://arxiv.org/abs/2309.06180)
- Understand tradeoffs: Ollama (ease) vs vLLM (performance)

#### Success Metrics
- [ ] vLLM serving llama3.1 successfully
- [ ] Backend API responding correctly
- [ ] 2x+ throughput improvement measured
- [ ] Documentation updated

---

## Phase 2: Advanced Caching (Week 3-4)

### 🎯 Add LMCache for KV Cache Optimization

#### Why LMCache?
- **RAG-optimized**: Designed for multi-turn QA with reusable contexts
- **3-5x TTFT reduction**: On follow-up questions about same document
- **CPU offloading**: Store cached contexts in CPU RAM when GPU is full
- **Non-prefix caching**: Reuse any repeated text, not just prefixes
- **Easy integration**: Transparent to application code

#### Our Use Case (Perfect Fit)
```
User: "What was Apple's revenue in Q4 2023?"
→ Retrieves 10-K filing (50K tokens) → Process on GPU

User: "What about their operating expenses?"
→ Same 10-K filing → Reuse cached KV from CPU → 5x faster

User: "Compare to Q3 2023"
→ Retrieve Q3 filing → Some overlap with Q4 → Partial cache hit
```

#### What to Implement

**1. Install LMCache**
```dockerfile
# In Dockerfile
RUN pip install lmcache
```

**2. Create LMCache Config**
```yaml
# config/lmcache_config.yaml
local_device: "cpu"  # Offload to CPU RAM
chunk_size: 256      # KV cache chunk size
max_cache_size: 10   # GB of CPU RAM for cache
```

**3. Update vLLM Command**
```yaml
vllm:
  command: |
    --model llama3.1
    --gpu-memory-utilization 0.9
    --enable-prefix-caching
    --lmcache-config-file /app/config/lmcache_config.yaml
  volumes:
    - ./config:/app/config
```

**4. Monitor Cache Hit Rate**
Add metrics to track:
- Cache hit rate (target: >60% for follow-up questions)
- CPU memory usage
- TTFT improvement on cached queries

#### What to Study

**Core Concepts** (2-3 hours):
1. **KV Cache Bottleneck**: Why it's the #1 memory constraint in LLMs
   - Each token generates Key and Value vectors
   - Stored for attention computation
   - 70B model: ~1GB per 1K tokens

2. **Cache Hierarchy**: GPU → CPU → Disk
   - GPU: Fastest, limited capacity (24GB)
   - CPU: Slower, larger capacity (128GB+)
   - Disk: Slowest, unlimited capacity

3. **CacheBlend Algorithm**: RAG-specific caching strategy
   - Read: [CacheBlend paper](https://dl.acm.org/doi/10.1145/3689031.3696098)
   - Key insight: Fuse cached document KV with new query KV

**Interview Prep** (1 hour):
- Understand when caching helps vs hurts
- Know the memory/latency tradeoffs
- Explain cache eviction policies (LRU, LFU)

#### Success Metrics
- [ ] LMCache integrated with vLLM
- [ ] Cache hit rate >50% on follow-up questions
- [ ] 3x+ TTFT reduction on cached queries
- [ ] CPU memory usage monitored

---

## Phase 3: Learning & Monitoring (Ongoing)

### 🎯 Production Observability

#### What to Implement

**1. Prometheus Metrics**
```python
# app/utils/metrics.py
from prometheus_client import Counter, Histogram

vllm_requests = Counter('vllm_requests_total', 'Total vLLM requests')
vllm_latency = Histogram('vllm_latency_seconds', 'vLLM request latency')
cache_hits = Counter('lmcache_hits_total', 'LMCache hit count')
cache_misses = Counter('lmcache_misses_total', 'LMCache miss count')
```

**2. Grafana Dashboard**
- Requests per second
- P50, P95, P99 latency
- GPU utilization
- Cache hit rate
- Token throughput

**3. Cost Tracking**
```python
# Track tokens processed
total_tokens = prompt_tokens + completion_tokens
cost_per_1m_tokens = 0.10  # Example
request_cost = (total_tokens / 1_000_000) * cost_per_1m_tokens
```

#### What to Study

**Production ML Systems** (5-10 hours):
1. **Monitoring**: RED method (Rate, Errors, Duration)
2. **Alerting**: When to page on-call (P99 latency > 5s)
3. **Capacity planning**: GPU memory vs request load
4. **Cost optimization**: Batch size vs latency tradeoff

---

## Technologies Analyzed but NOT Adopted

### ❌ vLLM Production Stack
**What it is**: Kubernetes-native deployment with request routing, monitoring, KV cache offloading

**Why we didn't pick it**:
- ❌ Requires Kubernetes (we use Docker Compose)
- ❌ Overkill for single-instance deployment
- ❌ Adds operational complexity
- ✅ **When to revisit**: If we need multi-GPU, multi-node deployment

**Learning value**: ⭐⭐⭐⭐ Study architecture for interviews

---

### ❌ llm-d (Distributed Inference)
**What it is**: K8s-native stack with intelligent scheduling, prefill/decode disaggregation, expert parallelism

**Why we didn't pick it**:
- ❌ Built for massive scale (70B+ models, multi-node clusters)
- ❌ Requires Kubernetes, Envoy, custom schedulers
- ❌ Early stage (v0.3), less battle-tested
- ❌ Our workload doesn't need disaggregation
- ✅ **When to revisit**: If serving 100+ concurrent users with 70B models

**Learning value**: ⭐⭐ Niche, not widely adopted yet

---

### ❌ KServe
**What it is**: K8s-native ML serving platform for generative + predictive AI

**Why we didn't pick it**:
- ❌ Requires Kubernetes
- ❌ Multi-framework support we don't need (TensorFlow, PyTorch, XGBoost)
- ❌ Adds abstraction layer without clear benefit for LLM-only serving
- ✅ **When to revisit**: If we add non-LLM models (embeddings, classifiers)

**Learning value**: ⭐⭐⭐⭐⭐ Industry standard, study for interviews

**What to study**:
- InferenceService pattern
- Predictor/Transformer/Explainer architecture
- Canary deployments, A/B testing
- Scale-to-zero on GPU resources

---

## Additional Technologies to Consider

### 🔍 Worth Exploring

#### 1. **Ray Serve** ⭐⭐⭐⭐
**What**: Python-first serving framework with autoscaling

**Why consider**:
- ✅ Python-native (easier than K8s for Python devs)
- ✅ Built-in autoscaling, batching, multiplexing
- ✅ Works with vLLM (vLLM uses Ray internally)
- ✅ Good for multi-model serving (supervisor, planner, synthesizer)

**When to adopt**: If we want autoscaling without Kubernetes

**Learning value**: ⭐⭐⭐⭐ Used at Uber, Shopify, Instacart

**Study**: [Ray Serve docs](https://docs.ray.io/en/latest/serve/index.html)

---

#### 2. **Triton Inference Server** ⭐⭐⭐⭐
**What**: NVIDIA's inference server for TensorRT, PyTorch, ONNX

**Why consider**:
- ✅ Industry standard for GPU inference
- ✅ Dynamic batching, model ensembles
- ✅ TensorRT optimization for NVIDIA GPUs
- ❌ More complex than vLLM for LLMs

**When to adopt**: If we need multi-framework support or TensorRT optimization

**Learning value**: ⭐⭐⭐⭐⭐ Standard at NVIDIA-centric companies

**Study**: [Triton Architecture](https://github.com/triton-inference-server/server)

---

#### 3. **SGLang** ⭐⭐⭐
**What**: Fast LLM serving with structured generation (JSON, regex)

**Why consider**:
- ✅ Faster than vLLM for structured outputs
- ✅ Built-in JSON schema validation
- ✅ Good for agent systems with tool calling
- ❌ Smaller community than vLLM

**When to adopt**: If we need guaranteed JSON output format

**Learning value**: ⭐⭐⭐ Growing adoption

**Study**: [SGLang GitHub](https://github.com/sgl-project/sglang)

---

#### 4. **LiteLLM** ⭐⭐⭐⭐
**What**: Unified API for 100+ LLM providers (OpenAI, Anthropic, Bedrock, vLLM)

**Why consider**:
- ✅ Single interface for multiple providers
- ✅ Built-in fallbacks, retries, caching
- ✅ Cost tracking across providers
- ✅ Easy to switch between local (vLLM) and cloud (OpenAI)

**When to adopt**: If we want provider flexibility

**Learning value**: ⭐⭐⭐⭐ Used in production at many startups

**Study**: [LiteLLM docs](https://docs.litellm.ai/)

---

#### 5. **Langfuse** ⭐⭐⭐⭐⭐
**What**: LLM observability platform (tracing, metrics, evals)

**Why consider**:
- ✅ Purpose-built for LLM apps (not generic APM)
- ✅ Trace full agent execution (supervisor → planner → RAG → synthesizer)
- ✅ Cost tracking, latency analysis, prompt versioning
- ✅ Open source + cloud offering

**When to adopt**: NOW (for production observability)

**Learning value**: ⭐⭐⭐⭐⭐ Standard for LLM observability

**Study**: [Langfuse docs](https://langfuse.com/docs)

---

## Interview Preparation Checklist

### Core Knowledge (Must Know)
- [ ] PagedAttention algorithm and why it matters
- [ ] KV cache memory bottleneck in LLMs
- [ ] Continuous batching vs static batching
- [ ] Prefix caching and when it helps
- [ ] Quantization techniques (GPTQ, AWQ, FP8)
- [ ] Tradeoffs: Latency vs throughput vs cost

### Advanced Topics (Nice to Have)
- [ ] Speculative decoding
- [ ] Tensor parallelism vs pipeline parallelism
- [ ] Flash Attention optimization
- [ ] KV cache compression (CacheGen)
- [ ] Disaggregated serving (prefill/decode split)

### Production Systems
- [ ] Monitoring LLM services (metrics that matter)
- [ ] Autoscaling strategies for GPU workloads
- [ ] Cost optimization techniques
- [ ] A/B testing LLM changes
- [ ] Handling rate limits and retries

---

## Implementation Timeline

### Week 1-2: vLLM Migration
- [ ] Day 1-2: Update docker-compose, test locally
- [ ] Day 3-4: Benchmark performance, document results
- [ ] Day 5: Deploy to production, monitor

### Week 3-4: LMCache Integration
- [ ] Day 1-2: Install LMCache, configure
- [ ] Day 3-4: Test cache hit rates, optimize config
- [ ] Day 5: Deploy, measure TTFT improvements

### Week 5+: Observability & Optimization
- [ ] Add Prometheus metrics
- [ ] Create Grafana dashboard
- [ ] Implement cost tracking
- [ ] Evaluate Langfuse for tracing

---

## Key Takeaways

### What We're Implementing
1. **vLLM**: 2-3x throughput improvement, production-ready
2. **LMCache**: 3-5x TTFT reduction for RAG workload
3. **Monitoring**: Prometheus + Grafana for observability

### What We're Learning
1. **vLLM/LMCache**: Core serving optimization
2. **KServe**: Industry patterns for ML serving
3. **Ray Serve**: Python-first autoscaling
4. **Langfuse**: LLM observability

### What We're Skipping
1. **vLLM Production Stack**: Too complex for our scale
2. **llm-d**: Overkill, early stage
3. **Kubernetes**: Not needed yet

---

## Resources

### Papers to Read
1. [vLLM: Efficient Memory Management](https://arxiv.org/abs/2309.06180)
2. [CacheGen: KV Cache Compression](https://dl.acm.org/doi/10.1145/3626246.3653368)
3. [CacheBlend: Fast LLM Serving for RAG](https://dl.acm.org/doi/10.1145/3689031.3696098)

### Blogs to Follow
1. [vLLM Blog](https://blog.vllm.ai/)
2. [LMCache Blog](https://blog.lmcache.ai/)
3. [Anyscale Blog](https://www.anyscale.com/blog) (Ray creators)

### Documentation
1. [vLLM Docs](https://docs.vllm.ai/)
2. [LMCache Docs](https://docs.lmcache.ai/)
3. [Ray Serve Docs](https://docs.ray.io/en/latest/serve/)
4. [Langfuse Docs](https://langfuse.com/docs)

---

## Questions for Future Investigation

1. Should we quantize models (FP8) for 2x memory reduction?
2. Is speculative decoding worth the complexity?
3. When do we need to move to Kubernetes?
4. Should we use LiteLLM for multi-provider support?
5. How do we implement A/B testing for prompt changes?

---

**Last Updated**: November 16, 2025  
**Next Review**: After Phase 1 completion (Week 2)