import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ArrowRight,
    Zap,
    Clock,
    Layers,
    ChevronRight,
    ChevronLeft,
    Database,
    List,
    Search,
    Filter,
    Copy,
    Check,
    BookOpen,
    Home,
    Share2
} from 'lucide-react';

// --- Helper: Simple Markdown Renderer ---
const FormatText = ({ text }) => {
    if (!text) return null;

    // Split by ** for bold
    const parts = text.split(/(\*\*.*?\*\*)/g);

    return (
        <span>
            {parts.map((part, i) => {
                if (part.startsWith('**') && part.endsWith('**')) {
                    return <strong key={i} className="font-bold text-slate-900">{part.slice(2, -2)}</strong>;
                }
                return <span key={i}>{part}</span>;
            })}
        </span>
    );
};

// --- Data & Scenario Configuration ---

const SCENARIO = {
    systemPrompt: "You are a financial analysis assistant specializing in SEC filings.",
    userPrompt: "What was Apple's revenue in Q4 2023?",
    response: " Based on the 10-K filing, Apple reported total net sales of $383.3 billion in fiscal year 2023."
};

const STEPS = [
    {
        id: 'init',
        title: "System Initialization",
        subtitle: "Memory Pre-allocation (PagedAttention)",
        content: "vLLM starts by pre-allocating GPU memory into fixed-size 'blocks' (like pages in an operating system). This is revolutionary: instead of requiring one giant continuous chunk of memory, vLLM can scatter these blocks anywhere in GPU RAM.\n\nThink of it like a hotel: traditional systems need all guests in consecutive rooms. vLLM can place guests in rooms 101, 203, and 405—whatever's available!",
        tech: "PagedAttention",
        metrics: { latency: 0, memory: 0 },
        visual: { mode: 'memory', showMemory: true },
        codeExample: `from vllm import LLM

# Initialize vLLM with PagedAttention
llm = LLM(
    model="llama-3.1-8b",
    gpu_memory_utilization=0.9  # Use 90% of GPU
)

# Source: https://docs.vllm.ai/en/latest/models/engine_args.html`,
        easyExplanation: "🏨 Hotel Analogy: vLLM books rooms ahead of time, but doesn't require them to be next to each other."
    },
    {
        id: 'input',
        title: "User Request Arrives",
        subtitle: "API Handling & Queue Entry",
        content: "A user sends their question. Behind the scenes, there are TWO prompts:\n\n1. **System Prompt** (hidden from user): \"You are a financial assistant...\"\n2. **User Prompt** (visible): \"What was Apple's revenue?\"\n\nThe request enters the Scheduler's Waiting Queue.",
        tech: "Request Queuing",
        metrics: { latency: 5, memory: 0 },
        visual: { mode: 'queue', showMemory: true, showQueue: true, showUser: true, queueState: 'waiting' },
        easyExplanation: "🎫 DMV Analogy: You take a number and wait in line."
    },
    {
        id: 'prefix_check',
        title: "Prefix Caching Lookup",
        subtitle: "Smart Optimization",
        content: "vLLM computes a 'hash' of your SystemPrompt and checks: 'Have I seen this before?'\n\nIf YES: vLLM reuses the cached Key/Value vectors instead of re-computing!\n\nThis is **Prefix Caching** and it can reduce Time-To-First-Token (TTFT) by 80%!",
        tech: "Prefix Caching",
        highlight: "For chatbots with fixed system prompts, this is a game-changer. The first user pays the cost, every subsequent user gets instant cache hits!",
        metrics: { latency: 10, memory: 15 },
        visual: { mode: 'memory', showMemory: true, showQueue: true, showUser: true, highlightShared: true },
        codeExample: `from vllm import LLM

llm = LLM(
    model="llama-3.1-8b",
    enable_prefix_caching=True  # 🚀 Enable prefix caching
)

# First request: Computes full KV cache
# Subsequent requests: Reuses cached system prompt

# Source: https://docs.vllm.ai/en/latest/automatic_prefix_caching/apc.html`,
        easyExplanation: "♻️ Recycling: Why re-manufacture when you can reuse?"
    },
    {
        id: 'scheduling',
        title: "Scheduler & Memory Allocation",
        subtitle: "Block Manager Magic",
        content: "The scheduler moves your request from WAITING → RUNNING queue.\n\nNext, it allocates NEW memory blocks for your User Prompt. Notice: these blocks are NOT next to the System Prompt blocks!\n\nPagedAttention handles this non-contiguous mapping automatically.",
        tech: "Scheduling & Allocation",
        metrics: { latency: 15, memory: 30 },
        visual: { mode: 'memory', showMemory: true, showQueue: true, showUser: true, allocatePrompt: true, queueState: 'running' },
        easyExplanation: "🧩 Puzzle: vLLM can scatter pieces and still solve it perfectly."
    },
    {
        id: 'prefill',
        title: "Prefill: Computing Keys & Values",
        subtitle: "The 'KV' in KV Cache",
        content: "The GPU processes your User Prompt token-by-token. For EVERY token, it computes:\n\n**Key (K):** A 'label' describing the token\n**Value (V):** The actual semantic meaning\n\nWhy cache? Computing them is expensive!",
        tech: "KV Cache Computation",
        highlight: "This step is unavoidable and computationally expensive. That's why prefix caching (reusing cached K/Vs) is so valuable!",
        metrics: { latency: 45, memory: 30 },
        visual: { mode: 'memory', showMemory: true, showQueue: true, showUser: true, processing: 'prompt' },
        codeExample: `# Simplified pseudocode of what happens internally
for token in user_prompt_tokens:
    # Run neural network forward pass
    key_vector = model.compute_key(token)    # Expensive!
    value_vector = model.compute_value(token) # Expensive!
    
    # Store in GPU memory blocks
    kv_cache.store(key_vector, value_vector)
    
# This is why caching matters - avoid recomputing K/V!`,
        easyExplanation: "📚 Library: Create catalog cards (Keys) and store books (Values)."
    },
    {
        id: 'decode_start',
        title: "Decoding: Attention Mechanism",
        subtitle: "Query (Q) meets Key (K)",
        content: "To generate the FIRST token, the model performs **Self-Attention**:\n\n1. **Generate Query (Q):** 'What info do I need?'\n2. **Compare Q against ALL Keys:** Like searching catalog\n3. **Calculate Scores:** Q · K (dot product)\n4. **Softmax:** Convert to probabilities\n5. **Weighted Sum:** Context = Σ(prob × Value)\n\n**Why long context is expensive:** Query must scan EVERY cached Key!",
        tech: "Attention (Q × K → V)",
        highlight: "Attention complexity is O(n²). Doubling context = 4x computation!",
        metrics: { latency: 60, memory: 32 },
        visual: { mode: 'memory', showMemory: true, showQueue: true, showUser: true, processing: 'token', tokenCount: 1, showAttention: true },
        codeExample: `# Simplified attention mechanism
import torch

def attention(query, keys, values):
    # 1. Compute attention scores
    scores = torch.matmul(query, keys.transpose(-2, -1))
    scores = scores / torch.sqrt(torch.tensor(keys.shape[-1]))
    
    # 2. Apply softmax to get probabilities
    weights = torch.softmax(scores, dim=-1)
    
    # 3. Weighted sum of values
    context = torch.matmul(weights, values)
    return context

# Source: "Attention Is All You Need" paper (Vaswani et al., 2017)`,
        easyExplanation: "🔍 Search: Query searches catalog (Keys) to find books (Values)."
    },
    {
        id: 'sampling',
        title: "Logits & Sampling Strategy",
        subtitle: "Picking the Next Word",
        content: "The Context Vector produces **Logits**—scores for EVERY word in vocabulary (50,000+ words!).\n\nSampling parameters:\n\n**Temperature:** Low (0.1) = deterministic, High (1.5) = creative\n**Top-P:** Consider top 90% probable words\n**Top-K:** Pick from top 50 candidates",
        tech: "Sampling",
        metrics: { latency: 65, memory: 32 },
        visual: { mode: 'sampling', showMemory: true, showQueue: true, showUser: true, processing: 'token' },
        codeExample: `from vllm import SamplingParams

# Create sampling parameters
sampling_params = SamplingParams(
    temperature=0.1,      # Low = factual answers
    top_p=0.9,           # Nucleus sampling
    top_k=50,            # Limit candidates
    max_tokens=500       # Stop after 500 tokens
)

# Generate text
outputs = llm.generate(prompts, sampling_params)

# Source: https://docs.vllm.ai/en/latest/dev/sampling_params.html`,
        easyExplanation: "🎲 Temperature controls how 'creative' vs 'predictable' the output is."
    },
    {
        id: 'continuous_batching',
        title: "Continuous Batching",
        subtitle: "Throughput Optimization",
        content: "**Traditional systems:**\n- Process Request A completely (30s)\n- Then Request B (30s)\n- Average wait: 45s\n\n**vLLM with Continuous Batching:**\n- All requests run in PARALLEL\n- Generate 1 token for A, B, C, repeat\n- Average wait: ~12s (3x improvement!)\n\nRequests can join the batch IMMEDIATELY—no waiting!",
        tech: "Continuous Batching",
        metrics: { latency: 70, memory: 32 },
        visual: { mode: 'memory', showMemory: true, showQueue: true, showUser: true, processing: 'paused', showBatchingHint: true, tokenCount: 1, showAttention: true },
        codeExample: `# vLLM handles continuous batching automatically
# No configuration needed!

# Request A arrives → starts generating
# Request B arrives → joins batch immediately  
# Request C arrives → joins batch immediately
# All generate in parallel

# This is the default behavior in vLLM
# Source: https://blog.vllm.ai/2023/06/20/vllm.html`,
        easyExplanation: "🍳 Chef uses multiple pans to cook pancakes simultaneously!"
    },
    {
        id: 'decode_rest',
        title: "Streaming Response",
        subtitle: "Auto-Regressive Generation",
        content: "Generating tokens one-by-one in a loop:\n\n1. Generate new Query (Q)\n2. Run attention over ALL Keys\n3. Sample next token\n4. Create new K/V pair\n5. Append to cache\n6. Stream to user\n7. Repeat until done",
        tech: "Streaming",
        metrics: { latency: 120, memory: 60 },
        visual: { mode: 'memory', showMemory: true, showQueue: true, showUser: true, processing: 'stream', autoType: true, showAttention: true },
        codeExample: `# Streaming output example
async for output in llm.generate(prompt, sampling_params, stream=True):
    if output.outputs:
        text = output.outputs[0].text
        print(text, end='', flush=True)
        # User sees: "Based" then " on" then " the"...

# vs non-streaming:
output = llm.generate(prompt, sampling_params)
print(output[0].outputs[0].text)  # Wait 30s, then see full answer

# Source: https://docs.vllm.ai/en/latest/serving/openai_compatible_server.html`,
        easyExplanation: "🎬 Like Netflix streaming vs downloading entire movie first."
    },
    {
        id: 'finish',
        title: "Request Completed",
        subtitle: "Garbage Collection",
        content: "Model generates stop token. Time to clean up!\n\n**Freed:**\n- User Prompt blocks\n- Response blocks\n\n**Kept cached:**\n- System Prompt blocks (for next request!)\n\nMemory efficiency: First request pays cost, subsequent requests are instant.",
        tech: "Cleanup",
        metrics: { latency: 125, memory: 15 },
        visual: { mode: 'memory', showMemory: true, showQueue: true, showUser: true, gc: true },
        codeExample: `# vLLM automatic memory management
# - Old blocks: Freed for next request
# - Shared prefix: Kept in cache
# - No manual management needed!

# Monitor cache statistics:
from vllm import LLM

llm = LLM(model="llama-3.1-8b", enable_prefix_caching=True)
# Cache hit rates logged automatically

# Source: https://docs.vllm.ai/en/latest/features/automatic_prefix_caching.html`,
        easyExplanation: "🧹 Throw away disposable plates, keep reusable silverware."
    }
];

