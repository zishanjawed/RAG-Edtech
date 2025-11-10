/**
 * Avatar Component
 * User avatar with image fallback to initials
 */
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { getInitials } from '@/utils/formatters'

export interface AvatarProps {
  src?: string
  alt?: string
  name?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  status?: 'online' | 'offline' | 'away' | 'busy'
  showStatus?: boolean
  className?: string
}

const avatarSizes = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-12 w-12 text-base',
  xl: 'h-16 w-16 text-lg',
}

const statusColors = {
  online: 'bg-green-500',
  offline: 'bg-slate-400',
  away: 'bg-yellow-500',
  busy: 'bg-red-500',
}

const statusSizes = {
  sm: 'h-2 w-2',
  md: 'h-2.5 w-2.5',
  lg: 'h-3 w-3',
  xl: 'h-4 w-4',
}

export function Avatar({
  src,
  alt,
  name = 'User',
  size = 'md',
  status,
  showStatus = false,
  className,
}: AvatarProps) {
  const [imageError, setImageError] = useState(false)

  const showInitials = !src || imageError
  const initials = getInitials(name)

  return (
    <div className={cn('relative inline-block', className)}>
      <div
        className={cn(
          'flex items-center justify-center rounded-full overflow-hidden',
          'bg-gradient-to-br from-primary-400 to-secondary-400 text-white font-semibold',
          avatarSizes[size]
        )}
      >
        {showInitials ? (
          <span>{initials}</span>
        ) : (
          <img
            src={src}
            alt={alt || name}
            className="h-full w-full object-cover"
            onError={() => setImageError(true)}
          />
        )}
      </div>

      {/* Status Indicator */}
      {showStatus && status && (
        <span
          className={cn(
            'absolute bottom-0 right-0 block rounded-full ring-2 ring-white',
            statusColors[status],
            statusSizes[size]
          )}
          aria-label={`Status: ${status}`}
        />
      )}
    </div>
  )
}

