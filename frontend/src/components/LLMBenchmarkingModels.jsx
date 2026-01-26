import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion } from 'framer-motion';
import { ArrowRight, ArrowLeft, Server, HardDrive, Cpu, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

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

const MODEL_CONFIGS = [
    {
        name: 'Current (Baseline)',
        supervisor: 'llama3.1:8b',
        planner: 'llama3.1:8b',
        synthesizer: 'llama3.1:8b',
        ram: '~7GB',
        params: '8B',
        rationale: 'Production config. Well-tuned prompts. Known behavior.',
        status: 'baseline'
    },
    {
        name: 'Qwen2.5:72b (All)',
        supervisor: 'qwen2.5:72b',
        planner: 'qwen2.5:72b',
        synthesizer: 'qwen2.5:72b',
        ram: '~41GB',
        params: '72B',
        rationale: 'Maximum quality hypothesis. Largest model that fits.',
        status: 'test'
    },
    {
        name: 'Qwen2.5:32b (All)',
        supervisor: 'qwen2.5:32b',
        planner: 'qwen2.5:32b',
        synthesizer: 'qwen2.5:32b',
        ram: '~18GB',
        params: '32B',
        rationale: 'Middle ground. Better than 8B, faster than 72B?',
        status: 'test'
    },
    {
        name: 'Mixtral:8x7b (MoE)',
        supervisor: 'mixtral:8x7b',
        planner: 'mixtral:8x7b',
        synthesizer: 'mixtral:8x7b',
        ram: '~26GB',
        params: '47B (8×7B, 2 active)',
        rationale: 'Mixture-of-Experts. Different architecture, possibly better efficiency.',
        status: 'experimental'
    },
    {
        name: 'Specialized Mix',
        supervisor: 'qwen2.5:72b',
        planner: 'mixtral:8x7b',
        synthesizer: 'llama3.1:8b',
        ram: '~45GB',
        params: 'Mixed',
        rationale: 'Best-of-each-family. 72B for reasoning, Mixtral for planning, 8B for speed.',
        status: 'experimental'
    },
    {
        name: 'Fast Mix',
        supervisor: 'qwen2.5:32b',
        planner: 'qwen2.5:32b',
        synthesizer: 'llama3.1:8b',
        ram: '~20GB',
        params: 'Mixed',
        rationale: 'Speed-optimized. Better reasoning up front, fast synthesis.',
        status: 'test'
    }
];

export default function LLMBenchmarkingModels() {
    return (
        <div className="min-h-screen bg-[#fdfcfb]" style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" }}>
            <Helmet>
                <title>LLM Benchmarking: Model Selection | 10kiq Research</title>
                <meta name="description" content="How we selected LLM configurations to test within 49GB RAM server constraints. Memory requirements for llama3.1, qwen2.5, and mixtral models." />
                <meta name="keywords" content="LLM model selection, llama3.1 8b, qwen2.5 72b, mixtral 8x7b, Ollama, server constraints, GPU inference, RTX 5060" />
                <link rel="canonical" href="https://10kiq.com/research/llm-benchmarking-models" />

                {/* Open Graph */}
                <meta property="og:title" content="LLM Benchmarking: Model Selection | 10kiq Research" />
                <meta property="og:description" content="How we selected LLM configurations to test within server constraints. Memory requirements and model families." />
                <meta property="og:type" content="article" />
                <meta property="og:url" content="https://10kiq.com/research/llm-benchmarking-models" />

                {/* Twitter Card */}
                <meta name="twitter:card" content="summary_large_image" />
                <meta name="twitter:title" content="LLM Benchmarking: Model Selection" />
                <meta name="twitter:description" content="How we selected LLMs to test within 49GB RAM constraints with RTX 5060." />

                {/* Article metadata */}
                <meta property="article:published_time" content="2025-11-03" />
                <meta property="article:section" content="Research" />
                <meta property="article:tag" content="LLM" />
                <meta property="article:tag" content="Model Selection" />
            </Helmet>

            <nav className="border-b border-[#e5e5e5]">
                <div className="max-w-4xl mx-auto px-6">
                    <div className="flex items-center justify-between h-16">
                        <Link to="/" className="text-xl font-semibold text-[#191919]">10kiq</Link>
                        <Link to="/research" className="text-[#666] hover:text-[#191919]">← Research</Link>
                    </div>
                </div>
            </nav>

            <SeriesNav current={3} />

            <main className="max-w-4xl mx-auto px-6 py-12">
                <motion.article
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-12"
                >
                    {/* Header */}
                    <header>
                        <div className="flex items-center gap-2 mb-4">
                            <span className="px-2 py-1 bg-[#1a1a1a] text-white text-xs font-medium rounded">Part 3 of 5</span>
                            <span className="text-[#999] text-sm">LLM Benchmarking Case Study</span>
                        </div>
                        <h1 className="text-4xl font-bold text-[#191919] mb-4">Model Selection</h1>
                        <p className="text-xl text-[#666] leading-relaxed">
                            We couldn't test every model. Server constraints determined what was possible.
                            Here's how we selected configurations that would answer our questions.
                        </p>
                    </header>

                    {/* Server Constraints */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">The Server Constraints</h2>
                        <p className="text-[#444] leading-relaxed mb-6">
                            This is production infrastructure, not a research cluster. We had to work
                            within what was available:
                        </p>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                                        <HardDrive className="w-5 h-5 text-blue-600" />
                                    </div>
                                    <div>
                                        <h4 className="font-semibold text-[#191919]">49.2GB RAM</h4>
                                        <span className="text-xs text-[#999]">Total available</span>
                                    </div>
                                </div>
                                <p className="text-sm text-[#666]">
                                    This is the hard ceiling. The 72B model alone needs ~41GB loaded.
                                </p>
                            </div>
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                                        <Cpu className="w-5 h-5 text-purple-600" />
                                    </div>
                                    <div>
                                        <h4 className="font-semibold text-[#191919]">8 CPU Cores</h4>
                                        <span className="text-xs text-[#999]">RTX 5060 GPU</span>
                                    </div>
                                </div>
                                <p className="text-sm text-[#666]">
                                    GPU-accelerated inference via Ollama. Larger models benefit from VRAM offloading.
                                </p>
                            </div>
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                                        <Server className="w-5 h-5 text-amber-600" />
                                    </div>
                                    <div>
                                        <h4 className="font-semibold text-[#191919]">NVMe SSD</h4>
                                        <span className="text-xs text-[#999]">Fast I/O</span>
                                    </div>
                                </div>
                                <p className="text-sm text-[#666]">
                                    Model loading is fast. The bottleneck is inference, not I/O.
                                </p>
                            </div>
                        </div>

                        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
                            <p className="text-[#191919] font-medium">The implication:</p>
                            <p className="text-sm text-[#666] mt-1">
                                Any model over ~45GB is out. We can't run multiple large models simultaneously.
                                The 72B model (41GB) leaves only 8GB for everything else—Postgres, Qdrant,
                                the backend, the OS.
                            </p>
                        </div>
                    </section>

                    {/* Test Constants */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">What Stayed Constant</h2>
                        <p className="text-[#444] leading-relaxed mb-4">
                            To isolate the effect of model choice, everything else was held constant:
                        </p>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            <div className="bg-white rounded-lg p-4 border border-[#e5e5e5] text-center">
                                <div className="text-lg font-bold text-[#191919]">10</div>
                                <div className="text-xs text-[#666]">Test queries</div>
                            </div>
                            <div className="bg-white rounded-lg p-4 border border-[#e5e5e5] text-center">
                                <div className="text-lg font-bold text-[#191919]">~50K</div>
                                <div className="text-xs text-[#666]">Chunks in vector DB</div>
                            </div>
                            <div className="bg-white rounded-lg p-4 border border-[#e5e5e5] text-center">
                                <div className="text-lg font-bold text-[#191919]">Qdrant</div>
                                <div className="text-xs text-[#666]">Vector database</div>
                            </div>
                            <div className="bg-white rounded-lg p-4 border border-[#e5e5e5] text-center">
                                <div className="text-lg font-bold text-[#191919]">Same</div>
                                <div className="text-xs text-[#666]">Prompts & logic</div>
                            </div>
                        </div>
                    </section>

                    {/* Software Stack */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Software Stack</h2>
                        <div className="bg-[#1a1a1a] text-green-400 p-5 rounded-xl font-mono text-sm mb-4">
                            <pre>{`Data:
  - 5 companies (AAPL, MSFT, AMZN, PFE, HOOD)
  - Latest 10-K filings
  - ~50K chunks in vector database

Embeddings:
  - Model: nomic-embed-text
  - Dimensions: 768
  - Stored in Qdrant vector DB

Inference:
  - Runtime: Ollama
  - Framework: LangGraph + LangChain
  - GPU: RTX 5060 (CUDA acceleration)`}</pre>
                        </div>
                    </section>

                    {/* What Models Fit */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">What Models Fit?</h2>
                        <p className="text-[#444] leading-relaxed mb-6">
                            We surveyed available models in the Ollama registry and their memory requirements.
                            These were the candidates that could run on our hardware:
                        </p>

                        <div className="space-y-3 mb-6">
                            {[
                                { model: 'llama3.1:8b', ram: '~7GB', fits: true, note: 'Current production' },
                                { model: 'qwen2.5:32b', ram: '~18GB', fits: true, note: 'Comfortable fit' },
                                { model: 'mixtral:8x7b', ram: '~26GB', fits: true, note: 'MoE architecture' },
                                { model: 'qwen2.5:72b', ram: '~41GB', fits: true, note: 'Tight fit, no headroom' },
                                { model: 'llama3.1:70b', ram: '~40GB', fits: true, note: 'Alternative to Qwen' },
                                { model: 'qwen2.5:110b', ram: '~60GB', fits: false, note: 'Exceeds available RAM' },
                            ].map((m, idx) => (
                                <div key={idx} className={`flex items-center justify-between p-3 rounded-lg ${m.fits ? 'bg-white border border-[#e5e5e5]' : 'bg-red-50 border border-red-200'}`}>
                                    <div className="flex items-center gap-3">
                                        {m.fits ? (
                                            <CheckCircle2 className="w-5 h-5 text-green-500" />
                                        ) : (
                                            <XCircle className="w-5 h-5 text-red-500" />
                                        )}
                                        <span className="font-mono text-sm text-[#191919]">{m.model}</span>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <span className="text-sm text-[#666]">{m.note}</span>
                                        <span className="font-mono text-xs text-[#999] w-16 text-right">{m.ram}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* The 6 Configurations */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">The 6 Configurations</h2>
                        <p className="text-[#444] leading-relaxed mb-6">
                            Based on our constraints and the questions we wanted to answer, we designed
                            these configurations. Each tests a specific hypothesis:
                        </p>

                        <div className="space-y-4">
                            {MODEL_CONFIGS.map((config, idx) => (
                                <div
                                    key={idx}
                                    className={`bg-white rounded-lg border p-5 ${config.status === 'baseline' ? 'border-green-300 bg-green-50/30' :
                                        config.status === 'experimental' ? 'border-amber-300 bg-amber-50/30' :
                                            'border-[#e5e5e5]'
                                        }`}
                                >
                                    <div className="flex items-start justify-between mb-3">
                                        <div>
                                            <h4 className="font-semibold text-[#191919] flex items-center gap-2">
                                                {config.name}
                                                {config.status === 'baseline' && (
                                                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">Baseline</span>
                                                )}
                                                {config.status === 'experimental' && (
                                                    <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded">Experimental</span>
                                                )}
                                            </h4>
                                            <p className="text-sm text-[#666] mt-1">{config.rationale}</p>
                                        </div>
                                        <div className="text-right">
                                            <span className="font-mono text-sm text-[#191919]">{config.ram}</span>
                                            <span className="text-xs text-[#999] block">{config.params}</span>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-3 gap-2 text-xs">
                                        <div className="bg-[#f8f7f5] rounded p-2">
                                            <span className="text-[#999] block">Supervisor</span>
                                            <span className="font-mono text-[#444]">{config.supervisor}</span>
                                        </div>
                                        <div className="bg-[#f8f7f5] rounded p-2">
                                            <span className="text-[#999] block">Planner</span>
                                            <span className="font-mono text-[#444]">{config.planner}</span>
                                        </div>
                                        <div className="bg-[#f8f7f5] rounded p-2">
                                            <span className="text-[#999] block">Synthesizer</span>
                                            <span className="font-mono text-[#444]">{config.synthesizer}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>

                    {/* Why These Combinations */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Why These Combinations?</h2>
                        <div className="space-y-4">
                            <div className="flex items-start gap-3">
                                <AlertCircle className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-[#191919]">Homogeneous configs test raw model quality</p>
                                    <p className="text-sm text-[#666]">Same model everywhere. No handoff friction. Pure model comparison.</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <AlertCircle className="w-5 h-5 text-amber-500 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-[#191919]">Mixed configs test "Mixture of Agents" hypothesis</p>
                                    <p className="text-sm text-[#666]">Best model for each role. Tests if specialization helps.</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <AlertCircle className="w-5 h-5 text-purple-500 mt-0.5 flex-shrink-0" />
                                <div>
                                    <p className="font-medium text-[#191919]">Mixtral tests a different architecture</p>
                                    <p className="text-sm text-[#666]">Mixture-of-Experts might behave differently than dense models.</p>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Navigation */}
                    <section className="pt-8 border-t border-[#e5e5e5]">
                        <div className="flex justify-between items-center">
                            <Link
                                to="/research/llm-benchmarking-data"
                                className="inline-flex items-center gap-2 px-4 py-2 text-[#666] hover:text-[#191919]"
                            >
                                <ArrowLeft size={16} />
                                Previous
                            </Link>
                            <Link
                                to="/research/llm-benchmarking-metrics"
                                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#1a1a1a] text-white rounded-lg hover:bg-[#333]"
                            >
                                Next: Measurement Protocol
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
