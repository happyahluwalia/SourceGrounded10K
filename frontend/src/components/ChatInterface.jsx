import React, { useState, useEffect, useRef, useMemo } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Send, Loader2, MessageSquarePlus, BookOpen, Rocket } from 'lucide-react';
import { Button } from './Button';
import { ChatMessage } from './ChatMessage';
import { Input } from './Input';
import { ProgressCard } from './ProgressCard';
import { RotatingMessage } from './RotatingMessage';
import { Sidebar } from './Sidebar';
import { chatWithAgentStreaming } from '../lib/api';
import { getRotatingMessages, STEP_INSIGHTS } from '../lib/content';
import { useConversations } from '../hooks/useConversations';
import { useNavigate } from 'react-router-dom';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const GPU_DEPLOYMENT = import.meta.env.VITE_GPU_DEPLOYMENT === 'true';

export function ChatInterface() {
    const navigate = useNavigate();
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
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const messagesRef = useRef(null);
    const messages = useMemo(() => {
        const msgs = activeConversation?.messages || [];
        messagesRef.current = msgs;
        return [...msgs];
    }, [activeConversation]);

    const sessionId = activeConversation?.session_id;
    const isLoading = loadingConversations.has(activeConversationId);

    const defaultSteps = {
        planning: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.planning },
        fetching: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.fetching },
        synthesis: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.synthesis }
    };
    const progressSteps = conversationProgress.get(activeConversationId) || defaultSteps;
    const showProgress = conversationProgress.has(activeConversationId);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

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

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading || !activeConversation) return;

        const queryConversationId = activeConversationId;
        const queryText = input;

        let currentSessionId = sessionId;
        if (!currentSessionId) {
            currentSessionId = uuidv4();
            updateConversationSessionId(queryConversationId, currentSessionId);
        }

        const userMessageId = Date.now();
        const userMessage = {
            id: userMessageId,
            role: 'user',
            content: input,
            timestamp: new Date().toISOString(),
        };

        const currentConversation = conversations.find(c => c.id === queryConversationId);
        const conversationMessages = currentConversation?.messages || [];

        const assistantMessageId = userMessageId + 1;
        const assistantMessage = {
            id: assistantMessageId,
            role: 'assistant',
            content: '',
            timestamp: new Date().toISOString(),
            isStreaming: true,
        };

        const messagesWithBoth = [...conversationMessages, userMessage, assistantMessage];
        updateConversationMessages(queryConversationId, messagesWithBoth);

        setInput('');
        setLoadingConversations(prev => new Set(prev).add(queryConversationId));

        setConversationProgress(prev => {
            const next = new Map(prev);
            next.set(queryConversationId, {
                planning: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.planning },
                fetching: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.fetching },
                synthesis: { status: 'pending', duration: null, metadata: {}, insight: STEP_INSIGHTS.synthesis }
            });
            return next;
        });

        const stepStartTimes = {};

        let currentMessages = messagesWithBoth;
        const updateLocalMessage = (messageId, updates) => {
            currentMessages = currentMessages.map(msg =>
                msg.id === messageId ? { ...msg, ...updates } : msg
            );
            updateConversationMessages(queryConversationId, currentMessages);
        };

        try {
            let accumulatedContent = '';

            await chatWithAgentStreaming(queryText, currentSessionId, {
                onToken: (content) => {
                    accumulatedContent += content;
                    updateLocalMessage(assistantMessageId, {
                        content: accumulatedContent
                    });
                },

                onStepStart: (step) => {
                    stepStartTimes[step] = Date.now();

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

                    setConversationProgress(prev => {
                        const next = new Map(prev);
                        const steps = next.get(queryConversationId) || defaultSteps;
                        next.set(queryConversationId, {
                            ...steps,
                            [step]: { ...steps[step], status: 'in_progress' }
                        });
                        return next;
                    });
                },

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
                },

                onToolStart: (toolName) => { },
                onToolEnd: (toolName) => { },

                onSourcesReady: (sources) => {
                    const ticker = sources && sources.length > 0 ? sources[0].ticker : null;

                    updateLocalMessage(assistantMessageId, {
                        sources: sources,
                        ticker: ticker
                    });
                },

                onComplete: (newSessionId, fullAnswer, sources, isStructured = false) => {
                    let parsedAnswer = fullAnswer;

                    if (isStructured) {
                        parsedAnswer = fullAnswer;
                    } else {
                        if (typeof fullAnswer === 'string') {
                            try {
                                parsedAnswer = JSON.parse(fullAnswer);
                            } catch (e) { }
                        }
                    }

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

                    if (newSessionId) {
                        updateConversationSessionId(queryConversationId, newSessionId);
                    }

                    const ticker = sources && sources.length > 0 ? sources[0].ticker : null;

                    updateLocalMessage(assistantMessageId, {
                        content: parsedAnswer,
                        isStreaming: false,
                        sessionId: newSessionId,
                        sources: sources || [],
                        ticker: ticker
                    });

                    setLoadingConversations(prev => {
                        const next = new Set(prev);
                        next.delete(queryConversationId);
                        return next;
                    });
                    inputRef.current?.focus();
                },

                onError: (error) => {
                    console.error('Streaming error:', error);

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

    const handleNewConversation = () => {
        createConversation();
        setInput('');
    };

    // Coming soon mode when GPU deployment is disabled
    if (!GPU_DEPLOYMENT) {
        return (
            <div className="flex h-full w-full bg-background">
                <Sidebar
                    conversations={conversations}
                    activeConversationId={activeConversationId}
                    onSelectConversation={selectConversation}
                    onNewConversation={handleNewConversation}
                    onDeleteConversation={deleteConversation}
                    loadingConversations={loadingConversations}
                />

                <div className="flex-1 flex flex-col ml-0 md:ml-64">
                    <div className="flex-1 flex items-center justify-center p-8">
                        <div className="max-w-2xl w-full text-center space-y-6">
                            <div className="flex justify-center">
                                <img 
                                    src="/images/GPU_maintenance.webp" 
                                    alt="GPU Maintenance" 
                                    className="w-64 h-64 object-contain"
                                />
                            </div>
                            
                            <div className="space-y-3">
                                <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                                    Adding More Brainpower 🧠⚡
                                </h2>
                                <p className="text-lg text-muted-foreground">
                                    We found a bigger GPU… now we just need to figure out where this cable goes.
                                </p>
                                <p className="text-muted-foreground font-medium">
                                    Back soon!
                                </p>
                            </div>

                            <div className="pt-4">
                                <Button
                                    onClick={() => navigate('/research')}
                                    size="lg"
                                    className="gap-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700"
                                >
                                    <BookOpen className="h-5 w-5" />
                                    Explore Research
                                </Button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex h-full w-full bg-background">
            <Sidebar
                conversations={conversations}
                activeConversationId={activeConversationId}
                onSelectConversation={selectConversation}
                onNewConversation={handleNewConversation}
                onDeleteConversation={deleteConversation}
                loadingConversations={loadingConversations}
            />

            <div className="flex-1 flex flex-col ml-0 md:ml-64">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto">
                    <div className="max-w-4xl mx-auto">
                        {messages.map((message) => (
                            <ChatMessage key={message.id} message={message} />
                        ))}

                        {showProgress && (
                            <div className="p-4">
                                <ProgressCard
                                    steps={progressSteps}
                                    isComplete={!isLoading}
                                    onCollapse={() => { }}
                                />

                                {isLoading && (
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
        </div>
    );
}
