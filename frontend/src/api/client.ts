/**
 * API Client
 * Axios instances with request/response interceptors for multiple services
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/features/auth/stores/authStore'
import type { ApiError } from './types'

// Import auth store for token synchronization (Zustand store can be used outside React)

// API Configuration for different services
export const API_CONFIG = {
  gateway: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  analytics: import.meta.env.VITE_ANALYTICS_URL || 'http://localhost:8005',
  ragQuery: import.meta.env.VITE_RAG_QUERY_URL || 'http://localhost:8004',
}

// Create axios instance factory
function createApiClient(baseURL: string): AxiosInstance {
  return axios.create({
    baseURL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  })
}

// Create separate clients for each service
export const gatewayClient = createApiClient(API_CONFIG.gateway)
export const analyticsClient = createApiClient(API_CONFIG.analytics)
export const ragQueryClient = createApiClient(API_CONFIG.ragQuery)

// Default client (gateway) for backward compatibility
export const apiClient = gatewayClient

// Request interceptor factory
function addRequestInterceptor(client: AxiosInstance) {
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = localStorage.getItem('access_token')

      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }

      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )
}

// Response interceptor factory
function addResponseInterceptor(client: AxiosInstance) {
  client.interceptors.response.use(
    (response) => {
      // Check if response contains an error field (backend error in success response)
      if (response.data && typeof response.data === 'object' && 'error' in response.data) {
        const errorData = response.data as { error: string; message: string; status_code?: number; details?: unknown }
        
        // Create a proper error object
        const apiError: ApiError = {
          message: errorData.message || 'An error occurred',
          status: errorData.status_code || response.status,
          details: errorData.details,
        }
        
        return Promise.reject(apiError)
      }
      
      return response
    },
    async (error: AxiosError<ApiError>) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

      // Handle 401 Unauthorized - Token expired
      // Don't retry if this is already a retry attempt, or if this is the refresh endpoint itself
      const isRefreshEndpoint = originalRequest.url?.includes('/api/auth/refresh')
      if (error.response?.status === 401 && !originalRequest._retry && !isRefreshEndpoint) {
        originalRequest._retry = true

        try {
          const refreshToken = localStorage.getItem('refresh_token')

          if (!refreshToken) {
            // No refresh token, logout user
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            window.location.href = '/login'
            return Promise.reject(error)
          }

          // Try to refresh token (always use gateway for auth)
          const response = await axios.post(`${API_CONFIG.gateway}/api/auth/refresh`, {
            refresh_token: refreshToken,
          })

          const { access_token } = response.data

          // Save new token to localStorage
          localStorage.setItem('access_token', access_token)

          // Sync with auth store
          try {
            const authStore = useAuthStore
            authStore.getState().setToken(access_token)
          } catch (storeError) {
            // Failed to sync token
          }

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`
          }

          return client(originalRequest)
        } catch (refreshError) {
          // Refresh failed, logout user
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          
          // Try to logout through auth store
          try {
            const authStore = useAuthStore
            authStore.getState().logout()
          } catch (storeError) {
            // Failed to logout
          }
          
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }

      // Handle other errors
      const apiError: ApiError = {
        message: error.response?.data?.message || error.message || 'An error occurred',
        status: error.response?.status,
        code: error.code,
        details: error.response?.data,
      }

      return Promise.reject(apiError)
    }
  )
}

// Add interceptors to all clients
addRequestInterceptor(gatewayClient)
addRequestInterceptor(analyticsClient)
addRequestInterceptor(ragQueryClient)

addResponseInterceptor(gatewayClient)
addResponseInterceptor(analyticsClient)
addResponseInterceptor(ragQueryClient)


// Helper function to create FormData for file uploads
export function createFormData(data: Record<string, unknown>): FormData {
  const formData = new FormData()

  Object.keys(data).forEach((key) => {
    const value = data[key]
    if (value !== undefined && value !== null) {
      if (value instanceof File) {
        formData.append(key, value)
      } else {
        formData.append(key, String(value))
      }
    }
  })

  return formData
}

