/**
 * Input Component
 * Modern input with floating labels, validation states, and animations
 */
import { forwardRef, InputHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement | HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  variant?: 'text' | 'email' | 'password' | 'textarea' | 'number' | 'tel'
  rows?: number
}

export const Input = forwardRef<HTMLInputElement | HTMLTextAreaElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      variant = 'text',
      className,
      rows = 4,
      disabled,
      ...props
    },
    ref
  ) => {
    const isTextarea = variant === 'textarea'
    const inputType = variant === 'textarea' ? undefined : variant
    const hasError = !!error

    const baseStyles = cn(
      'w-full rounded-lg border bg-background transition-all duration-200',
      'placeholder:text-muted-foreground',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
      'disabled:cursor-not-allowed disabled:opacity-50',
      hasError
        ? 'border-destructive focus-visible:ring-destructive/40'
        : 'border-input focus-visible:ring-primary/40',
      isTextarea ? 'px-4 py-3 resize-none' : 'h-10',
      // Padding based on icon presence
      !isTextarea && (leftIcon ? 'pl-12' : 'pl-4'),
      !isTextarea && (rightIcon ? 'pr-14' : 'pr-4'),
      className
    )

    const InputElement = isTextarea ? 'textarea' : 'input'

    return (
      <div className="w-full">
        {/* Label */}
        {label && (
          <label className={cn(
            "mb-2 block text-sm font-medium",
            hasError ? "text-destructive" : "text-foreground"
          )}>
            {label}
          </label>
        )}

        <div className="relative">
          {/* Left Icon */}
          {leftIcon && (
            <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground inline-flex items-center [&>*]:h-4 [&>*]:w-4">
              {leftIcon}
            </div>
          )}

          {/* Input Element */}
          <InputElement
            ref={ref as React.Ref<HTMLInputElement & HTMLTextAreaElement>}
            type={inputType}
            disabled={disabled}
            rows={isTextarea ? rows : undefined}
            className={baseStyles}
            aria-invalid={hasError}
            aria-describedby={
              error ? `${props.id}-error` : helperText ? `${props.id}-helper` : undefined
            }
            {...(props as React.InputHTMLAttributes<HTMLInputElement & HTMLTextAreaElement>)}
          />

          {/* Right Icon */}
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground inline-flex items-center [&>*]:h-4 [&>*]:w-4">
              {rightIcon}
            </div>
          )}
        </div>

        {/* Helper Text / Error */}
        {(error || helperText) && (
          <div className="mt-1.5">
            {error && (
              <p id={`${props.id}-error`} className="text-sm text-destructive">
                {error}
              </p>
            )}
            {!error && helperText && (
              <p id={`${props.id}-helper`} className="text-sm text-muted-foreground">
                {helperText}
              </p>
            )}
          </div>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

