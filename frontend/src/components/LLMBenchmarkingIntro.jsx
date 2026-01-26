import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion } from 'framer-motion';
import { ArrowRight, Brain, Database, Zap, GitBranch } from 'lucide-react';

const SeriesNav = ({ current = 1 }) => {
    const pages = [
        { num: 1, title: 'Problem', path: '/research/llm-benchmarking-intro' },
        { num: 2, title: 'Data', path: '/research/llm-benchmarking-data' },
        { num: 3, title: 'Models', path: '/research/llm-benchmarking-models' },
        { num: 4, title: 'Metrics', path: '/research/llm-benchmarking-metrics' },
        { num: 5, title: 'Results', path: '/research/llm-benchmarking-results' }
    ];

    return (
        <div className="flex items-center justify-center gap-1 sm:gap-2 py-4 flex-wrap">
            {pages.map((page, idx) => (
                <React.Fragment key={page.num}>
                    <Link
                        to={page.path}
                        className={`flex items-center gap-1.5 px-2 sm:px-3 py-1.5 rounded-full text-xs sm:text-sm transition-all ${page.num === current
                            ? 'bg-[#1a1a1a] text-white'
                            : page.num < current
                                ? 'bg-[#e8e4df] text-[#666] hover:bg-[#d4a574] hover:text-white'
                                : 'bg-[#f5f3f0] text-[#999] hover:bg-[#e8e4df]'
                            }`}
                    >
                        <span className="font-mono">{page.num}</span>
                        <span className="hidden sm:inline">{page.title}</span>
                    </Link>
                    {idx < pages.length - 1 && (
                        <div className="w-2 sm:w-4 h-px bg-[#ddd]" />
                    )}
                </React.Fragment>
            ))}
        </div>
    );
};

