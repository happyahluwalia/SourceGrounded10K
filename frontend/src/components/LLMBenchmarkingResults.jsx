import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion } from 'framer-motion';
import { ArrowLeft, Trophy, XCircle, AlertTriangle, TrendingDown, CheckCircle2, Lightbulb } from 'lucide-react';

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

const RESULTS_DATA = [
    { name: 'Current (llama3.1:8b)', time: '30.2s', accuracy: '72.5%', success: '10/10', status: 'winner' },
    { name: 'Qwen2.5:72b (All)', time: '692.9s', accuracy: '50.8%', success: '10/10', status: 'worst' },
    { name: 'Qwen2.5:32b (All)', time: '197.9s', accuracy: '51.7%', success: '10/10', status: 'poor' },
    { name: 'Mixtral:8x7b (All)', time: 'N/A', accuracy: 'N/A', success: '0/10', status: 'failed' },
    { name: 'Specialized Mix', time: '210.5s', accuracy: '34.2%', success: '10/10', status: 'worst-accuracy' },
    { name: 'Fast Mix', time: '105.5s', accuracy: '53.3%', success: '10/10', status: 'mediocre' },
];

export default function LLMBenchmarkingResults() {
    return (
        <div className="min-h-screen bg-[#fdfcfb]" style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" }}>
            <Helmet>
                <title>LLM Benchmarking Results: 8B vs 72B | 10kiq Research</title>
                <meta name="description" content="LLM benchmarking results: llama3.1:8b beat qwen2.5:72b on both speed (30s vs 693s) AND accuracy (72.5% vs 50.8%). The surprising data explained." />
                <meta name="keywords" content="LLM benchmark results, llama3.1 vs qwen2.5, model comparison, 8B vs 72B, accuracy metrics, response time comparison" />
                <link rel="canonical" href="https://10kiq.com/research/llm-benchmarking-results" />

                {/* Open Graph */}
                <meta property="og:title" content="LLM Benchmarking Results: 8B vs 72B | 10kiq Research" />
                <meta property="og:description" content="The 8B model beat the 72B on both speed AND accuracy. Here's the data." />
                <meta property="og:type" content="article" />
                <meta property="og:url" content="https://10kiq.com/research/llm-benchmarking-results" />

                {/* Twitter Card */}
                <meta name="twitter:card" content="summary_large_image" />
                <meta name="twitter:title" content="LLM Benchmarking: 8B Beat 72B" />
                <meta name="twitter:description" content="llama3.1:8b beat qwen2.5:72b on speed (30s vs 693s) AND accuracy (72.5% vs 50.8%)." />

                {/* Article metadata */}
                <meta property="article:published_time" content="2025-11-03" />
                <meta property="article:section" content="Research" />
                <meta property="article:tag" content="Results" />
                <meta property="article:tag" content="LLM Comparison" />
            </Helmet>

            <nav className="border-b border-[#e5e5e5]">
                <div className="max-w-4xl mx-auto px-6">
                    <div className="flex items-center justify-between h-16">
                        <Link to="/" className="text-xl font-semibold text-[#191919]">10kiq</Link>
                        <Link to="/research" className="text-[#666] hover:text-[#191919]">← Research</Link>
                    </div>
                </div>
            </nav>

            <SeriesNav current={5} />

            <main className="max-w-4xl mx-auto px-6 py-12">
                <motion.article
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-12"
                >
                    {/* Header */}
                    <header>
                        <div className="flex items-center gap-2 mb-4">
                            <span className="px-2 py-1 bg-[#1a1a1a] text-white text-xs font-medium rounded">Part 5 of 5</span>
                            <span className="text-[#999] text-sm">LLM Benchmarking Case Study</span>
                        </div>
                        <h1 className="text-4xl font-bold text-[#191919] mb-4">The Results</h1>
                        <p className="text-xl text-[#666] leading-relaxed">
                            The data surprised us. The 8B model beat the 72B model on both speed AND accuracy.
                            Here's what we found.
                        </p>
                    </header>

                    {/* Summary Table */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Summary</h2>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-[#e5e5e5]">
                                        <th className="text-left py-3 px-3 font-semibold text-[#191919]">Configuration</th>
                                        <th className="text-left py-3 px-3 font-semibold text-[#191919]">Avg Time</th>
                                        <th className="text-left py-3 px-3 font-semibold text-[#191919]">Accuracy</th>
                                        <th className="text-left py-3 px-3 font-semibold text-[#191919]">Success</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[#f0f0f0]">
                                    {RESULTS_DATA.map((r, idx) => (
                                        <tr
                                            key={idx}
                                            className={
                                                r.status === 'winner' ? 'bg-green-50' :
                                                    r.status === 'failed' ? 'bg-red-50' :
                                                        r.status === 'worst' || r.status === 'worst-accuracy' ? 'bg-amber-50' :
                                                            ''
                                            }
                                        >
                                            <td className="py-3 px-3 font-medium text-[#191919] flex items-center gap-2">
                                                {r.status === 'winner' && <Trophy className="w-4 h-4 text-green-600" />}
                                                {r.status === 'failed' && <XCircle className="w-4 h-4 text-red-600" />}
                                                {r.status === 'worst' && <TrendingDown className="w-4 h-4 text-amber-600" />}
                                                {r.name}
                                            </td>
                                            <td className={`py-3 px-3 font-mono ${r.status === 'winner' ? 'text-green-700 font-bold' : r.status === 'failed' ? 'text-red-600' : 'text-[#444]'}`}>
                                                {r.time}
                                            </td>
                                            <td className={`py-3 px-3 font-mono ${r.status === 'winner' ? 'text-green-700 font-bold' : r.status === 'failed' ? 'text-red-600' : 'text-[#444]'}`}>
                                                {r.accuracy}
                                            </td>
                                            <td className={`py-3 px-3 font-mono ${r.success === '10/10' ? 'text-[#444]' : 'text-red-600 font-bold'}`}>
                                                {r.success}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* Winner */}
                    <section className="bg-green-50 border border-green-200 rounded-xl p-6">
                        <div className="flex items-start gap-4">
                            <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                                <Trophy className="w-6 h-6 text-green-600" />
                            </div>
                            <div>
                                <h3 className="text-xl font-semibold text-[#191919] mb-2">Winner: llama3.1:8b</h3>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                    <div>
                                        <div className="text-2xl font-bold text-green-700">30.2s</div>
                                        <div className="text-xs text-[#666]">Average response</div>
                                    </div>
                                    <div>
                                        <div className="text-2xl font-bold text-green-700">72.5%</div>
                                        <div className="text-xs text-[#666]">Accuracy</div>
                                    </div>
                                    <div>
                                        <div className="text-2xl font-bold text-green-700">10/10</div>
                                        <div className="text-xs text-[#666]">Success rate</div>
                                    </div>
                                    <div>
                                        <div className="text-2xl font-bold text-green-700">~7GB</div>
                                        <div className="text-xs text-[#666]">Memory usage</div>
                                    </div>
                                </div>
                                <p className="text-[#444] text-sm">
                                    The production baseline won across every metric. Fastest, most accurate,
                                    most reliable, lowest resource usage.
                                </p>
                            </div>
                        </div>
                    </section>

                    {/* The 72B Failure */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">The 72B Model Failure</h2>
                        <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-6">
                            <div className="flex items-start gap-4">
                                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                                    <TrendingDown className="w-6 h-6 text-red-600" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-semibold text-[#191919] mb-2">qwen2.5:72b: 23x slower, 30% less accurate</h3>
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                                        <div>
                                            <div className="text-2xl font-bold text-red-700">692.9s</div>
                                            <div className="text-xs text-[#666]">Average (11.5 minutes!)</div>
                                        </div>
                                        <div>
                                            <div className="text-2xl font-bold text-red-700">50.8%</div>
                                            <div className="text-xs text-[#666]">Accuracy (vs 72.5%)</div>
                                        </div>
                                        <div>
                                            <div className="text-2xl font-bold text-red-700">399-1176s</div>
                                            <div className="text-xs text-[#666]">Range (6-19 min)</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <p className="text-[#444] leading-relaxed mb-4">
                            <strong>Example query:</strong> "Who is the CFO of Apple?"
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                                <div className="font-semibold text-[#191919] mb-2">llama3.1:8b</div>
                                <div className="text-sm text-[#666]">
                                    <span className="font-mono">22.8s</span> • <span className="font-mono">66.7%</span> accuracy
                                </div>
                            </div>
                            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                                <div className="font-semibold text-[#191919] mb-2">qwen2.5:72b</div>
                                <div className="text-sm text-[#666]">
                                    <span className="font-mono">424.8s</span> (18.6x slower) • <span className="font-mono">33.3%</span> accuracy (worse!)
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Mixtral Failure */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Mixtral: Complete Failure</h2>
                        <div className="bg-slate-100 border border-slate-300 rounded-xl p-6">
                            <div className="flex items-start gap-4">
                                <XCircle className="w-6 h-6 text-slate-600 flex-shrink-0 mt-1" />
                                <div>
                                    <p className="font-medium text-[#191919] mb-2">0/10 queries succeeded</p>
                                    <p className="text-sm text-[#666] mb-3">
                                        Every query errored with the same message:
                                    </p>
                                    <div className="bg-[#1a1a1a] text-red-400 p-3 rounded-lg font-mono text-xs mb-3">
                                        <code>registry.ollama.ai/library/mixtral:8x7b does not support tools (status code: 400)</code>
                                    </div>
                                    <p className="text-sm text-[#666]">
                                        Mixtral doesn't support LangChain's tool-calling interface in Ollama.
                                        Our architecture requires tools for agent routing. This isn't a model
                                        quality issue—it's an integration incompatibility.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Specialized Mix Failure */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Specialized Mix: Worst Accuracy</h2>
                        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
                            <div className="flex items-start gap-4">
                                <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-1" />
                                <div>
                                    <p className="font-medium text-[#191919] mb-2">34.2% accuracy — worse than any homogeneous config</p>
                                    <p className="text-sm text-[#666] mb-3">
                                        We expected the "best of each family" approach to combine strengths.
                                        Instead, it combined weaknesses.
                                    </p>
                                    <p className="text-sm text-[#666]">
                                        <strong>Likely cause:</strong> Different models have different output formats
                                        and tokenizers. Handoffs between models created silent failures.
                                        The Supervisor's output wasn't compatible with Mixtral's expected input format.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Key Findings */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Key Findings</h2>
                        <div className="space-y-4">
                            <div className="flex items-start gap-4 p-4 bg-[#f8f7f5] rounded-lg">
                                <Lightbulb className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-[#191919]">1. Size doesn't equal performance</p>
                                    <p className="text-sm text-[#666]">
                                        The 72B model was 23x slower with 30% worse accuracy. More parameters
                                        doesn't mean better results for well-defined RAG tasks.
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-start gap-4 p-4 bg-[#f8f7f5] rounded-lg">
                                <Lightbulb className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-[#191919]">2. Homogeneous beats mixed</p>
                                    <p className="text-sm text-[#666]">
                                        The Specialized Mix had the worst accuracy (34.2%) despite using the most resources.
                                        Mixing model families creates handoff friction.
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-start gap-4 p-4 bg-[#f8f7f5] rounded-lg">
                                <Lightbulb className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-[#191919]">3. Task-fit beats parameter count</p>
                                    <p className="text-sm text-[#666]">
                                        Our prompts were tuned for llama3.1. The model we'd been using had
                                        months of implicit optimization. New models started from scratch.
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-start gap-4 p-4 bg-[#f8f7f5] rounded-lg">
                                <Lightbulb className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-[#191919]">4. Consistency matters</p>
                                    <p className="text-sm text-[#666]">
                                        llama3.1 std dev: 8.7s. qwen72b std dev: 247s. Users prefer predictable
                                        30s over "sometimes 10s, sometimes 120s."
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Recommendation */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Recommendation</h2>
                        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
                            <div className="flex items-start gap-4">
                                <CheckCircle2 className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
                                <div>
                                    <p className="font-medium text-[#191919] mb-2">Keep the current configuration</p>
                                    <p className="text-sm text-[#666] mb-3">
                                        llama3.1:8b for all three roles. No changes needed.
                                    </p>
                                    <p className="text-sm text-[#666]">
                                        <strong>Next steps:</strong> Focus on prompt engineering, caching, and UX
                                        improvements rather than model upgrades. The bottleneck isn't model quality—it's
                                        everything else.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Series Complete */}
                    <section className="pt-8 border-t border-[#e5e5e5]">
                        <div className="text-center">
                            <p className="text-[#999] text-sm mb-4">End of series</p>
                            <div className="flex flex-col sm:flex-row gap-3 justify-center">
                                <Link
                                    to="/research/llm-benchmarking-intro"
                                    className="inline-flex items-center justify-center gap-2 px-5 py-2.5 border border-[#e5e5e5] text-[#666] rounded-lg hover:bg-[#f8f7f5]"
                                >
                                    <ArrowLeft size={16} />
                                    Start from beginning
                                </Link>
                                <Link
                                    to="/research"
                                    className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-[#1a1a1a] text-white rounded-lg hover:bg-[#333]"
                                >
                                    Back to Research
                                </Link>
                            </div>
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
