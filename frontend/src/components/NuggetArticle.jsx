import React, { useState } from 'react';
import { Link, useParams, Navigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion } from 'framer-motion';
import {
    ArrowLeft,
    Check,
    Copy,
    Twitter
} from 'lucide-react';
import { NUGGETS } from './KnowledgeHub';

export default function NuggetArticle() {
    const { id } = useParams();
    const [copied, setCopied] = useState(false);
    const [codeCopied, setCodeCopied] = useState(false);

    const nugget = NUGGETS.find(n => n.id === id);

    if (!nugget) {
        return <Navigate to="/research" replace />;
    }

    const handleShareOnX = () => {
        const tweetText = encodeURIComponent(
            `${nugget.title}\n\n${nugget.lesson.substring(0, 180)}...\n\nRead more:`
        );
        const tweetUrl = encodeURIComponent(window.location.href);
        window.open(
            `https://twitter.com/intent/tweet?text=${tweetText}&url=${tweetUrl}`,
            '_blank',
            'noopener,noreferrer,width=600,height=400'
        );
    };

    const handleCopyLink = () => {
        navigator.clipboard.writeText(window.location.href);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleCopyCode = () => {
        navigator.clipboard.writeText(nugget.codeExample);
        setCodeCopied(true);
        setTimeout(() => setCodeCopied(false), 2000);
    };

    return (
        <div className="min-h-screen bg-[#fdfcfb]" style={{ fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" }}>
            <Helmet>
                <title>{nugget.title} | Research - 10kiq</title>
                <meta name="description" content={`${nugget.problem} Learn how we solved this and the impact it had.`} />
                <meta property="og:title" content={`${nugget.title} | Research`} />
                <meta property="og:description" content={nugget.problem} />
                <meta property="og:type" content="article" />
                <meta property="og:site_name" content="10kiq" />
                <meta name="twitter:card" content="summary_large_image" />
                <meta name="twitter:title" content={nugget.title} />
                <meta name="twitter:description" content={nugget.problem} />
                <meta name="article:published_time" content={nugget.date} />
                <meta name="author" content="10kiq" />
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
            </Helmet>

            {/* Top Navigation */}
            <nav className="border-b border-[#e5e5e5]">
                <div className="max-w-4xl mx-auto px-6">
                    <div className="flex items-center justify-between h-16">
                        <Link to="/" className="text-xl font-semibold text-[#191919]">
                            10kiq
                        </Link>
                        <div className="flex items-center gap-8">
                            <Link to="/research" className="text-[#191919] font-medium">Research</Link>
                            <Link to="/" className="text-[#666] hover:text-[#191919] transition-colors">
                                Home
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            {/* Article */}
            <article className="max-w-4xl mx-auto px-6 py-12">
                {/* Back Link */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                >
                    <Link
                        to="/research"
                        className="inline-flex items-center gap-2 text-[#666] hover:text-[#191919] transition-colors mb-12 text-sm"
                    >
                        <ArrowLeft size={16} />
                        Research
                    </Link>
                </motion.div>

                {/* Header */}
                <motion.header
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-12"
                >
                    <div className="flex items-baseline gap-3 mb-6 text-sm">
                        <span className="text-[#d4a574] font-medium">{nugget.category}</span>
                        <span className="text-[#999]">·</span>
                        <span className="text-[#999]">{nugget.date}</span>
                        <span className="text-[#999]">·</span>
                        <span className="text-[#999]">{nugget.readTime} read</span>
                    </div>
                    <h1 className="font-['Times_New_Roman',_'Georgia',_serif] text-4xl lg:text-5xl text-[#191919] leading-tight">
                        {nugget.title}
                    </h1>
                </motion.header>

                {/* Content */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="space-y-12"
                >
                    {/* Problem */}
                    <section>
                        <h2 className="text-sm font-semibold text-[#d4a574] uppercase tracking-wider mb-4">
                            The Problem
                        </h2>
                        <p className="text-lg text-[#444] leading-relaxed">
                            {nugget.problem}
                        </p>
                    </section>

                    {/* Solution */}
                    <section>
                        <h2 className="text-sm font-semibold text-[#d4a574] uppercase tracking-wider mb-4">
                            The Solution
                        </h2>
                        <p className="text-lg text-[#444] leading-relaxed">
                            {nugget.solution}
                        </p>
                    </section>

                    {/* Impact */}
                    <section>
                        <h2 className="text-sm font-semibold text-[#d4a574] uppercase tracking-wider mb-4">
                            The Impact
                        </h2>
                        <p className="text-lg text-[#444] leading-relaxed">
                            {nugget.impact}
                        </p>
                    </section>

                    {/* Key Takeaway */}
                    {nugget.lesson && (
                        <section className="bg-[#f5f3ef] border-l-4 border-[#d4a574] p-8">
                            <h2 className="text-sm font-semibold text-[#191919] uppercase tracking-wider mb-4">
                                Key Takeaway
                            </h2>
                            <p className="text-lg text-[#444] leading-relaxed">
                                {nugget.lesson}
                            </p>
                        </section>
                    )}

                    {/* Code Example */}
                    {nugget.codeExample && (
                        <section>
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-sm font-semibold text-[#666] uppercase tracking-wider">
                                    Code Example
                                </h2>
                                <button
                                    onClick={handleCopyCode}
                                    className="text-sm text-[#666] hover:text-[#191919] transition-colors flex items-center gap-2"
                                >
                                    {codeCopied ? <Check size={14} className="text-green-600" /> : <Copy size={14} />}
                                    {codeCopied ? 'Copied' : 'Copy code'}
                                </button>
                            </div>
                            <div className="bg-[#1a1a1a] rounded-lg overflow-hidden">
                                <pre className="p-6 text-sm text-[#e5e5e5] overflow-x-auto leading-relaxed">
                                    <code>{nugget.codeExample}</code>
                                </pre>
                            </div>
                        </section>
                    )}
                </motion.div>

                {/* Share Actions */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="mt-16 pt-8 border-t border-[#e5e5e5]"
                >
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                        <Link
                            to="/research"
                            className="text-[#666] hover:text-[#191919] transition-colors flex items-center gap-2"
                        >
                            <ArrowLeft size={18} />
                            More research
                        </Link>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={handleCopyLink}
                                className="px-4 py-2 text-sm text-[#666] hover:text-[#191919] border border-[#e5e5e5] rounded hover:border-[#ccc] transition-colors flex items-center gap-2"
                            >
                                {copied ? <Check size={16} className="text-green-600" /> : <Copy size={16} />}
                                {copied ? 'Copied!' : 'Copy link'}
                            </button>
                            <button
                                onClick={handleShareOnX}
                                className="px-4 py-2 text-sm text-white bg-[#191919] hover:bg-[#333] rounded transition-colors flex items-center gap-2"
                            >
                                <Twitter size={16} />
                                Share on X
                            </button>
                        </div>
                    </div>
                </motion.div>
            </article>

            {/* Footer */}
            <footer className="border-t border-[#e5e5e5] mt-16">
                <div className="max-w-4xl mx-auto px-6 py-12 text-center text-sm text-[#999]">
                    <p>Found this helpful? Share it with someone who might benefit.</p>
                </div>
            </footer>
        </div>
    );
}
