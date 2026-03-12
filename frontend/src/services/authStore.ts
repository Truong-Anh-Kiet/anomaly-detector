/**
 * Auth Store - Zustand state management
 */

import { create } from 'zustand'
import { apiService } from '@/services/api'
import type { User, LoginRequest, RegisterRequest } from '@/types'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isLoading: boolean
  error: string | null

  // Actions
  login: (credentials: LoginRequest) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  loadUser: () => Promise<void>
  setError: (error: string | null) => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isLoading: false,
  error: null,

  login: async (credentials: LoginRequest) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiService.login(credentials)
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      set({
        user: response.user,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Login failed'
      set({ error: errorMsg, isLoading: false })
      throw error
    }
  },

  register: async (data: RegisterRequest) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiService.register(data)
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
      set({
        user: response.user,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Registration failed'
      set({ error: errorMsg, isLoading: false })
      throw error
    }
  },

  logout: async () => {
    set({ isLoading: true })
    try {
      await apiService.logout()
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isLoading: false,
      })
    }
  },

  loadUser: async () => {
    set({ isLoading: true })
    try {
      const user = await apiService.getCurrentUser()
      set({ user, isLoading: false })
    } catch (error: any) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isLoading: false,
      })
    }
  },

  setError: (error: string | null) => set({ error }),
  clearError: () => set({ error: null }),
}))
