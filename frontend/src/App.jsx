import React, { useState, useRef, useEffect } from 'react'
import { Send, Settings, Terminal, Loader2, TrendingUp } from 'lucide-react'
import { Button } from './components/Button'
import { Input } from './components/Input'
import { ChatMessage } from './components/ChatMessage'
import { DebugPanel } from './components/DebugPanel'
import { queryCompany } from './lib/api'
import { cn } from './lib/utils'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your AI financial analyst. Ask me questions about any company\'s SEC filings. For example: "What were Apple\'s revenues last year?" or "Who is Tesla\'s CFO?"',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [ticker, setTicker] = useState('AAPL')
  const [isLoading, setIsLoading] = useState(false)
  const [debugLogs, setDebugLogs] = useState([])
  const [showDebug, setShowDebug] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const eventSourceRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Connect to real-time log stream
  useEffect(() => {
    if (showDebug && !eventSourceRef.current) {
      console.log('Connecting to log stream...')
      
      try {
        const eventSource = new EventSource(`${API_BASE_URL}/api/logs/stream`)
        
        eventSource.onopen = () => {
          console.log('✅ Log stream connected')
        }
        
        eventSource.onmessage = (event) => {
          try {
            const log = JSON.parse(event.data)
            setDebugLogs((prev) => [...prev, log])
          } catch (error) {
            console.error('Error parsing log:', error, event.data)
          }
        }
        
        eventSource.onerror = (error) => {
          console.error('EventSource error:', error)
          
          // Check if it's a connection error
          if (eventSource.readyState === EventSource.CLOSED) {
            console.log('Connection closed, will retry...')
          } else if (eventSource.readyState === EventSource.CONNECTING) {
            console.log('Reconnecting...')
          }
          
          // Don't close on error - let it auto-reconnect
          // Only close if we're manually closing the panel
        }
        
        eventSourceRef.current = eventSource
      } catch (error) {
        console.error('Failed to create EventSource:', error)
        addLog('ERROR', `Failed to connect to log stream: ${error.message}`)
      }
    } else if (!showDebug && eventSourceRef.current) {
      console.log('Disconnecting from log stream...')
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }
  }, [showDebug])

  const addLog = (level, message) => {
    setDebugLogs((prev) => [
      ...prev,
      {
        timestamp: new Date().toISOString(),
        level,
        logger: 'frontend',
        message,
      },
    ])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || !ticker.trim() || isLoading) return

    const userMessage = {
      role: 'user',
      content: input,
      ticker: ticker.toUpperCase(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await queryCompany(input, ticker.toUpperCase(), {
        filing_type: '10-K',
        top_k: 5,
        score_threshold: 0.5,
      })

      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        ticker: ticker.toUpperCase(),
        timestamp: new Date(),
        metadata: {
          processing_time: response.processing_time,
          num_sources: response.num_sources,
        },
        sources: response.sources,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error querying company:', error)
      addLog('ERROR', `Error processing query: ${error.message}`)

      const errorMessage = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message}. Please make sure the API server is running and try again.`,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Main Chat Area */}
      <div className={cn('flex-1 flex flex-col transition-all duration-300', showDebug ? 'mr-0 md:mr-[50%] lg:mr-[40%]' : '')}>
        {/* Header */}
        <header className="border-b border-border bg-card px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">Finance Agent</h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant={showDebug ? 'default' : 'outline'}
              size="sm"
              onClick={() => setShowDebug(!showDebug)}
              className="gap-2"
            >
              <Terminal className="h-4 w-4" />
              <span className="hidden sm:inline">Debug Logs</span>
            </Button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto">
            {messages.map((message, idx) => (
              <ChatMessage key={idx} message={message} />
            ))}
            {isLoading && (
              <div className="flex gap-3 p-4 bg-background">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
                  <Loader2 className="h-5 w-5 animate-spin" />
                </div>
                <div className="flex-1">
                  <p className="text-muted-foreground">Analyzing financial data...</p>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-border bg-card p-4">
          <div className="max-w-4xl mx-auto">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <Input
                ref={inputRef}
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                placeholder="Ticker"
                className="w-24 uppercase"
                maxLength={5}
              />
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about financial data... (e.g., What were the revenues?)"
                className="flex-1"
                disabled={isLoading}
              />
              <Button type="submit" disabled={isLoading || !input.trim() || !ticker.trim()} size="icon">
                {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
              </Button>
            </form>
            <p className="text-xs text-muted-foreground mt-2">
              Enter a ticker symbol (e.g., AAPL, TSLA, GOOG) and ask questions about their SEC filings.
            </p>
          </div>
        </div>
      </div>

      {/* Debug Panel */}
      <DebugPanel logs={debugLogs} isOpen={showDebug} onClose={() => setShowDebug(false)} />
    </div>
  )
}

export default App
