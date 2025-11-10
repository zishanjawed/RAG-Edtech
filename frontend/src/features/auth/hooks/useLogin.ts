/**
 * useLogin Hook
 * React Query mutation for login
 */
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './useAuth'
import { useAuthStore } from '../stores/authStore'
import { useToast } from '@/hooks/useToast'
import type { LoginRequest } from '@/api/types'

export function useLogin() {
  const { login } = useAuth()
  const { success, error } = useToast()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (credentials: LoginRequest) => login(credentials),
    onSuccess: () => {
      success('Login successful', 'Welcome back!')
      
      // Redirect based on user role
      // Note: user state should be updated by login() before onSuccess is called
      const currentUser = useAuthStore.getState().user
      if (currentUser?.role === 'teacher') {
        navigate('/teacher/dashboard')
      } else {
        navigate('/analytics')
      }
    },
    onError: (err: Error) => {
      error('Login failed', err.message || 'Invalid email or password')
    },
  })
}

