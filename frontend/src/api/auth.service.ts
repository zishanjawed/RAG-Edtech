/**
 * Authentication Service
 * API calls for authentication
 */
import { apiClient } from './client'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  RefreshTokenResponse,
  User,
} from './types'

export const authService = {
  /**
   * Login user
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/api/auth/login', {
      email: credentials.email,
      password: credentials.password,
    })

    return response.data
  },

  /**
   * Register new user
   */
  async register(data: RegisterRequest): Promise<RegisterResponse> {
    const response = await apiClient.post<RegisterResponse>('/api/auth/register', data)
    return response.data
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    const response = await apiClient.post<RefreshTokenResponse>('/api/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  },

  /**
   * Logout (clear tokens)
   */
  logout(): void {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  /**
   * Get current user using access token
   */
  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/api/auth/me')
    return response.data
  },

  /**
   * Update profile (full_name only)
   */
  async updateProfile(data: { full_name?: string }): Promise<User> {
    const response = await apiClient.patch<User>('/api/auth/profile', data)
    return response.data
  },

  /**
   * Change password
   */
  async changePassword(data: { current_password: string; new_password: string }): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/api/auth/change-password', data)
    return response.data
  },
}

