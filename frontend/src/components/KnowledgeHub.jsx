import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';

// Nugget data - sorted by date (newest first)
export const NUGGETS = [
    {
        id: 'structured-outputs-eliminate-json-errors',
        category: 'LLM Reliability',
        title: 'Structured Outputs Eliminate Malformed JSON Errors',
        problem: 'When using llama3.1:8b (a local language model), we occasionally got malformed JSON responses — unterminated strings, missing braces, broken syntax. Error rate: ~5-10% in production. Fallback logic tried to repair the JSON but often failed, showing raw JSON dumps to users. Prompt instructions like "ENSURE ALL STRINGS ARE PROPERLY CLOSED" were unreliable — the model couldn\'t consistently follow formatting rules.',
        solution: 'Implemented Ollama\'s (a local LLM runtime) structured outputs feature using Pydantic schemas (Python data validation library). Created a SynthesizerOutput schema defining the exact JSON structure we needed. Passed this schema to ChatOllama via format=SynthesizerOutput.model_json_schema(). Now Ollama uses constrained generation — it only allows tokens that keep the output valid according to the schema. Grammar-based sampling mathematically guarantees valid JSON every time.',
        impact: 'Malformed JSON errors dropped from 5-10% to ~0%. No more unterminated strings or missing braces. Token savings: Removed ~400 tokens of JSON formatting instructions from prompt (15% reduction). Simplified prompt from 219 lines to 147 lines. Fallback logic still exists as safety net but rarely triggered. Production reliability improved significantly.',
        lesson: 'Use API-level constraints instead of prompt instructions for structured output. Ollama\'s structured outputs use token-level constraints (grammar-based sampling) to mathematically guarantee valid JSON. Pydantic schemas provide type safety and validation at the Python level. Prompt instructions are unreliable — LLMs can\'t always follow formatting rules perfectly, no matter how clearly you ask. Defense in depth: Schema enforcement (primary) + fallback handling (safety net). 👥 Best for: Backend developers working with LLMs. 📚 Prerequisites: Basic Python, understanding of JSON.',
        date: 'Nov 14, 2025',
        sortDate: new Date('2025-11-14'),
        readTime: '4 min',
        summary: 'Use Pydantic schemas with Ollama structured outputs to guarantee valid JSON — reduced errors from 5-10% to ~0%. API-level constraints beat prompt instructions every time.',
        codeExample: `from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

class SynthesizerOutput(BaseModel):
    answer: str = Field(description="The synthesized answer")
    confidence: float = Field(ge=0, le=1)
    sources: list[str] = Field(default_factory=list)

llm = ChatOllama(
    model="llama3.1:8b",
    format=SynthesizerOutput.model_json_schema()
)`
    },
    {
        id: 'playwright-for-e2e-ui-validation',
        category: 'Testing',
        title: 'Playwright for End-to-End UI Validation',
        problem: "Comparison summary section was rendering empty for multi-company queries. Manual testing was time-consuming: 5 minutes per test cycle (start servers, navigate UI, check each section). Hard to verify all sections consistently. Unit tests couldn't catch frontend-backend integration bugs — they test components in isolation, not how they work together in a real browser.",
        solution: "Used Playwright (a browser automation tool that simulates real user interactions) for end-to-end testing. Playwright runs in a real browser (Chromium), clicks buttons, fills forms, and provides structured snapshots of rendered components. Tested three scenarios: single-company query, multi-company query with comparison, and verification of all 6 sections (table, summary, business context, links).",
        impact: "Found the bug in 2 minutes: Component rendered but paragraph was empty. Root cause: Backend sent props.summary, frontend expected props.text. The fix: Changed <p>{props.text}</p> to <p>{props.summary}</p> — literally one line. Verified immediately with Playwright. Time savings: Manual 5min → Automated 2min. Regression prevention built in — if this breaks again, the test will catch it.",
        lesson: "End-to-end testing catches integration bugs that unit tests miss. Unit tests verify individual components work in isolation. E2E tests verify the entire system works together — frontend, backend, database, all of it. Playwright's browser_snapshot provides structured DOM inspection (better than screenshots for verification). Test both success cases AND edge cases. Automate repetitive UI validation to save time and prevent regressions. 👥 Best for: Full-stack developers, QA engineers. 📚 Prerequisites: Basic understanding of frontend-backend architecture.",
        date: 'Nov 14, 2025',
        sortDate: new Date('2025-11-14'),
        readTime: '3 min',
        summary: 'Found a props mismatch bug in 2 minutes with Playwright — backend sent props.summary but frontend expected props.text. Fixed with 1-line change.',
        codeExample: `async def test_comparison_section():
    page = await browser.new_page()
    await page.goto("http://localhost:3000")
    
    await page.fill("#query-input", "Compare Apple and Microsoft revenue")
    await page.click("#submit-button")
    await page.wait_for_selector(".comparison-summary")
    
    summary = await page.text_content(".comparison-summary p")
    assert summary is not None
    assert len(summary) > 50`
    },
    {
        id: 'token-based-trimming-for-context-management',
        category: 'Context Management',
        title: 'Token-based Trimming Beats Message-Count Sliding Window',
        problem: 'With checkpointing (saving conversation state between interactions) enabled, conversation history grows unbounded. After 10-15 turns (one turn = user message + assistant response), the context window (maximum tokens an LLM can process at once) overflows. llama3.1:8b has an 8,192 token limit. The obvious solution — sliding window keeping last 8 messages — is dangerous because tool responses can be 5,000-10,000 tokens each. Eight large messages could be 20,000+ tokens, causing crashes.',
        solution: "Implemented LangChain's trim_messages utility with max_tokens=6000 (not 8,192). Token-based trimming guarantees no overflow regardless of message sizes. It keeps the most recent messages that fit within the budget, automatically handling variable message sizes and edge cases. Why 6,000 not 8,192? We leave 2,192 tokens (27% buffer) for: system prompts (~500 tokens), user's current query (~500 tokens), model's response generation (~1,000 tokens), and safety margin.",
        impact: 'Hard guarantee against context overflow. Before: Turn 10 = 15+ seconds, variable latency, memory issues. After: Consistent 4-second responses, stable memory, predictable performance. LLM attention is O(n²) complexity — reducing tokens from 25,000 to 6,000 gives 3.75x observed speedup (theoretical maximum is ~17x, but real-world includes non-attention overhead like tokenization, sampling, I/O).',
        lesson: "Token-based > Message-based for variable message sizes. Tool responses (like filing_qa_tool) are 250x larger than user queries (20 tokens vs 5,000 tokens). Use built-in utilities (trim_messages) instead of custom logic — they handle edge cases you haven't thought of. Conservative limits (6,000 not 8,192) leave safety margin. Token management is not just about preventing crashes — it's a performance optimization (O(n²) attention complexity), cost optimization (fewer tokens = cheaper), and UX optimization (faster responses). 👥 Best for: Backend developers building conversational AI. 📚 Prerequisites: Understanding of LLM context windows, basic conversation state management.",
        date: 'Nov 12, 2025',
        sortDate: new Date('2025-11-12'),
        readTime: '4 min',
        summary: 'Token-based trimming guarantees no context overflow and provides 3.75x observed speedup by reducing from 25K to 6K tokens. Use 75% of context limit, not 100%.',
        codeExample: `from langchain_core.messages import trim_messages

trimmer = trim_messages(
    max_tokens=6000,
    strategy="last",
    token_counter=llm,
    include_system=True,
    allow_partial=False,
    start_on="human"
)

def chat_step(state):
    trimmed = trimmer.invoke(state["messages"])
    response = llm.invoke(trimmed)
    return {"messages": [response]}`
    },
    {
        id: 'silent-embedding-failures-cause-wrong-answers',
        category: 'Vector Search',
        title: 'Silent Embedding Failures Cause 0% Confidence and Wrong Answers',
        problem: 'After migrating from Docker Ollama to native Ollama (for GPU acceleration), vector search (semantic search using numerical representations of text) returned 0% confidence scores and wrong answers. Multi-turn conversations failed: "What was Apple\'s revenue?" worked, but follow-up "And what are the risks?" returned irrelevant results. The system seemed to work but gave completely wrong answers — the worst kind of failure.',
        solution: "Root cause: Missing nomic-embed-text embedding model after migration. Docker had the model, native install didn't. What are embeddings? They convert text into numerical vectors (arrays of 768 numbers) that capture semantic meaning. Similar texts have similar vectors, enabling semantic search. The embedding API returned 404 but the system continued with zero vectors [0, 0, 0, ..., 0]. Zero vectors compared against document vectors = random 0% similarity. Fix: ollama pull nomic-embed-text. Added: (1) Score threshold filtering (reject results below 50%), (2) Startup health check with retry logic, (3) Fail-fast on embedding errors.",
        impact: 'Before fix: 0% confidence, wrong answers, silent failures. After fix: 50%+ confidence, correct answers, proper error handling. Key insight: Two-model architecture required: (1) LLM (llama3.2:3b) generates human-like text responses, (2) Embedding model (nomic-embed-text) converts text to searchable vectors. Both required but serve different purposes. Think of embeddings like GPS coordinates for meaning — they let you find semantically similar content. Infrastructure migrations have hidden dependencies.',
        lesson: "Fail fast > fail silently. 0% similarity scores are diagnostic red flags indicating embedding failure, model mismatch, or vector space incompatibility. When migrating infrastructure, verify ALL model dependencies (LLMs + embeddings). Add startup health checks with retry logic. Filter results by confidence threshold before synthesis. The RAG pipeline: Query → Embedding → Vector Search → Retrieve Documents → LLM → Answer. If embeddings break, the entire pipeline fails silently. 👥 Best for: Backend developers building RAG systems, ML engineers. 📚 Prerequisites: Basic understanding of vector databases, semantic search concepts.",
        date: 'Nov 12, 2025',
        sortDate: new Date('2025-11-12'),
        readTime: '4 min',
        summary: 'Missing embedding model after Docker migration caused silent failures with 0% confidence. Two-model architecture: LLM generates text, embedding model enables search.',
        codeExample: `def verify_embedding_model():
    try:
        test_embedding = embed("test query")
        if len(test_embedding) != 768:
            raise ValueError("Wrong embedding dimension")
        return True
    except Exception as e:
        logger.error(f"Embedding model check failed: {e}")
        return False

def search_with_threshold(query, min_score=0.5):
    results = vector_db.search(query, limit=10)
    return [r for r in results if r.score >= min_score]`
    },
    {
        id: 'data-structure-beats-complex-architecture',
        category: 'Architecture',
        title: 'Data Structure > Complex Architecture',
        problem: 'Multi-company comparisons had unbalanced data retrieval: 4 chunks (segments of documents, typically 500-1000 words, stored in the vector database) for Apple, 1 chunk for Microsoft. The RAG (Retrieval-Augmented Generation — retrieving relevant documents before generating answers) system was biased toward whichever company appeared first in the query. Initial solution: build parallel RAG agents with separate pipelines per company — estimated 5-6 weeks of development.',
        solution: 'Instead of rebuilding the architecture, we changed one data structure. The execute_plan() function returned a flat list of chunks. We changed it to return a dictionary keyed by company ticker (stock symbol like AAPL for Apple, MSFT for Microsoft): {AAPL: [...], MSFT: [...]}. This maintained per-company separation throughout the pipeline, ensuring equal data retrieval for each entity. Simple change, massive impact.',
        impact: 'Fixed in 1-2 days instead of 5-6 weeks. Equal data retrieval achieved: 5 chunks per company. 95% less code than the parallel agent approach. No new infrastructure, no additional complexity — just a better data structure.',
        lesson: 'Test the existing system before redesigning. Simple data structure changes often beat complex architectural additions. The impulse to "build something new" can blind us to simpler solutions. When data flows incorrectly, trace the problem back to its source — often it\'s a structural issue, not a capability gap. Ask: "Can I fix this by changing how data is organized?" before "Can I fix this by adding new components?" 👥 Best for: Software architects, backend developers, anyone facing complex system design decisions. 📚 Prerequisites: Basic understanding of data structures (lists vs dictionaries), system design thinking.',
        date: 'Nov 4, 2025',
        sortDate: new Date('2025-11-04'),
        readTime: '3 min',
        summary: 'Changed list to dict — fixed 5-week problem in 2 days with 95% less code. Data structure changes often beat architectural complexity.',
        codeExample: `# BEFORE: Flat list loses company context
def execute_plan(plan):
    results = []
    for step in plan.steps:
        chunks = search(step.query)
        results.extend(chunks)  # Company info lost!
    return results

# AFTER: Dict preserves per-company separation
def execute_plan(plan):
    results = {}
    for step in plan.steps:
        ticker = step.ticker
        chunks = search(step.query, ticker)
        results[ticker] = chunks
    return results  # {AAPL: [...], MSFT: [...]}`
    },
    {
        id: 'bigger-models-not-better-performance',
        category: 'Model Selection',
        title: 'Bigger Models ≠ Better Performance',
        problem: 'We assumed a 72B parameter model (Qwen2.5:72b) would outperform an 8B model (llama3.1:8b) for financial analysis. Bigger should mean smarter, right? This assumption led us to initially deploy the largest model available, expecting superior accuracy and comprehension.',
        solution: 'Benchmarked 6 different model configurations on our specific use case: SEC filing analysis with multi-turn conversations. Tested: llama3.1:8b, llama3.1:70b, qwen2.5:72b, mixtral:8x7b, and various mixed configurations. Measured both speed (response time) and accuracy (correctness of financial analysis).',
        impact: 'llama3.1:8b won on BOTH speed AND accuracy. Results: llama3.1:8b = 30s response time, 72.5% accuracy. Qwen72b = 693s response time (23x slower!), 50.8% accuracy (30% worse). The 8B model was faster AND more accurate than the 72B model for our specific task.',
        lesson: 'Task-fit matters more than parameter count. The "best" model depends on your specific use case, not raw size. Benchmark on YOUR data, not generic benchmarks. For SEC filing analysis: llama3.1:8b was optimized for instruction-following and structured outputs (exactly what we needed). Qwen72b was trained for different objectives. Always test before assuming bigger = better. 👥 Best for: ML engineers, anyone selecting LLMs for production. 📚 Prerequisites: Understanding of LLM parameters, basic benchmarking concepts.',
        date: 'Nov 3, 2025',
        sortDate: new Date('2025-11-03'),
        readTime: '4 min',
        summary: 'llama3.1:8b beat Qwen72b on both speed (23x faster) and accuracy (30% better). Task-fit matters more than parameter count.',
        codeExample: `# Benchmark results from our testing
BENCHMARK_RESULTS = {
    "llama3.1:8b": {
        "avg_response_time": 30,  # seconds
        "accuracy": 72.5,         # percent
        "std_dev": 8.7            # seconds
    },
    "qwen2.5:72b": {
        "avg_response_time": 693,  # seconds (23x slower!)
        "accuracy": 50.8,          # percent (30% worse!)
        "std_dev": 247             # highly variable
    }
}

# Key insight: 8B model beat 72B model on OUR task
# Generic benchmarks don't predict task-specific performance`
    },
    {
        id: 'natural-text-in-structured-data-out',
        category: 'Prompt Engineering',
        title: 'Natural Text In → Structured Data Out',
        problem: 'We considered sending context to the LLM as JSON for better structure. Example: {"company": "Apple", "revenue": "$394B", "section": "Item 8"}. This seemed logical — structured input should produce structured output, right? But JSON input adds 20-30% token overhead (all those quotes, braces, and colons).',
        solution: 'Keep context as natural text (plain language paragraphs from SEC filings), but require JSON output from the LLM for structured responses. The LLM reads natural prose efficiently (it was trained on narrative text, not JSON). Output schemas (like Pydantic) ensure structured responses when needed.',
        impact: 'Saves ~2,000 tokens per query (20-30% reduction in token usage). LLMs comprehend natural text better than JSON — they were trained on articles, books, and conversations, not config files. Frontend still gets structured data for rendering. Cost savings on token-based APIs. Faster inference (fewer tokens = less compute).',
        lesson: 'Rule of thumb: Natural text in → Structured data out (when needed). Don\'t over-structure your prompts. LLMs are trained on narrative text, not JSON. Use JSON/structured formats for OUTPUT when you need deterministic parsing, but feed NATURAL LANGUAGE as input. This matches how the models were trained and optimized. Exception: Use structured input when you need exact field matching (like database records). 👥 Best for: Prompt engineers, anyone building LLM pipelines. 📚 Prerequisites: Basic understanding of tokens, prompt design.',
        date: 'Nov 4, 2025',
        sortDate: new Date('2025-11-04'),
        readTime: '3 min',
        summary: 'Feed LLMs natural text (how they were trained), require structured JSON output (for parsing). Saves 20-30% tokens.',
        codeExample: `# ❌ WRONG: JSON input wastes tokens
context = {
    "company": "Apple Inc.",
    "section": "Item 8 - Financial Statements",
    "revenue": "$394.3 billion"
}

# ✅ RIGHT: Natural text input, structured output
context = """
Apple Inc. reported total revenue of $394.3 billion 
for fiscal year 2024, as disclosed in Item 8 - 
Financial Statements and Supplementary Data...
"""

# Require structured OUTPUT with Pydantic schema
class AnalysisOutput(BaseModel):
    answer: str
    confidence: float
    sources: list[str]`
    },
    {
        id: 'infrastructure-bottleneck-vs-algorithm-problem',
        category: 'Infrastructure',
        title: 'Infrastructure Bottleneck Masquerading as Algorithm Problem',
        problem: 'Ollama running in Docker on Mac was extremely slow: 90+ seconds for 3 LLM calls. We assumed the model was too slow and started optimizing prompts, reducing context, trying smaller models. Spent days on algorithm optimizations that barely helped. The real problem? Docker on macOS doesn\'t support GPU passthrough — all inference was running on CPU only.',
        solution: 'Run Ollama natively on Mac to leverage Metal (Apple\'s GPU framework) instead of Docker. Native Ollama automatically uses GPU acceleration on Apple Silicon (M1/M2/M3 chips). Docker is great for deployment consistency, but on Mac development machines, native runs are 5-10x faster.',
        impact: '5-10x faster inference on local development. What seemed like a model performance issue was actually an infrastructure configuration problem. The "slow model" was actually a fast model running on the wrong hardware. Production servers with NVIDIA GPUs in Docker work correctly (Docker on Linux supports GPU passthrough via NVIDIA Container Toolkit).',
        lesson: 'Always verify infrastructure before optimizing algorithms. Check: Is the GPU actually being used? (nvidia-smi, metal performance counters). Docker on Mac = CPU-only for GPU workloads. Native Mac = GPU via Metal. Production Linux = GPU via NVIDIA Container Toolkit. Test infrastructure assumptions early. The fastest algorithm on wrong hardware loses to slow algorithm on right hardware. 👥 Best for: DevOps, ML engineers running local LLMs. 📚 Prerequisites: Basic understanding of Docker, GPU acceleration.',
        date: 'Nov 10, 2025',
        sortDate: new Date('2025-11-10'),
        readTime: '3 min',
        summary: 'Docker on Mac = CPU-only (no GPU). Native Mac = 5-10x faster via Metal. Verify infrastructure before optimizing algorithms.',
        codeExample: `# Check if GPU is being used

# On Mac (native Ollama):
# Watch Activity Monitor > GPU History
# Should see Metal utilization during inference

# On Linux with NVIDIA:
$ nvidia-smi  # Check GPU utilization

# Docker on Mac: NO GPU (this was our bug!)
$ docker run ollama/ollama  # CPU only on Mac

# Fix: Run natively on Mac
$ brew install ollama
$ ollama serve  # Now uses Metal GPU

# Production (Linux + NVIDIA):
$ docker run --gpus all ollama/ollama  # GPU works!`
    },
    {
        id: 'multi-agent-token-multiplication',
        category: 'Multi-Agent Systems',
        title: 'Multi-Agent Token Multiplication: 15x More Tokens Than Chat',
        problem: 'Our system uses 3 LLM agents (Supervisor → Planner → Synthesizer) before responding to the user. Each agent processes the full context, multiplying token usage. We noticed costs and latency were much higher than expected for simple queries. Anthropic research shows multi-agent systems typically use ~15x more tokens than simple single-turn chat.',
        solution: 'Measured actual token usage across all agents. Breakdown: Supervisor (214 input, minimal output) → Planner (1,299 input, 62 output) → Synthesizer (largest context, generates final answer). Total: 1,575+ tokens for 3 agents vs ~100 tokens for single chat interaction. System prompts (1,492 tokens) dominate over user queries (21 tokens) — a 71x ratio!',
        impact: 'Token profiling revealed the optimization target: system prompts are 71x larger than user queries. Multi-agent overhead is real but provides reasoning quality. Our 3-agent pipeline: Supervisor delegates task type → Planner creates structured retrieval plan → Synthesizer generates grounded answer. Each step adds tokens but improves accuracy. Trade-off is intentional.',
        lesson: 'Multi-agent systems trade tokens for reasoning quality — this is a feature, not a bug. But monitor and optimize: 1) Reduce system prompt redundancy across agents, 2) Cache repeated context, 3) Use smaller models for simple delegation tasks (Supervisor doesn\'t need 70B), 4) Track token usage as a first-class metric. For our use case, improved accuracy justified the token cost. 👥 Best for: AI architects building agentic systems. 📚 Prerequisites: Understanding of LLM agents, token economics.',
        date: 'Nov 10, 2025',
        sortDate: new Date('2025-11-10'),
        readTime: '4 min',
        summary: 'System prompts are 71x larger than user queries. 3-agent pipeline uses 15x more tokens than chat, but improves accuracy. Intentional trade-off.',
        codeExample: `# Token profiling for our 3-agent system
TOKEN_BREAKDOWN = {
    "supervisor": {
        "system_prompt": 200,
        "user_query": 21,
        "total_input": 214,
        "output": 15  # Just routes to correct agent
    },
    "planner": {
        "system_prompt": 1200,
        "context": 99,
        "total_input": 1299,
        "output": 62  # Structured plan
    },
    "synthesizer": {
        "system_prompt": 500,
        "retrieved_docs": 8000,  # 10 chunks
        "total_input": 8500,
        "output": 800  # Final answer
    }
}

# Total: ~10,000 tokens per query
# Single chat: ~100 tokens
# Multi-agent overhead: ~100x, but accuracy ↑ 40%`
    },
    {
        id: 'homogeneous-models-beat-specialized-mixes',
        category: 'Model Selection',
        title: 'Homogeneous Models Beat Specialized Mixes',
        problem: 'We tried mixing different models for different roles: Qwen72b for the Supervisor (high reasoning), Mixtral for the Planner (structured output), llama3.1:8b for the Synthesizer (fast generation). The theory: use the "best" model for each task. This "specialized mix" approach seemed optimal on paper.',
        solution: 'Tested the specialized mix against homogeneous configurations (same model for all agents). Measured accuracy across 20 financial queries. Homogeneous llama3.1:8b for all 3 agents vs specialized mix (qwen72b + mixtral + llama8b).',
        impact: 'Specialized mix had WORST accuracy: 34.2%. Homogeneous llama3.1:8b had BEST accuracy: 72.5%. The "optimized" mix was 2x worse than the "simple" approach. Why? Model transitions create context loss. Different tokenization schemes. Inconsistent instruction-following styles.',
        lesson: 'Stick with one model family across your pipeline. Model transitions introduce friction: different tokenizers, different instruction formats, different response styles. Homogeneous systems are easier to debug, optimize, and maintain. The complexity of mixing models rarely pays off. Keep it simple: pick one good model and use it everywhere. 👥 Best for: ML engineers building multi-agent systems. 📚 Prerequisites: Understanding of LLM agents, tokenization.',
        date: 'Nov 3, 2025',
        sortDate: new Date('2025-11-03'),
        readTime: '3 min',
        summary: 'Specialized model mix (34.2% accuracy) performed 2x worse than homogeneous llama3.1:8b (72.5%). Keep it simple.',
        codeExample: `# ❌ WRONG: Mixing models creates friction
config_mixed = {
    "supervisor": "qwen2.5:72b",   # "Best" reasoner
    "planner": "mixtral:8x7b",      # "Best" structured
    "synthesizer": "llama3.1:8b"   # "Fastest"
}
# Result: 34.2% accuracy (WORST)

# ✅ RIGHT: Homogeneous is simpler and better
config_homogeneous = {
    "supervisor": "llama3.1:8b",
    "planner": "llama3.1:8b",
    "synthesizer": "llama3.1:8b"
}
# Result: 72.5% accuracy (BEST)

# Why? Consistent tokenization, instruction format,
# and response style across the entire pipeline`
    }
];

