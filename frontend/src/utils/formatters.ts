/**
 * Common Formatters
 * Utility functions for formatting dates, file sizes, numbers, etc.
 */

/**
 * Parse an API date string safely.
 * Many backend dates are ISO without timezone (naive UTC). JS treats those as local time.
 * This helper assumes UTC when the timezone is missing to avoid timezone drift (e.g., -6h).
 */
export function parseApiDate(date: Date | string): Date {
  if (date instanceof Date) return date
  if (!date) return new Date(NaN)
  const hasTimezone = /([zZ]|[+-]\d{2}:\d{2})$/.test(date)
  const normalized = hasTimezone ? date : `${date}Z`
  return new Date(normalized)
}

/**
 * Format date to readable string
 * @example formatDate(new Date()) => "Nov 7, 2025"
 */
export function formatDate(date: Date | string): string {
  const d = parseApiDate(date)
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

/**
 * Format date with time
 * @example formatDateTime(new Date()) => "Nov 7, 2025 at 2:30 PM"
 */
export function formatDateTime(date: Date | string): string {
  const d = parseApiDate(date)
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

/**
 * Format relative time (time ago)
 * @example formatRelativeTime(Date.now() - 60000) => "1 minute ago"
 */
export function formatRelativeTime(date: Date | string): string {
  const d = parseApiDate(date)
  const now = new Date()
  const seconds = Math.floor((now.getTime() - d.getTime()) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`
  if (seconds < 2592000) return `${Math.floor(seconds / 604800)} weeks ago`
  if (seconds < 31536000) return `${Math.floor(seconds / 2592000)} months ago`
  return `${Math.floor(seconds / 31536000)} years ago`
}

/**
 * Format file size to human-readable string
 * @example formatFileSize(1024) => "1 KB"
 * @example formatFileSize(1048576) => "1 MB"
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'

  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${units[i]}`
}

/**
 * Format number with commas
 * @example formatNumber(1234567) => "1,234,567"
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('en-US')
}

/**
 * Format percentage
 * @example formatPercentage(0.1234) => "12.34%"
 */
export function formatPercentage(value: number, decimals: number = 2): string {
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * Format duration in seconds to human-readable string
 * @example formatDuration(125) => "2m 5s"
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`

  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60

  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  }

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60

  if (remainingMinutes > 0) {
    return `${hours}h ${remainingMinutes}m`
  }

  return `${hours}h`
}

/**
 * Truncate text with ellipsis
 * @example truncate("Hello World", 8) => "Hello..."
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - 3) + '...'
}

/**
 * Get initials from name
 * @example getInitials("John Doe") => "JD"
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

/**
 * Format grade level
 * @example formatGradeLevel("grade_11") => "Grade 11"
 */
export function formatGradeLevel(grade: string): string {
  if (grade.startsWith('grade_')) {
    const num = grade.replace('grade_', '')
    return `Grade ${num}`
  }
  return grade
}

/**
 * Capitalize first letter
 * @example capitalize("hello") => "Hello"
 */
export function capitalize(text: string): string {
  if (!text) return text
  return text.charAt(0).toUpperCase() + text.slice(1)
}

/**
 * Format role name
 * @example formatRole("student") => "Student"
 * @example formatRole("instructor") => "Instructor"
 */
export function formatRole(role: string): string {
  return capitalize(role)
}

