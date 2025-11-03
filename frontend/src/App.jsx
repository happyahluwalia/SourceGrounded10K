import React, { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid'; // Import uuid
import { Send, Settings, Terminal, Loader2, TrendingUp } from 'lucide-react';
import { Button } from './components/Button';
import { ChatMessage } from './components/ChatMessage';
import { Input } from './components/Input';
import { ProgressCard } from './components/ProgressCard';
import { RotatingMessage } from './components/RotatingMessage';
import { Sidebar } from './components/Sidebar';
import { DebugPanel } from './components/DebugPanel';
import { chatWithAgentStreaming } from './lib/api';
import { getRotatingMessages, STEP_INSIGHTS } from './lib/content';
import { useConversations } from './hooks/useConversations';
import { cn } from './lib/utils';
import { Bot, Bug } from 'lucide-react';
import './index.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  // Conversation management
  const {
    conversations,
    activeConversationId,
    activeConversation,
    createConversation,
    updateConversationMessages,
    updateConversationSessionId,
    deleteConversation,
    selectConversation
  } = useConversations();

  const [input, setInput] = useState('');
  const [loadingConversations, setLoadingConversations] = useState(new Set());
  const [conversationProgress, setConversationProgress] = useState(new Map());
  const [rotatingMessages] = useState(getRotatingMessages());
  const [debugLogs, setDebugLogs] = useState([]);
  const [showDebug, setShowDebug] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const eventSourceRef = useRef(null);

  // Get messages and sessionId from active conversation
  const messages = activeConversation?.messages || [];
  const sessionId = activeConversation?.session_id;
  
  // Check if active conversation is loading
  const isLoading = loadingConversations.has(activeConversationId);
  
  // Get progress for active conversation
  const defaultSteps = {
    planning: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.planning },
    fetching: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.fetching },
    synthesis: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.synthesis }
  };
  const progressSteps = conversationProgress.get(activeConversationId) || defaultSteps;
  const showProgress = conversationProgress.has(activeConversationId);

  // Helper to update a specific message in a specific conversation
  const updateMessageInConversation = (conversationId, messageId, updates) => {
    const conversation = conversations.find(c => c.id === conversationId);
    if (!conversation) {
      console.error('❌ Conversation not found:', conversationId);
      console.log('Available conversations:', conversations.map(c => c.id));
      return;
    }
    
    const updatedMessages = conversation.messages.map(msg =>
      msg.id === messageId ? { ...msg, ...updates } : msg
    );
    
    console.log(`🔄 Updating message ${messageId} in conversation ${conversationId}`);
    console.log(`   Found ${updatedMessages.length} messages`);
    
    updateConversationMessages(conversationId, updatedMessages);
  };

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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !activeConversation) return;

    // CRITICAL: Capture conversation ID FIRST before any state changes
    const queryConversationId = activeConversationId;
    const queryText = input;
    
    console.log('🚀 Starting query for conversation:', queryConversationId);

    // Generate session_id if this is the first message in the conversation
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      currentSessionId = uuidv4();
      updateConversationSessionId(queryConversationId, currentSessionId);
      console.log('🆕 Generated session ID:', currentSessionId, 'for conversation:', queryConversationId);
    }

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };
    
    // Get messages from the specific conversation
    const currentConversation = conversations.find(c => c.id === queryConversationId);
    const conversationMessages = currentConversation?.messages || [];
    
    // Create placeholder for streaming assistant message
    const assistantMessageId = Date.now();
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };
    
    // Add BOTH user and assistant messages together to avoid race condition
    const messagesWithBoth = [...conversationMessages, userMessage, assistantMessage];
    updateConversationMessages(queryConversationId, messagesWithBoth);
    
    console.log('📨 Added user + assistant messages to conversation, total messages:', messagesWithBoth.length);
    
    setInput('');
    setLoadingConversations(prev => new Set(prev).add(queryConversationId));

    // Reset progress steps for this conversation
    setConversationProgress(prev => {
      const next = new Map(prev);
      next.set(queryConversationId, {
        planning: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.planning },
        fetching: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.fetching },
        synthesis: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.synthesis }
      });
      return next;
    });

    // Track step start times for duration calculation
    const stepStartTimes = {};
    
    // Create a local updater that works with our captured messages array
    // This avoids reading stale state from the conversations hook
    let currentMessages = messagesWithBoth;
    const updateLocalMessage = (messageId, updates) => {
      currentMessages = currentMessages.map(msg =>
        msg.id === messageId ? { ...msg, ...updates } : msg
      );
      updateConversationMessages(queryConversationId, currentMessages);
      console.log(`🔄 Updated message, total messages now: ${currentMessages.length}`);
    };

    try {
      let accumulatedContent = '';
      
      await chatWithAgentStreaming(queryText, currentSessionId, {
        // Handle each token as it arrives
        onToken: (content) => {
          accumulatedContent += content;
          console.log(`📝 Token for conversation ${queryConversationId}, message ${assistantMessageId}`);
          updateLocalMessage(assistantMessageId, { 
            content: accumulatedContent 
          });
        },

        // Handle step start
        onStepStart: (step) => {
          stepStartTimes[step] = Date.now();
          
          // Mark previous step as completed when new step starts
          const stepOrder = ['planning', 'fetching', 'synthesis'];
          const currentIndex = stepOrder.indexOf(step);
          
          if (currentIndex > 0) {
            const prevStep = stepOrder[currentIndex - 1];
            if (stepStartTimes[prevStep]) {
              const duration = (Date.now() - stepStartTimes[prevStep]) / 1000;
              setConversationProgress(prev => {
                const next = new Map(prev);
                const steps = next.get(queryConversationId) || defaultSteps;
                next.set(queryConversationId, {
                  ...steps,
                  [prevStep]: { ...steps[prevStep], status: 'completed', duration }
                });
                return next;
              });
            }
          }
          
          // Mark current step as in progress
          setConversationProgress(prev => {
            const next = new Map(prev);
            const steps = next.get(queryConversationId) || defaultSteps;
            next.set(queryConversationId, {
              ...steps,
              [step]: { ...steps[step], status: 'in_progress' }
            });
            return next;
          });
          addLog('INFO', `▶️ Step started: ${step}`);
        },

        // Handle plan complete
        onPlanComplete: (plan) => {
          setConversationProgress(prev => {
            const next = new Map(prev);
            const steps = next.get(queryConversationId) || defaultSteps;
            next.set(queryConversationId, {
              ...steps,
              planning: { 
                ...steps.planning,
                metadata: { plan }
              }
            });
            return next;
          });
          addLog('INFO', `📋 Plan created: ${JSON.stringify(plan)}`);
        },

        // Handle tool execution start
        onToolStart: (toolName) => {
          addLog('INFO', `🔧 Tool started: ${toolName}`);
        },

        // Handle tool execution end
        onToolEnd: (toolName) => {
          addLog('INFO', `✅ Tool completed: ${toolName}`);
        },

        // Handle completion
        onComplete: (newSessionId, fullAnswer, sources) => {
          console.log('✅ Complete for conversation:', queryConversationId);
          console.log('   Message ID:', assistantMessageId);
          console.log('   Sources:', sources?.length || 0);
          console.log('   Answer length:', fullAnswer?.length || 0);
          
          // Mark synthesis step as completed
          if (stepStartTimes.synthesis) {
            const duration = (Date.now() - stepStartTimes.synthesis) / 1000;
            setConversationProgress(prev => {
              const next = new Map(prev);
              const steps = next.get(queryConversationId) || defaultSteps;
              next.set(queryConversationId, {
                ...steps,
                synthesis: { ...steps.synthesis, status: 'completed', duration }
              });
              return next;
            });
          }
          
          // Store session_id in conversation
          if (newSessionId) {
            updateConversationSessionId(queryConversationId, newSessionId);
            console.log('💾 Session ID updated:', newSessionId);
          }

          // Mark streaming as complete and add sources
          updateLocalMessage(assistantMessageId, { 
            isStreaming: false, 
            sessionId: newSessionId, 
            sources: sources || [] 
          });
          
          console.log('✅ Message updated in conversation');

          setLoadingConversations(prev => {
            const next = new Set(prev);
            next.delete(queryConversationId);
            return next;
          });
          inputRef.current?.focus();
        },

        // Handle errors
        onError: (error) => {
          console.error('Streaming error:', error);
          addLog('ERROR', `Error: ${error.message}`);

          const currentContent = currentMessages.find(m => m.id === assistantMessageId)?.content || '';
          
          updateLocalMessage(assistantMessageId, {
            content: currentContent || `Sorry, I encountered an error: ${error.message}. Please try again.`,
            isStreaming: false
          });

          setLoadingConversations(prev => {
            const next = new Set(prev);
            next.delete(queryConversationId);
            return next;
          });
        },
      });
    } catch (error) {
      console.error('Error in streaming:', error);
      addLog('ERROR', `Error: ${error.message}`);

      const currentContent = currentMessages.find(m => m.id === assistantMessageId)?.content || '';
      
      updateLocalMessage(assistantMessageId, {
        content: currentContent || `Sorry, I encountered an error: ${error.message}. Please try again.`,
        isStreaming: false
      });

      setLoadingConversations(prev => {
        const next = new Set(prev);
        next.delete(queryConversationId);
        return next;
      });
    }
  };

  // Handle new conversation
  const handleNewConversation = () => {
    createConversation();
    setInput('');
    // Progress will be set when first query is made
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={selectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={deleteConversation}
        loadingConversations={loadingConversations}
      />

      {/* Main Chat Area */}
      <div className={cn('flex-1 flex flex-col transition-all duration-300 ml-0 md:ml-64', showDebug ? 'mr-0 md:mr-[50%] lg:mr-[40%]' : '')}>
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
                <span>Active connection</span>
              </div>
            )}
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
            
            {/* Progress Card */}
            {showProgress && (
              <div className="p-4">
                <ProgressCard
                  steps={progressSteps}
                  isComplete={!isLoading}
                  onCollapse={() => setShowProgress(false)}
                />
                
                {/* Rotating Message during synthesis */}
                {isLoading && progressSteps.synthesis.status === 'in_progress' && (
                  <RotatingMessage
                    messages={rotatingMessages}
                    interval={5000}
                    isActive={true}
                  />
                )}
              </div>
            )}
            
            {isLoading && !showProgress && (
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
                placeholder={!activeConversation ? "Initializing..." : "Ask about a supported company... (e.g., What is Apple's revenue?)"}
                className="flex-1"
                disabled={isLoading || !activeConversation}
              />
              <Button type="submit" disabled={isLoading || !input.trim() || !activeConversation} size="icon">
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
