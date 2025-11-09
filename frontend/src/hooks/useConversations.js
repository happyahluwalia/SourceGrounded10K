import { useState, useEffect, useMemo } from 'react'

const STORAGE_KEY = 'finance_agent_conversations'
const ACTIVE_CONVERSATION_KEY = 'finance_agent_active_conversation'

export function useConversations() {
  const [conversations, setConversations] = useState([])
  const [activeConversationId, setActiveConversationId] = useState(null)

  // Load conversations from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        setConversations(parsed)
      }

      const activeId = localStorage.getItem(ACTIVE_CONVERSATION_KEY)
      if (activeId) {
        setActiveConversationId(activeId)
      }
    } catch (error) {
      console.error('Error loading conversations:', error)
    }
  }, [])

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
    } catch (error) {
      console.error('Error saving conversations:', error)
    }
  }, [conversations])

  // Save active conversation ID
  useEffect(() => {
    if (activeConversationId) {
      localStorage.setItem(ACTIVE_CONVERSATION_KEY, activeConversationId)
    }
  }, [activeConversationId])

  // Create new conversation
  const createConversation = () => {
    const newConversation = {
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      messages: [
        {
          id: 'welcome-message',
          role: 'assistant',
          content: 'Hello! I\'m your AI financial analyst. Ask me questions about supported companies.',
          timestamp: new Date().toISOString()
        }
      ],
      session_id: null // Will be set when first query is made
    }

    setConversations(prev => [newConversation, ...prev])
    setActiveConversationId(newConversation.id)
    
    return newConversation
  }

  // Get active conversation - memoized to update when conversations or activeConversationId changes
  const activeConversation = useMemo(() => {
    return conversations.find(c => c.id === activeConversationId);
  }, [conversations, activeConversationId])

  // Update conversation messages
  const updateConversationMessages = (conversationId, messages) => {
    setConversations(prev => 
      prev.map(c =>
        c.id === conversationId
          ? { ...c, messages, timestamp: new Date().toISOString() }
          : c
      )
    );
  }

  // Update conversation session_id
  const updateConversationSessionId = (conversationId, sessionId) => {
    setConversations(prev =>
      prev.map(c =>
        c.id === conversationId
          ? { ...c, session_id: sessionId }
          : c
      )
    )
  }

  // Delete conversation
  const deleteConversation = (conversationId) => {
    setConversations(prev => {
      const remaining = prev.filter(c => c.id !== conversationId);
      
      // If deleting active conversation, switch to most recent or create new
      if (conversationId === activeConversationId) {
        if (remaining.length > 0) {
          setActiveConversationId(remaining[0].id);
        } else {
          // Create new conversation after state update
          setTimeout(() => createConversation(), 0);
        }
      }
      
      return remaining;
    });
  }

  // Select conversation
  const selectConversation = (conversationId) => {
    setActiveConversationId(conversationId)
  }

  // Initialize with first conversation if none exist
  useEffect(() => {
    if (conversations.length === 0 && !activeConversationId) {
      createConversation()
    }
  }, [])

  return {
    conversations,
    activeConversationId,
    activeConversation,
    createConversation,
    updateConversationMessages,
    updateConversationSessionId,
    deleteConversation,
    selectConversation
  }
}