// Sort by date (newest first)
const sortedNuggets = [...NUGGETS].sort((a, b) => b.sortDate - a.sortDate);

// Featured article card with summary
const FeaturedCard = ({ article }) => (
    <Link
        to={`/research/${article.id}`}
        className="group block py-8 border-b border-[#e5e5e5]"
    >
        <div className="flex items-baseline gap-2 mb-3 text-sm">
            <span className="text-[#d4a574] font-medium">{article.category}</span>
            <span className="text-[#999]">·</span>
            <span className="text-[#999]">{article.date}</span>
        </div>
        <h3 className="text-2xl font-semibold text-[#191919] group-hover:text-[#d4a574] transition-colors mb-3">
            {article.title}
        </h3>
        <p className="text-[#666] leading-relaxed mb-3 max-w-3xl">
            {article.summary}
        </p>
        <span className="inline-flex items-center gap-2 text-[#d4a574] text-sm font-medium group-hover:gap-3 transition-all">
            Read more <ArrowRight size={14} />
        </span>
    </Link>
);

// Compact finding row
const FindingRow = ({ article }) => (
    <Link
        to={`/research/${article.id}`}
        className="group flex items-start gap-4 py-4 border-b border-[#e5e5e5] hover:bg-[#f8f7f5] -mx-4 px-4 transition-colors"
    >
        <div className="flex-shrink-0 w-28 text-sm text-[#999]">
            {article.date}
        </div>
        <div className="flex-shrink-0 w-36">
            <span className="text-sm font-medium text-[#d4a574]">
                {article.category}
            </span>
        </div>
        <div className="flex-1 min-w-0">
            <span className="text-[#191919] group-hover:text-[#d4a574] transition-colors">
                {article.title}
            </span>
        </div>
    </Link>
);

