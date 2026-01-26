import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion } from 'framer-motion';
import { ArrowRight, ArrowLeft, Target, BarChart3, Building2, CheckSquare } from 'lucide-react';

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

// Test query data from the actual documentation
const TEST_QUERIES = [
    { id: 1, query: "Who is the CFO of Apple?", category: "Simple Factual", difficulty: "Easy", keywords: ["Kevan Parekh", "CFO"] },
    { id: 2, query: "What were Apple's total revenues last fiscal year?", category: "Numerical", difficulty: "Easy", keywords: ["revenue", "416", "billion"] },
    { id: 3, query: "What are the main risk factors for investing in Amazon?", category: "Analysis", difficulty: "Medium", keywords: ["risk", "competition", "regulatory"] },
    { id: 4, query: "How much did Microsoft spend on R&D last year?", category: "Numerical", difficulty: "Easy", keywords: ["research", "development", "billion"] },
    { id: 5, query: "What is Microsoft's business strategy for cloud computing?", category: "Strategic", difficulty: "Medium", keywords: ["cloud", "Azure", "strategy"] },
    { id: 6, query: "Compare Apple's gross margin to Microsoft's gross margin", category: "Comparison", difficulty: "Hard", keywords: ["gross margin", "Apple", "Microsoft"] },
    { id: 7, query: "What were the key highlights from Pfizer's latest 10-K?", category: "Summarization", difficulty: "Medium", keywords: ["revenue", "product", "pipeline"] },
    { id: 8, query: "Who are the members of Apple's board of directors?", category: "List", difficulty: "Easy", keywords: ["director", "board", "Tim Cook"] },
    { id: 9, query: "What is Amazon's policy on stock-based compensation?", category: "Policy", difficulty: "Medium", keywords: ["stock", "compensation", "equity"] },
    { id: 10, query: "Explain Amazon's revenue recognition policy for AWS", category: "Technical", difficulty: "Hard", keywords: ["revenue recognition", "AWS"] },
];

const DifficultyBadge = ({ level }) => {
    const colors = {
        Easy: 'bg-green-100 text-green-700 border-green-200',
        Medium: 'bg-amber-100 text-amber-700 border-amber-200',
        Hard: 'bg-red-100 text-red-700 border-red-200'
    };
    return (
        <span className={`px-2 py-0.5 text-xs font-medium rounded border ${colors[level]}`}>
            {level}
        </span>
    );
};

