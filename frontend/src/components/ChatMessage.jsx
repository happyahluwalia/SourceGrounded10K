import React from 'react'
import { User, Bot, Clock, FileText } from 'lucide-react'
import { cn, formatTime } from '../lib/utils'
import { Badge } from './Badge'

export function ChatMessage({ message }) {
  const isUser = message.role === 'user'

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
          <p className="whitespace-pre-wrap text-foreground">
            {message.content}
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-primary animate-pulse" />
            )}
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
          <details className="group mt-2">
            <summary className="cursor-pointer text-xs text-muted-foreground hover:text-foreground transition-colors">
              View {message.sources.length} sources
            </summary>
            <div className="mt-2 space-y-2">
              {message.sources.map((source, idx) => (
                <div key={idx} className="rounded-md border border-border bg-muted/50 p-3 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{source.section || 'Unknown Section'}</span>
                    <Badge variant="secondary" className="text-xs">
                      Score: {(source.score * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  <p className="text-muted-foreground line-clamp-3">{source.text}</p>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </div>
  )
}
