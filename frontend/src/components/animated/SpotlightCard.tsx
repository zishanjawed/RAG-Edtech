import React from 'react'
import { cn } from '@/lib/utils'

export interface SpotlightCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

/**
 * Spotlight hover effect using a radial gradient, CSS only.
 * Uses mask-image for smooth spotlight reveal; reduced motion friendly.
 */
export function SpotlightCard({ className, children, ...props }: SpotlightCardProps) {
  return (
    <div
      className={cn(
        'relative rounded-xl transition-shadow shadow-soft-md hover:shadow-soft-lg',
        'bg-card',
        className
      )}
      {...props}
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 rounded-xl opacity-0 transition-opacity duration-200 hover:opacity-100"
        style={{
          background:
            'radial-gradient(400px 200px at var(--x,50%) var(--y,50%), hsl(var(--primary)/0.12), transparent 60%)',
        }}
      />
      <div
        onMouseMove={(e) => {
          const target = e.currentTarget.parentElement as HTMLElement
          const rect = target.getBoundingClientRect()
          target.style.setProperty('--x', `${e.clientX - rect.left}px`)
          target.style.setProperty('--y', `${e.clientY - rect.top}px`)
        }}
        className="relative rounded-xl"
      >
        {children}
      </div>
    </div>
  )
}