// Performance comparison data
const COMPARISON_DATA = [
    { feature: "Memory Management", naive: "Contiguous (60% waste)", vllm: "Paged (90% utilization)" },
    { feature: "Batching", naive: "Static (wait for batch)", vllm: "Continuous (join anytime)" },
    { feature: "Throughput (vs HF)", naive: "1x (Baseline)", vllm: "Up to 24x higher" },
    { feature: "Throughput (vs TGI)", naive: "1x (Baseline)", vllm: "Up to 3.5x higher" },
    { feature: "TTFT (cached)", naive: "100ms", vllm: "5ms (20x faster)" }
];

// Visual Components
const SamplingVisual = () => (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-4 h-full justify-center">
        <h4 className="text-xs font-bold text-slate-500 uppercase flex items-center gap-2 mb-2">
            <Filter size={14} /> Logit Sampling Pipeline
        </h4>
        <div className="flex flex-col md:flex-row items-center gap-4 w-full">
            <div className="flex-1 bg-slate-50 border border-slate-200 rounded p-3 flex flex-col items-center gap-2 w-full">
                <span className="text-xs text-slate-400 font-mono">Raw Logits</span>
                <div className="w-full h-20 flex items-end justify-center gap-1">
                    {[20, 45, 10, 80, 30, 15].map((h, i) => (
                        <div key={i} className="bg-slate-300 w-4 md:w-3 rounded-t" style={{ height: `${h}%` }}></div>
                    ))}
                </div>
            </div>
            <ArrowRight size={20} className="text-slate-300 hidden md:block rotate-90 md:rotate-0" />
            <div className="flex-1 bg-indigo-50 border border-indigo-200 rounded p-3 flex flex-col items-center gap-2 w-full">
                <span className="text-xs text-indigo-400 font-mono">Apply Params</span>
                <div className="text-xs font-mono text-indigo-700 flex flex-col gap-1 bg-white/50 p-2 rounded w-full">
                    <div className="flex justify-between"><span>temp:</span><span>0.1</span></div>
                    <div className="flex justify-between"><span>top_p:</span><span>0.9</span></div>
                </div>
            </div>
            <ArrowRight size={20} className="text-slate-300 hidden md:block rotate-90 md:rotate-0" />
            <div className="flex-1 bg-emerald-50 border border-emerald-200 rounded p-3 flex flex-col items-center justify-center gap-2 w-full">
                <span className="text-xs text-emerald-400 font-mono">Selected</span>
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="bg-emerald-500 text-white font-bold text-lg w-14 h-14 rounded flex items-center justify-center shadow-lg"
                >
                    "B"
                </motion.div>
            </div>
        </div>
    </div>
);

