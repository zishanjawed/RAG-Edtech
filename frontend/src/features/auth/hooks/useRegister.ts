/**
 * useRegister Hook
 * React Query mutation for registration
 */
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './useAuth'
import { useToast } from '@/hooks/useToast'
import type { RegisterRequest } from '@/api/types'

export function useRegister() {
  const { register } = useAuth()
  const { success, error } = useToast()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: RegisterRequest) => register(data),
    onSuccess: () => {
      success('Registration successful', 'Please login to continue')
      navigate('/login')
    },
    onError: (err: Error) => {
      error('Registration failed', err.message || 'Please try again')
    },
  })
}

