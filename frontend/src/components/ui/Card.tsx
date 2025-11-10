/**
 * Card Component
 * Modern card with gradient borders, glassmorphism, and hover effects
 */
import { HTMLAttributes, ReactNode } from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import type { Transition } from 'framer-motion'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const cardVariants = cva(
  'rounded-xl overflow-hidden transition-all duration-300',
  {
    variants: {
      variant: {
        default: 'bg-card text-card-foreground shadow-soft-md',
        elevated: 'bg-card text-card-foreground shadow-soft-lg',
        bordered: 'bg-card text-card-foreground border-2 border-border',
        glass: 'glass shadow-soft-md',
      },
      hover: {
        true: 'hover:shadow-soft-lg hover:-translate-y-1 cursor-pointer',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      hover: false,
    },
  }
)

export interface CardProps
  extends Omit<HTMLMotionProps<"div">, "children">,
    VariantProps<typeof cardVariants> {
  children: ReactNode
  gradientBorder?: boolean
  animated?: boolean
}

export interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export interface CardBodyProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export function Card({
  variant,
  hover,
  gradientBorder = false,
  animated = false,
  className,
  children,
  ...props
}: CardProps) {
  const hoverAnimation = hover || animated ? {
    y: -4,
    boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"
  } : undefined

  const transition: Transition = {
    type: "spring",
    stiffness: 300,
    damping: 20
  }

  if (gradientBorder) {
    return (
      <motion.div
        className={cn('p-px rounded-xl bg-gradient-to-br from-primary/20 via-transparent to-accent/20', className)}
        whileHover={hoverAnimation}
        transition={transition}
        {...props}
      >
        <div className={cn(cardVariants({ variant, hover: false }), 'rounded-[calc(0.75rem-1px)] relative')}>
          {children}
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      className={cn(cardVariants({ variant, hover: false }), className, 'relative')}
      whileHover={hoverAnimation}
      transition={transition}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export function CardHeader({ className, children, ...props }: CardHeaderProps) {
  return (
    <div className={cn('px-6 py-5', className)} {...props}>
      {children}
    </div>
  )
}

export function CardBody({ className, children, ...props }: CardBodyProps) {
  return (
    <div className={cn('px-6 py-4', className)} {...props}>
      {children}
    </div>
  )
}

export function CardFooter({ className, children, ...props }: CardFooterProps) {
  return (
    <div className={cn('px-6 py-4 flex items-center', className)} {...props}>
      {children}
    </div>
  )
}

// Alias CardContent to CardBody for shadcn compatibility
export const CardContent = CardBody

Card.Header = CardHeader
Card.Body = CardBody
Card.Footer = CardFooter

