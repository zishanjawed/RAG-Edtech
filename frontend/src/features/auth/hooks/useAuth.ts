/**
 * useAuth Hook
 * Access authentication state and actions
 */
import { useAuthStore } from '../stores/authStore'

export function useAuth() {
  const { user, token, isAuthenticated, isLoading, login, register, logout, refreshToken } =
    useAuthStore()

  return {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshToken,
  }
}