export default function LLMBenchmarkingData() {
    return (
        <div className="min-h-screen bg-[#fdfcfb]" style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" }}>
            <Helmet>
                <title>LLM Benchmarking: Test Data Design | 10kiq Research</title>
                <meta name="description" content="How we designed test queries for LLM benchmarking. Query categories, difficulty distribution, and keyword-based accuracy measurement methodology." />
                <meta name="keywords" content="LLM testing, benchmark design, test queries, accuracy scoring, keyword matching, SEC filings, financial data" />
                <link rel="canonical" href="https://10kiq.com/research/llm-benchmarking-data" />

                {/* Open Graph */}
                <meta property="og:title" content="LLM Benchmarking: Test Data Design | 10kiq Research" />
                <meta property="og:description" content="How we designed test queries for LLM benchmarking. Query categories, difficulty distribution, and accuracy measurement." />
                <meta property="og:type" content="article" />
                <meta property="og:url" content="https://10kiq.com/research/llm-benchmarking-data" />

                {/* Twitter Card */}
                <meta name="twitter:card" content="summary_large_image" />
                <meta name="twitter:title" content="LLM Benchmarking: Test Data Design" />
                <meta name="twitter:description" content="How we designed test queries for LLM benchmarking with keyword-based accuracy scoring." />

                {/* Article metadata */}
                <meta property="article:published_time" content="2025-11-03" />
                <meta property="article:section" content="Research" />
                <meta property="article:tag" content="Testing" />
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

            <SeriesNav current={2} />

            <main className="max-w-4xl mx-auto px-6 py-12">
                <motion.article
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-12"
                >
                    {/* Header */}
                    <header>
                        <div className="flex items-center gap-2 mb-4">
                            <span className="px-2 py-1 bg-[#1a1a1a] text-white text-xs font-medium rounded">Part 2 of 5</span>
                            <span className="text-[#999] text-sm">LLM Benchmarking Case Study</span>
                        </div>
                        <h1 className="text-4xl font-bold text-[#191919] mb-4">Designing Test Data</h1>
                        <p className="text-xl text-[#666] leading-relaxed">
                            Random queries won't tell you anything useful. We needed deliberate variety
                            across categories, difficulty levels, and companies.
                        </p>
                    </header>

                    {/* The Problem with Random Testing */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Why Not Just Ask "Random" Questions?</h2>

                        <div className="bg-purple-50 border-l-4 border-purple-500 p-4 rounded-r-lg mb-4">
                            <p className="text-[#191919] font-medium mb-2">💭 The Thinking Process</p>
                            <p className="text-sm text-[#666]">
                                Before designing the test set, we asked: "What would make a benchmark result meaningless?"
                                The answer shaped our approach.
                            </p>
                        </div>

                        <p className="text-[#444] leading-relaxed mb-4">
                            If you test with only easy questions, every model looks good. If you test with
                            only one company, you don't know if results generalize. If you test with
                            only one type of question, you miss blind spots.
                        </p>
                        <p className="text-[#444] leading-relaxed">
                            We needed a test set that would expose differences between models—if those
                            differences existed.
                        </p>
                    </section>

                    {/* Coverage Requirements */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Coverage Requirements</h2>

                        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg mb-6">
                            <p className="text-[#191919] font-medium mb-2">💭 The Thinking Process</p>
                            <p className="text-sm text-[#666]">
                                We needed breadth to catch where models differ. A model might excel at facts but
                                struggle with reasoning. Or handle tech companies well but falter on pharma jargon.
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                                        <Target className="w-5 h-5 text-purple-600" />
                                    </div>
                                    <h4 className="font-semibold text-[#191919]">7 Categories</h4>
                                </div>
                                <p className="text-sm text-[#666] mb-2">
                                    Factual, Numerical, Analysis, Strategic, Comparison, Summarization, Policy
                                </p>
                                <p className="text-xs text-[#999] italic">
                                    Why: Each tests a different cognitive skill—retrieval, extraction, synthesis, reasoning
                                </p>
                            </div>
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center">
                                        <BarChart3 className="w-5 h-5 text-orange-600" />
                                    </div>
                                    <h4 className="font-semibold text-[#191919]">3 Difficulties</h4>
                                </div>
                                <p className="text-sm text-[#666] mb-2">
                                    Easy (4), Medium (4), Hard (2) — weighted toward challenge
                                </p>
                                <p className="text-xs text-[#999] italic">
                                    Why: Hard queries separate strong models from weak; easy queries catch fundamental failures
                                </p>
                            </div>
                            <div className="bg-white rounded-lg p-5 border border-[#e5e5e5]">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                                        <Building2 className="w-5 h-5 text-blue-600" />
                                    </div>
                                    <h4 className="font-semibold text-[#191919]">5 Companies</h4>
                                </div>
                                <p className="text-sm text-[#666] mb-2">
                                    AAPL, MSFT, AMZN, PFE, HOOD — across 4 industries
                                </p>
                                <p className="text-xs text-[#999] italic">
                                    Why: 10-K language varies by industry; pharma ≠ fintech ≠ consumer tech
                                </p>
                            </div>
                        </div>
                    </section>

                    {/* The 10 Test Queries */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">The 10 Test Queries</h2>
                        <p className="text-[#444] leading-relaxed mb-6">
                            Each query was chosen to test a specific capability. The expected keywords
                            define what a correct answer must contain.
                        </p>

                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-[#e5e5e5]">
                                        <th className="text-left py-3 px-2 font-semibold text-[#191919] w-8">#</th>
                                        <th className="text-left py-3 px-2 font-semibold text-[#191919]">Query</th>
                                        <th className="text-left py-3 px-2 font-semibold text-[#191919]">Category</th>
                                        <th className="text-left py-3 px-2 font-semibold text-[#191919]">Level</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[#f0f0f0]">
                                    {TEST_QUERIES.map((q) => (
                                        <tr key={q.id} className="hover:bg-[#f8f7f5]">
                                            <td className="py-3 px-2 text-[#999] font-mono">{q.id}</td>
                                            <td className="py-3 px-2 text-[#444]">{q.query}</td>
                                            <td className="py-3 px-2 text-[#666]">{q.category}</td>
                                            <td className="py-3 px-2"><DifficultyBadge level={q.difficulty} /></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* Difficulty Distribution */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Why This Distribution?</h2>

                        <div className="space-y-4">
                            <div className="flex items-start gap-4">
                                <div className="w-16 text-right">
                                    <span className="text-2xl font-bold text-green-600">4</span>
                                    <span className="text-xs text-[#999] block">Easy</span>
                                </div>
                                <div className="flex-1">
                                    <div className="h-6 bg-green-100 rounded" style={{ width: '40%' }}></div>
                                    <p className="text-sm text-[#666] mt-1">
                                        Baseline sanity checks. If a model fails these, something is fundamentally wrong.
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-start gap-4">
                                <div className="w-16 text-right">
                                    <span className="text-2xl font-bold text-amber-600">4</span>
                                    <span className="text-xs text-[#999] block">Medium</span>
                                </div>
                                <div className="flex-1">
                                    <div className="h-6 bg-amber-100 rounded" style={{ width: '40%' }}></div>
                                    <p className="text-sm text-[#666] mt-1">
                                        Require synthesis of multiple sections. This is where model quality should show.
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-start gap-4">
                                <div className="w-16 text-right">
                                    <span className="text-2xl font-bold text-red-600">2</span>
                                    <span className="text-xs text-[#999] block">Hard</span>
                                </div>
                                <div className="flex-1">
                                    <div className="h-6 bg-red-100 rounded" style={{ width: '20%' }}></div>
                                    <p className="text-sm text-[#666] mt-1">
                                        Cross-company comparison, technical policy interpretation. Tests reasoning limits.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Accuracy Scoring */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">How We Measured Accuracy</h2>
                        <p className="text-[#444] leading-relaxed mb-4">
                            We used keyword matching, not subjective evaluation. Each query has expected
                            keywords that a correct answer must contain. <strong>These expected answers were
                                manually validated against the actual SEC filings</strong> before running any benchmarks.
                        </p>

                        <div className="bg-[#1a1a1a] text-green-400 p-5 rounded-xl font-mono text-sm mb-4">
                            <pre>{`accuracy = (keywords_found / total_keywords) × 100%

# Example: "Who is the CFO of Apple?"
expected = ["Kevan Parekh", "Chief Financial Officer", "CFO"]
answer   = "Kevan Parekh is the CFO of Apple"
found    = ["Kevan Parekh", "CFO"]
score    = 2/3 = 66.7%`}</pre>
                        </div>

                        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg mb-4">
                            <p className="text-[#191919] font-medium mb-2">Why keyword matching over LLM-as-judge?</p>
                            <ul className="text-sm text-[#666] space-y-1">
                                <li>• <strong>Reproducible</strong>: Same query, same expected output, deterministic score</li>
                                <li>• <strong>No model bias</strong>: An LLM judge might favor responses that sound like its own</li>
                                <li>• <strong>Fast</strong>: No extra inference call per evaluation</li>
                            </ul>
                        </div>

                        <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-r-lg">
                            <p className="text-[#191919] font-medium mb-2">Manual Validation Step</p>
                            <p className="text-sm text-[#666]">
                                Before trusting keyword matches, we manually verified that our expected keywords
                                were actually present in the source SEC filings. This ensures we're not penalizing
                                models for failing to hallucinate—only for failing to find real information.
                            </p>
                        </div>
                    </section>

                    {/* Company Selection */}
                    <section>
                        <h2 className="text-2xl font-semibold text-[#191919] mb-4">Company Selection</h2>
                        <p className="text-[#444] leading-relaxed mb-4">
                            We didn't just pick the biggest companies. We wanted variety in:
                        </p>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                            {[
                                { ticker: 'AAPL', name: 'Apple', sector: 'Consumer Tech' },
                                { ticker: 'MSFT', name: 'Microsoft', sector: 'Enterprise Tech' },
                                { ticker: 'AMZN', name: 'Amazon', sector: 'E-commerce/Cloud' },
                                { ticker: 'PFE', name: 'Pfizer', sector: 'Pharma' },
                                { ticker: 'HOOD', name: 'Robinhood', sector: 'Fintech' }
                            ].map(c => (
                                <div key={c.ticker} className="bg-white rounded-lg p-3 border border-[#e5e5e5] text-center">
                                    <div className="font-mono font-bold text-[#191919]">{c.ticker}</div>
                                    <div className="text-xs text-[#666]">{c.sector}</div>
                                </div>
                            ))}
                        </div>
                        <p className="text-sm text-[#666] mt-4">
                            Different industries have different 10-K structures and terminology.
                            A model that works for tech might struggle with pharma disclosure language.
                        </p>
                    </section>

                    {/* Navigation */}
                    <section className="pt-8 border-t border-[#e5e5e5]">
                        <div className="flex justify-between items-center">
                            <Link
                                to="/research/llm-benchmarking-intro"
                                className="inline-flex items-center gap-2 px-4 py-2 text-[#666] hover:text-[#191919] transition-colors"
                            >
                                <ArrowLeft size={16} />
                                Previous
                            </Link>
                            <Link
                                to="/research/llm-benchmarking-models"
                                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#1a1a1a] text-white rounded-lg hover:bg-[#333] transition-colors"
                            >
                                Next: Model Selection
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