export default function KnowledgeHub() {
    const featured = sortedNuggets.slice(0, 2);  // First 2 as featured
    const remaining = sortedNuggets.slice(2);     // Rest as compact list

    return (
        <div className="min-h-screen bg-[#fdfcfb]" style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" }}>
            <Helmet>
                <title>Research | 10kiq</title>
                <meta name="description" content="We investigate, experiment, and document our findings from building AI-powered systems. Practical learnings on vLLM, structured outputs, model selection, and production best practices." />
                <meta name="keywords" content="vLLM, LLM, AI, machine learning, prompt engineering, RAG, structured outputs, Pydantic, model selection, PagedAttention, KV cache" />
                <meta property="og:title" content="Research | 10kiq" />
                <meta property="og:description" content="We investigate, experiment, and document our findings from building AI-powered systems." />
                <meta property="og:type" content="website" />
                <meta property="og:site_name" content="10kiq" />
                <meta name="twitter:card" content="summary_large_image" />
                <meta name="twitter:title" content="Research | 10kiq" />
                <meta name="twitter:description" content="We investigate, experiment, and document our findings from building AI-powered systems." />
                <meta name="author" content="10kiq" />
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
            </Helmet>

            {/* Top Navigation */}
            <nav className="border-b border-[#e5e5e5]">
                <div className="max-w-5xl mx-auto px-6">
                    <div className="flex items-center justify-between h-16">
                        <Link to="/" className="text-xl font-semibold text-[#191919]">
                            10kiq
                        </Link>
                        <div className="flex items-center gap-8">
                            <span className="text-[#191919] font-medium">Research</span>
                            <Link to="/" className="text-[#666] hover:text-[#191919] transition-colors">
                                Home
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Hero - Two column like Anthropic */}
            <header className="border-b border-[#e5e5e5]">
                <div className="max-w-5xl mx-auto px-6 py-16 lg:py-20">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-16">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <h1 className="text-5xl lg:text-6xl font-semibold text-[#191919] tracking-tight">
                                Research
                            </h1>
                        </motion.div>
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="flex items-center"
                        >
                            <p className="text-lg text-[#666] leading-relaxed">
                                We investigate, experiment, and document our findings from building
                                AI-powered systems — exploring trade-offs, options, and what
                                actually works in production.
                            </p>
                        </motion.div>
                    </div>
                </div>
            </header>

            {/* Featured Deep Dive */}
            <section className="border-b border-[#e5e5e5]">
                <div className="max-w-5xl mx-auto px-6 py-12">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <Link to="/research/vllm" className="group block">
                            <div className="flex items-baseline gap-2 mb-3 text-sm">
                                <span className="text-[#d4a574] font-medium">Deep Dive</span>
                                <span className="px-2 py-0.5 bg-[#d4a574] text-white text-xs rounded">
                                    Interactive
                                </span>
                            </div>
                            <h2 className="text-3xl font-semibold text-[#191919] group-hover:text-[#d4a574] transition-colors mb-3">
                                vLLM Request Lifecycle
                            </h2>
                            <p className="text-[#666] max-w-2xl mb-4">
                                Explore how vLLM achieves 24x higher throughput with PagedAttention,
                                Continuous Batching, and Prefix Caching.
                            </p>
                            <span className="inline-flex items-center gap-2 text-[#d4a574] font-medium group-hover:gap-3 transition-all">
                                Start walkthrough <ArrowRight size={18} />
                            </span>
                        </Link>
                    </motion.div>
                </div>
            </section>

            {/* Featured Findings (with summaries) */}
            <section className="max-w-5xl mx-auto px-6 pt-12">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    {featured.map((article) => (
                        <FeaturedCard key={article.id} article={article} />
                    ))}
                </motion.div>
            </section>

            {/* Field Notes (compact list) */}
            {remaining.length > 0 && (
                <section className="max-w-5xl mx-auto px-6 py-12">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                    >
                        <h2 className="text-xl font-semibold text-[#191919] mb-6">
                            Field Notes
                        </h2>
                        <div className="border-t border-[#e5e5e5]">
                            {remaining.map((article) => (
                                <FindingRow key={article.id} article={article} />
                            ))}
                        </div>
                    </motion.div>
                </section>
            )}

            {/* Footer */}
            <footer className="border-t border-[#e5e5e5] mt-8">
                <div className="max-w-5xl mx-auto px-6 py-12 text-center text-sm text-[#999]">
                    <p>Built with curiosity and countless experiments</p>
                </div>
            </footer>
        </div>
    );
}
