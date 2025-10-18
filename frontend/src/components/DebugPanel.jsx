import React, { useEffect, useRef } from 'react'
import { Terminal, X } from 'lucide-react'
import { Button } from './Button'
import { formatTimestamp } from '../lib/utils'
import { cn } from '../lib/utils'

export function DebugPanel({ logs, isOpen, onClose }) {
  const logsEndRef = useRef(null)

  useEffect(() => {
    if (isOpen && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, isOpen])

  if (!isOpen) return null

  const getLogColor = (level) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-500'
      case 'WARNING':
        return 'text-yellow-500'
      case 'INFO':
        return 'text-blue-500'
      case 'DEBUG':
        return 'text-gray-500'
      default:
        return 'text-foreground'
    }
  }

  return (
    <div className="fixed right-0 top-0 h-full w-full md:w-1/2 lg:w-2/5 bg-background border-l border-border shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-muted/50">
        <div className="flex items-center gap-2">
          <Terminal className="h-5 w-5 text-primary" />
          <h2 className="font-semibold">Debug Logs</h2>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-5 w-5" />
        </Button>
      </div>

      {/* Logs Container */}
      <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-1 bg-black/5 dark:bg-black/20">
        {logs.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <p>No logs yet. Ask a question to see the RAG pipeline in action.</p>
          </div>
        ) : (
          <>
            {logs.map((log, idx) => {
              // Check if this is a delimiter line
              const isDelimiter = log.message && log.message.includes('='.repeat(20))
              const isNewQuery = log.message && log.message.includes('NEW QUERY')
              const isCompleted = log.message && log.message.includes('QUERY COMPLETED')
              
              if (isDelimiter) {
                return (
                  <div key={idx} className="border-t-2 border-primary/30 my-2" />
                )
              }
              
              if (isNewQuery) {
                return (
                  <div key={idx} className="bg-primary/10 px-3 py-2 rounded-md my-2 border-l-4 border-primary">
                    <span className="text-primary font-bold text-sm">{log.message}</span>
                  </div>
                )
              }
              
              if (isCompleted) {
                return (
                  <div key={idx} className="bg-green-500/10 px-3 py-2 rounded-md my-2 border-l-4 border-green-500">
                    <span className="text-green-600 dark:text-green-400 font-bold text-sm">{log.message}</span>
                  </div>
                )
              }
              
              return (
                <div key={idx} className="flex gap-2 hover:bg-muted/50 px-2 py-1 rounded text-xs">
                  <span className="text-muted-foreground shrink-0 w-20">
                    {formatTimestamp(log.timestamp)}
                  </span>
                  <span className={cn('shrink-0 font-semibold w-16', getLogColor(log.level))}>
                    [{log.level}]
                  </span>
                  {log.logger && (
                    <span className="text-muted-foreground shrink-0 w-32 truncate" title={log.logger}>
                      {log.logger.split('.').pop()}
                    </span>
                  )}
                  <span className="text-foreground/90 flex-1">{log.message}</span>
                </div>
              )
            })}
            <div ref={logsEndRef} />
          </>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-border bg-muted/50 text-xs text-muted-foreground">
        <p>
          <strong>Tip:</strong> These logs show the RAG pipeline steps: embedding generation, vector search, chunk
          retrieval, and LLM generation.
        </p>
      </div>
    </div>
  )
}
