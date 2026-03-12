/**
 * Custom Hooks for API calls
 */

import { useState, useCallback, useEffect } from 'react'
import { apiService } from '@/services/api'
import type { Anomaly, AnomalyFilterParams, AnomalyStats, User, CreateUserRequest, UpdateUserRequest } from '@/types'

// Generic hook for API calls
export function useApiCall<T>(
  apiFunction: () => Promise<T>,
  immediate = true
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await apiFunction()
      setData(result)
      return result
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'An error occurred'
      setError(errorMsg)
      throw err
    } finally {
      setLoading(false)
    }
  }, [apiFunction])

  useEffect(() => {
    if (immediate) {
      execute()
    }
  }, [execute, immediate])

  return { data, loading, error, execute, setError }
}

// Hook for fetching anomalies
export function useAnomalies(filters?: AnomalyFilterParams) {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAnomalies = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiService.getAnomalies(filters)
      setAnomalies(data)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to fetch anomalies'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    fetchAnomalies()
  }, [fetchAnomalies])

  const updateStatus = useCallback(
    async (anomalyId: string, status: string, notes?: string) => {
      try {
        const updated = await apiService.updateAnomalyStatus(anomalyId, status, notes)
        setAnomalies((prev) =>
          prev.map((a) => (a.anomaly_id === anomalyId ? updated : a))
        )
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || 'Failed to update anomaly'
        setError(errorMsg)
        throw err
      }
    },
    []
  )

  return { anomalies, loading, error, refetch: fetchAnomalies, updateStatus }
}

// Hook for anomaly statistics
export function useAnomalyStats() {
  const [stats, setStats] = useState<AnomalyStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiService.getAnomalyStats()
      setStats(data)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to fetch statistics'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStats()
    // Refresh stats every minute
    const interval = setInterval(fetchStats, 60000)
    return () => clearInterval(interval)
  }, [fetchStats])

  return { stats, loading, error, refetch: fetchStats }
}

// Hook for audit logs
export function useAuditLogs(days = 30) {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiService.getAuditLogs({ days, limit: 100 })
      setLogs(data)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to fetch audit logs'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  return { logs, loading, error, refetch: fetchLogs }
}

// Hook for thresholds
export function useThresholds() {
  const [thresholds, setThresholds] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchThresholds = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiService.getThresholds()
      setThresholds(data)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to fetch thresholds'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }, [])

  const updateThreshold = useCallback(async (category: string, threshold: number) => {
    try {
      const updated = await apiService.updateThreshold({
        category,
        threshold,
      })
      setThresholds((prev) =>
        prev.map((t: any) => (t.category === category ? updated : t))
      )
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update threshold'
      setError(errorMsg)
      throw err
    }
  }, [])

  useEffect(() => {
    fetchThresholds()
  }, [fetchThresholds])

  return { thresholds, loading, error, refetch: fetchThresholds, updateThreshold }
}

// Hook for user management
export function useUsers() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiService.getUsers()
      setUsers(data)
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to fetch users'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }, [])

  const createUser = useCallback(async (userData: CreateUserRequest) => {
    try {
      const newUser = await apiService.createUser(userData)
      setUsers((prev) => [...prev, newUser])
      return newUser
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to create user'
      setError(errorMsg)
      throw err
    }
  }, [])

  const updateUser = useCallback(async (userId: string, userData: UpdateUserRequest) => {
    try {
      const updated = await apiService.updateUser(userId, userData)
      setUsers((prev) => prev.map((u) => (u.user_id === userId ? updated : u)))
      return updated
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update user'
      setError(errorMsg)
      throw err
    }
  }, [])

  const deleteUser = useCallback(async (userId: string) => {
    try {
      await apiService.deleteUser(userId)
      setUsers((prev) => prev.filter((u) => u.user_id !== userId))
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete user'
      setError(errorMsg)
      throw err
    }
  }, [])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  return { users, loading, error, refetch: fetchUsers, createUser, updateUser, deleteUser }
}
