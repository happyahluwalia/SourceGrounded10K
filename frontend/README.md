# Finance Agent UI

A modern, ChatGPT-like interface for the Finance Agent RAG system.

## Features

- 🎨 **Modern UI**: Clean, responsive design with dark mode support
- 💬 **Chat Interface**: Natural conversation flow similar to ChatGPT/Claude
- 🔍 **Debug Panel**: Toggle-able panel showing RAG pipeline logs in real-time
- 📊 **Source Citations**: View the exact chunks used to generate answers
- ⚡ **Real-time Updates**: See processing time and number of sources used
- 🎯 **Ticker-based Queries**: Easy ticker selection for company-specific questions

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Finance Agent API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start development server
npm run dev
```

The UI will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

## Usage

1. **Enter a ticker symbol** (e.g., AAPL, TSLA, GOOG)
2. **Ask a question** about the company's financials
3. **View the answer** with source citations
4. **Toggle debug logs** to see the RAG pipeline in action

### Example Questions

- "What were Apple's revenues last year?"
- "Who is the CFO of Tesla?"
- "What are Google's main risk factors?"
- "How much did Microsoft spend on R&D?"

## Debug Panel

The debug panel shows:
- Query processing steps
- Vector search operations
- Chunk retrieval details
- LLM generation progress
- Processing times

This helps users understand how the RAG system works behind the scenes.

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Lucide React** - Icons
- **Axios** - API client

## API Integration

The UI connects to the Finance Agent API at `/api/query`. Make sure the backend is running before starting the frontend.

## Deployment

See the main project README for deployment instructions to Digital Ocean, Railway, or Render.
