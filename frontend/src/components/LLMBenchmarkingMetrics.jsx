import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion } from 'framer-motion';
import { ArrowRight, ArrowLeft, Clock, Target, Gauge, Cpu, HardDrive, Activity } from 'lucide-react';

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
                    {idx < pages.length - 1 && <div className="w-2 sm:w-4 h-px bg-[#ddd]" />}
                </React.Fragment>
            ))}
        </div>
    );
};

export default function LLMBenchmarkingMetrics() {
    return (
        <div className="min-h-screen bg-[#fdfcfb]" style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" }}>
            <Helmet>
                <title>LLM Benchmarking: Measurement Protocol | 10kiq Research</title>
                <meta name="description" content="How we measured LLM performance. Response time breakdown, accuracy scoring with keywords, and server resource usage during inference." />
                <meta name="keywords" content="LLM performance metrics, response time, accuracy scoring, benchmark methodology, CPU usage, RAM usage, inference speed" />
                <link rel="canonical" href="https://10kiq.com/research/llm-benchmarking-metrics" />

                {/* Open Graph */}
                <meta property="og:title" content="LLM Benchmarking: Measurement Protocol | 10kiq Research" />
                <meta property="og:description" content="How we measured LLM performance with response time breakdown, accuracy scoring, and server stats." />
                <meta property="og:type" content="article" />
                <meta property="og:url" content="https://10kiq.com/research/llm-benchmarking-metrics" />

                {/* Twitter Card */}
                <meta name="twitter:card" content="summary_large_image" />
                <meta name="twitter:title" content="LLM Benchmarking: Measurement Protocol" />
                <meta name="twitter:description" content="How we measured LLM performance with response time and accuracy scoring." />

                {/* Article metadata */}
                <meta property="article:published_time" content="2025-11-03" />
                <meta property="article:section" content="Research" />
                <meta property="article:tag" content="Metrics" />
                <meta property="article:tag" content="Benchmarking" />
            </Helmet>

            <nav className="border-b border-[#e5e5e5]">
                <div className="max-w-4xl mx-auto px-6">
                    <div className="flex items-center justify-between h-16">
                        <Link to="/" className="text-xl font-semibold text-[#191919]">10kiq</Link>
                        <Link to="/research" className="text-[#666] hover:text-[#191919]">← Research</Link>
                    </div>
                </div>
            </nav>

            <SeriesNav current={4} />

            <main className="max-w-4xl mx-auto px-6 py-12">
                <motion.article
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-12"
                >
                    {/* Header */}
                    <header>
                        <div className="flex items-center gap-2 mb-4">
                            <span className="px-2 py-1 bg-[#1a1a1a] text-white text-xs font-medium rounded">Part 4 of 5</span>
                            <span className="text-[#999] text-sm">LLM Benchmarking Case Study</span>
                        </div>
                        <h1 className="text-4xl font-bold text-[#191919] mb-4">Measurement Protocol</h1>
                        <p className="text-xl text-[#666] leading-relaxed">
                            What exactly we measured, how we measured it, and what the numbers mean.
                            This is the methodology that makes results reproducible.
                        </p>
                    </header>

                    {/* What We Measured */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">The Four Core Metrics</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                                        <Clock className="w-5 h-5 text-blue-600" />
                                    </div>
                                    <h4 className="font-semibold text-[#191919]">Response Time</h4>
                                </div>
                                <p className="text-sm text-[#666] mb-2">
                                    Total seconds from query submission to final answer. End-to-end, not
                                    tokens-per-second.
                                </p>
                                <p className="text-xs text-[#999]">
                                    Measured with Python time.time() around the full agent invocation.
                                </p>
                            </div>
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                                        <Target className="w-5 h-5 text-green-600" />
                                    </div>
                                    <h4 className="font-semibold text-[#191919]">Accuracy Score</h4>
                                </div>
                                <p className="text-sm text-[#666] mb-2">
                                    Percentage of expected keywords found in the answer. 0-100%.
                                </p>
                                <p className="text-xs text-[#999]">
                                    Case-insensitive substring matching against predefined keyword list.
                                </p>
                            </div>
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                                        <Activity className="w-5 h-5 text-amber-600" />
                                    </div>
                                    <h4 className="font-semibold text-[#191919]">Success Rate</h4>
                                </div>
                                <p className="text-sm text-[#666] mb-2">
                                    Queries completed without errors. X/10 per configuration.
                                </p>
                                <p className="text-xs text-[#999]">
                                    Errors include timeouts, model failures, and malformed outputs.
                                </p>
                            </div>
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                                        <Gauge className="w-5 h-5 text-purple-600" />
                                    </div>
                                    <h4 className="font-semibold text-[#191919]">Consistency</h4>
                                </div>
                                <p className="text-sm text-[#666] mb-2">
                                    Standard deviation of response times across queries.
                                </p>
                                <p className="text-xs text-[#999]">
                                    Low std dev = predictable UX. High std dev = unpredictable waits.
                                </p>
                            </div>
                        </div>
                    </section>

                    {/* Time Breakdown */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Response Time Breakdown</h2>
                        <p className="text-[#444] leading-relaxed mb-6">
                            Where does the time actually go? We instrumented each stage to understand
                            which components dominate latency.
                        </p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* llama3.1:8b breakdown */}
                            <div className="bg-white rounded-lg p-5 border border-green-200">
                                <h4 className="font-semibold text-[#191919] mb-4 flex items-center gap-2">
                                    <span className="w-3 h-3 rounded-full bg-green-500"></span>
                                    llama3.1:8b (30.2s total)
                                </h4>
                                <div className="space-y-3">
                                    {[
                                        { stage: 'Pre-processing', time: '~0.5s', pct: 2, color: 'bg-slate-300' },
                                        { stage: 'Planning (LLM)', time: '~8s', pct: 26, color: 'bg-amber-400' },
                                        { stage: 'Vector Search', time: '~10s', pct: 33, color: 'bg-blue-400' },
                                        { stage: 'Synthesis (LLM)', time: '~12s', pct: 39, color: 'bg-emerald-400' }
                                    ].map((s, idx) => (
                                        <div key={idx}>
                                            <div className="flex justify-between text-sm mb-1">
                                                <span className="text-[#444]">{s.stage}</span>
                                                <span className="text-[#666]">{s.time} ({s.pct}%)</span>
                                            </div>
                                            <div className="h-2 bg-[#f0f0f0] rounded-full overflow-hidden">
                                                <div className={`h-full ${s.color} rounded-full`} style={{ width: `${s.pct}%` }}></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <p className="text-xs text-[#666] mt-4">
                                    LLM inference (Planning + Synthesis) = 65% of total time.
                                    Vector search is significant at 33%.
                                </p>
                            </div>

                            {/* qwen72b breakdown */}
                            <div className="bg-white rounded-lg p-5 border border-red-200">
                                <h4 className="font-semibold text-[#191919] mb-4 flex items-center gap-2">
                                    <span className="w-3 h-3 rounded-full bg-red-500"></span>
                                    qwen2.5:72b (692.9s total)
                                </h4>
                                <div className="space-y-3">
                                    {[
                                        { stage: 'Pre-processing', time: '~0.5s', pct: 0.1, color: 'bg-slate-300' },
                                        { stage: 'Planning (LLM)', time: '~250s', pct: 36, color: 'bg-amber-400' },
                                        { stage: 'Vector Search', time: '~10s', pct: 1, color: 'bg-blue-400' },
                                        { stage: 'Synthesis (LLM)', time: '~430s', pct: 62, color: 'bg-emerald-400' }
                                    ].map((s, idx) => (
                                        <div key={idx}>
                                            <div className="flex justify-between text-sm mb-1">
                                                <span className="text-[#444]">{s.stage}</span>
                                                <span className="text-[#666]">{s.time} ({s.pct}%)</span>
                                            </div>
                                            <div className="h-2 bg-[#f0f0f0] rounded-full overflow-hidden">
                                                <div className={`h-full ${s.color} rounded-full`} style={{ width: `${Math.min(s.pct, 100)}%` }}></div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <p className="text-xs text-[#666] mt-4">
                                    LLM inference = 98% of total time.
                                    Vector search is now negligible (1%).
                                </p>
                            </div>
                        </div>

                        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg mt-6">
                            <p className="text-[#191919] font-medium">Key insight:</p>
                            <p className="text-sm text-[#666] mt-1">
                                For large models, LLM inference completely dominates. The 72B model
                                spends 680+ seconds just generating text. Everything else is in the noise.
                            </p>
                        </div>
                    </section>

                    {/* Server Stats */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Server Stats During Inference</h2>
                        <p className="text-[#444] leading-relaxed mb-6">
                            We monitored system resources during each benchmark run. Here's what the
                            server looks like under different model loads:
                        </p>

                        <div className="overflow-x-auto mb-6">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-[#e5e5e5]">
                                        <th className="text-left py-3 px-3 font-semibold text-[#191919]">Process</th>
                                        <th className="text-left py-3 px-3 font-semibold text-[#191919]" colSpan={2}>llama3.1:8b</th>
                                        <th className="text-left py-3 px-3 font-semibold text-[#191919]" colSpan={2}>qwen2.5:72b</th>
                                    </tr>
                                    <tr className="border-b border-[#f0f0f0] text-xs text-[#999]">
                                        <th className="py-1 px-3"></th>
                                        <th className="py-1 px-3">RAM</th>
                                        <th className="py-1 px-3">CPU</th>
                                        <th className="py-1 px-3">RAM</th>
                                        <th className="py-1 px-3">CPU</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[#f0f0f0]">
                                    <tr className="bg-[#f8f7f5]">
                                        <td className="py-3 px-3 font-medium text-[#191919]">Ollama</td>
                                        <td className="py-3 px-3 font-mono text-green-600">6.7GB</td>
                                        <td className="py-3 px-3 font-mono text-green-600">105%</td>
                                        <td className="py-3 px-3 font-mono text-red-600">41GB</td>
                                        <td className="py-3 px-3 font-mono text-red-600">479%</td>
                                    </tr>
                                    <tr>
                                        <td className="py-3 px-3 font-medium text-[#191919]">Backend</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">232MB</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">0.18%</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">257MB</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">0.11%</td>
                                    </tr>
                                    <tr className="bg-[#f8f7f5]">
                                        <td className="py-3 px-3 font-medium text-[#191919]">Postgres</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">28MB</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">4.5%</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">32MB</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">0%</td>
                                    </tr>
                                    <tr>
                                        <td className="py-3 px-3 font-medium text-[#191919]">Qdrant</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">59MB</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">0.09%</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">41MB</td>
                                        <td className="py-3 px-3 font-mono text-[#666]">0.06%</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg border border-green-200">
                                <HardDrive className="w-5 h-5 text-green-600 mt-0.5" />
                                <div>
                                    <p className="font-medium text-[#191919]">llama3.1:8b</p>
                                    <p className="text-sm text-[#666]">
                                        Uses 14% of RAM (6.7GB/49GB). CPU comfortable at 105%.
                                        Plenty of headroom.
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3 p-4 bg-red-50 rounded-lg border border-red-200">
                                <Cpu className="w-5 h-5 text-red-600 mt-0.5" />
                                <div>
                                    <p className="font-medium text-[#191919]">qwen2.5:72b</p>
                                    <p className="text-sm text-[#666]">
                                        Uses 83% of RAM (41GB/49GB). CPU maxed at 479% (all 8 cores).
                                        No room for error.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Output Format */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Output Format We Compared</h2>
                        <p className="text-[#444] leading-relaxed mb-4">
                            Each query produced a structured JSON result. Here's the format we captured
                            for analysis:
                        </p>

                        <div className="bg-[#1a1a1a] text-green-400 p-5 rounded-xl font-mono text-xs overflow-x-auto mb-4">
                            <pre>{`{
  "query": "Who is the CFO of Apple?",
  "category": "simple_factual",
  "difficulty": "easy",
  "response_time_seconds": 22.76,
  "answer_length_chars": 765,
  "answer_preview": "According to all five documents...",
  "full_answer": "According to all five documents, the CFO of Apple is...",
  "accuracy_score": 0.667,
  "expected_keywords": ["Kevan Parekh", "Chief Financial Officer", "CFO"],
  "found_keywords": ["Chief Financial Officer", "CFO"],
  "success": true
}`}</pre>
                        </div>

                        <p className="text-sm text-[#666]">
                            This structure allowed us to calculate aggregate metrics (avg time, avg accuracy)
                            per configuration and drill down into individual query performance.
                        </p>
                    </section>

                    {/* UX Thresholds */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">User Experience Thresholds</h2>
                        <p className="text-[#444] leading-relaxed mb-6">
                            We defined these thresholds before running benchmarks. They come from
                            observing actual user behavior, not theory:
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4">
                            <div className="flex-1 p-5 bg-emerald-50 border border-emerald-200 rounded-lg text-center">
                                <div className="text-3xl font-bold text-emerald-700 mb-1">&lt;30s</div>
                                <div className="text-sm text-emerald-600 font-medium">Acceptable</div>
                                <p className="text-xs text-emerald-700 mt-2">Users will wait</p>
                            </div>
                            <div className="flex-1 p-5 bg-amber-50 border border-amber-200 rounded-lg text-center">
                                <div className="text-3xl font-bold text-amber-700 mb-1">30-60s</div>
                                <div className="text-sm text-amber-600 font-medium">Borderline</div>
                                <p className="text-xs text-amber-700 mt-2">Users get impatient</p>
                            </div>
                            <div className="flex-1 p-5 bg-red-50 border border-red-200 rounded-lg text-center">
                                <div className="text-3xl font-bold text-red-700 mb-1">&gt;60s</div>
                                <div className="text-sm text-red-600 font-medium">Unacceptable</div>
                                <p className="text-xs text-red-700 mt-2">Users abandon</p>
                            </div>
                        </div>
                    </section>

                    {/* Navigation */}
                    <section className="pt-8 border-t border-[#e5e5e5]">
                        <div className="flex justify-between items-center">
                            <Link
                                to="/research/llm-benchmarking-models"
                                className="inline-flex items-center gap-2 px-4 py-2 text-[#666] hover:text-[#191919]"
                            >
                                <ArrowLeft size={16} />
                                Previous
                            </Link>
                            <Link
                                to="/research/llm-benchmarking-results"
                                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#1a1a1a] text-white rounded-lg hover:bg-[#333]"
                            >
                                Next: Results
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
