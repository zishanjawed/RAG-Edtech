import React from 'react'
import { cn } from '@/lib/utils'

export interface TextRevealProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  delayMs?: number
}

/**
 * Subtle text reveal using clip-path and opacity, reduced-motion safe.
 */
export function TextReveal({ className, children, delayMs = 0, ...props }: TextRevealProps) {
  return (
    <div
      className={cn(
        'motion-safe:[--reveal-delay:0ms] motion-safe:opacity-0 motion-safe:animate-[reveal_600ms_ease_forwards]',
        className
      )}
      style={{ animationDelay: `${delayMs}ms` } as React.CSSProperties}
      {...props}
    >
      {children}
      <style>{`
        @keyframes reveal {
          0% { opacity: 0; transform: translateY(6px) }
          100% { opacity: 1; transform: translateY(0) }
        }
      `}</style>
    </div>
  )
}


