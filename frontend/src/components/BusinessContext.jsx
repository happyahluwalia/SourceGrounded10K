import React from 'react';
import { Card } from './Card';
import { TrendingUp, TrendingDown, HelpCircle, FileText } from 'lucide-react';

export function BusinessContext({ companyTicker, context, onCitationClick }) {
  if (!context) return null;

  const { growth_drivers, headwinds, explanation, citations } = context;

  return (
    <Card className="mt-4 p-4 bg-secondary/10 border-secondary/20">
      <h3 className="font-semibold text-base mb-3">Business Context for {companyTicker}</h3>
      <div className="space-y-3 text-sm">
        {growth_drivers && (
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-1">
              <TrendingUp className="h-5 w-5 text-green-500" />
            </div>
            <div>
              <h4 className="font-semibold text-muted-foreground">Growth Drivers</h4>
              <p className="text-foreground">{growth_drivers}</p>
            </div>
          </div>
        )}
        {headwinds && (
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-1">
              <TrendingDown className="h-5 w-5 text-red-500" />
            </div>
            <div>
              <h4 className="font-semibold text-muted-foreground">Headwinds</h4>
              <p className="text-foreground">{headwinds}</p>
            </div>
          </div>
        )}
        {explanation && (
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 mt-1">
              <HelpCircle className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <h4 className="font-semibold text-muted-foreground">Analyst Explanation</h4>
              <p className="text-foreground">{explanation}</p>
            </div>
          </div>
        )}
      </div>
      {citations && citations.length > 0 && (
        <div className="mt-3 border-t border-border pt-2 flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted-foreground">Context Sources:</span>
          {citations.map((citationId) => (
            <button
              key={citationId}
              onClick={() => onCitationClick(citationId)}
              className="inline-flex items-center gap-1 text-primary hover:text-primary/80 underline decoration-dotted underline-offset-2 cursor-pointer transition-colors text-xs"
              title="Click to view source"
            >
              Source {citationId + 1}
            </button>
          ))}
        </div>
      )}
    </Card>
  );
}
