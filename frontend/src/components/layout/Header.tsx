import { cn } from '@/lib/utils'
import { Bell } from 'lucide-react'
import React from 'react'
import { ThemeToggle } from '@/components/ui/theme-toggle'

export interface HeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  actions?: React.ReactNode
  children?: React.ReactNode
}

export function Header({ title, actions, className, children, ...props }: HeaderProps) {
  return (
    <div
      className={cn(
        'sticky top-0 z-40 flex h-14 items-center justify-between border-b bg-background/70 px-4 backdrop-blur-md',
        className
      )}
      {...props}
    >
      <div className="flex min-w-0 items-center gap-3">
        {title && <div className="truncate font-semibold text-foreground">{title}</div>}
        {children && <div className="hidden sm:block text-sm text-muted-foreground truncate">{children}</div>}
      </div>
      <div className="flex items-center gap-2">
        {actions}
        <ThemeToggle />
        <button
          type="button"
          aria-label="Notifications"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md hover:bg-accent text-muted-foreground"
        >
          <Bell className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}


