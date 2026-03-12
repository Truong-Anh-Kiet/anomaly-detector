/**
 * Application Type Definitions
 */

// Auth Types
export interface User {
  user_id: string
  username: string
  email: string
  full_name: string
  role: 'admin' | 'analyst' | 'auditor' | 'guest'
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name: string
}

export interface CreateUserRequest {
  username: string
  email: string
  password: string
  full_name: string
  role: 'admin' | 'analyst' | 'auditor' | 'guest'
}

export interface UpdateUserRequest {
  email?: string
  full_name?: string
  role?: 'admin' | 'analyst' | 'auditor' | 'guest'
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

// Anomaly Types
export interface Anomaly {
  anomaly_id: string
  detection_timestamp: string
  category: 'payment' | 'network' | 'behavioral' | 'system'
  amount: number
  score: number
  threshold: number
  status: 'pending_review' | 'confirmed' | 'false_positive' | 'resolved'
  review_notes?: string
  reviewed_by?: string
  user_id?: string
}

export interface AnomalyFilterParams {
  category?: string
  status?: string
  min_score?: number
  max_score?: number
  days?: number
  limit?: number
  offset?: number
}

export interface AnomalyStats {
  total_anomalies: number
  pending_review: number
  confirmed: number
  false_positive: number
  average_score: number
  distribution_by_category: Record<string, number>
}

// Audit Log Types
export interface AuditLog {
  id: string
  user_id: string
  action: string
  resource_type?: string
  resource_id?: string
  details?: Record<string, any>
  timestamp: string
  archived_at?: string
}

export interface AuditLogFilterParams {
  user_id?: string
  action?: string
  days?: number
  limit?: number
  offset?: number
}

// Threshold Types
export interface ThresholdConfig {
  category: string
  min: number
  max: number
  default: number
  description: string
  current_value: number
}

export interface UpdateThresholdRequest {
  category: string
  threshold: number
}

// Settings Types
export interface AppSettings {
  app_name: string
  version: string
  environment: 'development' | 'staging' | 'production'
  default_anomaly_threshold: number
  rate_limit_enabled: boolean
  email_enabled: boolean
}

// API Response Wrapper
export interface ApiResponse<T> {
  data: T
  status: number
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// Error Type
export interface ApiError {
  detail: string
  status_code: number
  error_type?: string
}
