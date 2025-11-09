import React, { useState } from 'react'
import { MessageSquare, Plus, Trash2, ChevronLeft, ChevronRight, Menu, Loader2 } from 'lucide-react'
import { cn, formatTime } from '../lib/utils'

export function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  loadingConversations = new Set()
}) {
  const [isOpen, setIsOpen] = useState(true)

  const formatConversationTime = (timestamp) => {
    const now = new Date()
    const date = new Date(timestamp)
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  const getConversationTitle = (conversation) => {
    // Use first user message as title
    const firstUserMsg = conversation.messages.find(m => m.role === 'user')
    if (firstUserMsg) {
      // Ensure content is a string (defensive coding)
      const content = typeof firstUserMsg.content === 'string' 
        ? firstUserMsg.content 
        : 'New Conversation';
      return content.length > 50 
        ? content.substring(0, 50) + '...'
        : content
    }
    return 'New Conversation'
  }

  return (
    <>
      {/* Toggle button for mobile/collapsed state */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed top-4 left-4 z-50 p-2 rounded-md bg-secondary hover:bg-secondary/80 transition-colors"
          title="Open sidebar"
        >
          <Menu className="h-5 w-5" />
        </button>
      )}

      {/* Sidebar */}
      <div
        className={cn(
          "fixed top-0 left-0 h-full bg-muted border-r border-border transition-all duration-300 z-40 flex flex-col",
          isOpen ? "w-64" : "w-0"
        )}
      >
        {isOpen && (
          <>
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h2 className="font-semibold text-sm">Conversations</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded hover:bg-secondary transition-colors"
                title="Close sidebar"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
            </div>

            {/* New Chat Button */}
            <div className="p-3 border-b border-border">
              <button
                onClick={onNewConversation}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span className="text-sm font-medium">New Chat</span>
              </button>
            </div>

            {/* Conversation List */}
            <div className="flex-1 overflow-y-auto p-2">
              {conversations.length === 0 ? (
                <div className="text-center text-muted-foreground text-sm py-8">
                  No conversations yet
                </div>
              ) : (
                <div className="space-y-1">
                  {conversations.map((conversation) => (
                    <div
                      key={conversation.id}
                      className={cn(
                        "group relative flex items-start gap-2 p-2 rounded-md cursor-pointer transition-colors",
                        activeConversationId === conversation.id
                          ? "bg-secondary"
                          : "hover:bg-secondary/50"
                      )}
                      onClick={() => onSelectConversation(conversation.id)}
                    >
                      <MessageSquare className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <div className="text-sm font-medium truncate">
                            {getConversationTitle(conversation)}
                          </div>
                          {loadingConversations.has(conversation.id) && (
                            <Loader2 className="h-3 w-3 animate-spin text-primary flex-shrink-0" />
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {formatConversationTime(conversation.timestamp)}
                        </div>
                      </div>
                      
                      {/* Delete button */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          if (window.confirm('Delete this conversation? This cannot be undone.')) {
                            onDeleteConversation(conversation.id)
                          }
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-destructive/10 hover:text-destructive transition-all"
                        title="Delete conversation"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-border text-xs text-muted-foreground">
              {conversations.length} conversation{conversations.length !== 1 ? 's' : ''}
            </div>
          </>
        )}
      </div>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-30 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  )
}
