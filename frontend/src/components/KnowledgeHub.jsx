import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion } from 'framer-motion';

// Nugget data - will be moved to a separate file as it grows
export const NUGGETS = [
    {
        id: 'structured-outputs-eliminate-json-errors',
        category: 'LLM Reliability',
        title: 'Structured Outputs Eliminate Malformed JSON Errors',
        emoji: '🛡️',
        problem: 'llama3.1:8b occasionally generated malformed JSON (unterminated strings, missing braces) for complex comparison queries. Error rate: ~5-10% in production. Fallback logic tried to repair JSON but often failed, showing raw JSON dumps to users. Prompt instructions like "ENSURE ALL STRINGS ARE PROPERLY CLOSED" were unreliable.',
        solution: 'Implemented Ollama\'s structured outputs feature using Pydantic schemas. Created SynthesizerOutput schema matching expected JSON structure. Passed schema to ChatOllama via format=SynthesizerOutput.model_json_schema(). Ollama now uses constrained generation — only allows tokens that keep output valid according to schema. Grammar-based sampling guarantees valid JSON.',
        impact: 'Malformed JSON errors dropped from 5-10% to ~0%. No more unterminated strings or missing braces. Token savings: Removed ~400 tokens of JSON formatting instructions from prompt (15% reduction). Simplified prompt from 219 lines to 147 lines. Fallback logic still exists as safety net but rarely triggered. Production reliability improved significantly.',
        lesson: 'Use API-level constraints instead of prompt instructions for structured output. Ollama\'s structured outputs use token-level constraints (grammar-based sampling) to mathematically guarantee valid JSON. Pydantic schemas provide type safety and validation. Prompt instructions are unreliable — LLMs can\'t always follow formatting rules perfectly. Defense in depth: Schema enforcement (primary) + fallback handling (safety net).',
        date: 'Nov 14, 2025',
        readTime: '4 min',
        codeExample: `from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

# Define your schema
class SynthesizerOutput(BaseModel):
    answer: str = Field(description="The synthesized answer")
    confidence: float = Field(ge=0, le=1)
    sources: list[str] = Field(default_factory=list)

# Use structured outputs
llm = ChatOllama(
    model="llama3.1:8b",
    format=SynthesizerOutput.model_json_schema()
)

# Now the LLM MUST output valid JSON matching the schema`
    },
    {
        id: 'data-structure-beats-complex-architecture',
        category: 'Architecture',
        title: 'Data Structure > Complex Architecture',
        emoji: '🏗️',
        problem: 'Multi-company comparisons had unbalanced data retrieval: 4 chunks for Apple, 1 chunk for Microsoft. The RAG system was biased toward whichever company appeared first in the query. Initial solution: build parallel RAG agents with separate pipelines per company — estimated 5-6 weeks of development.',
        solution: 'Instead of rebuilding the architecture, we changed one data structure. The execute_plan() function returned a flat list of chunks. We changed it to return a dictionary keyed by company ticker: {AAPL: [...], MSFT: [...]}. This maintained per-company separation throughout the pipeline, ensuring equal data retrieval for each entity.',
        impact: 'Fixed in 1-2 days instead of 5-6 weeks. Equal data retrieval achieved: 5 chunks per company. 95% less code than the parallel agent approach. No new infrastructure, no additional complexity — just a better data structure.',
        lesson: 'Test the existing system before redesigning. Simple data structure changes often beat complex architectural additions. The impulse to "build something new" can blind us to simpler solutions. When data flows incorrectly, trace the problem back to its source — often it\'s a structural issue, not a capability gap.',
        date: 'Nov 4, 2025',
        readTime: '3 min',
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
        results[ticker] = chunks  # Each company isolated
    return results  # {AAPL: [...], MSFT: [...]}`
    },
    {
        id: 'token-based-trimming-for-context-management',
        category: 'Context Management',
        title: 'Token-based Trimming Beats Message-Count Sliding Window',
        emoji: '📏',
        problem: 'With checkpointing enabled, conversation history grows unbounded. After 10-15 turns, the context window overflows (8,192 tokens for llama3.1:8b). The obvious solution — sliding window keeping last 8 messages — is dangerous because tool responses can be 5,000-10,000 tokens each. Eight large messages could be 20,000+ tokens.',
        solution: "Implemented LangChain's trim_messages utility with max_tokens=6000. Token-based trimming guarantees no overflow regardless of message sizes. It keeps the most recent messages that fit within the budget, automatically handling variable message cases and edge cases.",
        impact: 'Hard guarantee against context overflow. Before: Turn 10 = 15+ seconds, variable latency, memory issues. After: Consistent 4-second responses, stable memory, predictable performance. LLM attention is O(n²) complexity — reducing tokens from 25,000 to 6,000 gives 3.75x speedup.',
        lesson: "Token-based > Message-based for variable message sizes. Tool responses (like filing_qa_tool) are 250x larger than user queries. Use built-in utilities (trim_messages) instead of custom logic. Conservative limits (6,000 not 8,192) leave safety margin. Token management is not just about preventing crashes — it's a performance, cost, and UX optimization.",
        date: 'Nov 12, 2025',
        readTime: '4 min',
        codeExample: `from langchain_core.messages import trim_messages

# Configure token-based trimming
trimmer = trim_messages(
    max_tokens=6000,
    strategy="last",  # Keep most recent
    token_counter=llm,
    include_system=True,
    allow_partial=False,
    start_on="human"
)

# Apply in workflow before LLM call
def chat_step(state):
    # Trim history to fit context window
    trimmed = trimmer.invoke(state["messages"])
    response = llm.invoke(trimmed)
    return {"messages": [response]}`
    },
    {
        id: 'silent-embedding-failures-cause-wrong-answers',
        category: 'Vector Search',
        title: 'Silent Embedding Failures Cause 0% Confidence and Wrong Answers',
        emoji: '🔇',
        problem: 'After migrating from Docker Ollama to native Ollama (for GPU acceleration), vector search returned 0% confidence scores and wrong answers. Multi-turn conversations failed: "What was Apple\'s revenue?" worked, but follow-up "And what are the risks?" returned irrelevant results. The system seemed to work but gave completely wrong answers.',
        solution: "Root cause: Missing nomic-embed-text model after migration. Docker had the model, native install didn't. The embedding API returned 404 but the system continued with zero/default vectors. Zero vectors compared against document vectors = random 0% similarity. Fix: ollama pull nomic-embed-text. Added: (1) Score threshold filtering — reject results below 50%, (2) Startup health check with retry logic, (3) Fail-fast on embedding errors.",
        impact: 'Before fix: 0% confidence, wrong answers, silent failures. After fix: 50%+ confidence, correct answers, proper error handling. Key insight: LLM models (llama3.2:3b) ≠ Embedding models (nomic-embed-text). Both required but serve different purposes. Infrastructure migrations have hidden dependencies.',
        lesson: "Fail fast > fail silently. 0% similarity scores are diagnostic red flags indicating embedding failure, model mismatch, or vector space incompatibility. When migrating infrastructure, verify ALL model dependencies (LLMs + embeddings). Add startup health checks with retry logic. Filter results by confidence threshold before synthesis.",
        date: 'Nov 12, 2025',
        readTime: '4 min',
        codeExample: `# Health check for embedding model
def verify_embedding_model():
    try:
        test_embedding = embed("test query")
        if len(test_embedding) != 768:
            raise ValueError("Wrong embedding dimension")
        return True
    except Exception as e:
        logger.error(f"Embedding model check failed: {e}")
        return False

# Filter low-confidence results
def search_with_threshold(query, min_score=0.5):
    results = vector_db.search(query, limit=10)
    return [r for r in results if r.score >= min_score]`
    }
];

