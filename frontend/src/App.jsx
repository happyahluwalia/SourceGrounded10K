import React, { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid'; // Import uuid
import { Send, Settings, Terminal, Loader2, TrendingUp, MessageSquarePlus } from 'lucide-react';
import { Button } from './components/Button';
import { Input } from './components/Input';
import { ChatMessage } from './components/ChatMessage';
import { DebugPanel } from './components/DebugPanel';
import { chatWithAgent } from './lib/api'; // Import the new API function
import { cn } from './lib/utils';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your AI financial analyst. Ask me questions about supported companies. For example: "What were Apple\'s revenues last year?" or "Who is the CFO of Microsoft?"',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [debugLogs, setDebugLogs] = useState([]);
  const [showDebug, setShowDebug] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const eventSourceRef = useRef(null);

  // Initialize session ID from localStorage or create new one
  useEffect(() => {
    try {
      const storedSessionId = localStorage.getItem('finance_agent_session_id');
      if (storedSessionId) {
        console.log('📝 Loaded existing session:', storedSessionId);
        setSessionId(storedSessionId);
      } else {
        const newSessionId = uuidv4();
        console.log('🆕 Created new session:', newSessionId);
        try {
          localStorage.setItem('finance_agent_session_id', newSessionId);
          setSessionId(newSessionId);
        } catch (storageError) {
          console.error('Failed to save session to localStorage:', storageError);
          // Still set session for current page load
          setSessionId(newSessionId);
          addLog('WARN', 'Session will not persist across refreshes (localStorage unavailable)');
        }
      }
    } catch (error) {
      console.error('Error accessing localStorage:', error);
      // Fallback: create session without persistence
      const newSessionId = uuidv4();
      setSessionId(newSessionId);
      addLog('ERROR', 'localStorage unavailable - session will not persist');
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Warn user if they try to refresh during active query
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (isLoading) {
        e.preventDefault();
        e.returnValue = 'Your query is still processing. Are you sure you want to leave?';
        return e.returnValue;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [isLoading]);

  // Connect to real-time log stream
  useEffect(() => {
    if (showDebug && !eventSourceRef.current) {
      console.log('Connecting to log stream...');
      
      try {
        const eventSource = new EventSource(`${API_BASE_URL}/api/logs/stream`);
        
        eventSource.onopen = () => {
          console.log('✅ Log stream connected');
        };
        
        eventSource.onmessage = (event) => {
          try {
            const log = JSON.parse(event.data);
            setDebugLogs((prev) => [...prev, log]);
          } catch (error) {
            console.error('Error parsing log:', error, event.data);
          }
        };
        
        eventSource.onerror = (error) => {
          console.error('EventSource error:', error);
          
          if (eventSource.readyState === EventSource.CLOSED) {
            console.log('Connection closed, will retry...');
          } else if (eventSource.readyState === EventSource.CONNECTING) {
            console.log('Reconnecting...');
          }
        };
        
        eventSourceRef.current = eventSource;
      } catch (error) {
        console.error('Failed to create EventSource:', error);
        addLog('ERROR', `Failed to connect to log stream: ${error.message}`);
      }
    } else if (!showDebug && eventSourceRef.current) {
      console.log('Disconnecting from log stream...');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [showDebug]);

  const addLog = (level, message) => {
    setDebugLogs((prev) => [
      ...prev,
      {
        timestamp: new Date().toISOString(),
        level,
        logger: 'frontend',
        message,
      },
    ]);
  };

  const startNewConversation = () => {
    if (confirm('Start a new conversation? Current context will be lost.')) {
      // Clear session from localStorage
      localStorage.removeItem('finance_agent_session_id');
      
      // Generate new session ID
      const newSessionId = uuidv4();
      localStorage.setItem('finance_agent_session_id', newSessionId);
      setSessionId(newSessionId);
      
      // Clear messages except welcome message
      setMessages([
        {
          role: 'assistant',
          content: 'Hello! I\'m your AI financial analyst. Ask me questions about supported companies. For example: "What were Apple\'s revenues last year?" or "Who is the CFO of Microsoft?"',
          timestamp: new Date(),
        },
      ]);
      
      console.log('🆕 Started new conversation:', newSessionId);
      addLog('INFO', `Started new conversation: ${newSessionId}`);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    // Wait for session to be initialized
    if (!sessionId) {
      console.warn('⚠️ Session not initialized yet, please wait...');
      return;
    }

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Call the new v2 chat endpoint
      const response = await chatWithAgent(input, sessionId);

      // Store session_id from backend response (for conversation continuity)
      if (response.session_id) {
        localStorage.setItem('finance_agent_session_id', response.session_id);
        setSessionId(response.session_id);
        console.log('💾 Session ID updated:', response.session_id);
      }

      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sessionId: response.session_id, // Store session_id in message for debugging
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error querying agent:', error);
      addLog('ERROR', `Error processing query: ${error.message}`);

      const errorMessage = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.response?.data?.detail || error.message}. Please make sure the API server is running and try again.`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Main Chat Area */}
      <div className={cn('flex-1 flex flex-col transition-all duration-300', showDebug ? 'mr-0 md:mr-[50%] lg:mr-[40%]' : '')}>
        {/* Header */}
        <header className="border-b border-border bg-card px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">10kiq</h1>
            <span className="text-sm text-muted-foreground">AI Financial Analysis</span>
          </div>
          <div className="flex items-center gap-2">
            {sessionId && (
              <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground mr-2">
                <span className="inline-flex h-2 w-2 rounded-full bg-green-500"></span>
                <span>Active conversation</span>
              </div>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={startNewConversation}
              className="gap-2"
            >
              <MessageSquarePlus className="h-4 w-4" />
              <span className="hidden sm:inline">New Chat</span>
            </Button>
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
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={!sessionId ? "Initializing session..." : "Ask about a supported company... (e.g., What is Apple\'s revenue?)"}
                className="flex-1"
                disabled={isLoading || !sessionId}
              />
              <Button type="submit" disabled={isLoading || !input.trim() || !sessionId} size="icon">
                {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
              </Button>
            </form>
            <p className="text-xs text-muted-foreground mt-2">
              Currently supported companies: Apple, Microsoft, Pfizer, Robinhood, Amazon.
            </p>
          </div>
        </div>
      </div>

      {/* Debug Panel */}
      <DebugPanel logs={debugLogs} isOpen={showDebug} onClose={() => setShowDebug(false)} />
    </div>
  );
}

export default App;
