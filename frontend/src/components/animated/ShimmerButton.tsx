import React from 'react'
import { cn } from '@/lib/utils'

export interface ShimmerButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
}

/**
 * Button with subtle shimmer border effect (CSS only).
 */
export function ShimmerButton({ className, children, ...props }: ShimmerButtonProps) {
  return (
    <button
      className={cn(
        'relative inline-flex items-center justify-center rounded-lg px-4 py-2',
        'bg-primary text-primary-foreground',
        'before:absolute before:inset-0 before:rounded-lg before:p-px before:content-[""]',
        'before:[background:linear-gradient(90deg,hsl(var(--primary)),hsl(var(--accent)),hsl(var(--primary)))_0_0/200%_100%_no-repeat]',
        'before:opacity-40 motion-safe:before:animate-[shimmer_2.5s_linear_infinite]',
        className
      )}
      {...props}
    >
      <span className="relative z-10">{children}</span>
      <style>{`
        @keyframes shimmer {
          0% { background-position: 0% 0%; }
          100% { background-position: 200% 0%; }
        }
      `}</style>
    </button>
  )
}