export default function LLMBenchmarkingIntro() {
    return (
        <div className="min-h-screen bg-[#fdfcfb]" style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" }}>
            <Helmet>
                <title>LLM Benchmarking: The Problem | 10kiq Research</title>
                <meta name="description" content="Why we needed to benchmark LLM configurations in our 3-agent RAG system. The architectural question behind model selection for financial analysis." />
                <meta name="keywords" content="LLM benchmarking, RAG system, model selection, llama3.1, qwen2.5, agent architecture, financial AI" />
                <link rel="canonical" href="https://10kiq.com/research/llm-benchmarking-intro" />

                {/* Open Graph */}
                <meta property="og:title" content="LLM Benchmarking: The Problem | 10kiq Research" />
                <meta property="og:description" content="Why we needed to benchmark LLM configurations in our 3-agent RAG system. The architectural question behind model selection." />
                <meta property="og:type" content="article" />
                <meta property="og:url" content="https://10kiq.com/research/llm-benchmarking-intro" />

                {/* Twitter Card */}
                <meta name="twitter:card" content="summary_large_image" />
                <meta name="twitter:title" content="LLM Benchmarking: The Problem" />
                <meta name="twitter:description" content="Why we needed to benchmark LLM configurations in our 3-agent RAG system." />

                {/* Article metadata */}
                <meta property="article:published_time" content="2025-11-03" />
                <meta property="article:section" content="Research" />
                <meta property="article:tag" content="LLM" />
                <meta property="article:tag" content="Benchmarking" />
                <meta property="article:tag" content="RAG" />
            </Helmet>

            <nav className="border-b border-[#e5e5e5]">
                <div className="max-w-4xl mx-auto px-6">
                    <div className="flex items-center justify-between h-16">
                        <Link to="/" className="text-xl font-semibold text-[#191919]">10kiq</Link>
                        <Link to="/research" className="text-[#666] hover:text-[#191919]">← Research</Link>
                    </div>
                </div>
            </nav>

            <SeriesNav current={1} />

            <main className="max-w-4xl mx-auto px-6 py-12">
                <motion.article
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-12"
                >
                    {/* Header */}
                    <header>
                        <div className="flex items-center gap-2 mb-4">
                            <span className="px-2 py-1 bg-[#1a1a1a] text-white text-xs font-medium rounded">Part 1 of 5</span>
                            <span className="text-[#999] text-sm">LLM Benchmarking Case Study</span>
                        </div>
                        <h1 className="text-4xl font-bold text-[#191919] mb-4">The Problem</h1>
                        <p className="text-xl text-[#666] leading-relaxed">
                            We had a working system. The question was whether we could make it better
                            by changing the models—and whether "better" even meant what we assumed.
                        </p>
                    </header>

                    {/* Context */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">The Context</h2>
                        <p className="text-[#444] leading-relaxed mb-4">
                            10kiq is a RAG-based financial analysis system. Users ask questions about SEC filings,
                            and the system retrieves relevant sections and synthesizes answers with citations.
                        </p>
                        <p className="text-[#444] leading-relaxed">
                            We'd been running llama3.1:8b for months. It worked. But "works" isn't the same
                            as "optimal." We kept wondering: are we leaving performance on the table by not
                            using larger models?
                        </p>
                    </section>

                    {/* The Architecture */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">The Architecture</h2>
                        <p className="text-[#444] leading-relaxed mb-6">
                            Our v2 architecture uses three specialized LLM roles. This wasn't an accident—it
                            was a deliberate design to separate concerns. Each role can be configured with
                            a different model.
                        </p>

                        {/* Architecture Diagram */}
                        <div className="bg-[#1a1a1a] text-green-400 p-6 rounded-xl font-mono text-sm overflow-x-auto mb-4">
                            <pre className="whitespace-pre">{`User Query
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
Final Answer`}</pre>
                        </div>
                        <p className="text-xs text-[#999] italic mb-6">
                            This is a simplified view showing only the LLM touchpoints. The actual system includes
                            vector database queries, embedding generation, prompt construction, and output parsing.
                        </p>

                        {/* Role Explanations */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                                        <Brain className="w-5 h-5 text-blue-600" />
                                    </div>
                                    <h4 className="font-semibold text-[#191919]">Supervisor</h4>
                                </div>
                                <p className="text-sm text-[#666]">
                                    Routes the query. Is this a filing question? A comparison? Needs different
                                    handling? It's the traffic controller.
                                </p>
                            </div>
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                                        <Database className="w-5 h-5 text-amber-600" />
                                    </div>
                                    <h4 className="font-semibold text-[#191919]">Planner</h4>
                                </div>
                                <p className="text-sm text-[#666]">
                                    Structures the retrieval. Extracts tickers, determines which SEC sections
                                    to search. Builds the execution plan.
                                </p>
                            </div>
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                                        <Zap className="w-5 h-5 text-emerald-600" />
                                    </div>
                                    <h4 className="font-semibold text-[#191919]">Synthesizer</h4>
                                </div>
                                <p className="text-sm text-[#666]">
                                    Generates the answer. Takes retrieved chunks, produces structured JSON
                                    with citations. The final output quality depends on this.
                                </p>
                            </div>
                        </div>
                    </section>

                    {/* The Flexibility */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">The Flexibility Problem</h2>
                        <p className="text-[#444] leading-relaxed mb-4">
                            This architecture gives us flexibility. Each role can use a different model.
                            You could run a 72B model for complex reasoning in the Supervisor, a
                            fast 8B model for Synthesis, and something in between for Planning.
                        </p>
                        <p className="text-[#444] leading-relaxed mb-6">
                            This is sometimes called "Mixture of Agents"—the idea that specialized models
                            for specialized tasks will outperform one model doing everything.
                        </p>

                        <div className="bg-amber-50 border-l-4 border-amber-500 p-5 rounded-r-lg">
                            <p className="text-[#191919] font-medium mb-2">But flexibility creates questions:</p>
                            <ul className="text-[#444] space-y-2 text-sm">
                                <li>• Is a 72B model actually better than 8B for our specific tasks?</li>
                                <li>• Does mixing models create handoff friction that hurts overall quality?</li>
                                <li>• Is the latency hit of larger models worth the accuracy gain (if any)?</li>
                                <li>• Do Mixture-of-Experts architectures (like Mixtral) behave differently?</li>
                            </ul>
                        </div>
                    </section>

                    {/* The Assumption */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">The Assumption We Wanted to Test</h2>
                        <div className="bg-[#f0f7ff] border-l-4 border-blue-500 p-6 rounded-r-lg mb-6">
                            <p className="text-[#191919] text-lg leading-relaxed italic">
                                "Larger models have more parameters and should produce better outputs.
                                The cost is latency, but for a financial analysis tool where accuracy matters,
                                users will accept slower responses for better answers."
                            </p>
                        </div>
                        <p className="text-[#444] leading-relaxed">
                            This sounds reasonable. It's what the benchmarks suggest. But benchmarks test
                            models in isolation on generic tasks. We needed to test models in our system,
                            on our data, with our prompts.
                        </p>
                    </section>

                    {/* What We Decided to Do */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">What We Decided to Do</h2>
                        <p className="text-[#444] leading-relaxed mb-4">
                            Instead of debating, we'd measure. We designed a systematic benchmark:
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div className="flex items-start gap-3 p-4 bg-[#f8f7f5] rounded-lg">
                                <GitBranch className="w-5 h-5 text-[#d4a574] mt-0.5" />
                                <div>
                                    <h4 className="font-semibold text-[#191919] text-sm">Multiple Configurations</h4>
                                    <p className="text-xs text-[#666]">Test homogeneous vs mixed model setups</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3 p-4 bg-[#f8f7f5] rounded-lg">
                                <Database className="w-5 h-5 text-[#d4a574] mt-0.5" />
                                <div>
                                    <h4 className="font-semibold text-[#191919] text-sm">Real Production Data</h4>
                                    <p className="text-xs text-[#666]">Actual SEC filings, not synthetic benchmarks</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3 p-4 bg-[#f8f7f5] rounded-lg">
                                <Brain className="w-5 h-5 text-[#d4a574] mt-0.5" />
                                <div>
                                    <h4 className="font-semibold text-[#191919] text-sm">Reproducible Accuracy</h4>
                                    <p className="text-xs text-[#666]">Keyword matching, not subjective evaluation</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3 p-4 bg-[#f8f7f5] rounded-lg">
                                <Zap className="w-5 h-5 text-[#d4a574] mt-0.5" />
                                <div>
                                    <h4 className="font-semibold text-[#191919] text-sm">End-to-End Metrics</h4>
                                    <p className="text-xs text-[#666]">Full system timing, not isolated model speed</p>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Navigation */}
                    <section className="pt-8 border-t border-[#e5e5e5]">
                        <div className="flex justify-between items-center">
                            <span className="text-[#999] text-sm">Part 1 of 5</span>
                            <Link
                                to="/research/llm-benchmarking-data"
                                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#1a1a1a] text-white rounded-lg hover:bg-[#333] transition-colors"
                            >
                                Next: Designing Test Data
                                <ArrowRight size={16} />
                            </Link>
                        </div>
                    </section>
                </motion.article>
            </main>

            <footer className="border-t border-[#e5e5e5] mt-16">
                <div className="max-w-4xl mx-auto px-6 py-8 text-center text-sm text-[#999]">
                    LLM Benchmarking Case Study • November 2025
                </div>
            </footer>
        </div>
    );
}
