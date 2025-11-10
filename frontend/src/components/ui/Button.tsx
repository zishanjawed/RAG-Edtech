/**
 * Button Component
 * Modern button with gradient effects, ripple animation, and variants
 */
import { forwardRef, ButtonHTMLAttributes } from 'react'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default:
          'bg-primary text-primary-foreground shadow-soft-sm hover:shadow-soft-md hover:-translate-y-px active:scale-[0.98] focus-visible:ring-primary/40',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80 shadow-soft-sm hover:shadow-soft-md hover:-translate-y-px',
        outline:
          'border-2 border-input bg-background hover:bg-accent hover:text-accent-foreground hover:-translate-y-px',
        ghost:
          'hover:bg-accent hover:text-accent-foreground',
        link:
          'text-primary underline-offset-4 hover:underline',
        destructive:
          'bg-destructive text-destructive-foreground shadow-soft-sm hover:shadow-soft-md hover:-translate-y-px active:scale-[0.98]',
      },
      size: {
        sm: 'h-9 px-3 text-sm',
        md: 'h-10 px-4 py-2',
        lg: 'h-11 px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
)

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  ripple?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant,
      size,
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading

    return (
      <motion.button
        ref={ref}
        disabled={isDisabled}
        className={cn(buttonVariants({ variant, size }), className)}
        whileTap={!isDisabled ? { scale: 0.97 } : undefined}
        whileHover={!isDisabled ? { scale: 1.02 } : undefined}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
        {...props}
      >
        {isLoading && (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <Loader2 className="mr-2 h-4 w-4" />
          </motion.div>
        )}
        {!isLoading && leftIcon && <span className="inline-flex items-center mr-2 [&>*]:h-4 [&>*]:w-4">{leftIcon}</span>}
        {children}
        {!isLoading && rightIcon && <span className="inline-flex items-center ml-2 [&>*]:h-4 [&>*]:w-4">{rightIcon}</span>}
      </motion.button>
    )
  }
)

Button.displayName = 'Button'

