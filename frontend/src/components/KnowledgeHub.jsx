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
        to={article.href || `/learn/nuggets/${article.id}`}
        className="group block"
    >
        <article className={`py-8 ${featured ? '' : 'border-t border-[#e5e5e5]'}`}>
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
            <h3 className={`font-['Times_New_Roman',_'Georgia',_serif] ${featured ? 'text-3xl' : 'text-2xl'} text-[#191919] group-hover:text-[#d4a574] transition-colors leading-tight mb-3`}>
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