const MemoryGrid = ({ visualState }) => {
    const getBlockStatus = (i) => {
        if (i === 0 || i === 1) {
            if (visualState.highlightShared || visualState.allocatePrompt || visualState.processing || visualState.gc) return 'shared';
            return 'empty';
        }
        if (i === 4 || i === 5) {
            if (visualState.allocatePrompt || visualState.processing || visualState.gc === false) return 'prompt';
            return 'empty';
        }
        if (i === 6 || i === 7 || i === 2) {
            if (visualState.tokenCount > 0 && i === 6) return 'response';
            if (visualState.tokenCount > 5 && i === 2) return 'response';
            if (visualState.tokenCount > 10 && i === 7) return 'response';
            return 'empty';
        }
        return 'empty';
    };

    const getLabel = (i, status) => {
        if (status === 'shared') return 'SYS';
        if (status === 'prompt') return 'USR';
        if (status === 'response') return 'GEN';
        return `${i}`;
    }

    const blocks = Array.from({ length: 16 }, (_, i) => {
        const status = getBlockStatus(i);
        let color = "bg-slate-100 border-slate-200 text-slate-300";
        let glow = "";

        if (status === 'shared') color = "bg-indigo-100 border-indigo-500 text-indigo-700";
        if (status === 'prompt') color = "bg-blue-100 border-blue-500 text-blue-700";
        if (status === 'response') color = "bg-emerald-100 border-emerald-500 text-emerald-700";

        if (visualState.showAttention && status !== 'empty') {
            glow = "ring-2 ring-amber-400 ring-offset-1";
        }

        return (
            <motion.div
                key={i}
                layout
                initial={false}
                animate={{
                    scale: status !== 'empty' ? 1 : 0.95,
                    borderColor: (visualState.showAttention && status !== 'empty') ? '#fbbf24' : undefined
                }}
                className={`h-12 md:h-10 rounded-md border-2 flex items-center justify-center text-xs md:text-[10px] font-bold font-mono transition-all duration-300 ${color} ${glow}`}
            >
                {getLabel(i, status)}
            </motion.div>
        );
    });

    return (
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm relative">
            <div className="flex justify-between items-center mb-3">
                <h4 className="text-xs font-bold text-slate-500 uppercase flex items-center gap-2">
                    <Database size={12} /> GPU Memory (KV Cache)
                </h4>
                <div className="flex gap-2 text-[10px]">
                    <span className="flex items-center gap-1"><div className="w-2 h-2 bg-indigo-500 rounded-full"></div> Shared</span>
                    <span className="flex items-center gap-1"><div className="w-2 h-2 bg-blue-500 rounded-full"></div> User</span>
                    <span className="flex items-center gap-1"><div className="w-2 h-2 bg-emerald-500 rounded-full"></div> Gen</span>
                </div>
            </div>
            <div className="grid grid-cols-4 gap-2 relative z-0">
                {blocks}
            </div>
            <AnimatePresence>
                {visualState.showAttention && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 bg-amber-500 text-white px-3 py-2 rounded-full shadow-xl flex items-center gap-2 border-2 border-white text-xs"
                    >
                        <Search size={14} className="animate-pulse" />
                        <span className="font-bold whitespace-nowrap">Query Scanning...</span>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

const QueueVisual = ({ state, batchingHint }) => (
    <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <h4 className="text-xs font-bold text-slate-500 uppercase flex items-center gap-2 mb-4">
            <List size={12} /> Scheduler Queue
        </h4>
        <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 p-3 bg-slate-50 rounded border border-slate-100 min-h-[60px]">
                <div className="text-[10px] text-slate-400 mb-1 text-center">WAITING</div>
                {state === 'waiting' && (
                    <motion.div layoutId="req-card" className="bg-white border-l-4 border-slate-400 shadow-sm p-2 rounded text-[10px] font-mono">
                        REQ-001
                    </motion.div>
                )}
            </div>
            <div className="flex items-center justify-center text-slate-300">
                <ArrowRight size={16} className="rotate-90 md:rotate-0" />
            </div>
            <div className={`flex-1 p-3 rounded border min-h-[60px] transition-colors ${batchingHint ? 'bg-emerald-50 border-emerald-200' : 'bg-slate-50 border-slate-100'}`}>
                <div className="text-[10px] text-slate-400 mb-1 text-center">RUNNING</div>
                {state === 'running' && (
                    <motion.div layoutId="req-card" className="bg-white border-l-4 border-indigo-500 shadow-sm p-2 rounded text-[10px] font-mono flex justify-between items-center">
                        <span>REQ-001</span>
                        <div className="animate-spin w-2 h-2 border-2 border-indigo-500 border-t-transparent rounded-full"></div>
                    </motion.div>
                )}
                {batchingHint && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 0.5, y: 0 }}
                        className="mt-1 border-2 border-dashed border-emerald-400 bg-emerald-50/50 p-2 rounded text-[10px] text-emerald-600 font-mono text-center"
                    >
                        + OPEN SLOT
                    </motion.div>
                )}
            </div>
        </div>
    </div>
);

