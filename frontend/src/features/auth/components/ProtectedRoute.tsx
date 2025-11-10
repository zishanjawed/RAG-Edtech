/**
 * ProtectedRoute Component
 * HOC to protect routes that require authentication
 */
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Spinner } from '@/components/ui'

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  // Show loading spinner while checking auth state
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

