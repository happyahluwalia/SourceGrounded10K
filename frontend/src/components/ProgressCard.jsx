import React, { useState, useEffect } from 'react'
import { CheckCircle2, Loader2, Circle, Info } from 'lucide-react'
import { cn } from '../lib/utils'

export function ProgressCard({ steps, isComplete, onCollapse }) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [showInsight, setShowInsight] = useState(null)

  // Auto-collapse after completion
  useEffect(() => {
    if (isComplete) {
      const timer = setTimeout(() => {
        setIsCollapsed(true)
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [isComplete])

  return (
    <div className="mb-4 rounded-lg border border-border bg-muted/30 animate-fade-in">
      {/* Header - always visible */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-foreground">
            {isComplete ? '✓ Processing Complete' : '⏳ Processing...'}
          </span>
          {isComplete && (
            <span className="text-xs text-muted-foreground">
              (click to {isCollapsed ? 'expand' : 'collapse'})
            </span>
          )}
        </div>
        <svg
          className={`h-4 w-4 text-muted-foreground transition-transform ${
            isCollapsed ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Content - collapsible */}
      {!isCollapsed && (
        <div className="px-4 pb-4 space-y-2 border-t border-border pt-3">
          {Object.entries(steps).map(([stepName, stepData]) => (
            <ProgressStep
              key={stepName}
              name={stepName}
              status={stepData.status}
              duration={stepData.duration}
              metadata={stepData.metadata}
              insight={stepData.insight}
              showInsight={showInsight === stepName}
              onToggleInsight={() => setShowInsight(showInsight === stepName ? null : stepName)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function ProgressStep({ name, status, duration, metadata, insight, showInsight, onToggleInsight }) {
  const getIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'in_progress':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      default:
        return <Circle className="h-4 w-4 text-muted-foreground" />
    }
  }

  const getStepLabel = () => {
    const labels = {
      planning: 'Planning search strategy',
      fetching: 'Fetching & searching documents',
      synthesis: 'Generating answer'
    }
    return labels[name] || name
  }

  return (
    <div className="flex items-start gap-2">
      <div className="mt-0.5">{getIcon()}</div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className={cn(
            'text-sm font-medium',
            status === 'completed' && 'text-muted-foreground',
            status === 'in_progress' && 'text-foreground',
            status === 'pending' && 'text-muted-foreground'
          )}>
            {getStepLabel()}
          </span>
          {duration && (
            <span className="text-xs text-muted-foreground">
              ({duration.toFixed(1)}s)
            </span>
          )}
          {insight && (
            <button
              onClick={onToggleInsight}
              className="text-muted-foreground hover:text-foreground transition-colors"
              title="Show insight"
            >
              <Info className="h-3 w-3" />
            </button>
          )}
        </div>
        {metadata && Object.keys(metadata).length > 0 && (
          <div className="mt-2">
            {/* Show plan for planning step */}
            {name === 'planning' && metadata.plan && (
              <div className="p-3 rounded bg-muted/50 border border-border">
                <div className="text-xs font-semibold text-muted-foreground mb-1">
                  Execution Plan:
                </div>
                <div className="text-sm font-mono text-foreground whitespace-pre-wrap break-all leading-relaxed">
                  {JSON.stringify(metadata.plan, null, 2)}
                </div>
              </div>
            )}
            
            {/* Show search results for searching step */}
            {name === 'searching' && (
              <div className="text-xs text-muted-foreground">
                {metadata.chunksFound && `Found ${metadata.chunksFound} chunks`}
                {metadata.topScore && ` • ${(metadata.topScore * 100).toFixed(0)}% relevance`}
              </div>
            )}
          </div>
        )}
        {showInsight && insight && (
          <div className="mt-2 p-2 rounded bg-muted/50 border border-border text-xs">
            <div className="font-semibold text-foreground mb-1">{insight.title}</div>
            <div className="text-muted-foreground mb-1">{insight.content}</div>
            {insight.trade_off && (
              <div className="text-muted-foreground italic">
                Trade-off: {insight.trade_off}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
