/**
 * Badge Component
 * Label badges with variants and optional dot indicator
 */
import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface BadgeProps {
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'error' | 'info'
  size?: 'sm' | 'md' | 'lg'
  dot?: boolean
  children: ReactNode
  className?: string
}

const badgeVariants = {
  default: 'bg-slate-100 text-slate-700 border-slate-200',
  secondary: 'bg-primary-100 text-primary-700 border-primary-200',
  success: 'bg-accent-100 text-accent-700 border-accent-200',
  warning: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  error: 'bg-red-100 text-red-700 border-red-200',
  info: 'bg-blue-100 text-blue-700 border-blue-200',
}

const badgeSizes = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
}

const dotVariants = {
  default: 'bg-slate-500',
  secondary: 'bg-primary-500',
  success: 'bg-accent-500',
  warning: 'bg-yellow-500',
  error: 'bg-red-500',
  info: 'bg-blue-500',
}

export function Badge({
  variant = 'default',
  size = 'md',
  dot = false,
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border font-medium',
        badgeVariants[variant],
        badgeSizes[size],
        className
      )}
    >
      {dot && <span className={cn('h-1.5 w-1.5 rounded-full', dotVariants[variant])} />}
      {children}
    </span>
  )
}

