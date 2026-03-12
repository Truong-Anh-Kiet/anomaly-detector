/**
 * API Service Layer
 * Handles all backend communication
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  User,
  LoginRequest,
  RegisterRequest,
  CreateUserRequest,
  UpdateUserRequest,
  AuthResponse,
  Anomaly,
  AnomalyFilterParams,
  AnomalyStats,
  AuditLog,
  AuditLogFilterParams,
  ThresholdConfig,
  UpdateThresholdRequest,
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

class ApiService {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add token to requests
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Handle token refresh on 401
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Try to refresh token
          try {
            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
              const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                refresh_token: refreshToken,
              })
              const { access_token } = response.data
              localStorage.setItem('access_token', access_token)
              // Retry original request
              return this.client(error.config!)
            }
          } catch {
            // Refresh failed, clear auth and redirect to login
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            window.location.href = '/login'
          }
        }
        return Promise.reject(error)
      }
    )
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post('/auth/login', credentials)
    return response.data
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await this.client.post('/auth/register', data)
    return response.data
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout')
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get('/auth/me')
    return response.data
  }

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await this.client.post('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  }

  // Anomaly endpoints
  async getAnomalies(params?: AnomalyFilterParams): Promise<Anomaly[]> {
    const response = await this.client.get('/anomalies', { params })
    return response.data
  }

  async getAnomaly(id: string): Promise<Anomaly> {
    const response = await this.client.get(`/anomalies/${id}`)
    return response.data
  }

  async createAnomaly(data: Partial<Anomaly>): Promise<Anomaly> {
    const response = await this.client.post('/anomalies', data)
    return response.data
  }

  async updateAnomalyStatus(
    id: string,
    status: string,
    notes?: string
  ): Promise<Anomaly> {
    const response = await this.client.patch(`/anomalies/${id}`, {
      status,
      review_notes: notes,
    })
    return response.data
  }

  async getAnomalyStats(): Promise<AnomalyStats> {
    const response = await this.client.get('/anomalies/stats')
    return response.data
  }

  async exportAnomalies(format: 'json' | 'csv', filters?: AnomalyFilterParams): Promise<Blob> {
    const response = await this.client.get('/anomalies/export', {
      params: { ...filters, format },
      responseType: 'blob',
    })
    return response.data
  }

  // Audit log endpoints
  async getAuditLogs(params?: AuditLogFilterParams): Promise<AuditLog[]> {
    const response = await this.client.get('/audit-logs', { params })
    return response.data
  }

  async getAuditLogStats(): Promise<Record<string, any>> {
    const response = await this.client.get('/audit-logs/stats')
    return response.data
  }

  // Threshold endpoints
  async getThresholds(): Promise<ThresholdConfig[]> {
    const response = await this.client.get('/thresholds')
    return response.data
  }

  async updateThreshold(data: UpdateThresholdRequest): Promise<ThresholdConfig> {
    const response = await this.client.put(`/thresholds/${data.category}`, data)
    return response.data
  }

  // User endpoints
  async getUsers(): Promise<User[]> {
    const response = await this.client.get('/users')
    return response.data
  }

  async getUser(id: string): Promise<User> {
    const response = await this.client.get(`/users/${id}`)
    return response.data
  }

  async createUser(data: CreateUserRequest): Promise<User> {
    const response = await this.client.post('/users', data)
    return response.data
  }

  async updateUser(id: string, data: UpdateUserRequest): Promise<User> {
    const response = await this.client.put(`/users/${id}`, data)
    return response.data
  }

  async deleteUser(id: string): Promise<void> {
    await this.client.delete(`/users/${id}`)
  }

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await this.client.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    })
  }

  // Health check
  async getHealth(): Promise<Record<string, any>> {
    const response = await this.client.get('/health')
    return response.data
  }
}

export const apiService = new ApiService()
