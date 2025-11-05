import React, { useState, useRef } from 'react'
import { User, Bot, Clock, FileText, TrendingUp, AlertCircle } from 'lucide-react'
import { cn, formatTime } from '../lib/utils'
import { Badge } from './Badge'
import { Card } from './Card'
import { BusinessContext } from './BusinessContext'

export function ChatMessage({ message }) {
  const isUser = message.role === 'user'
  const [highlightedSource, setHighlightedSource] = useState(null)
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const detailsRef = useRef(null)
  const sourceRefs = useRef([])

  const scrollToSource = (index) => {
    // Open sources if closed
    if (!sourcesOpen) {
      setSourcesOpen(true)
      // Wait for details to open before scrolling
      setTimeout(() => {
        sourceRefs.current[index]?.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest'
        })
      }, 100)
    } else {
      sourceRefs.current[index]?.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      })
    }

    setHighlightedSource(index)
    // Remove highlight after 3 seconds
    setTimeout(() => setHighlightedSource(null), 3000)
  }

  // Render citation badge
  const CitationBadge = ({ citation, onClick }) => (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1 px-2 py-0.5 mx-0.5 text-xs bg-primary/10 hover:bg-primary/20 text-primary rounded border border-primary/20 transition-colors cursor-pointer"
      title={`${citation.ticker} - ${citation.filing_type} ${citation.section}\nClick to view source`}
    >
      <FileText className="h-3 w-3" />
      {citation.text}
    </button>
  )

  // Render structured answer sections
  const renderStructuredAnswer = (answer) => {
    if (!answer || (!answer.sections && !answer.metadata)) {
      return (
        <div className="whitespace-pre-wrap text-foreground text-base leading-relaxed">
          {message.isStreaming && (
            <div className="flex gap-1 items-center">
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}
        </div>
      )
    }

    const companies = answer.metadata?.companies;

    return (
      <div className="space-y-4">
        {answer.sections && answer.sections.map((section, idx) => {
          const { component, props } = section

          switch (component) {
            case 'Paragraph':
              return (
                <div key={idx} className="text-foreground text-base leading-relaxed">
                  {props.text}
                  {props.citations && props.citations.length > 0 && (
                    <span className="ml-1">
                      {props.citations.map((citation, citIdx) => (
                        <CitationBadge
                          key={citIdx}
                          citation={citation}
                          onClick={() => scrollToSource(citation.id)}
                        />
                      ))}
                    </span>
                  )}
                </div>
              )
            
            case 'Table':
              return (
                <Card key={idx} className="p-4">
                  {props.title && (
                    <h4 className="font-semibold text-sm mb-3">{props.title}</h4>
                  )}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          {props.headers && props.headers.map((header, hIdx) => (
                            <th key={hIdx} className="text-left p-2 font-semibold">
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {props.rows && props.rows.map((row, rIdx) => (
                          <tr key={rIdx} className="border-b last:border-0 hover:bg-muted/50">
                            {row.map((cell, cIdx) => (
                              <td key={cIdx} className="p-2">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {props.citations && props.citations.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {props.citations.map((citation, citIdx) => (
                        <CitationBadge
                          key={citIdx}
                          citation={citation}
                          onClick={() => scrollToSource(citation.id)}
                        />
                      ))}
                    </div>
                  )}
                </Card>
              )
            
            case 'KeyFindings':
              return (
                <Card key={idx} className="p-4 bg-primary/5 border-primary/20">
                  <div className="flex items-center gap-2 mb-3">
                    <TrendingUp className="h-4 w-4 text-primary" />
                    <h4 className="font-semibold text-sm">Key Findings</h4>
                  </div>
                  <ul className="space-y-2 text-sm">
                    {props.items && props.items.map((item, iIdx) => (
                      <li key={iIdx} className="flex items-start gap-2">
                        <span className="text-primary mt-1">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                  {props.citations && props.citations.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {props.citations.map((citation, citIdx) => (
                        <CitationBadge
                          key={citIdx}
                          citation={citation}
                          onClick={() => scrollToSource(citation.id)}
                        />
                      ))}
                    </div>
                  )}
                </Card>
              )
            
            case 'ComparisonSummary':
              return (
                <Card key={idx} className="p-4 bg-secondary/50">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertCircle className="h-4 w-4 text-secondary-foreground" />
                    <h4 className="font-semibold text-sm">Summary</h4>
                  </div>
                  <p className="text-sm leading-relaxed">{props.text}</p>
                  {props.citations && props.citations.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {props.citations.map((citation, citIdx) => (
                        <CitationBadge
                          key={citIdx}
                          citation={citation}
                          onClick={() => scrollToSource(citation.id)}
                        />
                      ))}
                    </div>
                  )}
                </Card>
              )
            
            default:
              console.warn(`Unknown component type: ${component}`)
              return (
                <div key={idx} className="text-foreground text-base leading-relaxed">
                  {props.text || JSON.stringify(props)}
                </div>
              )
          }
        })}

        {/* Render Business Context */}
        {companies && Object.keys(companies).map(ticker => (
          companies[ticker].business_context && (
            <BusinessContext
              key={ticker}
              companyTicker={ticker}
              context={companies[ticker].business_context}
              onCitationClick={scrollToSource}
            />
          )
        ))}
        
        {message.isStreaming && (
          <span className="inline-block w-2 h-5 ml-1 bg-primary animate-pulse" />
        )}
      </div>
    )
  }

  // Parse content and make citations clickable (legacy format)
  const renderContentWithCitations = () => {
    if (isUser || !message.sources || message.sources.length === 0) {
      return (
        <>
          {message.content}
          {message.isStreaming && !message.content && (
            <div className="flex gap-1 items-center">
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          )}
          {message.isStreaming && message.content && (
            <span className="inline-block w-2 h-5 ml-1 bg-primary animate-pulse" />
          )}
        </>
      )
    }
    
    // Pattern to match citations - be permissive to catch various formats
    // Matches: "10-K Item 1 - Executive Officers table", "Financial Table", etc.
    const citationPattern = /(?:10-[KQ]|8-K)\s+(?:filing\s+\([^)]+\),\s+)?Item\s+\d+[A-Z]?(?:\s*[-:]\s*[A-Za-z\s]+(?:table|section|statement|officers?|directors?|governance|analysis|factors)?)?|Financial\s+Table\s*(?:sections?)?|Executive\s+Officers?\s+table/gi
    
    const matches = message.content.match(citationPattern) || []

    const handleCitationClick = (citationText) => {
      if (!citationText) return
      
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



    // Split content and insert clickable citations
    const parts = []
    let lastIndex = 0
    
    matches.forEach((match, idx) => {
      const matchIndex = message.content.indexOf(match, lastIndex)
      
      // Add text before match
      if (matchIndex > lastIndex) {
        parts.push(
          <React.Fragment key={`text-${idx}`}>
            {message.content.substring(lastIndex, matchIndex)}
          </React.Fragment>
        )
      }
      
      // Add clickable citation
      parts.push(
        <button
          key={`citation-${idx}`}
          onClick={() => handleCitationClick(match)}
          className="inline-flex items-center gap-1 text-primary hover:text-primary/80 underline decoration-dotted underline-offset-2 cursor-pointer transition-colors"
          title="Click to view source"
        >
          {match}
        </button>
      )
      
      lastIndex = matchIndex + match.length
    })
    
    // Add remaining text
    if (lastIndex < message.content.length) {
      parts.push(
        <React.Fragment key="text-end">
          {message.content.substring(lastIndex)}
        </React.Fragment>
      )
    }

    return (
      <>
        {parts}
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
          {/* Check if content is structured format or legacy plain text */}
          {typeof message.content === 'object' && message.content !== null
            ? renderStructuredAnswer(message.content)
            : <div className="whitespace-pre-wrap text-foreground text-base leading-relaxed">
                {renderContentWithCitations()}
              </div>
          }
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
