/**
 * StreamingText Component
 * Displays text character-by-character with typing cursor animation
 */
import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

export interface StreamingTextProps {
  text: string
  speed?: number // milliseconds per character
  showCursor?: boolean
  onComplete?: () => void
  className?: string
}

export function StreamingText({
  text,
  speed = 30,
  showCursor = true,
  onComplete,
  className,
}: StreamingTextProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [isComplete, setIsComplete] = useState(false)

  useEffect(() => {
    if (!text) {
      setDisplayedText('')
      setIsComplete(false)
      return
    }

    // Reset if text changes
    setDisplayedText('')
    setIsComplete(false)

    let currentIndex = 0
    const intervalId = setInterval(() => {
      if (currentIndex < text.length) {
        setDisplayedText(text.slice(0, currentIndex + 1))
        currentIndex++
      } else {
        setIsComplete(true)
        clearInterval(intervalId)
        onComplete?.()
      }
    }, speed)

    return () => clearInterval(intervalId)
  }, [text, speed, onComplete])

  return (
    <span className={cn('inline', className)}>
      {displayedText}
      {showCursor && !isComplete && (
        <span className="ml-0.5 inline-block h-4 w-0.5 animate-blink bg-current" />
      )}
    </span>
  )
}

