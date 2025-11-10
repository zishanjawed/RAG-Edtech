import { cn } from '@/lib/utils'
import React from 'react'

export interface PageShellProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  fullBleed?: boolean
}

/**
 * Provides consistent page gutters and max-width.
 * fullBleed allows sections to escape the max width when needed.
 */
export function PageShell({ className, children, fullBleed = false, ...props }: PageShellProps) {
  return (
    <div className={cn('w-full', className)} {...props}>
      <div className={cn(fullBleed ? '' : 'mx-auto w-full max-w-[1200px] px-4 sm:px-6 lg:px-8')}>
        {children}
      </div>
    </div>
  )
}


