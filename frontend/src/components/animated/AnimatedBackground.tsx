import { cn } from '@/lib/utils'

export interface AnimatedBackgroundProps {
  className?: string
  opacity?: number
}

/**
 * Animated mesh gradient background using pure CSS.
 * Respects reduced motion preferences.
 */
export function AnimatedBackground({ className, opacity = 0.5 }: AnimatedBackgroundProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        'pointer-events-none absolute inset-0 -z-10 overflow-hidden',
        'bg-[radial-gradient(1200px_600px_at_0%_0%,hsl(var(--primary)/0.18),transparent_60%),radial-gradient(800px_400px_at_100%_30%,hsl(var(--accent)/0.18),transparent_60%),radial-gradient(1000px_500px_at_50%_100%,hsl(var(--secondary-foreground)/0.06),transparent_60%)]',
        'motion-safe:animate-none',
        className
      )}
      style={{ opacity }}
    />
  )
}


