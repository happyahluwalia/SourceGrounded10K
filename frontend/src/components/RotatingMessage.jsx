import React, { useState, useEffect } from 'react'
import { Lightbulb, Sparkles } from 'lucide-react'

export function RotatingMessage({ messages, interval = 5000, isActive = true }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [fade, setFade] = useState(true)

  useEffect(() => {
    if (!isActive || !messages || messages.length === 0) return

    const timer = setInterval(() => {
      setFade(false)
      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % messages.length)
        setFade(true)
      }, 300)
    }, interval)

    return () => clearInterval(timer)
  }, [messages, interval, isActive])

  if (!isActive || !messages || messages.length === 0) {
    return null
  }

  const currentMessage = messages[currentIndex]
  const isPun = currentMessage.category === 'pun'

  return (
    <div
      className={`mt-2 p-3 rounded-lg border border-border bg-gradient-to-r ${
        isPun ? 'from-purple-500/10 to-pink-500/10' : 'from-blue-500/10 to-cyan-500/10'
      } transition-opacity duration-300 ${fade ? 'opacity-100' : 'opacity-0'}`}
    >
      <div className="flex items-start gap-2">
        <div className="mt-0.5">
          {isPun ? (
            <Sparkles className="h-4 w-4 text-purple-500" />
          ) : (
            <Lightbulb className="h-4 w-4 text-blue-500" />
          )}
        </div>
        <div className="flex-1">
          <div className="text-xs font-semibold text-foreground mb-1">
            {isPun ? '💭 While you wait...' : '💡 Did you know?'}
          </div>
          <div className="text-xs text-muted-foreground">
            {currentMessage.content}
          </div>
        </div>
      </div>
    </div>
  )
}
