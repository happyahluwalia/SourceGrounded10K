import React, { useState, useEffect, useRef } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { Send, Terminal, Loader2, TrendingUp, MessageSquarePlus, BookOpen } from 'lucide-react';
import { Button } from './components/Button';
import { ChatMessage } from './components/ChatMessage';
import { Input } from './components/Input';
import { ProgressCard } from './components/ProgressCard';
import { RotatingMessage } from './components/RotatingMessage';
import { Sidebar } from './components/Sidebar';
import { DebugPanel } from './components/DebugPanel';
import VLLMDeepDive from './components/VLLMDeepDive';
import KnowledgeHub from './components/KnowledgeHub';
import NuggetArticle from './components/NuggetArticle';
import { ChatInterface } from './components/ChatInterface';
import { cn } from './lib/utils';
import './index.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const location = useLocation();
  const [showDebug, setShowDebug] = useState(false);
  const [debugLogs, setDebugLogs] = useState([]);
  const [feedbackExpanded, setFeedbackExpanded] = useState(false);
  const eventSourceRef = useRef(null);

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
        };

        eventSourceRef.current = eventSource;
      } catch (error) {
        console.error('Failed to create EventSource:', error);
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

  // Load Ko-fi widget script
  useEffect(() => {
    const scriptId = 'kofi-widget-script';

    if (document.getElementById(scriptId)) {
      return;
    }

    const script = document.createElement('script');
    script.id = scriptId;
    script.src = 'https://storage.ko-fi.com/cdn/scripts/overlay-widget.js';
    script.async = true;

    script.onload = () => {
      try {
        kofiWidgetOverlay.draw('happyiness', {
          'type': 'floating-chat',
          'floating-chat.donateButton.text': 'Support me',
          'floating-chat.donateButton.background-color': '#00b9fe',
          'floating-chat.donateButton.text-color': '#fff'
        });
      } catch (e) {
        console.error("Ko-fi widget error:", e);
      }
    };

    document.body.appendChild(script);
  }, []);

  const handleFeedbackClick = () => {
    window.open('https://docs.google.com/spreadsheets/d/16mGF47L0caGkPrHzmwEoC9YfZhqMmASl7SA2hDkSf6Y/edit?usp=sharing', '_blank', 'noopener,noreferrer');
  };

  const isVLLMPage = location.pathname === '/research/vllm';
  const isResearchPage = location.pathname.startsWith('/research');

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header - Show on all pages */}
      {!isResearchPage && (
        <header className="border-b border-border bg-card px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold">10kiq</h1>
            <span className="text-sm text-muted-foreground">AI Financial Analysis</span>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/research"
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white transition-colors text-sm font-medium"
            >
              <BookOpen className="h-4 w-4" />
              <span className="hidden sm:inline">Research</span>
            </Link>
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
      )}

      {/* Routes */}
      <div className={`flex-1 ${isResearchPage ? 'overflow-auto' : 'overflow-hidden'}`}>
        {/* Chat Interface - Persisted but hidden when on research pages */}
        <div className={cn('flex h-full', showDebug ? 'mr-0 md:mr-[50%] lg:mr-[40%]' : '', isResearchPage ? 'hidden' : '')}>
          <ChatInterface />
        </div>

        <Routes>
          <Route path="/research/vllm" element={<VLLMDeepDive />} />
          <Route path="/research" element={<KnowledgeHub />} />
          <Route path="/research/:id" element={<NuggetArticle />} />
        </Routes>
      </div>

      {/* Debug Panel - Show on non-vLLM pages only */}
      {!isResearchPage && (
        <DebugPanel logs={debugLogs} isOpen={showDebug} onClose={() => setShowDebug(false)} />
      )}

      {/* Floating Feedback Button - Show on non-vLLM pages only */}
      {!isResearchPage && (
        <button
          onClick={handleFeedbackClick}
          onMouseEnter={() => setFeedbackExpanded(true)}
          onMouseLeave={() => setFeedbackExpanded(false)}
          className="fixed left-4 md:left-6 bottom-20 md:bottom-24 z-50 flex items-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 group"
          style={{
            padding: feedbackExpanded ? '0.75rem 1rem' : '0.75rem',
            width: feedbackExpanded ? 'auto' : '3rem',
            height: '3rem'
          }}
          aria-label="Share Feedback"
          title="Share Feature Ideas"
        >
          <MessageSquarePlus className="h-5 w-5 flex-shrink-0" />
          <span
            className={`font-medium text-sm whitespace-nowrap overflow-hidden transition-all duration-300 ${feedbackExpanded ? 'max-w-xs opacity-100 ml-2' : 'max-w-0 opacity-0 ml-0'
              } hidden md:inline`}
          >
            Feature Ideas?
          </span>
        </button>
      )}
    </div>
  );
}

export default App;