export default function VLLMDeepDive() {
    const [currentStepIdx, setCurrentStepIdx] = useState(0);
    const [displayedResponse, setDisplayedResponse] = useState("");
    const [showCode, setShowCode] = useState(false);
    const [copied, setCopied] = useState(false);

    const step = STEPS[currentStepIdx];

    const visualState = {
        ...step.visual,
        tokenCount: step.id === 'decode_rest' ? displayedResponse.length : (step.id === 'decode_start' || step.id === 'continuous_batching') ? 1 : 0
    };

    useEffect(() => {
        if (step.id === 'decode_rest') {
            let i = 1;
            const interval = setInterval(() => {
                if (i <= SCENARIO.response.length) {
                    setDisplayedResponse(SCENARIO.response.substring(0, i));
                    i++;
                } else {
                    clearInterval(interval);
                }
            }, 50);
            return () => clearInterval(interval);
        } else if (step.id === 'decode_start' || step.id === 'continuous_batching' || step.id === 'sampling') {
            setDisplayedResponse(SCENARIO.response.substring(0, 1));
        } else if (step.id === 'finish') {
            setDisplayedResponse(SCENARIO.response);
        } else {
            setDisplayedResponse("");
        }
    }, [step.id]);

    const nextStep = () => {
        if (currentStepIdx < STEPS.length - 1) setCurrentStepIdx(p => p + 1);
    };

    const prevStep = () => {
        if (currentStepIdx > 0) setCurrentStepIdx(p => p - 1);
    };

    const handleShare = async () => {
        const shareData = {
            title: `vLLM Deep Dive - ${step.title}`,
            text: step.content.substring(0, 100) + "...",
            url: window.location.href + "#step-" + step.id
        };

        if (navigator.share) {
            try {
                await navigator.share(shareData);
            } catch (err) {
                console.log('Share cancelled or failed');
            }
        } else {
            navigator.clipboard.writeText(window.location.href + "#step-" + step.id);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const copyCode = () => {
        if (step.codeExample) {
            navigator.clipboard.writeText(step.codeExample);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 text-slate-800 font-sans selection:bg-indigo-100 flex flex-col">
            <Helmet>
                <title>vLLM Request Lifecycle - Interactive Deep Dive</title>
                <meta name="description" content="Interactive visualization of how vLLM optimizes Large Language Model serving with PagedAttention, Continuous Batching, and Prefix Caching." />
                <meta property="og:title" content="vLLM Request Lifecycle - Interactive Deep Dive" />
                <meta property="og:description" content="Explore how vLLM achieves 24x higher throughput than HuggingFace. Interactive visualization of PagedAttention and memory management." />
                <meta property="og:type" content="article" />
                <meta name="twitter:card" content="summary_large_image" />
                <meta name="twitter:title" content="vLLM Request Lifecycle - Interactive Deep Dive" />
                <meta name="twitter:description" content="Explore how vLLM achieves 24x higher throughput than HuggingFace. Interactive visualization of PagedAttention and memory management." />
            </Helmet>

            {/* Top Bar */}
            <header className="bg-white border-b border-slate-200 px-4 md:px-6 py-4 sticky top-0 z-20">
                <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
                    <div className="flex items-center gap-3">
                        <div className="bg-indigo-600 text-white p-2 rounded-lg">
                            <Zap size={20} fill="currentColor" />
                        </div>
                        <div>
                            <h1 className="font-bold text-xl text-slate-900">vLLM Request Lifecycle</h1>
                            <p className="text-xs text-slate-500">Step {currentStepIdx + 1} of {STEPS.length}</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <Link
                            to="/"
                            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-600 hover:bg-slate-700 text-white transition-colors text-sm mr-2"
                        >
                            <Home size={16} />
                            <span className="hidden sm:inline">Home</span>
                        </Link>

                        <button
                            onClick={handleShare}
                            className="p-2 rounded-full hover:bg-slate-100 transition-colors text-slate-600 mr-2"
                            title="Share this step"
                        >
                            {copied ? <Check size={20} className="text-green-600" /> : <Share2 size={20} />}
                        </button>

                        <button
                            onClick={prevStep}
                            disabled={currentStepIdx === 0}
                            className="p-2 rounded-full hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                        >
                            <ChevronLeft size={24} />
                        </button>

                        <div className="flex gap-1">
                            {STEPS.map((_, idx) => (
                                <div
                                    key={idx}
                                    className={`w-2 h-2 rounded-full transition-colors duration-300 cursor-pointer ${idx === currentStepIdx ? 'bg-indigo-600' : idx < currentStepIdx ? 'bg-indigo-200' : 'bg-slate-200'}`}
                                    onClick={() => setCurrentStepIdx(idx)}
                                />
                            ))}
                        </div>

                        <button
                            onClick={nextStep}
                            disabled={currentStepIdx === STEPS.length - 1}
                            className="p-2 rounded-full bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-30 disabled:cursor-not-allowed shadow-lg shadow-indigo-200 transition-all hover:scale-105 ml-2"
                        >
                            <ChevronRight size={24} />
                        </button>
                    </div>
                </div>
            </header>

            <main className="flex-1 max-w-6xl mx-auto w-full p-4 md:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 md:gap-8">

                {/* LEFT PANEL */}
                <div className="lg:col-span-4 flex flex-col gap-6">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={step.id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 10 }}
                            className="flex flex-col gap-4"
                        >
                            <div className="inline-block self-start px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold border border-indigo-100">
                                {step.tech}
                            </div>
                            <div>
                                <h2 className="text-2xl md:text-3xl font-bold text-slate-900 mb-1">{step.title}</h2>
                                <h3 className="text-base md:text-lg text-indigo-600 font-medium">{step.subtitle}</h3>
                            </div>
                            <p className="text-slate-600 leading-relaxed whitespace-pre-line text-sm md:text-base">
                                <FormatText text={step.content} />
                            </p>

                            {step.highlight && (
                                <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-lg">
                                    <p className="text-sm text-amber-900 font-medium italic">
                                        💡 <FormatText text={step.highlight} />
                                    </p>
                                </div>
                            )}

                            {step.easyExplanation && (
                                <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-r-lg">
                                    <p className="text-sm text-blue-900 font-medium">
                                        <FormatText text={step.easyExplanation} />
                                    </p>
                                </div>
                            )}

                            {/* Code Example */}
                            {step.codeExample && (
                                <div className="mt-2 w-full">
                                    <button
                                        onClick={() => setShowCode(!showCode)}
                                        className="flex items-center gap-2 text-sm text-indigo-600 hover:text-indigo-700 font-medium mb-2"
                                    >
                                        <BookOpen size={16} />
                                        {showCode ? 'Hide' : 'Show'} Code Example
                                    </button>

                                    <AnimatePresence>
                                        {showCode && (
                                            <motion.div
                                                initial={{ opacity: 0, height: 0 }}
                                                animate={{ opacity: 1, height: 'auto' }}
                                                exit={{ opacity: 0, height: 0 }}
                                                className="relative w-full"
                                            >
                                                <div className="bg-slate-900 rounded-lg w-full overflow-hidden">
                                                    <div className="flex justify-between items-center px-4 py-2 bg-slate-800 border-b border-slate-700">
                                                        <span className="text-xs text-slate-400 font-mono">python</span>
                                                        <button
                                                            onClick={copyCode}
                                                            className="text-slate-400 hover:text-white transition-colors"
                                                            title="Copy code"
                                                        >
                                                            {copied ? <Check size={14} /> : <Copy size={14} />}
                                                        </button>
                                                    </div>
                                                    <pre className="p-4 text-green-400 text-xs md:text-sm overflow-x-auto whitespace-pre w-full">
                                                        <code>{step.codeExample}</code>
                                                    </pre>
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>
                            )}
                        </motion.div>
                    </AnimatePresence>

                    {/* Metrics */}
                    <div className="mt-auto bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
                        <h4 className="text-xs font-bold text-slate-400 uppercase mb-4">Simulated Metrics</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
                                    <Clock size={14} /> Latency
                                </div>
                                <div className="text-xl font-mono font-bold text-slate-800">{step.metrics.latency}ms</div>
                            </div>
                            <div>
                                <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
                                    <Layers size={14} /> VRAM
                                </div>
                                <div className="text-xl font-mono font-bold text-slate-800">{step.metrics.memory}%</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* RIGHT PANEL */}
                <div className="lg:col-span-8 flex flex-col gap-6">

                    {/* User View */}
                    <div className="bg-slate-900 rounded-2xl p-6 min-h-[200px] relative overflow-hidden flex flex-col justify-end shadow-xl">
                        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(#6366f1 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

                        <div className="relative z-10 space-y-4">
                            {step.visual.highlightShared && (
                                <motion.div
                                    initial={{ opacity: 0, y: -10 }} animate={{ opacity: 0.6, y: 0 }}
                                    className="flex items-center gap-2 text-xs text-indigo-300 bg-indigo-900/50 p-2 rounded w-fit"
                                >
                                    <Database size={12} /> System: "{SCENARIO.systemPrompt}" (Cached)
                                </motion.div>
                            )}

                            <AnimatePresence>
                                {step.visual.showUser && (
                                    <motion.div
                                        initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
                                        className="bg-slate-800 border border-slate-700 p-3 rounded-xl rounded-tl-none text-slate-200 max-w-[90%] md:max-w-[80%]"
                                    >
                                        <span className="text-xs text-slate-500 block mb-1">User</span>
                                        {SCENARIO.userPrompt}
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            <AnimatePresence>
                                {displayedResponse && (
                                    <motion.div
                                        initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
                                        className="bg-emerald-900/20 border border-emerald-500/30 p-3 rounded-xl rounded-tr-none text-emerald-100 self-end ml-auto max-w-[90%] md:max-w-[80%]"
                                    >
                                        <span className="text-xs text-emerald-500 block mb-1">Assistant</span>
                                        {displayedResponse}
                                        {step.id === 'decode_rest' && <span className="inline-block w-2 h-4 bg-emerald-500 ml-1 animate-pulse" />}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </div>

                    {/* Internals */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {step.visual.mode === 'sampling' ? (
                            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="md:col-span-2">
                                <SamplingVisual />
                            </motion.div>
                        ) : (
                            <>
                                {step.visual.showQueue && (
                                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                        <QueueVisual state={step.visual.queueState} batchingHint={step.visual.showBatchingHint} />
                                    </motion.div>
                                )}
                                {step.visual.showMemory && (
                                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                        <MemoryGrid visualState={visualState} />
                                    </motion.div>
                                )}
                            </>
                        )}
                    </div>

                    {/* Performance Table */}
                    {currentStepIdx === STEPS.length - 1 && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm"
                        >
                            <h3 className="text-lg font-bold mb-4">Performance: Naive vs vLLM</h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-slate-200">
                                            <th className="text-left py-2 px-3 font-bold text-slate-700">Feature</th>
                                            <th className="text-left py-2 px-3 font-bold text-red-600">Naive</th>
                                            <th className="text-left py-2 px-3 font-bold text-green-600">vLLM</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {COMPARISON_DATA.map((row, idx) => (
                                            <tr key={idx} className="border-b border-slate-100">
                                                <td className="py-2 px-3 font-medium">{row.feature}</td>
                                                <td className="py-2 px-3 text-slate-600">{row.naive}</td>
                                                <td className="py-2 px-3 text-slate-600 font-semibold">{row.vllm}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            <div className="mt-4 text-xs text-slate-500">
                                <p className="font-bold mb-2">Sources:</p>
                                <ul className="list-disc list-inside space-y-1">
                                    <li>vLLM Blog: <a href="https://blog.vllm.ai/2023/06/20/vllm.html" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention</a> (24x vs HF, 3.5x vs TGI)</li>
                                    <li>Paper: "Efficient Memory Management for Large Language Model Serving with PagedAttention" (Kwon et al., 2023)</li>
                                </ul>
                            </div>
                        </motion.div>
                    )}

                </div>
            </main>
        </div>
    );
}
