// Puns and knowledge content for rotating messages
// This is a simplified version - full content is in app/content/*.json

export const PUNS = [
  { category: 'pun', content: "Why do developers prefer dark mode? Light attracts bugs! 🐛" },
  { category: 'pun', content: "Why was the developer broke? They used up all their cache! 💸" },
  { category: 'pun', content: "How do you comfort a JavaScript bug? You console it! 🎮" },
  { category: 'pun', content: "Why did the CFO go to therapy? Too many issues to reconcile! 📊" },
  { category: 'pun', content: "What's a stock's favorite music? Heavy metal... markets! 📉" },
];

export const KNOWLEDGE = [
  { category: 'fact', content: "💡 Vector search can find relevant info in <1 second across millions of words" },
  { category: 'fact', content: "🧠 This system uses embeddings to understand meaning, not just keywords" },
  { category: 'fact', content: "📊 A typical 10-K filing contains 100,000+ words across 200+ pages" },
  { category: 'fact', content: "⚡ Streaming tokens reduces perceived latency by 90%" },
  { category: 'fact', content: "🎯 Metadata filtering reduces search space by 96%" },
  { category: 'fact', content: "🚀 Deterministic planning is 40% faster than LLM routing" },
];

export const STEP_INSIGHTS = {
  planning: {
    title: "Why deterministic planning?",
    content: "Using a structured planner saves ~2-3s per query and ensures consistent execution.",
    trade_off: "Less flexible than pure agent routing, but 40% faster and more predictable."
  },
  fetching: {
    title: "Fetching & Searching ✨",
    content: "Retrieves filing from local cache, embeds query, and performs semantic search to find relevant sections.",
    trade_off: "Local caching uses ~2GB disk but saves 80% on network calls. Vector search requires embedding model but finds relevant content even without exact keyword matches."
  },
  synthesis: {
    title: "Why synthesis takes longest",
    content: "LLM reads 10 document chunks (~10,000 words) and generates a grounded answer.",
    trade_off: "Could use smaller/faster model, but accuracy drops 15-20%."
  }
};

// Mix puns and knowledge 50/50
export function getRotatingMessages() {
  const mixed = [];
  const maxLength = Math.max(PUNS.length, KNOWLEDGE.length);
  
  for (let i = 0; i < maxLength; i++) {
    if (i < PUNS.length) mixed.push(PUNS[i]);
    if (i < KNOWLEDGE.length) mixed.push(KNOWLEDGE[i]);
  }
  
  // Shuffle for variety
  return mixed.sort(() => Math.random() - 0.5);
}
