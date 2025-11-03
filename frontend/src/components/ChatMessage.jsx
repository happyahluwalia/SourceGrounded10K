import React, { useState, useRef } from 'react'
import { User, Bot, Clock, FileText } from 'lucide-react'
import { cn, formatTime } from '../lib/utils'
import { Badge } from './Badge'

export function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const [highlightedSource, setHighlightedSource] = useState(null)
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const detailsRef = useRef(null)
  const sourceRefs = useRef([])

  // Parse content and make citations clickable
  const renderContentWithCitations = () => {
    if (isUser || !message.sources || message.sources.length === 0) {
      return (
        <>
          {message.content}
          {message.isStreaming && (
            <span className="inline-block w-2 h-5 ml-1 bg-primary animate-pulse" />
          )}
        </>
      )
    }

    // Pattern to match citations in multiple formats:
    // 1. "10-K filing (2025-06-30), Item 1: E OFFICERS"
    // 2. "10-K Item 10 - Directors"
    // 3. "Financial Table sections"
    // 4. "Document 3, Section Item 10"
    const citationPattern = /(?:(?:10-[KQ]|8-K)\s+filing\s+\([^)]+\),\s+Item\s+\d+[A-Z]?:\s*[A-Z\s]+|(?:10-[KQ]|8-K)\s+Item\s+\d+[A-Z]?(?:\s*[-:]\s*[A-Za-z\s,]+)?|Financial\s+Table\s+sections?|Document\s+\d+,\s+Section\s+Item\s+\d+[A-Z]?(?:\s*-\s*[A-Za-z\s,]+)?)/g
    const parts = message.content.split(citationPattern)
    const matches = message.content.match(citationPattern) || []

    const handleCitationClick = (citationText) => {
      // Extract Item number from citation
      // Handles: "10-K Item 10", "Document 3, Section Item 10", etc.
      const itemMatch = citationText.match(/Item\s+(\d+[A-Z]?)/i)
      
      // Find matching source by Item number or full text
      const matchedIndex = message.sources.findIndex(source => {
        if (!source.section) return false
        
        const sectionLower = source.section.toLowerCase()
        const citationLower = citationText.toLowerCase()
        
        // Try exact match first
        if (sectionLower.includes(citationLower)) return true
        
        // Try Item number match
        if (itemMatch) {
          const itemNum = itemMatch[1].toLowerCase()
          return sectionLower.includes(`item ${itemNum}`) || 
                 sectionLower.includes(`item${itemNum}`)
        }
        
        return false
      })

      if (matchedIndex !== -1) {
        // Open sources if closed
        if (!sourcesOpen) {
          setSourcesOpen(true)
          // Wait for details to open
          setTimeout(() => {
            scrollToSource(matchedIndex)
          }, 100)
        } else {
          scrollToSource(matchedIndex)
        }
      }
    }

    const scrollToSource = (index) => {
      setHighlightedSource(index)
      sourceRefs.current[index]?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'nearest' 
      })
      // Remove highlight after 3 seconds
      setTimeout(() => setHighlightedSource(null), 3000)
    }

    let matchIndex = 0
    return (
      <>
        {parts.map((part, i) => (
          <React.Fragment key={i}>
            {part}
            {i < parts.length - 1 && matches[matchIndex] && (
              <button
                onClick={() => handleCitationClick(matches[matchIndex])}
                className="inline-flex items-center gap-1 text-primary hover:text-primary/80 underline decoration-dotted underline-offset-2 cursor-pointer transition-colors"
                title="Click to view source"
              >
                {matches[matchIndex++]}
              </button>
            )}
          </React.Fragment>
        ))}
        {message.isStreaming && (
          <span className="inline-block w-2 h-5 ml-1 bg-primary animate-pulse" />
        )}
      </>
    )
  }

  return (
    <div className={cn('flex gap-3 p-4 animate-fade-in', isUser ? 'bg-muted/50' : 'bg-background')}>
      <div className={cn('flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-md', isUser ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground')}>
        {isUser ? <User className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
      </div>

      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="flex items-center gap-2">
          <span className="font-semibold">{isUser ? 'You' : 'Finance Agent'}</span>
          {message.ticker && (
            <Badge variant="outline" className="text-xs">
              {message.ticker}
            </Badge>
          )}
        </div>

        <div className="prose prose-sm max-w-none dark:prose-invert">
          <p className="whitespace-pre-wrap text-foreground text-base leading-relaxed">
            {renderContentWithCitations()}
          </p>
        </div>

        {message.metadata && (
          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
            {message.metadata.processing_time && (
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>{formatTime(message.metadata.processing_time)}</span>
              </div>
            )}
            {message.metadata.num_sources && (
              <div className="flex items-center gap-1">
                <FileText className="h-3 w-3" />
                <span>{message.metadata.num_sources} sources</span>
              </div>
            )}
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <details 
            ref={detailsRef}
            open={sourcesOpen}
            onToggle={(e) => setSourcesOpen(e.target.open)}
            className="group mt-2"
          >
            <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground transition-colors">
              View {message.sources.length} sources
            </summary>
            <div className="mt-2 space-y-2">
              {message.sources.map((source, idx) => (
                <div 
                  key={idx}
                  ref={el => sourceRefs.current[idx] = el}
                  className={cn(
                    "rounded-md border p-3 text-xs transition-all duration-300",
                    highlightedSource === idx 
                      ? "border-primary bg-primary/10 shadow-md" 
                      : "border-border bg-muted/50"
                  )}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{source.section || 'Unknown Section'}</span>
                    <Badge variant="secondary" className="text-xs">
                      Score: {(source.score * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  <p className={cn(
                    "text-muted-foreground",
                    highlightedSource === idx ? "line-clamp-none" : "line-clamp-3"
                  )}>
                    {source.text}
                  </p>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  )
}