// Featured deep dive
const FEATURED = {
    id: 'vllm-deep-dive',
    category: 'Deep Dive',
    title: 'vLLM Request Lifecycle',
    description: 'Explore how vLLM achieves 24x higher throughput with PagedAttention, Continuous Batching, and Prefix Caching. Step-by-step interactive visualization with code examples.',
    href: '/learn/vllm',
    isInteractive: true
};

// Article card matching Anthropic style
const ArticleCard = ({ article, featured = false }) => (
    <Link
        to={article.href || `/ learn / nuggets / ${article.id}`}
        className="group block"
    >
        <article className={`py - 8 ${featured ? '' : 'border-t border-[#e5e5e5]'}`}>
            <div className="flex items-baseline gap-2 mb-3 text-sm">
                <span className="text-[#666]">{article.category}</span>
                {article.date && (
                    <>
                        <span className="text-[#999]">·</span>
                        <span className="text-[#999]">{article.date}</span>
                    </>
                )}
                {article.isInteractive && (
                    <span className="ml-2 px-2 py-0.5 bg-[#d4a574] text-white text-xs rounded">
                        Interactive
                    </span>
                )}
            </div>
            <h3 className={`font - ['Times_New_Roman', _'Georgia', _serif] ${featured ? 'text-3xl' : 'text-2xl'} text - [#191919] group - hover: text - [#d4a574] transition - colors leading - tight mb - 3`}>
                {article.title}
            </h3>
            <p className="text-[#666] leading-relaxed max-w-3xl">
                {article.description || article.problem}
            </p>
        </article>
    </Link>
);

export default function KnowledgeHub() {
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

            {/* Top Navigation - Anthropic style */}
            <nav className="border-b border-[#e5e5e5]">
                <div className="max-w-7xl mx-auto px-6 lg:px-12">
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
                <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16 lg:py-24">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-16">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <h1 className="text-6xl lg:text-7xl font-semibold text-[#191919] tracking-tight">
                                Research
                            </h1>
                        </motion.div>
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                            className="flex items-center"
                        >
                            <p className="text-xl text-[#666] leading-relaxed">
                                We investigate, experiment, and document our findings from building
                                AI-powered systems — exploring trade-offs, options, and what
                                actually works in production.
                            </p>
                        </motion.div>
                    </div>
                </div>
            </header>

            {/* Content */}
            <main className="max-w-7xl mx-auto px-6 lg:px-12 py-12">
                {/* Featured */}
                <motion.section
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                >
                    <ArticleCard article={FEATURED} featured />
                </motion.section>

                {/* Articles */}
                <motion.section
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                >
                    {NUGGETS.map((nugget, index) => (
                        <ArticleCard key={nugget.id} article={nugget} />
                    ))}
                </motion.section>
            </main>

            {/* Footer */}
            <footer className="border-t border-[#e5e5e5] mt-16">
                <div className="max-w-7xl mx-auto px-6 lg:px-12 py-12 text-center text-sm text-[#999]">
                    <p>Built with curiosity and countless experiments</p>
                </div>
            </footer>
        </div>
    );
}
