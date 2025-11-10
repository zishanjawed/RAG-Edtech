/**
 * DashboardPage
 * Role-based dashboard router
 */
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { Spinner } from '@/components/ui'

export function DashboardPage() {
  const navigate = useNavigate()
  const { user, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && user) {
      // Redirect based on user role
      if (user.role === 'teacher') {
        navigate('/teacher/dashboard', { replace: true })
      } else {
        navigate('/analytics', { replace: true })
      }
    }
  }, [navigate, user, isLoading])

  // Show loading spinner while determining role
  return (
    <div className="flex h-screen items-center justify-center">
      <Spinner size="lg" />
    </div>
  )
}

