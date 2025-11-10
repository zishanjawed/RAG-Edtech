import React from 'react'
import { cn } from '@/lib/utils'

export interface FloatingDockProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

/**
 * Mobile floating dock container (add nav items as children).
 */
export function FloatingDock({ className, children, ...props }: FloatingDockProps) {
  return (
    <div
      className={cn(
        'fixed inset-x-0 bottom-4 z-50 mx-auto w-[92%] rounded-2xl border bg-card/90 backdrop-blur-md shadow-soft-lg md:hidden',
        className
      )}
      {...props}
    >
      <div className="flex items-center justify-around p-2">{children}</div>
    </div>
  )
}


