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
        impact: 'Hard guarantee against context overflow. Before: Turn 10 = 15+ seconds, variable latency, memory issues. After: Consistent 4-second responses, stable memory, predictable performance. LLM attention is O(n²) complexity — reducing tokens from 25,000 to 6,000 gives 3.75x speedup.',
        lesson: "Token-based > Message-based for variable message sizes. Tool responses (like filing_qa_tool) are 250x larger than user queries (20 tokens vs 5,000 tokens). Use built-in utilities (trim_messages) instead of custom logic — they handle edge cases you haven't thought of. Conservative limits (6,000 not 8,192) leave safety margin. Token management is not just about preventing crashes — it's a performance optimization (O(n²) attention complexity), cost optimization (fewer tokens = cheaper), and UX optimization (faster responses). 👥 Best for: Backend developers building conversational AI. 📚 Prerequisites: Understanding of LLM context windows, basic conversation state management.",
        date: 'Nov 12, 2025',
        sortDate: new Date('2025-11-12'),
        readTime: '4 min',
        summary: 'Token-based trimming guarantees no context overflow and provides 3.75x speedup by reducing from 25K to 6K tokens. Use 75% of context limit, not 100%.',
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
        problem: 'After migrating from Docker Ollama to native Ollama (for GPU acceleration), vector search returned 0% confidence scores and wrong answers. Multi-turn conversations failed: "What was Apple\'s revenue?" worked, but follow-up "And what are the risks?" returned irrelevant results. The system seemed to work but gave completely wrong answers.',
        solution: "Root cause: Missing nomic-embed-text model after migration. Docker had the model, native install didn't. The embedding API returned 404 but the system continued with zero/default vectors. Zero vectors compared against document vectors = random 0% similarity. Fix: ollama pull nomic-embed-text. Added: (1) Score threshold filtering — reject results below 50%, (2) Startup health check with retry logic, (3) Fail-fast on embedding errors.",
        impact: 'Before fix: 0% confidence, wrong answers, silent failures. After fix: 50%+ confidence, correct answers, proper error handling. Key insight: LLM models (llama3.2:3b) ≠ Embedding models (nomic-embed-text). Both required but serve different purposes. Infrastructure migrations have hidden dependencies.',
        lesson: "Fail fast > fail silently. 0% similarity scores are diagnostic red flags indicating embedding failure, model mismatch, or vector space incompatibility. When migrating infrastructure, verify ALL model dependencies (LLMs + embeddings). Add startup health checks with retry logic. Filter results by confidence threshold before synthesis.",
        date: 'Nov 12, 2025',
        sortDate: new Date('2025-11-12'),
        readTime: '4 min',
        summary: 'Missing embedding model after Docker migration caused silent failures with 0% confidence — fail fast, not silently.',
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
        problem: 'Multi-company comparisons had unbalanced data retrieval: 4 chunks for Apple, 1 chunk for Microsoft. The RAG system was biased toward whichever company appeared first in the query. Initial solution: build parallel RAG agents with separate pipelines per company — estimated 5-6 weeks of development.',
        solution: 'Instead of rebuilding the architecture, we changed one data structure. The execute_plan() function returned a flat list of chunks. We changed it to return a dictionary keyed by company ticker: {AAPL: [...], MSFT: [...]}. This maintained per-company separation throughout the pipeline, ensuring equal data retrieval for each entity.',
        impact: 'Fixed in 1-2 days instead of 5-6 weeks. Equal data retrieval achieved: 5 chunks per company. 95% less code than the parallel agent approach. No new infrastructure, no additional complexity — just a better data structure.',
        lesson: 'Test the existing system before redesigning. Simple data structure changes often beat complex architectural additions. The impulse to "build something new" can blind us to simpler solutions. When data flows incorrectly, trace the problem back to its source — often it\'s a structural issue, not a capability gap.',
        date: 'Nov 4, 2025',
        sortDate: new Date('2025-11-04'),
        readTime: '3 min',
        summary: 'Changed list to dict — fixed 5-week problem in 2 days with 95% less code than planned parallel agent approach.',
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
